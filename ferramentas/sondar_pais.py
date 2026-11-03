#!/usr/bin/env python3
"""GIN - sondagem automatica das fontes de um pais, pelo proprio coletor (certificados completos,
gzip, identidades honestas). Para cada site: abre (ou mostra o erro real), procura feeds anunciados
e em caminhos comuns, testa cada feed e mapeia as pastas com mais manchetes (data no endereco e
data dentro da 1a noticia). Uso: python3 ferramentas/sondar_pais.py URL [URL ...]"""
import re
import sys
import urllib.parse
from collections import Counter, defaultdict
from datetime import timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "coletor"))
from leitores import IDENTIDADES, baixar, data_do_artigo, data_no_endereco, ler_data, ler_feed, limpar  # noqa: E402

SUFIXOS = ["feed", "feed/", "rss", "rss.xml", "atom.xml", "feed.xml", "index.xml", "?feed=rss2"]
ALTERNATE = re.compile(r'<link[^>]+application/(?:rss|atom)\+xml[^>]*>', re.I)
HREF = re.compile(r'href=["\']([^"\']+)["\']', re.I)
ANCORA = re.compile(r'<a\s[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', re.S | re.I)


def abrir(url):
    try:
        return baixar(url, tentativas=1), "padrao"
    except Exception as erro:
        if "403" in str(erro):
            try:
                return baixar(url, tentativas=1, ua=IDENTIDADES["simples"]), "simples"
            except Exception:
                pass
        raise erro


def recente(itens):
    datas = [d for d in (ler_data(i.get("data"), timezone.utc) for i in itens) if d]
    return max(datas).date().isoformat() if datas else "-"


def testar_feed(url):
    try:
        (conteudo, final), _ = abrir(url)
        itens = ler_feed(conteudo)
        if itens:
            return final, itens
    except Exception:
        pass
    return None


def sondar(url):
    print(f"\n===== {url}")
    try:
        (conteudo, final), ident = abrir(url)
    except Exception as erro:
        print(f"  ERRO {type(erro).__name__}: {str(erro)[:90]}")
        return
    pagina = conteudo.decode("utf-8", "replace")
    print(f"  abre: {len(pagina)} caracteres (identificacao {ident}) -> {final}")
    candidatos = [final] + [urllib.parse.urljoin(final, h) for tag in ALTERNATE.findall(pagina) for h in HREF.findall(tag)]
    base = f"{urllib.parse.urlsplit(final).scheme}://{urllib.parse.urlsplit(final).netloc}/"
    candidatos += [urllib.parse.urljoin(base, s) for s in SUFIXOS]
    vistos = set()
    for c in dict.fromkeys(candidatos):
        r = testar_feed(c)
        if r and r[0] not in vistos:
            vistos.add(r[0])
            final_feed, itens = r
            print(f"  FEED {len(itens):3d} itens | com data {sum(1 for i in itens if i.get('data')):3d} | recente {recente(itens)} | {final_feed}")
            print(f"       1o: {itens[0]['titulo'][:80]}")
    host = urllib.parse.urlsplit(final).netloc
    pastas = defaultdict(list)
    for href, texto in ANCORA.findall(pagina):
        link = urllib.parse.urljoin(final, href)
        partes = urllib.parse.urlsplit(link)
        titulo = re.sub(r"\s+", " ", limpar(texto)).strip()
        if partes.netloc == host and len(titulo) >= 25:
            segs = partes.path.split("/")
            # endereco plano (/agencia/noticia-titulo-123.aspx): agrupa pelo prefixo do nome do arquivo
            chave = "/".join(segs[:2]) + "/" + re.split(r"[-_]", segs[2])[0] if len(segs) == 3 else "/".join(segs[:3]) + "/"
            if link not in [l for l, _ in pastas[chave]]:
                pastas[chave].append((link, titulo))
    for chave, links in sorted(pastas.items(), key=lambda kv: -len(kv[1]))[:4]:
        if len(links) < 3:
            break
        com_data_url = sum(1 for l, _ in links if data_no_endereco(l))
        print(f"  PASTA {chave} -> {len(links)} manchetes | data no endereco: {com_data_url}")
        for l, t in links[:2]:
            print(f"       - {t[:80]}")
    if pastas:
        chave, links = max(pastas.items(), key=lambda kv: len(kv[1]))
        if len(links) >= 3:
            try:
                bruto = data_do_artigo(links[0][0])
                d = ler_data(bruto, timezone.utc)
                print(f"  DATA na 1a noticia de {chave}: {bruto!r} -> {d.date().isoformat() if d else 'NAO INTERPRETADA'}")
            except Exception as erro:
                print(f"  DATA na 1a noticia: erro {type(erro).__name__}")


if __name__ == "__main__":
    for u in sys.argv[1:]:
        sondar(u)
