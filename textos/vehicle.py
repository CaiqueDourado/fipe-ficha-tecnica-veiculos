"""Text from a vehicle's specification sheet: an "about" paragraph, the equipment by section, and a FAQ.

The input is one row of the `fichas` table (a dict, a pandas
Series, anything with .get). Rewritten from the author's 2022 C# page generator (AutomoveiseVeiculos):
same idea, without its bugs (the "ABC" debug text that reached public pages, consumption written as
"7.5Km/l (Etanol)") and with the fuel of each measure kept in the sentence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .text import is_missing, join, lower_item, number, sentence

# column -> (section, phrase used in lists, phrase used in questions)
ITEMS: dict[str, tuple[str, str, str]] = {
    "ajuste_de_altura": ("Bancos", "ajuste de altura", "bancos com ajuste de altura"),
    "ajuste_eletrico": ("Bancos", "ajuste elétrico", "bancos com ajuste elétrico"),
    "bancos_de_couro": ("Bancos", "revestimento de couro", "bancos de couro"),
    "ar_condicionado": ("Conforto", "ar-condicionado", "ar-condicionado"),
    "ar_quente": ("Conforto", "ar quente", "ar quente"),
    "cambio_automatico": ("Conforto", "câmbio automático", "câmbio automático"),
    "direcao_eletrica": ("Conforto", "direção elétrica", "direção elétrica"),
    "direcao_hidraulica": ("Conforto", "direção hidráulica", "direção hidráulica"),
    "kit_acendimento_automatico_dos_farois": ("Conforto", "acendimento automático dos faróis",
                                              "acendimento automático dos faróis"),
    "piloto_automatico": ("Conforto", "piloto automático", "piloto automático"),
    "retrovisores_eletricos": ("Conforto", "retrovisores elétricos", "retrovisores elétricos"),
    "travas_eletricas": ("Conforto", "travas elétricas", "travas elétricas"),
    "trio_eletrico": ("Conforto", "trio elétrico", "trio elétrico"),
    "volante_com_regulagem_de_altura": ("Conforto", "volante com regulagem de altura", "volante com regulagem de altura"),
    "volante_multifuncional": ("Conforto", "volante multifuncional", "volante multifuncional"),
    "desemb_traseiro": ("Janelas", "desembaçador traseiro", "desembaçador traseiro"),
    "limp_traseiro": ("Janelas", "limpador traseiro", "limpador traseiro"),
    "teto_solar": ("Janelas", "teto solar", "teto solar"),
    "vidros_eletricos_dianteiros": ("Janelas", "vidros elétricos dianteiros", "vidros elétricos dianteiros"),
    "vidros_eletricos_traseiros": ("Janelas", "vidros elétricos traseiros", "vidros elétricos traseiros"),
    "adaptado_para_deficiente_fisico": ("Outros", "adaptação para pessoa com deficiência",
                                        "adaptação para pessoa com deficiência"),
    "aerofolio": ("Outros", "aerofólio", "aerofólio"),
    "calotas": ("Outros", "calotas", "calotas"),
    "capa_de_banco": ("Outros", "capas de banco", "capas de banco"),
    "capota_maritima": ("Outros", "capota marítima", "capota marítima"),
    "cacamba_de_fibra": ("Outros", "caçamba de fibra", "caçamba de fibra"),
    "computador_de_bordo": ("Outros", "computador de bordo", "computador de bordo"),
    "farol_de_neblina": ("Outros", "farol de neblina", "farol de neblina"),
    "friso_lateral": ("Outros", "friso lateral", "friso lateral"),
    "gps": ("Outros", "GPS", "GPS"),
    "kit_gas": ("Outros", "kit gás", "kit gás"),
    "protetor_de_cacamba": ("Outros", "protetor de caçamba", "protetor de caçamba"),
    "rodas_de_liga_leve": ("Outros", "rodas de liga leve", "rodas de liga leve"),
    "sensor_de_chuva": ("Outros", "sensor de chuva", "sensor de chuva"),
    "sensor_de_estacionamento": ("Outros", "sensor de estacionamento", "sensor de estacionamento"),
    "sensor_de_farol": ("Outros", "sensor de farol", "sensor de farol"),
    "tracao_4x4": ("Outros", "tração 4x4", "tração 4x4"),
    "airbag_lateral": ("Segurança", "airbags laterais", "airbags laterais"),
    "airbag_motorista": ("Segurança", "airbag do motorista", "airbag do motorista"),
    "airbag_passageiro": ("Segurança", "airbag do passageiro", "airbag do passageiro"),
    "alarme": ("Segurança", "alarme", "alarme"),
    "brake_light": ("Segurança", "brake light", "brake light"),
    "calha_de_chuva": ("Segurança", "calha de chuva", "calha de chuva"),
    "controle_de_tracao": ("Segurança", "controle de tração", "controle de tração"),
    "distribuicao_eletronica_de_frenagem": ("Segurança", "distribuição eletrônica de frenagem (EBD)",
                                            "distribuição eletrônica de frenagem (EBD)"),
    "freios_abs": ("Segurança", "freios ABS", "freios ABS"),
    "kit_visibilidade": ("Segurança", "kit visibilidade", "kit visibilidade"),
    "sensor_estacionamento_re": ("Segurança", "sensor de ré", "sensor de ré"),
    "trava_multilock": ("Segurança", "trava multilock", "trava multilock"),
    "cd_player": ("Som", "CD player", "CD player"),
    "cd_player_com_mp3": ("Som", "CD player com MP3", "CD player com MP3"),
    "entrada_usb": ("Som", "entrada USB", "entrada USB"),
    "kit_multimidia": ("Som", "central multimídia", "central multimídia"),
    "kit_multimidia_com_tv_e_camera_de_re": ("Som", "central multimídia com TV e câmera de ré",
                                             "central multimídia com TV e câmera de ré"),
    "mylink": ("Som", "MyLink", "MyLink"),
    "radio_com_bluetooth": ("Som", "rádio com Bluetooth", "rádio com Bluetooth"),
    "radio_fm_am": ("Som", "rádio FM/AM", "rádio FM/AM"),
    "toca_fitas": ("Som", "toca-fitas", "toca-fitas"),
}

# section -> (title, sentence that opens the list), from the dataset's ficha_titulos, lightly edited
SECTIONS: dict[str, tuple[str, str]] = {
    "Segurança": ("Itens de segurança", "Itens de segurança disponíveis:"),
    "Conforto": ("Itens de conforto", "Em conforto, os ocupantes dispõem de"),
    "Bancos": ("Bancos", "Os bancos têm"),
    "Janelas": ("Vidros e janelas", "Os vidros e janelas contam com"),
    "Som": ("Áudio e multimídia", "Em áudio e multimídia, há"),
    "Outros": ("Outros acessórios", "Além disso, o veículo tem"),
}

MEASURE = re.compile(r"([\d]+(?:[.,]\d+)?)\s*(?:\(([^)]*)\))?")
GENERIC_FUELS = {"flex", "multiflex"}


def _yes(value) -> bool | None:
    if is_missing(value):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return True if text in ("true", "sim", "1") else False if text in ("false", "não", "nao", "0") else None


def _num(value) -> float | None:
    if is_missing(value):
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def measures(value, unit: str, decimals: int = 1) -> str | None:
    """'122 (Etanol) / 115 (Gasolina)', 'cv' -> '122 cv com etanol e 115 cv com gasolina'.
    A generic fuel (Flex, MultiFlex) is not repeated: '127 (Flex)' -> '127 cv'."""
    if is_missing(value):
        return None
    parts = []
    for m in MEASURE.finditer(str(value)):
        n = float(m.group(1).replace(",", "."))
        shown = number(n, 0 if n == int(n) else decimals) + (f" {unit}" if unit else "")
        fuel = (m.group(2) or "").strip()
        parts.append(f"{shown} com {fuel.lower()}" if fuel and fuel.lower() not in GENERIC_FUELS else shown)
    return join(parts) or None


def fuel(value) -> str | None:
    """'Etanol / Gasolina' -> 'etanol ou gasolina (flex)'; 'Flex / Gasolina' -> 'flex'; 'Diesel' -> 'diesel'."""
    if is_missing(value):
        return None
    parts = [p.strip() for p in str(value).split("/") if p.strip()]
    low = [p.lower() for p in parts]
    if any(p.split(" ")[0] in GENERIC_FUELS for p in low):
        return "flex"
    if set(low) == {"etanol", "gasolina"}:
        return "flex (etanol ou gasolina)"
    return lower_item(join(parts, "ou"))


@dataclass
class Vehicle:
    """One version. `spec` is a fichas row; `name` overrides the name built from brand, model, version, year."""

    spec: dict
    name: str | None = None

    def get(self, key):
        v = self.spec.get(key) if hasattr(self.spec, "get") else None
        return None if is_missing(v) else v

    @property
    def title(self) -> str:
        if self.name:
            return self.name
        brand, model, version = self.get("marca"), self.get("modelo"), self.get("versao")
        if model and version and str(version).lower().startswith(str(model).lower()):
            model = None  # "EcoSport" + "Ecosport XL 1.6" -> "Ecosport XL 1.6"
        parts = [brand, model, version]
        year = self.get("ano_modelo")
        text = " ".join(str(p) for p in parts if p)
        return f"{text} {int(float(year))}" if year else text

    @property
    def is_motorcycle(self) -> bool:
        return self.get("tipo_veiculo") == "moto"

    # ---------------------------------------------------------------- about
    def about(self) -> str:
        """One paragraph with engine, fuel, power, gearbox, consumption, performance, size and capacities."""
        s = []
        engine, fl = self.get("motorizacao"), fuel(self.get("combustivel"))
        power, torque = measures(self.get("potencia_cv"), "cv"), measures(self.get("torque_kgf_m"), "kgf.m")
        gearbox, traction = self.get("cambio"), self.get("tracao")
        if traction and str(traction).strip().lower() in ("tração", "tracao"):
            traction = None
        drive = join([x for x in (gearbox and f"câmbio {lower_item(gearbox)}",
                                  traction and f"tração {lower_item(traction)}") if x])
        if engine:
            s.append(sentence(f"O {self.title} tem motor {engine}" + (f", {drive}" if drive else "")))
        elif drive:
            s.append(sentence(f"O {self.title} tem {drive}"))
        if fl:
            s.append(sentence(f"É {fl}" if fl.startswith("flex") else f"É movido a {fl}"))
        if power and torque:
            s.append(sentence(f"A potência é de {power}, e o torque, de {torque}"))
        elif power:
            s.append(sentence(f"A potência é de {power}"))
        city, road = measures(self.get("consumo_cidade_km_l"), "km/l"), measures(self.get("consumo_estrada_km_l"), "km/l")
        if city and road:
            s.append(sentence(f"Faz {city} na cidade e {road} na estrada"))
        elif city or road:
            s.append(sentence(f"Faz {city or road} {'na cidade' if city else 'na estrada'}"))
        top, sprint = _num(self.get("velocidade_maxima_km_h")), measures(self.get("tempo_0_100_s"), "s")
        if top and sprint:
            s.append(sentence(f"Chega a {number(top)} km/h e vai de 0 a 100 km/h em {sprint}"))
        elif top:
            s.append(sentence(f"Chega a {number(top)} km/h"))
        size = []
        length, width, height = (_num(self.get(k)) for k in ("comprimento_mm", "largura_mm", "altura_mm"))
        if length:
            size.append(f"{number(length / 1000, 2)} m de comprimento")
        if width:
            size.append(f"{number(width / 1000, 2)} m de largura")
        if height:
            size.append(f"{number(height / 1000, 2)} m de altura")
        if size:
            s.append(sentence("Mede " + join(size)))
        cap = []
        weight, seats, tank, trunk = (_num(self.get(k)) for k in ("peso_kg", "ocupantes", "tanque_l", "porta_malas_l"))
        if weight:
            cap.append(f"pesa {number(weight)} kg")
        if seats:
            cap.append(f"leva {number(seats)} {'pessoa' if seats == 1 else 'pessoas'}")
        if tank:
            cap.append(f"tem tanque de {number(tank)} litros")
        if trunk and not self.is_motorcycle:
            cap.append(f"porta-malas de {number(trunk)} litros")
        if cap:
            s.append(sentence(join(cap)))
        for key, label in (("freios_dianteiros", "Freios dianteiros"), ("freios_traseiros", "Freios traseiros")):
            if self.get(key):
                s.append(sentence(f"{label}: {str(self.get(key)).rstrip('.')[0].lower()}{str(self.get(key)).rstrip('.')[1:]}"))
        for key, label in (("suspensao_dianteira", "dianteira"), ("suspensao_traseira", "traseira")):
            v = self.get(key)
            if v:
                v = re.sub(r"^suspens[aã]o\s+", "", str(v).strip(), flags=re.I).rstrip(".")
                v = re.sub(r" e (dianteira|traseira) com barra", ", com barra", v)
                v = v.replace("molas helicoidal", "molas helicoidais")
                s.append(sentence(f"A suspensão {label} é {v[0].lower()}{v[1:]}"))
        return " ".join(s)

    # ---------------------------------------------------------------- equipment
    def equipment(self) -> dict[str, str]:
        """Section title -> paragraph listing the items the version has ('...: alarme, airbag do motorista e
        freios ABS.'). Sections with no item are left out."""
        out = {}
        for section, (title, opening) in SECTIONS.items():
            have = [label for col, (sec, label, _) in ITEMS.items() if sec == section and _yes(self.get(col))]
            if have:
                out[title] = sentence(f"{opening} {join(have)}")
        return out

    def missing(self, columns: list[str] | None = None) -> list[str]:
        """Items the version does NOT have (answered 'Não' in the source), for comparisons."""
        cols = columns or list(ITEMS)
        return [ITEMS[c][1] for c in cols if c in ITEMS and _yes(self.get(c)) is False]

    # ---------------------------------------------------------------- FAQ
    def faq(self, include_no: bool = True) -> list[tuple[str, str]]:
        """(question, answer) pairs: the measures that are filled, then every yes/no item."""
        t, qa = self.title, []
        facts = [
            ("Qual a motorização do {t}?", self.get("motorizacao"), "O {t} tem motor {v}."),
            ("Qual a potência do {t}?", measures(self.get("potencia_cv"), "cv"), "A potência é de {v}."),
            ("Qual o torque do {t}?", measures(self.get("torque_kgf_m"), "kgf.m"), "O torque é de {v}."),
            ("Qual o combustível do {t}?", fuel(self.get("combustivel")), "O {t} é {v}."),
            ("Qual o câmbio do {t}?", self.get("cambio") and lower_item(self.get("cambio")), "O câmbio é {v}."),
            ("Qual o consumo do {t} na cidade?", measures(self.get("consumo_cidade_km_l"), "km/l"), "Faz {v} na cidade."),
            ("Qual o consumo do {t} na estrada?", measures(self.get("consumo_estrada_km_l"), "km/l"), "Faz {v} na estrada."),
            ("Qual a velocidade máxima do {t}?", _num(self.get("velocidade_maxima_km_h")) and
             f"{number(_num(self.get('velocidade_maxima_km_h')))} km/h", "Chega a {v}."),
            ("Quantas pessoas cabem no {t}?", _num(self.get("ocupantes")) and number(_num(self.get("ocupantes"))),
             "Cabem {v} pessoas."),
            ("Qual a capacidade do tanque do {t}?", _num(self.get("tanque_l")) and f"{number(_num(self.get('tanque_l')))} litros",
             "O tanque leva {v}."),
            ("Qual o tamanho do porta-malas do {t}?", None if self.is_motorcycle else
             _num(self.get("porta_malas_l")) and f"{number(_num(self.get('porta_malas_l')))} litros", "O porta-malas tem {v}."),
        ]
        for q, v, a in facts:
            if v:
                qa.append((q.format(t=t), a.format(t=t, v=v)))
        for col, (_, _, phrase) in ITEMS.items():
            yes = _yes(self.get(col))
            if yes is None or (yes is False and not include_no):
                continue
            q = f"O {t} tem {phrase}?"
            qa.append((q, f"Sim, o {t} tem {phrase}." if yes else f"Não, o {t} não tem {phrase}."))
        return qa
