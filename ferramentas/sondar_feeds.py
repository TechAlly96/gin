#!/usr/bin/env python3
"""GIN - sonda feeds candidatos: status HTTP, tipo, quantidade de itens e primeiro titulo.
Somente biblioteca padrao do Python (sem dependencias)."""
import html
import re
import urllib.error
import urllib.request

UA = "GIN-Coletor/0.1 (leitor pessoal de feeds oficiais)"

CANDIDATOS = [
    ("governo", "Governo do Brasil (geral)", "https://www.gov.br/rss.xml"),
    ("governo", "Planalto - noticias", "https://www.gov.br/planalto/pt-br/acompanhe-o-planalto/noticias/RSS"),
    ("chancelaria", "Itamaraty - notas a imprensa", "https://www.gov.br/mre/pt-br/canais_atendimento/imprensa/notas-a-imprensa/RSS"),
    ("defesa", "Ministerio da Defesa - noticias", "https://www.gov.br/defesa/pt-br/centrais-de-conteudo/noticias/RSS"),
    ("parlamento", "Camara - ultimas noticias", "https://www.camara.leg.br/noticias/rss/ultimas-noticias"),
    ("parlamento", "Senado - noticias", "https://www12.senado.leg.br/noticias/rss"),
    ("agencia", "Agencia Brasil - ultimas", "https://agenciabrasil.ebc.com.br/feed/ultimasnoticias/feed.xml"),
]

ITEM = re.compile(r"<(item|entry)[\s>]", re.I)
TITULO = re.compile(r"<(?:item|entry)[\s>].*?<title[^>]*>(.*?)</title>", re.I | re.S)


def limpar(texto):
    texto = re.sub(r"<!\[CDATA\[|\]\]>", "", texto)
    return html.unescape(re.sub(r"\s+", " ", texto)).strip()


def sondar(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            corpo = r.read(3_000_000).decode("utf-8", "replace")
            return f"HTTP {r.status}", r.headers.get("Content-Type", "?"), corpo, r.geturl()
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}", "", "", url
    except Exception as e:
        return f"ERRO {type(e).__name__}: {e}", "", "", url


for categoria, nome, url in CANDIDATOS:
    status, tipo, corpo, final = sondar(url)
    itens = len(ITEM.findall(corpo))
    m = TITULO.search(corpo)
    titulo = limpar(m.group(1))[:90] if m else "-"
    print(f"[{categoria}] {nome}")
    print(f"   {status} | {tipo[:40]} | itens: {itens}")
    if final != url:
        print(f"   redirecionado para: {final}")
    print(f"   mais recente: {titulo}")
