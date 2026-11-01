#!/usr/bin/env python3
"""GIN - testa se um endereco bloqueia o coletor e por que (identificacao ou origem).
So usa identificacoes HONESTAS de robo; nunca se passa por navegador.
Uso: python3 -u ferramentas/testar_acesso.py URL [URL2 ...]"""
import re
import sys
import time
import urllib.error
import urllib.request

PROJETO = "https://github.com/TechAlly96/gin"
IDENTIDADES = {
    "gin-atual": "GIN-Coletor/0.2 (leitor pessoal de fontes oficiais)",
    "robo-padrao": f"Mozilla/5.0 (compatible; GIN-Coletor/0.2; +{PROJETO})",
    "curl": "curl/8.0",
}


def testar(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            corpo = r.read(4000).decode("utf-8", "replace")
            return r.status, r.headers.get("Content-Type", "?"), corpo
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "?"), e.read(600).decode("utf-8", "replace")
    except Exception as e:
        return "ERRO", type(e).__name__, str(e)


for url in sys.argv[1:]:
    print(f"\n=== {url}")
    for nome, ua in IDENTIDADES.items():
        status, tipo, corpo = testar(url, ua)
        itens = len(re.findall(r"<(?:item|entry)[\s>]", corpo))
        inicio = re.sub(r"\s+", " ", corpo)[:70]
        print(f"  {nome:<12} {status} | {tipo[:30]:<30} | itens(4KB): {itens} | {inicio}")
        time.sleep(2)
