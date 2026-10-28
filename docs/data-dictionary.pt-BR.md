# Dicionário de dados: Tabela FIPE e ficha técnica de veículos (Brasil)

Gerado por `scripts/docs.py` a partir de `schema/columns.json`. Nulos e exemplos vêm da amostra em `sample/`.

## `marcas`

Marcas da FIPE de carros, motos e caminhões.

| Coluna | Tipo | Nulos | Exemplo | Descrição |
|---|---|---|---|---|
| `codigo_marca` | integer | 0,0% | `128` | Código da marca na FIPE. Chave primária. |
| `marca` | string | 0,0% | `FYM` | Nome da marca como a FIPE escreve (a mesma montadora pode aparecer uma vez por tipo: 'GM - Chevrolet' em carros, 'CHEVROLET' em caminhões). |
| `tipo_veiculo` | string | 0,0% | `moto` | carro, moto ou caminhao. |
| `slug` | string | 12,2% | `puma-alfa` | Slug de URL usado nos sites do autor; vazio nas marcas que só vieram da API da FIPE. |
| `fonte` | string | 0,0% | `dump` | dump (banco do autor, 2020-2023) ou fipe_api (coletado do site oficial da FIPE). |

## `modelos`

Modelos da FIPE (um por versão) com os nomes curtos usados no casamento com produtos.

| Coluna | Tipo | Nulos | Exemplo | Descrição |
|---|---|---|---|---|
| `codigo_modelo` | integer | 0,0% | `6119` | Código do modelo na FIPE (um por versão). Chave primária. |
| `codigo_marca` | integer | 0,0% | `39` | Marca (marcas.codigo_marca). |
| `tipo_veiculo` | string | 0,0% | `carro` | carro, moto ou caminhao. |
| `codigo_fipe` | string | 0,0% | `021258-0` | Código FIPE (000000-0). Um código pode estar em mais de um modelo quando a FIPE renomeou a versão. |
| `modelo` | string | 0,0% | `E-63 AMG 5.5 V8 Bi-Turbo Aut.` | Nome da versão como a FIPE escreve. |
| `modelo_curto` | string | 14,3% | `i30cw` | Nome até o primeiro número (motorização), usado no casamento. Vazio nos modelos que só vieram da API. |
| `primeiro_nome` | string | 14,3% | `i30cw` | Primeira palavra do nome ('Gol', 'Palio'). |
| `primeiro_segundo_nome` | string | 21,3% | `C30 T-5` | Duas primeiras palavras do nome. |
| `primeiro_nome_marca` | string | 14,3% | `Hyundai i30cw` | Marca curta + primeira palavra ('VW Gol'), a chave de casamento mais usada. |
| `slug` | string | 14,3% | `i30cw-2-0-16v-145cv-mec-5p` | Slug de URL usado nos sites do autor. |
| `fonte` | string | 0,0% | `dump` | dump ou fipe_api (modelos lançados depois de fevereiro de 2023). |

## `precos`

Preços médios da FIPE por mês de referência, código FIPE, ano-modelo e combustível: janeiro de 2020 a fevereiro de 2023 e outubro de 2026 em diante.

| Coluna | Tipo | Nulos | Exemplo | Descrição |
|---|---|---|---|---|
| `referencia` | string | 0,0% | `2021-09-01` | Mês de referência da tabela FIPE (primeiro dia, AAAA-MM-DD). |
| `codigo_fipe` | string | 0,0% | `024095-8` | Código FIPE. |
| `codigo_modelo` | integer | 0,0% | `1861` | Modelo (modelos.codigo_modelo). |
| `ano_modelo` | integer | 3,1% | `2002` | Ano-modelo; vazio para zero km. |
| `zero_km` | boolean | 0,0% | `false` | Verdadeiro para o preço de zero km (ano 32000 na FIPE). |
| `combustivel` | string | 0,0% | `Gasolina` | Combustível como a FIPE classifica: Gasolina (inclui flex), Diesel, Álcool, Elétrico... |
| `valor` | float | 0,0% | `10712.0` | Preço médio em reais. |
| `fonte` | string | 0,0% | `dump` | dump (2020-01 a 2023-02) ou fipe_api (2026-10 em diante). |

## `fichas`

Ficha técnica de 37.794 versões de carros e motos (Mobiauto, setembro de 2022), uma linha por versão, 81 colunas de características.

| Coluna | Tipo | Nulos | Exemplo | Descrição |
|---|---|---|---|---|
| `id_versao` | integer | 0,0% | `52892` | Id da versão no crawler do autor. Chave primária. |
| `tipo_veiculo` | string | 0,0% | `carro` | carro ou moto, pela URL (a fonte não tem caminhões). |
| `marca` | string | 0,0% | `Volvo` | Marca como o Mobiauto escreve. |
| `modelo` | string | 0,0% | `S40` | Modelo como o Mobiauto escreve. |
| `ano_modelo` | integer | 0,0% | `2001` | Ano-modelo, pela URL. |
| `ano_url` | string | 0,0% | `2001` | Trecho do ano na URL como coletado (mantido quando não é número). |
| `versao` | string | 0,0% | `T4 1.9 Turbo` | Nome da versão. |
| `codigo_fipe` | string | 0,0% | `029013-0` | Código FIPE informado pela fonte; liga com precos e modelos. O mesmo código pode cobrir várias versões. |
| `preco_mobiauto` | float | 11,3% | `94435.0` | Preço mostrado pelo Mobiauto no dia da coleta (setembro de 2022); vazio quando mostrava zero. |
| `data_coleta` | string | 0,0% | `2022-09-06` | Data da coleta. |
| `url` | string | 0,0% | `https://www.mobiauto.com.br/tabela-fi…` | Página de origem. |
| `ajuste_de_altura` | boolean | 17,7% | `false` | Bancos: possui 'Ajuste de altura' (Sim/Não na fonte). |
| `ajuste_eletrico` | boolean | 17,7% | `false` | Bancos: possui 'Ajuste elétrico' (Sim/Não na fonte). |
| `bancos_de_couro` | boolean | 17,7% | `false` | Bancos: possui 'Bancos de couro' (Sim/Não na fonte). |
| `ar_condicionado` | boolean | 17,7% | `false` | Conforto: possui 'Ar condicionado' (Sim/Não na fonte). |
| `ar_quente` | boolean | 17,7% | `false` | Conforto: possui 'Ar-quente' (Sim/Não na fonte). |
| `cambio_automatico` | boolean | 17,7% | `false` | Conforto: possui 'Câmbio automático' (Sim/Não na fonte). |
| `direcao_eletrica` | boolean | 17,7% | `false` | Conforto: possui 'Direção elétrica' (Sim/Não na fonte). |
| `direcao_hidraulica` | boolean | 17,7% | `false` | Conforto: possui 'Direção hidráulica' (Sim/Não na fonte). |
| `kit_acendimento_automatico_dos_farois` | boolean | 17,7% | `false` | Conforto: possui 'Kit acendimento automático dos faróis' (Sim/Não na fonte). |
| `piloto_automatico` | boolean | 17,7% | `false` | Conforto: possui 'Piloto automático' (Sim/Não na fonte). |
| `retrovisores_eletricos` | boolean | 17,7% | `false` | Conforto: possui 'Retrovisores elétricos' (Sim/Não na fonte). |
| `travas_eletricas` | boolean | 17,7% | `false` | Conforto: possui 'Travas elétricas' (Sim/Não na fonte). |
| `trio_eletrico` | boolean | 17,7% | `false` | Conforto: possui 'Trio eletrico' (Sim/Não na fonte). |
| `volante_com_regulagem_de_altura` | boolean | 17,7% | `false` | Conforto: possui 'Volante com regulagem de altura' (Sim/Não na fonte). |
| `volante_multifuncional` | boolean | 17,7% | `false` | Conforto: possui 'Volante multifuncional' (Sim/Não na fonte). |
| `altura_mm` | string | 27,1% | `1740` | Dimensões: 'Altura (mm)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `comprimento_mm` | string | 27,5% | `4215` | Dimensões: 'Comprimento (mm)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `entre_eixos_mm` | string | 44,7% | `2725` | Dimensões: 'Entre-eixos (mm)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `largura_mm` | string | 28,5% | `2098` | Dimensões: 'Largura (mm)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `ocupantes` | string | 44,8% | `7` | Dimensões: 'Ocupantes' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `peso_kg` | string | 41,3% | `1060` | Dimensões: 'Peso (kg)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `porta_malas_l` | string | 46,0% | `125` | Dimensões: 'Porta-Malas (L)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `tanque_l` | string | 31,7% | `66` | Dimensões: 'Tanque (L)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `desemb_traseiro` | boolean | 17,7% | `false` | Janelas: possui 'Desemb. traseiro' (Sim/Não na fonte). |
| `limp_traseiro` | boolean | 17,7% | `false` | Janelas: possui 'Limp. traseiro' (Sim/Não na fonte). |
| `teto_solar` | boolean | 17,7% | `false` | Janelas: possui 'Teto solar' (Sim/Não na fonte). |
| `vidros_eletricos_dianteiros` | boolean | 17,7% | `false` | Janelas: possui 'Vidros elétricos dianteiros' (Sim/Não na fonte). |
| `vidros_eletricos_traseiros` | boolean | 17,7% | `false` | Janelas: possui 'Vidros elétricos traseiros' (Sim/Não na fonte). |
| `combustivel` | string | 31,9% | `Gasolina` | Mecânica: 'Combustível' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `consumo_cidade_km_l` | string | 67,8% | `6 (Etanol)` | Mecânica: 'Consumo cidade (km/l)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `consumo_estrada_km_l` | string | 67,8% | `7.4 (Etanol)` | Mecânica: 'Consumo estrada (km/l)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `cambio` | string | 28,5% | `Manual` | Mecânica: 'Câmbio' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `direcao` | string | 95,5% | `Elétrica` | Mecânica: 'Direção' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `freios_dianteiros` | string | 37,1% | `Dois freios à disco.` | Mecânica: 'Freios dianteiros' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `freios_traseiros` | string | 83,4% | `Disco de 245 mm, pinça de 2 pistões` | Mecânica: 'Freios traseiros' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `motorizacao` | string | 35,0% | `1.8` | Mecânica: 'Motorização' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `potencia_cv` | string | 27,3% | `340 (Gasolina)` | Mecânica: 'Potência (cv)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `suspensao_dianteira` | string | 48,3% | `Independente, Braços triangulares dup…` | Mecânica: 'Suspensão dianteira' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `suspensao_traseira` | string | 47,4% | `Suspensão tipo multibraço e traseira …` | Mecânica: 'Suspensão traseira' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `tempo_0_100_s` | string | 55,8% | `5.2 (Etanol)` | Mecânica: 'Tempo 0-100 (s)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `torque_kgf_m` | string | 34,9% | `11.2 (Gasolina)` | Mecânica: 'Torque (kgf.m)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `tracao` | string | 44,2% | `4x4` | Mecânica: 'Tração' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `velocidade_maxima_km_h` | string | 46,8% | `220` | Mecânica: 'Velocidade máxima (km/h)' como texto (números podem trazer o combustível, ex. '122 (Etanol) / 115 (Gasolina)'). |
| `adaptado_para_deficiente_fisico` | boolean | 17,7% | `false` | Outros: possui 'Adaptado para deficiente físico' (Sim/Não na fonte). |
| `aerofolio` | boolean | 17,7% | `false` | Outros: possui 'Aerofólio' (Sim/Não na fonte). |
| `calotas` | boolean | 17,7% | `false` | Outros: possui 'Calotas' (Sim/Não na fonte). |
| `capa_de_banco` | boolean | 17,7% | `false` | Outros: possui 'Capa de banco' (Sim/Não na fonte). |
| `capota_maritima` | boolean | 17,7% | `false` | Outros: possui 'Capota marítima' (Sim/Não na fonte). |
| `cacamba_de_fibra` | boolean | 17,7% | `false` | Outros: possui 'Caçamba de fibra' (Sim/Não na fonte). |
| `computador_de_bordo` | boolean | 17,7% | `false` | Outros: possui 'Computador de bordo' (Sim/Não na fonte). |
| `farol_de_neblina` | boolean | 17,7% | `false` | Outros: possui 'Farol de neblina' (Sim/Não na fonte). |
| `friso_lateral` | boolean | 17,7% | `false` | Outros: possui 'Friso lateral' (Sim/Não na fonte). |
| `gps` | boolean | 17,7% | `false` | Outros: possui 'Gps' (Sim/Não na fonte). |
| `kit_gas` | boolean | 17,7% | `false` | Outros: possui 'Kit gás' (Sim/Não na fonte). |
| `protetor_de_cacamba` | boolean | 17,7% | `false` | Outros: possui 'Protetor de caçamba' (Sim/Não na fonte). |
| `rodas_de_liga_leve` | boolean | 17,7% | `false` | Outros: possui 'Rodas de liga leve' (Sim/Não na fonte). |
| `sensor_de_chuva` | boolean | 17,7% | `false` | Outros: possui 'Sensor de chuva' (Sim/Não na fonte). |
| `sensor_de_estacionamento` | boolean | 17,7% | `false` | Outros: possui 'Sensor de estacionamento' (Sim/Não na fonte). |
| `sensor_de_farol` | boolean | 17,7% | `false` | Outros: possui 'Sensor de farol' (Sim/Não na fonte). |
| `tracao_4x4` | boolean | 17,7% | `false` | Outros: possui 'Tração 4x4' (Sim/Não na fonte). |
| `airbag_lateral` | boolean | 17,7% | `false` | Segurança: possui 'Airbag lateral' (Sim/Não na fonte). |
| `airbag_motorista` | boolean | 17,7% | `false` | Segurança: possui 'Airbag motorista' (Sim/Não na fonte). |
| `airbag_passageiro` | boolean | 17,7% | `false` | Segurança: possui 'Airbag passageiro' (Sim/Não na fonte). |
| `alarme` | boolean | 17,7% | `false` | Segurança: possui 'Alarme' (Sim/Não na fonte). |
| `brake_light` | boolean | 17,7% | `false` | Segurança: possui 'Brake light' (Sim/Não na fonte). |
| `calha_de_chuva` | boolean | 17,7% | `false` | Segurança: possui 'Calha de chuva' (Sim/Não na fonte). |
| `controle_de_tracao` | boolean | 17,7% | `false` | Segurança: possui 'Controle de tração' (Sim/Não na fonte). |
| `distribuicao_eletronica_de_frenagem` | boolean | 17,7% | `false` | Segurança: possui 'Distribuição eletrônica de frenagem' (Sim/Não na fonte). |
| `freios_abs` | boolean | 17,7% | `false` | Segurança: possui 'Freios abs' (Sim/Não na fonte). |
| `kit_visibilidade` | boolean | 17,7% | `false` | Segurança: possui 'Kit visibilidade' (Sim/Não na fonte). |
| `sensor_estacionamento_re` | boolean | 17,7% | `false` | Segurança: possui 'Sensor estacionamento ré' (Sim/Não na fonte). |
| `trava_multilock` | boolean | 17,7% | `false` | Segurança: possui 'Trava multilock' (Sim/Não na fonte). |
| `cd_player` | boolean | 17,7% | `false` | Som: possui 'Cd player' (Sim/Não na fonte). |
| `cd_player_com_mp3` | boolean | 17,7% | `false` | Som: possui 'Cd player com mp3' (Sim/Não na fonte). |
| `entrada_usb` | boolean | 17,7% | `false` | Som: possui 'Entrada usb' (Sim/Não na fonte). |
| `kit_multimidia` | boolean | 17,7% | `false` | Som: possui 'Kit multimídia' (Sim/Não na fonte). |
| `kit_multimidia_com_tv_e_camera_de_re` | boolean | 17,7% | `false` | Som: possui 'Kit multimídia com tv e câmera de ré' (Sim/Não na fonte). |
| `mylink` | boolean | 17,7% | `false` | Som: possui 'Mylink' (Sim/Não na fonte). |
| `radio_com_bluetooth` | boolean | 17,7% | `false` | Som: possui 'Rádio com bluetooth' (Sim/Não na fonte). |
| `radio_fm_am` | boolean | 17,7% | `false` | Som: possui 'Rádio fm/am' (Sim/Não na fonte). |
| `toca_fitas` | boolean | 17,7% | `false` | Som: possui 'Toca-fitas' (Sim/Não na fonte). |

## `ficha_caracteristicas`

A mesma ficha em formato longo: versão, seção, chave, valor.

| Coluna | Tipo | Nulos | Exemplo | Descrição |
|---|---|---|---|---|
| `id_versao` | integer | 0,0% | `50847` | Versão (fichas.id_versao). |
| `secao` | string | 0,0% | `Mecânica` | Seção: Bancos, Conforto, Dimensões, Janelas, Mecânica, Outros, Segurança, Som. |
| `chave` | string | 0,0% | `Torque (kgf.m)` | Nome da característica. |
| `valor` | string | 14,7% | `175 (Gasolina)` | Valor como coletado; Sim/Não nos itens (decodificado dos ícones da fonte); vazio quando a fonte deixou em branco. |

## `ficha_titulos`

Títulos de seção, frases de abertura e perguntas de FAQ usadas para escrever texto a partir da ficha.

| Coluna | Tipo | Nulos | Exemplo | Descrição |
|---|---|---|---|---|
| `tipo` | string | 0,0% | `faq` | secao (título da seção e frase de abertura) ou faq (pergunta de um item sim/não). |
| `secao` | string | 93,1% | `Janelas` | Seção, quando tipo = secao. |
| `chave` | string | 6,9% | `Mylink` | Nome da característica, quando tipo = faq. |
| `titulo` | string | 0,0% | `Possui Retrovisores elétricos?` | Título da seção ou pergunta do FAQ. |
| `texto_introdutorio` | string | 93,1% | `Os vidros e janelas dispõem de` | Frase que abre a lista de itens da seção. |

## `veiculo_produto`

Modelo de veículo x grupo de produto do e-commerce, casados pelo nome, com nível de confiança (alerta). Muito ruidoso: filtre por confianca.

| Coluna | Tipo | Nulos | Exemplo | Descrição |
|---|---|---|---|---|
| `codigo_modelo` | integer | 0,0% | `6157` | Modelo do veículo (modelos.codigo_modelo). |
| `group_id` | integer | 0,0% | `10805245` | Grupo de produto da base do catálogo de e-commerce (grupos.id). |
| `chave` | string | 0,0% | `EcoSport` | Nome que casou: o nome do modelo foi procurado dentro do nome do produto. |
| `nivel` | string | 0,0% | `modelo_primeiro_nome` | Qual nome do modelo casou: modelo_primeiro_nome_marca, modelo_primeiro_nome ou modelo_primeiro_segundo_nome. |
| `produtos_da_chave` | integer | 0,0% | `12656` | Quantos grupos de produto a mesma chave casou. Números grandes indicam nome genérico. |
| `modelos_da_chave` | integer | 0,0% | `34` | Quantos modelos de veículo têm a mesma chave. |
| `confianca` | string | 0,0% | `baixa` | NÍVEL DE ALERTA: alta (< 100 produtos para a chave), media (100-999), baixa (1.000 ou mais). A maioria é baixa; leia o relatório de qualidade. |
