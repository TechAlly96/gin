#!/usr/bin/env python3
"""GIN - monta dados/paises.json a partir de dados/<pais>/resumo.json. Cada pais grava so o proprio
resumo, entao e seguro com coletas em paralelo. Mantem a ordem atual (botoes do app) e acrescenta
paises novos no fim; se a coleta de um pais falhar, preserva a entrada anterior dele."""
import json
import os
from pathlib import Path

DADOS = Path(__file__).resolve().parent.parent / "dados"


def ler(caminho, padrao):
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except Exception:
        return padrao


antigo = ler(DADOS / "paises.json", {})
novos = {r.parent.name.upper(): v for r in sorted(DADOS.glob("*/resumo.json")) if (v := ler(r, None))}
saida = {cod: novos.get(cod, antigo.get(cod)) for cod in list(antigo) + [c for c in novos if c not in antigo]}
temp = DADOS / "paises.json.tmp"
temp.write_text(json.dumps(saida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
os.replace(temp, DADOS / "paises.json")
print(f"paises.json: {len(saida)} paises ({len(novos)} atualizados nesta coleta)")
