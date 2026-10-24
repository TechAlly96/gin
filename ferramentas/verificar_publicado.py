#!/usr/bin/env python3
"""GIN - confere o estado PUBLICADO de um pais no GitHub Pages.
Uso: python3 ferramentas/verificar_publicado.py ar"""
import json
import sys
import urllib.request

BASE = "https://techally96.github.io/gin/dados/"


def obter(caminho):
    with urllib.request.urlopen(BASE + caminho, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


pais = sys.argv[1].lower()
d = obter(f"{pais}/indice.json")
print(f"{d['nome']} | atualizado (UTC): {d['atualizado']}")
print(f"total: {d['total']} | completo: {d['completo']}")
for f in d["fontes"]:
    estado = "OK  " if f["ok"] else "ERRO"
    ultima = (f.get("mais_recente") or "-")[:10]
    linha = f"  {estado} {f['id']:<26} validos {f.get('validos', 0):<3} ultima {ultima}"
    if f.get("buscadas") or f.get("adiadas"):
        linha += f" | buscadas {f.get('buscadas', 0)}, adiadas {f.get('adiadas', 0)}"
    if not f["ok"]:
        linha += " | " + f.get("erro", "")
    print(linha)
for cat, c in d["cobertura"].items():
    if c.get("lacuna"):
        print(f"  LACUNA {cat}: {c['lacuna'][:60]}...")
print("paises publicados:", {k: v["completo"] for k, v in obter("paises.json").items()})
