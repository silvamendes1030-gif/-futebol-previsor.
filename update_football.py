import os
import json
import requests
from datetime import datetime

API_KEY = os.environ["API_FOOTBALL_KEY"]

URL = "https://v3.football.api-sports.io/fixtures"

HEADERS = {
    "x-apisports-key": API_KEY
}

LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    78: "Bundesliga",
    135: "Serie A",
    61: "Ligue 1",
    94: "Primeira Liga",
}

SEASON = 2026


def buscar_jogos(league_id):

    resposta = requests.get(
        URL,
        headers=HEADERS,
        params={
            "league": league_id,
            "season": SEASON
        },
        timeout=30
    )

    resposta.raise_for_status()

    return resposta.json()["response"]


def main():

    dados = []

    for league_id, league_name in LEAGUES.items():

        print("A carregar:", league_name)

        jogos = buscar_jogos(league_id)

        lista = []

        for jogo in jogos:

            fixture = jogo["fixture"]
            teams = jogo["teams"]
            goals = jogo["goals"]

            data = datetime.fromisoformat(
                fixture["date"].replace("Z", "+00:00")
            )

            data_formatada = data.strftime("%m-%d %H:%M")

            casa = teams["home"]["name"]
            fora = teams["away"]["name"]

            golos_casa = goals["home"]
            golos_fora = goals["away"]

            if golos_casa is None:
                golos_casa = ""

            if golos_fora is None:
                golos_fora = ""

            linha = (
                f"{data_formatada}|"
                f"{casa}|"
                f"{fora}|"
                f"{golos_casa}|"
                f"{golos_fora}"
            )

            lista.append(linha)

        lista.sort()

        dados.append([
            league_name,
            lista
        ])

    with open(
        "dados.json",
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )

    print("dados.json criado com sucesso.")


if __name__ == "__main__":
    main()
