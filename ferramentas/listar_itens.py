#!/usr/bin/env python3
"""GIN - lista todos os itens de um feed (data | titulo | link), com filtro opcional no link.
Uso: python3 ferramentas/listar_itens.py URL_DO_FEED [TEXTO_NO_LINK]"""
import html
import re
import sys
import time
import urllib.error
import urllib.request

UA = "GIN-Coletor/0.1 (leitor pessoal de feeds oficiais)"
BLOCO = re.compile(r"<(item|entry)[\s>](.*?)</\1>", re.I | re.S)
TITULO = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
DATA = re.compile(r"<(pubDate|updated|published|dc:date)[^>]*>(.*?)</\1>", re.I | re.S)
LINK_RSS = re.compile(r"<link>(.*?)</link>", re.I | re.S)
LINK_ATOM = re.compile(r"<link[^>]*href=[\"']([^\"']+)[\"']", re.I)


def limpar(t):
    t = re.sub(r"<!\[CDATA\[|\]\]>", "", t)
    return html.unescape(re.sub(r"\s+", " ", t)).strip()


def baixar(url, tentativas=3):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for n in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read(5_000_000).decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code}")
            return ""
        except Exception as e:
            print(f"  tentativa {n}: ERRO {type(e).__name__}")
            time.sleep(3 * n)
    return ""


url = sys.argv[1]
filtro = sys.argv[2] if len(sys.argv) > 2 else ""
corpo = baixar(url)
blocos = BLOCO.findall(corpo)
total, mostrados = len(blocos), 0
for _, b in blocos:
    mt, md = TITULO.search(b), DATA.search(b)
    ml = LINK_RSS.search(b) or LINK_ATOM.search(b)
    link = limpar(ml.group(1)) if ml else "-"
    if filtro and filtro not in link:
        continue
    mostrados += 1
    data = limpar(md.group(2))[:25] if md else "-"
    titulo = limpar(mt.group(1))[:70] if mt else "-"
    print(f"{data} | {titulo}\n    {link}")
print(f"\nTOTAL no feed: {total} | exibidos (filtro '{filtro}'): {mostrados}")
