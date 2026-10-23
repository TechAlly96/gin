#!/usr/bin/env python3
"""GIN - descobre o feed de uma pagina: testa sufixos comuns e links <link rel=alternate>.
Uso: python3 ferramentas/descobrir_feed.py URL_DA_PAGINA [URL2 ...]"""
import html
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = "GIN-Coletor/0.1 (leitor pessoal de feeds oficiais)"
SUFIXOS = ["/RSS", "/rss.xml", "/atom.xml", "/feed", "/rss"]
ITEM = re.compile(r"<(item|entry)[\s>]", re.I)
BLOCO = re.compile(r"<(item|entry)[\s>](.*?)</\1>", re.I | re.S)
TITULO = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
DATA = re.compile(r"<(pubDate|updated|published|dc:date)[^>]*>(.*?)</\1>", re.I | re.S)
ALT = re.compile(r"<link[^>]+type=[\"']application/(?:rss|atom)\+xml[\"'][^>]*>", re.I)
HREF = re.compile(r"href=[\"']([^\"']+)[\"']", re.I)


def limpar(t):
    t = re.sub(r"<!\[CDATA\[|\]\]>", "", t)
    return html.unescape(re.sub(r"\s+", " ", t)).strip()


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read(3_000_000).decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, "", url
    except Exception as e:
        return f"ERRO {type(e).__name__}", "", url


def resumo(url):
    status, corpo, final = baixar(url)
    n = len(ITEM.findall(corpo))
    titulo, data = "-", "-"
    b = BLOCO.search(corpo)
    if b:
        mt, md = TITULO.search(b.group(2)), DATA.search(b.group(2))
        titulo = limpar(mt.group(1))[:80] if mt else "-"
        data = limpar(md.group(2)) if md else "-"
    marca = "OK " if n else "-- "
    print(f"  {marca}{status} itens:{n:<4} {url}")
    if n:
        print(f"       recente: {data} | {titulo}")
    return corpo, final


for pagina in sys.argv[1:]:
    print(f"\n=== {pagina}")
    corpo, final = resumo(pagina)
    candidatos = []
    for tag in ALT.findall(corpo):
        h = HREF.search(tag)
        if h:
            candidatos.append(urllib.parse.urljoin(final, html.unescape(h.group(1))))
    base = pagina.rstrip("/")
    candidatos += [base + s for s in SUFIXOS]
    vistos = set()
    for c in candidatos:
        if c not in vistos:
            vistos.add(c)
            resumo(c)
