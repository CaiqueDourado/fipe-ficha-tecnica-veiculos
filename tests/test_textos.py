import json

from textos import Vehicle, by_model_year, faq_page, fuel, history, ipva, join, lower_item, measures, money, number

ECOSPORT = {
    "tipo_veiculo": "carro", "marca": "Ford", "modelo": "EcoSport", "versao": "Ecosport XL 1.6 (Flex)", "ano_modelo": 2012,
    "motorizacao": "1.6", "combustivel": "Etanol / Gasolina", "cambio": "Manual", "tracao": "dianteira",
    "potencia_cv": "107 (Etanol) / 101 (Gasolina)", "torque_kgf_m": "15.3 (Etanol) / 14.5 (Gasolina)",
    "consumo_cidade_km_l": "7.6 (Etanol)", "consumo_estrada_km_l": None, "velocidade_maxima_km_h": "165.0",
    "ocupantes": "5.0", "tanque_l": "54.0", "porta_malas_l": "296.0", "comprimento_mm": "4228.0",
    "suspensao_dianteira": "Suspensão tipo McPherson e dianteira com barra estabilizadora, roda tipo independente e molas helicoidal.",
    "airbag_motorista": False, "freios_abs": False, "ar_condicionado": True, "direcao_hidraulica": True, "teto_solar": None,
}


def test_text_helpers():
    assert join(["a", "b", "c"]) == "a, b e c" and join(["a"]) == "a" and join([]) == ""
    assert number(1234.5, 1) == "1.234,5" and money(38640) == "R$ 38.640"
    assert lower_item("Cd player com mp3") == "CD player com MP3"


def test_measures_and_fuel():
    assert measures("107 (Etanol) / 101 (Gasolina)", "cv") == "107 cv com etanol e 101 cv com gasolina"
    assert measures("127 (Flex)", "cv") == "127 cv"
    assert measures("20.904182 (Etanol)", "kgf.m") == "20,9 kgf.m com etanol"
    assert fuel("Etanol / Gasolina") == "flex (etanol ou gasolina)"
    assert fuel("MultiFlex (Etanol, Gas, GNV)") == "flex" and fuel("Diesel") == "diesel"


def test_title_does_not_repeat_the_model():
    assert Vehicle(ECOSPORT).title == "Ford Ecosport XL 1.6 (Flex) 2012"
    assert Vehicle(ECOSPORT, name="EcoSport 2012").title == "EcoSport 2012"


def test_about():
    text = Vehicle(ECOSPORT).about()
    assert text.startswith("O Ford Ecosport XL 1.6 (Flex) 2012 tem motor 1.6, câmbio manual e tração dianteira.")
    assert "É flex (etanol ou gasolina)." in text
    assert "A potência é de 107 cv com etanol e 101 cv com gasolina, e o torque, de 15,3 kgf.m com etanol" in text
    assert "Faz 7,6 km/l com etanol na cidade." in text
    assert "Mede 4,23 m de comprimento." in text
    assert "A suspensão dianteira é tipo McPherson, com barra estabilizadora, roda tipo independente e molas helicoidais." in text
    assert "ABC" not in text and "nan" not in text


def test_missing_values_are_skipped():
    assert Vehicle({"marca": "X", "modelo": "Y", "ano_modelo": float("nan")}).about() == ""


def test_equipment_and_missing():
    eq = Vehicle(ECOSPORT).equipment()
    assert eq == {"Itens de conforto": "Em conforto, os ocupantes dispõem de ar-condicionado e direção hidráulica."}
    assert Vehicle(ECOSPORT).missing() == ["airbag do motorista", "freios ABS"]


def test_faq_and_jsonld():
    qa = dict(Vehicle(ECOSPORT, name="EcoSport 2012").faq())
    assert qa["O EcoSport 2012 tem freios ABS?"] == "Não, o EcoSport 2012 não tem freios ABS."
    assert qa["O EcoSport 2012 tem ar-condicionado?"] == "Sim, o EcoSport 2012 tem ar-condicionado."
    assert "O EcoSport 2012 tem teto solar?" not in qa  # unknown in the source: no answer
    assert qa["Qual a velocidade máxima do EcoSport 2012?"] == "Chega a 165 km/h."
    data = json.loads(faq_page(list(qa.items())))
    assert data["@type"] == "FAQPage" and len(data["mainEntity"]) == len(qa)


def test_history_flat_and_drop():
    assert "praticamente o mesmo" in history([("2020-01-01", 100), ("2021-01-01", 101)], "X")
    assert "50% a menos" in history([("2020-01-01", 100), ("2021-01-01", 50)], "X")
    assert history([], "X") == ""


def test_by_model_year_without_zero_km():
    assert by_model_year([(2012, 38640)], "EcoSport", "2023-02-01") == \
        "Na tabela FIPE de fevereiro de 2023, o EcoSport 2012 vale R$ 38.640."


def test_ipva_takes_the_rate_given():
    assert "R$ 773" in ipva(38640, 2, "Paraná", "no")
