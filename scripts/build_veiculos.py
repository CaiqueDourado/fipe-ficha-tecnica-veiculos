"""Build the vehicle dataset from the raw export (exportar_fipe.py) and the FIPE API collection (coletor_fipe.py).

    python build_veiculos.py --raw D:\\fipe_raw --out D:\\fipe_out

Writes <out>/kaggle/*.parquet (full), <out>/sample/*.csv (GitHub sample) and <out>/stats.json.

Tables
    marcas                 FIPE brands: code, name, vehicle type
    modelos                FIPE models (versions): code, brand, FIPE code, name and the short names used for matching
    precos                 FIPE prices: one row per reference month, FIPE code, model year and fuel
    fichas                 vehicle specifications (Mobiauto, September 2022), one row per version, wide
    ficha_caracteristicas  the same specifications in long form (section, key, value)
    ficha_titulos          section titles and FAQ questions used to turn the specifications into text
    veiculo_produto        vehicle model x catalog product group, matched by name, with a warning level
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import duckdb

TIPO = "CASE {} WHEN 1 THEN 'carro' WHEN 2 THEN 'moto' WHEN 3 THEN 'caminhao' END"
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
         "novembro", "dezembro"]


LOST_BYTE = {"Ãlcool": "Álcool", "Ã\xa0": "à", "Ã ": "à "}  # Á and à lose their second byte (0x81, 0xA0) when mangled


def fix_text(s: str | None) -> str | None:
    """Undo UTF-8 read as Latin-1 ("Ãlcool", "Ã  disco"), the only encoding damage found in the profile."""
    if s is None or "Ã" not in s:
        return s
    for bad, good in LOST_BYTE.items():
        s = s.replace(bad, good)
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return s


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--sample-models", type=int, default=300, help="models in the GitHub sample")
    a = ap.parse_args()
    k, s = a.out / "kaggle", a.out / "sample"
    k.mkdir(parents=True, exist_ok=True)
    s.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.create_function("fix_text", fix_text, ["VARCHAR"], "VARCHAR", null_handling="special")
    for folder in sorted(p for p in a.raw.iterdir() if p.is_dir() and not p.name.startswith("_") and p.name != "api"):
        con.execute(f"CREATE VIEW raw_{folder.name} AS SELECT * FROM read_parquet('{(folder / '*.parquet').as_posix()}')")
    stats: dict = {}

    # ---------- FIPE API collection (latest months), flattened ----------
    api = sorted((a.raw / "api").glob("*/precos.jsonl")) if (a.raw / "api").exists() else []
    con.execute("""CREATE TABLE api_precos (referencia DATE, codigo_tabela INT, tipo INT, codigo_marca INT, marca VARCHAR,
                   codigo_modelo INT, modelo VARCHAR, codigo_fipe VARCHAR, ano_modelo INT, combustivel VARCHAR,
                   valor DOUBLE, data_consulta VARCHAR)""")
    rows = []
    for path in api:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            p, q = r["resposta"], r["pedido"]
            if not p or "Valor" not in p:
                continue
            mes, ano = p["MesReferencia"].strip().rsplit(" de ", 1)
            rows.append((f"{ano}-{MESES.index(mes.strip().lower()) + 1:02d}-01", q["codigoTabelaReferencia"],
                         q["codigoTipoVeiculo"], int(q["codigoMarca"]), p["Marca"], int(q["codigoModelo"]),
                         p["Modelo"].strip(), p["CodigoFipe"], int(p["AnoModelo"]), p["Combustivel"],
                         float(re.sub(r"[^\d,]", "", p["Valor"]).replace(",", ".")), p.get("DataConsulta")))
    if rows:
        con.executemany("INSERT INTO api_precos VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    stats["api_precos"] = len(rows)

    # ---------- marcas ----------
    con.execute(f"""CREATE TABLE marcas AS
        SELECT codigo_marca, any_value(marca) marca, any_value({TIPO.format('tipo')}) tipo_veiculo, any_value(slug) slug,
               'dump' fonte
        FROM raw_fp_marca GROUP BY codigo_marca""")
    con.execute(f"""INSERT INTO marcas SELECT codigo_marca, any_value(marca), any_value({TIPO.format('tipo')}),
                    NULL, 'fipe_api' FROM api_precos WHERE codigo_marca NOT IN (SELECT codigo_marca FROM marcas)
                    GROUP BY codigo_marca""")

    # ---------- modelos ----------
    con.execute("""CREATE TABLE modelos AS
        SELECT m.codigo_modelo, m.codigo_marca, b.tipo_veiculo, m.codigo_fipe, trim(m.modelo) modelo,
               nullif(trim(m.modelo_curto), '') modelo_curto, nullif(trim(m.modelo_primeiro_nome), '') primeiro_nome,
               nullif(trim(m.modelo_primeiro_segundo_nome), '') primeiro_segundo_nome,
               nullif(trim(m.modelo_primeiro_nome_marca), '') primeiro_nome_marca, m.slug, 'dump' fonte
        FROM raw_fp_modelo m LEFT JOIN marcas b USING (codigo_marca)""")
    con.execute("""INSERT INTO modelos
        SELECT codigo_modelo, any_value(codigo_marca), any_value(CASE tipo WHEN 1 THEN 'carro' WHEN 2 THEN 'moto'
               ELSE 'caminhao' END), any_value(codigo_fipe), any_value(modelo), NULL, NULL, NULL, NULL, NULL, 'fipe_api'
        FROM api_precos WHERE codigo_modelo NOT IN (SELECT codigo_modelo FROM modelos) GROUP BY codigo_modelo""")

    # ---------- precos ----------
    # dump: the zero-km year (32000) had been replaced by max(year)+1 and flagged in _temp_alterado;
    # those rows become zero_km with no model year. Duplicates keep the last loaded row.
    con.execute("""CREATE TABLE precos AS
        WITH d AS (
          SELECT make_date(referencia_ano, referencia_mes, 1) referencia, codigo_fipe, codigo_modelo,
                 CASE WHEN coalesce(_temp_alterado, false) THEN NULL ELSE TRY_CAST(ano AS INT) END ano_modelo,
                 coalesce(_temp_alterado, false) zero_km, fix_text(combustivel) combustivel, valor, 'dump' fonte,
                 row_number() OVER (PARTITION BY referencia_ano, referencia_mes, codigo_fipe, ano, combustivel
                                    ORDER BY id_ano DESC) rn
          FROM raw_fp_ano WHERE referencia_ano IS NOT NULL AND valor > 0)
        SELECT referencia, codigo_fipe, codigo_modelo, ano_modelo, zero_km, combustivel, valor, fonte FROM d WHERE rn = 1""")
    stats["dump_precos_descartados"] = con.execute(
        "SELECT (SELECT count(*) FROM raw_fp_ano) - (SELECT count(*) FROM precos)").fetchone()[0]
    con.execute("""INSERT INTO precos
        SELECT referencia, codigo_fipe, codigo_modelo, CASE WHEN ano_modelo = 32000 THEN NULL ELSE ano_modelo END,
               ano_modelo = 32000, combustivel, valor, 'fipe_api'
        FROM api_precos WHERE referencia NOT IN (SELECT DISTINCT referencia FROM precos WHERE fonte = 'dump')""")

    # ---------- fichas (Mobiauto) ----------
    con.execute("""CREATE TABLE ficha_no AS
        SELECT * FROM (SELECT *, row_number() OVER (PARTITION BY url ORDER BY id) rn FROM raw_ficha) WHERE rn = 1""")
    con.execute("""CREATE TABLE versoes AS
        SELECT v.id id_versao, CASE split_part(v.url, '/', 5) WHEN 'motos' THEN 'moto' ELSE 'carro' END tipo_veiculo,
               b.nome marca, m.nome modelo, TRY_CAST(split_part(v.url, '/', 8) AS INT) ano_modelo, split_part(v.url, '/', 8) ano_url, v.nome versao,
               CASE WHEN regexp_matches(trim(v.codigoFipe), '^[0-9]{7}$')           -- 6 of 34,788 came without the hyphen
                    THEN substr(trim(v.codigoFipe), 1, 6) || '-' || substr(trim(v.codigoFipe), 7, 1)
                    ELSE nullif(trim(v.codigoFipe), '') END codigo_fipe, nullif(p.preco, 0) preco_mobiauto,
               CAST(coalesce(p.data_preco, v."data") AS DATE) data_coleta, v.url
        FROM ficha_no v
        JOIN ficha_no y ON y.id = v.idPai JOIN ficha_no m ON m.id = y.idPai JOIN ficha_no b ON b.id = m.idPai
        LEFT JOIN (SELECT idCrawlerFichaTecnica, any_value(preco) AS preco, min("data") AS data_preco FROM raw_ficha_preco GROUP BY 1) p
               ON p.idCrawlerFichaTecnica = v.id
        WHERE v.tipo = 'Carro'""")
    con.execute("""CREATE TABLE ficha_caracteristicas AS
        SELECT id_versao, secao, chave, valor FROM (
          SELECT d.idCrawlerFichaTecnica id_versao,
                 CASE d.tipo WHEN 'som' THEN 'Som' ELSE d.tipo END secao, trim(d.chave) chave,
                 nullif(trim(fix_text(d.valor)), '') valor,
                 row_number() OVER (PARTITION BY d.idCrawlerFichaTecnica, d.tipo, d.chave ORDER BY d.id) rn
          FROM raw_ficha_detalhes d WHERE d.idCrawlerFichaTecnica IN (SELECT id_versao FROM versoes))
        WHERE rn = 1""")
    chaves = con.execute("""SELECT secao, chave, bool_and(valor IS NULL OR valor IN ('Sim', 'Não')) booleana
                            FROM ficha_caracteristicas GROUP BY 1, 2 ORDER BY 1, 2""").fetchall()

    def col(secao: str, chave: str) -> str:
        import unicodedata
        name = unicodedata.normalize("NFKD", f"{chave}").encode("ascii", "ignore").decode().lower()
        name = re.sub(r"\(([^)]*)\)", r"_\1", name)
        return re.sub(r"[^a-z0-9]+", "_", name).strip("_")

    names = {}
    for secao, chave, boolean in chaves:
        n = col(secao, chave)
        if n in names.values():
            n = col("", secao) + "_" + n
        names[(secao, chave)] = (n, boolean)
    selects = []
    for (secao, chave), (n, boolean) in names.items():
        sel = f"max(valor) FILTER (WHERE secao = '{secao}' AND chave = '{chave.replace(chr(39), chr(39) * 2)}')"
        selects.append(f"CASE {sel} WHEN 'Sim' THEN true WHEN 'Não' THEN false END AS {n}" if boolean else f"{sel} AS {n}")
    con.execute(f"""CREATE TABLE fichas AS SELECT v.*, {', '.join(selects)}
                    FROM versoes v LEFT JOIN ficha_caracteristicas c USING (id_versao) GROUP BY ALL""")
    con.execute("""CREATE TABLE ficha_titulos AS
        SELECT 'secao' tipo, CASE tipo WHEN 'som' THEN 'Som' ELSE tipo END secao, NULL chave,
               CASE titulo WHEN 'Audio e Multimídia' THEN 'Áudio e Multimídia' ELSE titulo END titulo,
               textoIntrodutorio texto_introdutorio FROM raw_ficha_titulo_texto
        UNION ALL SELECT 'faq', NULL, chave, titulo, NULL FROM raw_ficha_titulo_faq""")

    # ---------- veiculo_produto (B10) ----------
    con.execute("""CREATE TABLE veiculo_produto AS
        WITH k AS (SELECT chave, count(DISTINCT productGroupId) produtos_da_chave,
                          count(DISTINCT codigo_modelo) modelos_da_chave FROM raw_modelo_produto GROUP BY chave)
        SELECT r.codigo_modelo, r.productGroupId group_id, r.chave, r.tipo nivel, k.produtos_da_chave,
               k.modelos_da_chave,
               CASE WHEN k.produtos_da_chave >= 1000 THEN 'baixa' WHEN k.produtos_da_chave >= 100 THEN 'media'
                    ELSE 'alta' END confianca
        FROM raw_modelo_produto r JOIN k USING (chave)""")

    # ---------- write ----------
    order = {"marcas": "codigo_marca", "modelos": "codigo_modelo", "precos": "referencia, codigo_fipe, ano_modelo",
             "fichas": "id_versao", "ficha_caracteristicas": "id_versao, secao, chave", "ficha_titulos": "tipo, titulo",
             "veiculo_produto": "codigo_modelo, group_id"}
    for t, o in order.items():
        con.execute(f"COPY (SELECT * FROM {t} ORDER BY {o}) TO '{(k / (t + '.parquet')).as_posix()}' "
                    f"(FORMAT parquet, COMPRESSION zstd)")
        stats[t] = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    # sample: whole small tables; the rest for a random set of models (and their specs and products)
    con.execute(f"""CREATE TABLE amostra AS SELECT codigo_modelo, codigo_fipe FROM modelos
                    USING SAMPLE {a.sample_models} ROWS (reservoir, 2026)""")
    samples = {
        "marcas": "SELECT * FROM marcas ORDER BY codigo_marca",
        "modelos": "SELECT * FROM modelos WHERE codigo_modelo IN (SELECT codigo_modelo FROM amostra) ORDER BY 1",
        "precos": "SELECT * FROM precos WHERE codigo_modelo IN (SELECT codigo_modelo FROM amostra) ORDER BY referencia, codigo_fipe, ano_modelo",
        "fichas": "SELECT * FROM fichas WHERE codigo_fipe IN (SELECT codigo_fipe FROM amostra) ORDER BY id_versao",
        "ficha_caracteristicas": """SELECT * FROM ficha_caracteristicas WHERE id_versao IN
                                    (SELECT id_versao FROM versoes WHERE codigo_fipe IN (SELECT codigo_fipe FROM amostra)) ORDER BY 1, 2, 3""",
        "ficha_titulos": "SELECT * FROM ficha_titulos ORDER BY tipo, titulo",
        "veiculo_produto": """SELECT * FROM veiculo_produto WHERE codigo_modelo IN (SELECT codigo_modelo FROM amostra)
                              USING SAMPLE 20000 ROWS (reservoir, 2026)""",
    }
    for t, q in samples.items():
        con.execute(f"COPY ({q}) TO '{(s / (t + '_sample.csv')).as_posix()}' (HEADER)")
    stats["referencias"] = [str(r[0]) for r in con.execute(
        "SELECT DISTINCT referencia FROM precos ORDER BY 1").fetchall()]
    stats["veiculo_produto_confianca"] = dict(con.execute(
        "SELECT confianca, count(*) FROM veiculo_produto GROUP BY 1").fetchall())
    stats["fichas_por_tipo"] = dict(con.execute("SELECT tipo_veiculo, count(*) FROM fichas GROUP BY 1").fetchall())
    stats["precos_por_fonte"] = dict(con.execute("SELECT fonte, count(*) FROM precos GROUP BY 1").fetchall())
    stats["precos_zero_km"] = con.execute("SELECT count(*) FROM precos WHERE zero_km").fetchone()[0]
    stats["fichas_colunas"] = len(names)
    stats["fichas_sem_ano"] = dict(con.execute(
        "SELECT ano_url, count(*) FROM fichas WHERE ano_modelo IS NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10").fetchall())
    stats["fichas_sem_codigo_fipe"] = con.execute("SELECT count(*) FROM fichas WHERE codigo_fipe IS NULL").fetchone()[0]
    stats["fichas_sem_preco"] = con.execute("SELECT count(*) FROM fichas WHERE preco_mobiauto IS NULL").fetchone()[0]
    stats["precos_por_tipo"] = dict(con.execute("""SELECT m.tipo_veiculo, count(*) FROM precos p
        LEFT JOIN modelos m USING (codigo_modelo) GROUP BY 1""").fetchall())
    stats["caracteristicas_vazias"] = con.execute(
        "SELECT count(*) FROM ficha_caracteristicas WHERE valor IS NULL").fetchone()[0]
    (a.out / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({x: y for x, y in stats.items() if x != "referencias"}, ensure_ascii=False, indent=1, default=str))
    print(f"{len(stats['referencias'])} reference months: {stats['referencias'][0]} .. {stats['referencias'][-1]}")


if __name__ == "__main__":
    main()
