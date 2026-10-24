#!/usr/bin/env python3
"""GIN - mapeia os links de uma pagina por pasta do endereco, para descobrir onde ficam
as noticias em sites sem feed. Conta titulos longos (cara de manchete) e datas.
Uso: python3 -u ferramentas/mapear_links.py URL [URL2 ...]"""
import collections
import html
import re
import sys
import time
import urllib.parse
import urllib.request

UA = "GIN-Coletor/0.2 (leitor pessoal de fontes oficiais)"
ANCORA = re.compile(r"<a\s[^>]*href=[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
MESES = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
DATA_ES = re.compile(rf"\b\d{{1,2}} de (?:{MESES}) de \d{{4}}", re.I)
DATA_NUM = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")


def limpar(t):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))).strip()


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read(5_000_000).decode("utf-8", "replace"), r.geturl()
    except Exception as e:
        return f"ERRO {type(e).__name__}: {e}", url


for pagina in sys.argv[1:]:
    corpo, final = baixar(pagina)
    print(f"\n=== {pagina}  ({len(corpo)} caracteres)")
    if corpo.startswith("ERRO"):
        print("  " + corpo)
        continue
    host = urllib.parse.urlsplit(final).netloc
    grupos = collections.defaultdict(list)
    for href, txt in ANCORA.findall(corpo):
        u = urllib.parse.urlsplit(urllib.parse.urljoin(final, html.unescape(href)))
        if u.netloc != host:
            continue
        partes = [p for p in u.path.split("/") if p]
        titulo = limpar(txt)
        if len(partes) >= 2 and len(titulo) >= 25 and titulo not in grupos["/" + "/".join(partes[:-1])]:
            grupos["/" + "/".join(partes[:-1])].append(titulo)
    for pasta, titulos in sorted(grupos.items(), key=lambda kv: -len(kv[1]))[:5]:
        print(f"  {len(titulos):>3} manchetes em {pasta}/")
        for t in titulos[:2]:
            print(f"        - {t[:72]}")
    es, num = DATA_ES.findall(corpo), DATA_NUM.findall(corpo)
    print(f"  datas: {len(es)} em espanhol {DATA_ES.findall(corpo)[:2]} | {len(num)} numericas {num[:2]}")
    time.sleep(2)
