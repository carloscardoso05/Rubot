import re
from datetime import date
from typing import List, cast, Dict
from dataclasses import dataclass
from enum import Enum
import requests
from bs4 import BeautifulSoup, ResultSet, Tag

Dia = Enum("Dia", ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"])


@dataclass
class Prato:
    principal: str
    vegano: str
    acompanhamentos: List[str]


@dataclass
class Cardapio:
    data: date
    dia: Dia
    almoco: Prato
    janta: Prato


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


# def getAlmoco(almoco_td: Tag) -> Prato:
#     regex_principal = r'\s*([\w])\s*'
#     principal: str = almoco_td.getText()


# def getCardapio(row: Tag) -> Cardapio:
#     tds: ResultSet[Tag] = row.find_all("td")
#     data_td, almoco_td, janta_td = tds
#     print(getAlmoco(almoco_td))


if __name__ == "__main__":
    URL: str = "https://saest.ufpa.br/ru/index.php/component/cardapio/"
    dias = ["segunda", "terça", "quarta", "quinta", "sexta"]
    response: requests.Response = requests.get(URL)
    soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
    menu_tbody: Tag = next(
        filter(
            lambda tbody: len(cast(Tag, tbody).find_all("tr")) == 6,
            soup.find_all("tbody"),
        )
    )

    rows: Dict[Dia, Tag] = getDiasRows(menu_tbody)

    for row in rows.values():
        getCardapio(row)
