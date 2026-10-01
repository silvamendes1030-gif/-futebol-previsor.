#!/usr/bin/env python3
"""Vai buscar jogos e resultados a football-data.org e atualiza jogos.json, jogos.csv e jogos.ics."""
import csv, json, os, sys, time, urllib.request
from datetime import datetime, timedelta, timezone

TOKEN = os.environ.get("FOOTBALL_DATA_TOKEN", "")
LIGAS = {"PL": "Premier League", "PD": "La Liga", "BL1": "Bundesliga", "SA": "Serie A",
         "FL1": "Ligue 1", "DED": "Eredivisie", "PPL": "Liga Portugal Betclic",
         "CL": "Liga dos Campeões"}


def pedir(codigo):
    req = urllib.request.Request(
        f"https://api.football-data.org/v4/competitions/{codigo}/matches",
        headers={"X-Auth-Token": TOKEN})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def converter(m, liga):
    estado = {"FINISHED": "terminado", "TIMED": "por realizar", "SCHEDULED": "por realizar"}.get(m["status"])
    if not estado:
        return None
    ft = (m.get("score") or {}).get("fullTime") or {}
    fim = estado == "terminado"
    nome = lambda t: t.get("shortName") or t.get("name") or "?"
    return {"liga": liga, "data_utc": m["utcDate"], "hora_confirmada": m["status"] != "SCHEDULED",
            "casa": nome(m["homeTeam"]), "fora": nome(m["awayTeam"]),
            "golos_casa": ft.get("home") if fim else None,
            "golos_fora": ft.get("away") if fim else None, "estado": estado}


def main():
    if not TOKEN:
        sys.exit("Falta a variavel FOOTBALL_DATA_TOKEN.")
    antigo = {}
    if os.path.exists("jogos.json"):
        antigo = json.load(open("jogos.json", encoding="utf-8"))
    jogos_antigos = antigo.get("jogos", [])
    agora = datetime.now(timezone.utc)
    de, ate = agora - timedelta(days=30), agora + timedelta(days=60)
    novos, estado_ligas = [], {}
    for i, (codigo, liga) in enumerate(LIGAS.items()):
        if i:
            time.sleep(7)  # o plano gratis permite 10 pedidos por minuto
        try:
            jogos = []
            for m in pedir(codigo)["matches"]:
                dt = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
                if de <= dt <= ate:
                    j = converter(m, liga)
                    if j:
                        jogos.append(j)
            novos += jogos
            estado_ligas[liga] = f"OK ({len(jogos)} jogos)"
        except Exception as e:  # mantem os dados anteriores desta liga
            novos += [j for j in jogos_antigos if j["liga"] == liga]
            estado_ligas[liga] = f"ERRO: {e}"
        print(liga, "->", estado_ligas[liga])
    outras = [j for j in jogos_antigos if j["liga"] not in LIGAS.values()]
    for l in {j["liga"] for j in outras}:
        estado_ligas[l] = "nao atualizada (fora do plano gratis)"
    todos = sorted(novos + outras, key=lambda j: (j["liga"], j["data_utc"]))
    saida = dict(antigo)
    saida["dados_de"] = agora.strftime("%Y-%m-%d")
    saida["ligas"] = sorted({j["liga"] for j in todos})
    saida["atualizacao"] = {"em": agora.strftime("%Y-%m-%dT%H:%M:%SZ"), "ligas": estado_ligas}
    saida["jogos"] = todos
    with open("jogos.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    campos = ["liga", "data_utc", "hora_confirmada", "casa", "fora", "golos_casa", "golos_fora", "estado"]
    with open("jogos.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(todos)
    linhas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Previsor de jogos//PT", "CALSCALE:GREGORIAN"]
    for n, j in enumerate(todos):
        d = j["data_utc"]
        linhas += ["BEGIN:VEVENT", f"UID:{n}-{d}-{j['casa']}@previsor", f"DTSTAMP:{agora:%Y%m%dT%H%M%SZ}"]
        if len(d) == 10:
            linhas.append("DTSTART;VALUE=DATE:" + d.replace("-", ""))
        else:
            ini = datetime.fromisoformat(d.replace("Z", "+00:00"))
            linhas += [f"DTSTART:{ini:%Y%m%dT%H%M%SZ}", f"DTEND:{ini + timedelta(hours=2):%Y%m%dT%H%M%SZ}"]
        placar = f" ({j['golos_casa']}-{j['golos_fora']})" if j["estado"] == "terminado" else ""
        linhas += [f"SUMMARY:{j['casa']} x {j['fora']}{placar}", f"DESCRIPTION:{j['liga']}", "END:VEVENT"]
    linhas.append("END:VCALENDAR")
    with open("jogos.ics", "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(linhas) + "\r\n")


if __name__ == "__main__":
    main()
