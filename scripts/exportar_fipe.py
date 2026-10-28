"""Export the vehicle databases (bases 7 FIPE and 8 vehicle specifications, plus the vehicle x product
matches) from the author's SQL Server into Parquet files (raw layer).

Same exporter as the catalog and the reviews: keyset pagination, one Parquet file per block, resumable.

    python -m pip install --user pyodbc pyarrow
    python exportar_fipe.py --out D:\\fipe_raw              # every table (~1 GB free)
    python exportar_fipe.py --out D:\\fipe_raw --status     # progress only

Windows authentication, no password in the script.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

DB = "fipe.dbo"


@dataclass
class Table:
    name: str
    source: str              # schema-qualified table
    columns: list[tuple[str, str, pa.DataType]]  # (SQL expression, output name, Arrow type)
    block: int = 500_000
    small: bool = False      # exported whole, in one file
    key: str = "id"          # column used for keyset pagination

    @property
    def select(self) -> str:
        return ", ".join(f"{expr} AS [{name}]" for expr, name, _ in self.columns)

    @property
    def schema(self) -> pa.Schema:
        return pa.schema([(name, kind) for _, name, kind in self.columns])


S, I, B, F, T = pa.string(), pa.int64(), pa.bool_(), pa.float64(), pa.timestamp("ms")


TABLES = [
    Table("fp_tipo", f"{DB}.fp_tipo", [("id", "id", I), ("tipo", "tipo", S), ("slug", "slug", S)], small=True),
    Table("fp_marca", f"{DB}.fp_marca", [
        ("id", "id", I), ("codigo_marca", "codigo_marca", I), ("marca", "marca", S), ("tipo", "tipo", I),
        ("_id", "_id", I), ("slug", "slug", S), ("creationDate", "creationDate", T)], small=True),
    Table("fp_modelo", f"{DB}.fp_modelo", [
        ("_id", "_id", I), ("codigo_modelo", "codigo_modelo", I), ("codigo_marca", "codigo_marca", I),
        ("codigo_fipe", "codigo_fipe", S), ("modelo", "modelo", S), ("modelo_curto", "modelo_curto", S),
        ("modelo_primeiro_nome", "modelo_primeiro_nome", S),
        ("modelo_primeiro_segundo_nome", "modelo_primeiro_segundo_nome", S),
        ("modelo_primeiro_nome_marca", "modelo_primeiro_nome_marca", S), ("slug", "slug", S),
        ("creationDate", "creationDate", T)], small=True),
    Table("fp_ano", f"{DB}.fp_ano", [
        ("id_ano", "id_ano", I), ("codigo_modelo", "codigo_modelo", I), ("codigo_fipe", "codigo_fipe", S),
        ("ano", "ano", S), ("combustivel", "combustivel", S), ("CAST(valor AS float)", "valor", F),
        ("atualizado", "atualizado", I), ("referencia", "referencia", S), ("_id", "_id", I),
        ("referencia_ano", "referencia_ano", I), ("referencia_mes", "referencia_mes", I),
        ("_temp_alterado", "_temp_alterado", B), ("creationDate", "creationDate", T)], key="id_ano"),
    Table("ficha", f"{DB}.CrawlerFichaTecnica", [
        ("id", "id", I), ("url", "url", S), ("tipo", "tipo", S), ("crawleado", "crawleado", B),
        ("codigoFipe", "codigoFipe", S), ("data", "data", T), ("idPai", "idPai", I), ("nome", "nome", S)]),
    Table("ficha_detalhes", f"{DB}.CrawlerFichaTecnicaDetalhes", [
        ("id", "id", I), ("idCrawlerFichaTecnica", "idCrawlerFichaTecnica", I), ("chave", "chave", S),
        ("valor", "valor", S), ("tipo", "tipo", S)], block=1_000_000),
    Table("ficha_preco", f"{DB}.CrawlerFichaTecnicaPreco", [
        ("id", "id", I), ("idCrawlerFichaTecnica", "idCrawlerFichaTecnica", I),
        ("CAST(preco AS float)", "preco", F), ("data", "data", T)]),
    Table("ficha_titulo_faq", f"{DB}.CrawlerFichaTecnicaDetalhesTituloFAQ", [
        ("id", "id", I), ("chave", "chave", S), ("titulo", "titulo", S)], small=True),
    Table("ficha_titulo_texto", f"{DB}.CrawlerFichaTecnicaDetalhesTituloTextoSobre", [
        ("id", "id", I), ("tipo", "tipo", S), ("titulo", "titulo", S), ("textoIntrodutorio", "textoIntrodutorio", S)],
        small=True),
    Table("aliquota_ipva", f"{DB}.AliquotaIPVA", [
        ("id", "id", I), ("estado", "estado", S), ("tipo", "tipo", S), ("CAST(aliquota AS float)", "aliquota", F),
        ("pronome", "pronome", S)], small=True),
    Table("modelo_produto", f"{DB}.fp_modeloRelProductGroup", [
        ("id", "id", I), ("chave", "chave", S), ("productGroupId", "productGroupId", I),
        ("codigo_modelo", "codigo_modelo", I), ("tipo", "tipo", S), ("creationDate", "creationDate", T)],
        block=2_000_000),
]
BY_NAME = {t.name: t for t in TABLES}


BROKEN_TEXT = {"values": 0}


def decode_utf16(raw: bytes | None) -> str | None:
    """nvarchar comes as UTF-16. Some scraped texts hold half of an emoji (a lone surrogate), which
    is invalid UTF-16 and makes pyodbc fail; those characters become U+FFFD and are counted."""
    if raw is None:
        return None
    try:
        return raw.decode("utf-16-le")
    except UnicodeDecodeError:
        BROKEN_TEXT["values"] += 1
        return raw.decode("utf-16-le", errors="replace")


def connect(server: str):
    import pyodbc

    connection = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};Trusted_Connection=yes",
        autocommit=True,
    )
    for sql_type in (pyodbc.SQL_WVARCHAR, pyodbc.SQL_WCHAR, pyodbc.SQL_WLONGVARCHAR):
        connection.add_output_converter(sql_type, decode_utf16)
    return connection


def last_id(folder: Path) -> int:
    """Highest id already exported, read from the file names (part-<first>-<last>.parquet)."""
    ends = [int(p.stem.rsplit("-", 1)[1]) for p in folder.glob("part-*.parquet") if p.stem != "part-all"]
    return max(ends, default=0)


def estimated_rows(cursor, table: Table) -> int:
    """Row count from catalog metadata: instant, unlike COUNT(*) on hundreds of millions of rows."""
    db, schema, name = table.source.split(".")
    cursor.execute(
        f"SELECT SUM(p.rows) FROM {db}.sys.partitions p JOIN {db}.sys.objects o ON o.object_id = p.object_id "
        f"WHERE o.name = ? AND p.index_id IN (0, 1)", name)
    return int(cursor.fetchone()[0] or 0)


def to_arrow(rows: list, table: Table) -> pa.Table:
    columns = list(zip(*rows)) if rows else [[] for _ in table.columns]
    arrays = [pa.array(list(values), type=kind) for values, (_, _, kind) in zip(columns, table.columns)]
    return pa.Table.from_arrays(arrays, schema=table.schema)


def export(cursor, table: Table, out: Path) -> None:
    folder = out / table.name
    folder.mkdir(parents=True, exist_ok=True)
    if table.small:
        cursor.execute(f"SELECT {table.select} FROM {table.source} WITH (NOLOCK)")
        rows = cursor.fetchall()
        pq.write_table(to_arrow(rows, table), folder / "part-all.parquet", compression="zstd")
        print(f"== {table.name}: {len(rows):,} rows")
        return
    start = last_id(folder)
    total = estimated_rows(cursor, table)
    done = sum(pq.ParquetFile(p).metadata.num_rows for p in folder.glob("part-*.parquet"))
    print(f"== {table.name}: about {total:,} rows, {done:,} already exported, resuming after id {start:,}")
    query = (f"SELECT TOP ({table.block}) {table.select} FROM {table.source} WITH (NOLOCK) "
             f"WHERE {table.key} > ? ORDER BY {table.key}")
    began = time.time()
    exported = 0
    while True:
        cursor.execute(query, start)
        rows = cursor.fetchall()
        if not rows:
            break
        first, last = rows[0][0], rows[-1][0]  # the key is the first column
        target = folder / f"part-{first:012d}-{last:012d}.parquet"
        temporary = target.with_suffix(".tmp")
        pq.write_table(to_arrow(rows, table), temporary, compression="zstd")
        temporary.replace(target)  # a block is either fully written or absent
        start = last
        exported += len(rows)
        done += len(rows)
        rate = exported / max(time.time() - began, 1)
        left = max(total - done, 0) / rate if rate else 0
        print(f"   {done:,}/{total:,} rows  ({rate:,.0f}/s, about {left / 60:,.0f} min left)", flush=True)
        if len(rows) < table.block:
            break
    print(f"   {table.name} finished: {done:,} rows in {folder}")
    if BROKEN_TEXT["values"]:
        print(f"   {BROKEN_TEXT['values']:,} text values had broken characters (half emojis), replaced by U+FFFD")
        BROKEN_TEXT["values"] = 0


def status(out: Path) -> None:
    for table in TABLES:
        files = list((out / table.name).glob("part-*.parquet"))
        rows = sum(pq.ParquetFile(p).metadata.num_rows for p in files)
        size = sum(p.stat().st_size for p in files) / 1e9
        print(f"{table.name:16} {len(files):5} files {rows:15,} rows {size:8.2f} GB")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, type=Path, help="folder for the Parquet files (needs ~1 GB free)")
    parser.add_argument("--tables", nargs="*", default=[t.name for t in TABLES], choices=list(BY_NAME))
    parser.add_argument("--server", default="localhost")
    parser.add_argument("--status", action="store_true", help="show what was exported and stop")
    args = parser.parse_args()
    if args.status:
        status(args.out)
        return
    cursor = connect(args.server).cursor()
    try:
        for name in args.tables:
            export(cursor, BY_NAME[name], args.out)
    except KeyboardInterrupt:
        print("\nStopped. Run the same command again to resume.", file=sys.stderr)


if __name__ == "__main__":
    main()
