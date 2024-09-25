import re
from datetime import date
from typing import List, cast, Dict
from dataclasses import dataclass
from enum import Enum
import requests
from bs4 import BeautifulSoup, ResultSet, Tag
from atproto import Client

Dia = Enum("Dia", ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"])


@dataclass
class Prato:
    principal: str
    vegano: str
    acompanhamentos: List[str]

    def toString(self, identation_n=0) -> str:
        text = " " * identation_n + f"Principal: {self.principal}\n"
        text += " " * identation_n + f"Vegano: {self.vegano}\n"
        text += " " * identation_n + "Acompanhamentos:\n"
        for acompanhamento in self.acompanhamentos:
            text += " " * identation_n + f"   - {acompanhamento}\n"
        return text


@dataclass
class CardapioDoDia:
    data: date
    dia: Dia
    almoco: Prato
    janta: Prato

    def almocoStr(self) -> str:
        text = f"""
{self.dia.name} ({self.data.strftime(r'%d/%m')}) - Almoço
Pri.: {self.almoco.principal.capitalize()}
Veg.: {self.almoco.vegano.capitalize()}
Acompanhamentos:
{''.join([f'- {acompanhamento}\n' for acompanhamento in self.almoco.acompanhamentos])}
"""
        return text

    def jantaStr(self) -> str:
        text = f"""
{self.dia.name} ({self.data.strftime(r'%d/%m')}) - Janta
Pri.: {self.janta.principal.capitalize()}
Veg.: {self.janta.vegano.capitalize()}
Acompanhamentos:
{''.join([f'- {acompanhamento}\n' for acompanhamento in self.janta.acompanhamentos])}
"""
        return text


def getAlmocoTds(html: BeautifulSoup) -> ResultSet[Tag]:
    return html.find_all("td", class_="cardapioAlmoco")


def getJantaTds(html: BeautifulSoup) -> ResultSet[Tag]:
    return html.find_all("td", class_="cardapioAlmoco")


def getDiasRows(tbody: Tag) -> Dict[Dia, Tag]:
    return {Dia(dia): row for dia, row in enumerate(tbody.find_all("tr")) if dia > 0}


def getData(data_td: Tag) -> date:
    regex: re.Pattern = re.compile(r"(\d{2})\/(\d{2})")
    search: re.Match[str] | None = regex.search(data_td.getText())
    if not search:
        raise Exception("Data não encontrada")
    dia: int = int(search.group(1))
    mes: int = int(search.group(2))
    ano: int = date.today().year
    return date(ano, mes, dia)


def getAlmoco(almoco_td: Tag) -> Prato:
    regex_principal = re.compile(r"\s*(.+)\s*", re.I)
    principal_search: re.Match[str] | None = regex_principal.match(almoco_td.getText())
    if not principal_search:
        raise Exception("Data não encontrada")
    principal: str = principal_search.group(1)
    regex_vegano = re.compile(r"\s*(vegetariano|vegano)\s*\:\s*(.+)", re.I)
    vegano_search: re.Match[str] | None = regex_vegano.search(almoco_td.getText())
    if not vegano_search:
        raise Exception("Data não encontrada")
    vegano: str = vegano_search.group(2)
    regex_complementos = re.compile(r"(.+;)", re.I)
    acompanhamentos_str: str = regex_complementos.search(almoco_td.getText()).group(1)
    acompanhamentos: List[str] = [a for a in acompanhamentos_str.split(";") if a != ""]
    return Prato(principal, vegano, acompanhamentos)


def getJanta(janta_td: Tag) -> Prato:
    regex_principal = re.compile(r"\s*(.+)\s*", re.I)
    principal: str = regex_principal.match(janta_td.getText()).group(1)
    regex_vegano = re.compile(r"\s*(vegetariano|vegano)\s*\:\s*(.+)", re.I)
    vegano: str = regex_vegano.search(janta_td.getText()).group(2)
    regex_complementos = re.compile(r"(.+;)", re.I)
    acompanhamentos_str: str = regex_complementos.search(janta_td.getText()).group(1)
    acompanhamentos: List[str] = [a for a in acompanhamentos_str.split(";") if a != ""]
    return Prato(principal, vegano, acompanhamentos)


def getCardapioDoDia(row: Tag) -> CardapioDoDia:
    tds: ResultSet[Tag] = row.find_all("td")
    data_td, almoco_td, janta_td = tds
    data = getData(data_td)
    almoco = getAlmoco(almoco_td)
    janta = getJanta(janta_td)
    return CardapioDoDia(data, Dia(data.isoweekday()), almoco, janta)


if __name__ == "__main__":
    URL: str = "https://saest.ufpa.br/ru/index.php/component/cardapio/"
    dias = ["segunda", "terça", "quarta", "quinta", "sexta"]
    response: requests.Response = requests.get(URL)
    html: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
    menu_tbody: Tag = next(
        filter(
            lambda tbody: len(cast(Tag, tbody).find_all("tr")) == 6,
            html.find_all("tbody"),
        )
    )

    rows: Dict[Dia, Tag] = getDiasRows(menu_tbody)

    diasCardapio: Dict[Dia, CardapioDoDia] = {}

    for dia, row in rows.items():
        diasCardapio[dia] = getCardapioDoDia(row)

    key: str = ""
    with open("pass.txt", "r") as txt:
        key = txt.read()
        if not key:
            raise Exception("Chave não encontrada")

    client = Client()
    client.login("rubot050.bsky.social", key)
    text = diasCardapio[Dia.Segunda].almocoStr()
    for cardapio in diasCardapio.values():
        client.send_post(text=cardapio.almocoStr())
        client.send_post(text=cardapio.jantaStr())
