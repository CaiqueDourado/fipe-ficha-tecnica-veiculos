# Tabela FIPE e ficha técnica de veículos

[![validate](https://github.com/CaiqueDourado/fipe-ficha-tecnica-veiculos/actions/workflows/validate.yml/badge.svg)](https://github.com/CaiqueDourado/fipe-ficha-tecnica-veiculos/actions/workflows/validate.yml)
[![Dados: CC BY 4.0](https://img.shields.io/badge/dados-CC%20BY%204.0-lightgrey.svg)](LICENSE-DATA.md)
[![Código: MIT](https://img.shields.io/badge/c%C3%B3digo-MIT-blue.svg)](LICENSE)
[![Kaggle](https://img.shields.io/badge/Kaggle-dataset-20BEFF.svg)](https://www.kaggle.com/datasets/caiquedourado/fipe-ficha-tecnica-veiculos)

[Read in English](README.md)

![Tabela FIPE e ficha técnica de veículos](docs/img/cover.pt-BR.png)

Dados de veículos do Brasil em três partes:

- **Preços FIPE**, a referência mensal de preços de veículos usados e novos no Brasil. São 1,65 milhão de
  preços de carros, motos e caminhões, de janeiro de 2020 a fevereiro de 2023, mais outubro de 2026,
  coletado no site oficial da FIPE.
- **Ficha técnica** de 37.794 versões de carros e motos: motor, potência, consumo, medidas e 58 itens de
  sim ou não (airbags, ABS, ar-condicionado...). Veio das páginas da tabela FIPE do Mobiauto, em setembro
  de 2022.
- **Casamento veículo × produto**: 25,5 milhões de pares candidatos entre modelos da FIPE e os grupos de
  produto da [base do catálogo de e-commerce](https://github.com/CaiqueDourado/catalogo-produtos-ecommerce-brasil)
  (tapetes, palhetas, capas...). Cada par tem um nível de alerta, porque a maioria está errada.

| Arquivo | Linhas | O que tem |
|---|---:|---|
| `marcas` | 245 | marcas da FIPE e tipo de veículo |
| `modelos` | 11.948 | modelos (versões) da FIPE, código FIPE e nomes curtos usados no casamento |
| `precos` | 1.653.840 | preço por mês, código FIPE, ano-modelo e combustível |
| `fichas` | 37.794 | uma linha por versão, com 81 colunas de ficha técnica |
| `ficha_caracteristicas` | 2.704.962 | a mesma ficha em formato longo |
| `ficha_titulos` | 87 | títulos de seção e perguntas de FAQ para escrever texto a partir da ficha |
| `veiculo_produto` | 25.456.723 | modelo de veículo × grupo de produto, com `confianca` (alta, media, baixa) |

Os arquivos completos (Parquet) estão no [Kaggle](https://www.kaggle.com/datasets/caiquedourado/fipe-ficha-tecnica-veiculos).
Este repositório tem os scripts, a documentação e a pasta `sample/`, com todas as linhas de 300 modelos
sorteados.

## Um carro nas três partes

**Ford EcoSport Freestyle 1.6 16V Flex 2012** (código FIPE `003367-7`, modelo 6157), em `sample/`:

| | |
|---|---|
| FIPE, janeiro de 2020 | R$ 33.276 |
| FIPE, janeiro de 2022 | R$ 41.247 |
| FIPE, fevereiro de 2023 | R$ 42.026 |
| FIPE, outubro de 2026 | R$ 41.862 |
| Mobiauto, setembro de 2022 | R$ 41.403 |
| Ficha técnica | 115 cv (etanol) / 110 cv (gasolina), porta-malas de 296 l, airbag do motorista e do passageiro, ABS |
| Produtos casados por "EcoSport" | todos com `confianca = baixa`: a chave casou 12.656 produtos |

Um carro que tinha oito anos em 2020 ficou 24% mais caro em dois anos, e em outubro de 2026 ainda valia
26% a mais que em janeiro de 2020. Não foi exceção:

![Preços de usados, janeiro de 2020 = 100](docs/img/used-prices.pt-BR.png)

Carros, motos e caminhões usados, do mesmo código FIPE e ano-modelo, subiram de 20% a 28% entre meados de
2021 e meados de 2022, quando faltavam veículos novos. Em fevereiro de 2023, os preços ainda não tinham
voltado.

Quanto do preço de zero km um carro mantém, por idade, em outubro de 2026 (mediana de 917 carros com preço
de zero km e preços de usado do mesmo código FIPE):

![Parte do preço de zero km por idade](docs/img/depreciation.pt-BR.png)

86% no primeiro ano, 57% depois de cinco anos, 39% depois de dez e 28% depois de quinze.

## De onde vieram os dados

![Fontes e tabelas](docs/img/flow.pt-BR.png)

- **2020–2023:** dumps mensais da tabela FIPE, carregados no SQL Server do autor para os sites de veículos
  dele (preços, "quanto custa um X usado", autopeças por modelo).
- **2026:** para atualizar a série, o projeto passou por três fontes:
  1. Primeiro, os arquivos JSON do **g1** que alimentam a página de preços da Globo. Eles pararam por volta
     de 2022 e não trazem o mês de referência.
  2. Depois, a **BrasilAPI**. A busca de preços dela estava falhando do lado da FIPE.
  3. Por fim, a **API JSON do site oficial da FIPE**, que é a fonte que as duas anteriores repassam. Ficou
     esta.

  O coletor pode parar e continuar de onde parou, e respeita o limite do site: quando recebe HTTP 429, vai
  mais devagar.
- **Ficha técnica:** um crawler nas páginas da tabela FIPE do Mobiauto, em setembro de 2022. Os itens de
  sim ou não são ícones na página, e o crawler distinguia "sim" de "não" pelo desenho (path SVG) de cada
  ícone.
- **Veículo × produto:** é o casamento por nome feito pelo autor em 2022. Os nomes dos modelos da FIPE
  foram procurados dentro dos nomes dos produtos do catálogo. A tabela está publicada como rodou, com a
  abrangência de cada chave.

Detalhes na [metodologia](docs/methodology.md) (em inglês). O que está errado e o que foi corrigido está no
[relatório de qualidade](docs/data-quality.md).

## Como usar

```python
import pandas as pd

precos = pd.read_csv("sample/precos_sample.csv", dtype={"codigo_fipe": str}, parse_dates=["referencia"])
fichas = pd.read_csv("sample/fichas_sample.csv", dtype={"codigo_fipe": str})

# histórico de preço de uma versão e ano-modelo
precos.query("codigo_fipe == '003367-7' and ano_modelo == 2012").set_index("referencia").valor

# ficha técnica ao lado do preço FIPE do mesmo código e ano
ultimo = precos[precos.referencia == "2026-10-01"]
fichas.merge(ultimo, on=["codigo_fipe", "ano_modelo"])[["marca", "versao", "ano_modelo", "potencia_cv", "valor"]]
```

```sql
-- DuckDB, arquivos completos do Kaggle: só os casamentos confiáveis
SELECT m.modelo, v.group_id, v.chave
FROM 'veiculo_produto.parquet' v JOIN 'modelos.parquet' m USING (codigo_modelo)
WHERE v.confianca = 'alta';
```

`group_id` liga com a tabela `grupos` do [catálogo](https://www.kaggle.com/datasets/caiquedourado/catalogo-produtos-ecommerce-brasil),
que tem nomes de produtos, preços e EANs.

Cada coluna está no [dicionário de dados](docs/data-dictionary.pt-BR.md) ([EN](docs/data-dictionary.md)).

## Texto a partir dos dados

A pasta `textos/` escreve texto em português a partir destas tabelas, por regras:

- o parágrafo "sobre" de uma versão;
- os itens de série por seção;
- o histórico de preço FIPE;
- um FAQ, com o JSON-LD dele.

É o gerador de páginas de 2022 do autor ("Tudo sobre <marca> <modelo>") reescrito, com os erros
corrigidos ([metodologia, seção 4](docs/methodology.md#4-text-from-the-data), em inglês).

```bash
pip install "git+https://github.com/CaiqueDourado/fipe-ficha-tecnica-veiculos"
python -m textos sample 003367-7 2012
```

```python
from textos import Vehicle, history
v = Vehicle(fichas.query("codigo_fipe == '003367-7' and ano_modelo == 2012").iloc[1])
v.about()
```

> O Ford EcoSport Freestyle 1.6 16V (Flex) 2012 tem motor 1.6, tração dianteira. É flex (etanol ou
> gasolina). A potência é de 115 cv com etanol e 110 cv com gasolina, e o torque, de 16,2 kgf.m com etanol
> e 15,8 kgf.m com gasolina. Mede 4,24 m de comprimento, 1,73 m de largura e 1,67 m de altura…

```python
v.equipment()   # {'Itens de segurança': 'Itens de segurança disponíveis: airbag do motorista, airbag do passageiro, alarme, controle de tração, distribuição eletrônica de frenagem (EBD) e freios ABS.', ...}
v.faq()         # [..., ('O Ford EcoSport Freestyle 1.6 16V (Flex) 2012 tem freios ABS?', 'Sim, o Ford EcoSport Freestyle 1.6 16V (Flex) 2012 tem freios ABS.'), ...]
serie = precos.query("codigo_fipe == '003367-7' and ano_modelo == 2012").sort_values("referencia")
history(zip(serie.referencia, serie.valor), v.title)
```

> Em outubro de 2026, o Ford EcoSport Freestyle 1.6 16V (Flex) 2012 valia R$ 41.862 na tabela FIPE, 26% a mais
> que em janeiro de 2020 (R$ 33.276). O maior valor foi R$ 44.119, em maio de 2022.

## Estrutura do repositório

```text
sample/        todas as linhas de 300 modelos sorteados, em CSV
schema/        definição das colunas e metadados
scripts/       exportar_fipe.py (SQL Server -> Parquet), coletor_fipe.py (API oficial da FIPE),
               probe_globo_fipe.py, probe_brasilapi_fipe.py, perfil_fipe.py, build_veiculos.py,
               validate.py, make_figures.py, docs.py
textos/        texto a partir dos dados (python -m textos); tests/ os testes
notebooks/     eda.ipynb
docs/          metodologia, qualidade, dicionário de dados, descrição do Kaggle, imagens
kaggle/        dataset-metadata.json
stats.json     contagens de cada etapa do build
```

## Relacionados

- [catalogo-produtos-ecommerce-brasil](https://github.com/CaiqueDourado/catalogo-produtos-ecommerce-brasil): os grupos de produto de `veiculo_produto`.
- [DedupKit](https://github.com/CaiqueDourado/DedupKit): casamento de nomes de produtos em português, o problema por trás do ruído de `veiculo_produto`.
- [municipios-e-estados-do-brasil](https://github.com/CaiqueDourado/municipios-e-estados-do-brasil): estados e municípios, para análises regionais.

## Licença

A compilação e as colunas derivadas estão em [CC BY 4.0](LICENSE-DATA.md). Código: [MIT](LICENSE). Pedidos de remoção: abra uma issue.

## Autor

**Caique Dourado**: 20 anos construindo crawlers, pipelines de dados e SEO programático em .NET e SQL Server. Mais em [github.com/CaiqueDourado](https://github.com/CaiqueDourado).
