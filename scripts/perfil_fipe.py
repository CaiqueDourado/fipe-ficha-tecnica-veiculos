"""Profile of the exported vehicle tables: small CSVs to decide the build, without uploading the data.

    python perfil_fipe.py --raw D:\\fipe_raw --grupos D:\\portfolio_manter\\grupos.parquet

Writes <raw>/_perfil/*.csv. The small tables go whole (types, brands, models, FAQ titles, section titles,
IPVA rates); the large ones as counts, distributions and a random sample.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

QUERIES = {
    "contagens": """
        SELECT 'fp_ano' t, count(*) n FROM fp_ano UNION ALL SELECT 'ficha', count(*) FROM ficha
        UNION ALL SELECT 'ficha_detalhes', count(*) FROM ficha_detalhes UNION ALL SELECT 'ficha_preco', count(*) FROM ficha_preco
        UNION ALL SELECT 'modelo_produto', count(*) FROM modelo_produto UNION ALL SELECT 'fp_modelo', count(*) FROM fp_modelo
        UNION ALL SELECT 'fp_marca', count(*) FROM fp_marca""",
    # FIPE prices
    "ano_por_referencia": """
        SELECT referencia, referencia_ano, referencia_mes, count(*) linhas, count(DISTINCT codigo_fipe) codigos,
               sum(CASE WHEN valor = 0 OR valor IS NULL THEN 1 ELSE 0 END) valor_zero,
               sum(CASE WHEN _temp_alterado THEN 1 ELSE 0 END) temp_alterado,
               min(creationDate) primeira_gravacao, max(creationDate) ultima_gravacao
        FROM fp_ano GROUP BY ALL ORDER BY referencia_ano NULLS FIRST, referencia_mes""",
    "ano_modelo": """SELECT ano, count(*) linhas, sum(CASE WHEN _temp_alterado THEN 1 ELSE 0 END) temp_alterado
                     FROM fp_ano GROUP BY ano ORDER BY ano""",
    "combustivel": "SELECT combustivel, count(*) linhas FROM fp_ano GROUP BY 1 ORDER BY 2 DESC",
    "ano_duplicados": """
        SELECT count(*) chaves_repetidas, sum(n) linhas FROM (
          SELECT codigo_fipe, ano, combustivel, referencia, count(*) n FROM fp_ano GROUP BY ALL HAVING count(*) > 1)""",
    "ano_sem_modelo": """SELECT count(*) linhas, count(DISTINCT a.codigo_modelo) modelos FROM fp_ano a
                         LEFT JOIN fp_modelo m USING (codigo_modelo) WHERE m.codigo_modelo IS NULL""",
    "modelo_por_marca_tipo": """
        SELECT b.tipo, count(DISTINCT b.codigo_marca) marcas, count(m.codigo_modelo) modelos
        FROM fp_marca b LEFT JOIN fp_modelo m USING (codigo_marca) GROUP BY 1 ORDER BY 1""",
    "marca_codigo_repetido": """SELECT codigo_marca, count(*) n, string_agg(marca || ' (tipo ' || tipo || ')', ' | ') marcas
                                FROM fp_marca GROUP BY 1 HAVING count(*) > 1 ORDER BY 1""",
    # specifications (Mobiauto)
    "ficha_niveis": """
        SELECT tipo, regexp_extract(url, 'tabela-fipe/([a-z-]+)/', 1) segmento,
               length(url) - length(replace(url, '/', '')) barras, count(*) n,
               sum(CASE WHEN coalesce(codigoFipe, '') = '' THEN 1 ELSE 0 END) sem_codigo,
               sum(CASE WHEN crawleado THEN 1 ELSE 0 END) crawleados, min(data) primeira, max(data) ultima
        FROM ficha GROUP BY ALL ORDER BY barras, tipo""",
    "ficha_codigo_repetido": """SELECT count(*) codigos, sum(n) versoes FROM (
                                SELECT codigoFipe, count(*) n FROM ficha WHERE coalesce(codigoFipe,'') <> ''
                                GROUP BY 1 HAVING count(*) > 1)""",
    "ficha_url_repetida": "SELECT count(*) urls, sum(n) linhas FROM (SELECT url, count(*) n FROM ficha GROUP BY 1 HAVING count(*) > 1)",
    "ficha_codigo_na_fipe": """
        SELECT count(DISTINCT f.codigoFipe) codigos_ficha,
               count(DISTINCT CASE WHEN m.codigo_fipe IS NOT NULL THEN f.codigoFipe END) presentes_em_fp_modelo
        FROM ficha f LEFT JOIN (SELECT DISTINCT codigo_fipe FROM fp_ano) m ON m.codigo_fipe = f.codigoFipe
        WHERE coalesce(f.codigoFipe, '') <> ''""",
    "detalhes_chaves": """SELECT tipo, chave, count(*) n, count(DISTINCT valor) valores_distintos,
                          any_value(valor) exemplo FROM ficha_detalhes GROUP BY 1, 2 ORDER BY 1, 3 DESC""",
    "detalhes_valores_suspeitos": """
        SELECT CASE WHEN valor LIKE '%<%' THEN 'html' WHEN lower(valor) LIKE '%undefined%' THEN 'undefined'
                    WHEN coalesce(trim(valor), '') = '' THEN 'vazio' WHEN valor LIKE '%N/C%' THEN 'N/C'
                    WHEN valor LIKE '%Ã%' THEN 'mojibake' ELSE 'ok' END problema, count(*) n, any_value(valor) exemplo
        FROM ficha_detalhes GROUP BY 1 ORDER BY 2 DESC""",
    "detalhes_por_versao": """SELECT n_chaves, count(*) versoes FROM (
                              SELECT idCrawlerFichaTecnica, count(*) n_chaves FROM ficha_detalhes GROUP BY 1)
                              GROUP BY 1 ORDER BY 1""",
    "detalhes_amostra": """SELECT d.*, f.nome, f.url FROM ficha_detalhes d JOIN ficha f ON f.id = d.idCrawlerFichaTecnica
                           WHERE d.idCrawlerFichaTecnica IN (SELECT id FROM ficha WHERE id IN
                             (SELECT DISTINCT idCrawlerFichaTecnica FROM ficha_detalhes) USING SAMPLE 40 ROWS (reservoir, 7))
                           ORDER BY d.idCrawlerFichaTecnica, d.id""",
    "preco": """SELECT count(*) linhas, sum(CASE WHEN preco = 0 THEN 1 ELSE 0 END) zero, min(preco) FILTER (WHERE preco > 0) minimo,
                max(preco) maximo, min(data) primeira, max(data) ultima, count(DISTINCT idCrawlerFichaTecnica) versoes
                FROM ficha_preco""",
    # vehicle x product matches (B10)
    "produto_por_tipo": """SELECT tipo, count(*) linhas, count(DISTINCT codigo_modelo) modelos,
                           count(DISTINCT productGroupId) grupos, count(DISTINCT chave) chaves
                           FROM modelo_produto GROUP BY 1 ORDER BY 2 DESC""",
    "produto_pares": """SELECT count(*) linhas, count(DISTINCT (productGroupId, codigo_modelo)) pares,
                        count(DISTINCT productGroupId) grupos, count(DISTINCT codigo_modelo) modelos FROM modelo_produto""",
    "produto_chaves_mais_largas": """SELECT chave, count(DISTINCT productGroupId) grupos, count(DISTINCT codigo_modelo) modelos
                                     FROM modelo_produto GROUP BY 1 ORDER BY 2 DESC LIMIT 300""",
    "produto_grupos_por_modelo": """SELECT CASE WHEN g < 10 THEN '1-9' WHEN g < 100 THEN '10-99' WHEN g < 1000 THEN '100-999'
                                    WHEN g < 10000 THEN '1000-9999' ELSE '10000+' END faixa, count(*) modelos
                                    FROM (SELECT codigo_modelo, count(DISTINCT productGroupId) g FROM modelo_produto GROUP BY 1)
                                    GROUP BY 1 ORDER BY min(g)""",
}

WHOLE = ["fp_tipo", "fp_marca", "fp_modelo", "ficha_titulo_faq", "ficha_titulo_texto", "aliquota_ipva"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--grupos", type=Path, help="the catalog's grupos.parquet, to check the product group ids")
    a = ap.parse_args()
    out = a.raw / "_perfil"
    out.mkdir(exist_ok=True)
    con = duckdb.connect()
    for folder in sorted(p for p in a.raw.iterdir() if p.is_dir() and not p.name.startswith("_")):
        con.execute(f"CREATE VIEW {folder.name} AS SELECT * FROM read_parquet('{(folder / '*.parquet').as_posix()}')")
    for name in WHOLE:
        con.execute(f"COPY {name} TO '{(out / (name + '.csv')).as_posix()}' (HEADER)")
    queries = dict(QUERIES)
    if a.grupos:
        con.execute(f"CREATE VIEW grupos AS SELECT * FROM read_parquet('{a.grupos.as_posix()}')")
        queries["produto_grupos_no_catalogo"] = """
            SELECT count(DISTINCT m.productGroupId) grupos_no_casamento,
                   count(DISTINCT CASE WHEN g.id IS NOT NULL THEN m.productGroupId END) existem_no_catalogo
            FROM modelo_produto m LEFT JOIN grupos g ON g.id = m.productGroupId"""
        queries["produto_amostra"] = """
            SELECT m.chave, m.tipo, m.codigo_modelo, mo.modelo, m.productGroupId, g.short_name
            FROM modelo_produto m LEFT JOIN fp_modelo mo USING (codigo_modelo) LEFT JOIN grupos g ON g.id = m.productGroupId
            USING SAMPLE 3000 ROWS (reservoir, 7)"""
    for name, sql in queries.items():
        try:
            con.execute(f"COPY ({sql}) TO '{(out / (name + '.csv')).as_posix()}' (HEADER)")
            print(f"ok    {name}")
        except duckdb.Error as e:
            print(f"ERRO  {name}: {str(e).splitlines()[0]}")
    print(f"-> {out}  (compacte a pasta _perfil e me envie)")


if __name__ == "__main__":
    main()
