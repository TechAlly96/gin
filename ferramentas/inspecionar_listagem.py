#!/usr/bin/env python3
"""GIN - inspeciona uma pagina de listagem publica (para fontes sem feed).
Mostra links que contem PADRAO, o texto de cada um, datas encontradas e o HTML ao redor do 1o item.
Uso: python3 ferramentas/inspecionar_listagem.py URL_DA_PAGINA PADRAO_NO_LINK"""
import html
import re
import sys
import time
import urllib.request

UA = "GIN-Coletor/0.1 (leitor pessoal de fontes oficiais)"
ANCORA = re.compile(r"<a\s[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
DATA_BR = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")


def limpar(t):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))).strip()


def baixar(url, tentativas=3):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for n in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read(5_000_000).decode("utf-8", "replace")
        except Exception as e:
            print(f"tentativa {n}: ERRO {type(e).__name__}")
            time.sleep(3 * n)
    return ""


url, padrao = sys.argv[1], sys.argv[2]
corpo = baixar(url)
print(f"Tamanho do HTML: {len(corpo)} caracteres")
vistos, primeiro = [], None
for m in ANCORA.finditer(corpo):
    href, texto = m.group(1), limpar(m.group(2))
    alvo = href.split("?")[0].rstrip("/")
    if padrao in href and not alvo.endswith(padrao.rstrip("/")) and href not in [v[0] for v in vistos]:
        vistos.append((href, texto))
        if primeiro is None:
            primeiro = m.start()
print(f"Links com '{padrao}': {len(vistos)}")
for href, texto in vistos[:12]:
    print(f"  - {texto[:75]}\n      {href}")
datas = DATA_BR.findall(corpo)
print(f"\nDatas dd/mm/aaaa na pagina: {len(datas)} -> primeiras: {datas[:6]}")
if primeiro is not None:
    trecho = re.sub(r"\s+", " ", corpo[max(0, primeiro - 700):primeiro + 500])
    print(f"\n--- HTML ao redor do 1o item ---\n{trecho}")
