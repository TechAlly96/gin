#!/usr/bin/env python3
"""GIN - leitores de fontes: download educado, feeds RSS/Atom, listagens Plone e datas.
Somente biblioteca padrao. Conteudo coletado e NAO confiavel: so texto e extraido, nada e executado.
Teste: python3 coletor/leitores.py br"""
import email.utils
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

UA = "GIN-Coletor/0.2 (leitor pessoal de fontes oficiais)"
PAUSA_MESMO_SITE = 3
LIMITE_BYTES = 8_000_000
ATOM = "{http://www.w3.org/2005/Atom}"
RSS1 = "{http://purl.org/rss/1.0/}"
DC = "{http://purl.org/dc/elements/1.1/}"
_ultimo_acesso = {}
MESES_NUM = {m: i for i, m in enumerate("enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(), 1)}
MESES_NUM.update({m: i for i, m in enumerate("janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split(), 1)})
MESES_NUM["setiembre"] = 9
DATA_TEXTO = re.compile(r"(?:(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s*,?\s+)?\d{1,2} de (?:"
                        + "|".join(MESES_NUM) + r") de \d{4}", re.I)


def limpar(texto, limite=None):
    if not texto:
        return ""
    t = re.sub(r"<[^>]+>", " ", texto)
    t = re.sub(r"<[^>]+>", " ", html.unescape(t))
    t = re.sub(r"\s+", " ", t).strip()
    if limite and len(t) > limite:
        t = t[:limite].rsplit(" ", 1)[0] + "..."
    return t


def baixar(url, tentativas=3):
    host = urllib.parse.urlsplit(url).netloc
    espera = PAUSA_MESMO_SITE - (time.monotonic() - _ultimo_acesso.get(host, -1e9))
    if espera > 0:
        time.sleep(espera)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    erro = ""
    for n in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                dados = r.read(LIMITE_BYTES)
                _ultimo_acesso[host] = time.monotonic()
                return dados, r.geturl()
        except urllib.error.HTTPError as e:
            _ultimo_acesso[host] = time.monotonic()
            if e.code < 500:
                raise RuntimeError(f"HTTP {e.code}")
            erro = f"HTTP {e.code}"
        except Exception as e:
            _ultimo_acesso[host] = time.monotonic()
            erro = f"{type(e).__name__}: {e}"
        time.sleep(4 * n)
    raise RuntimeError(f"falhou apos {tentativas} tentativas ({erro})")


def ler_data(valor, fuso):
    if not valor:
        return None
    v = valor.strip()
    try:
        dt = email.utils.parsedate_to_datetime(v)
        return dt if dt.tzinfo else dt.replace(tzinfo=fuso)
    except (TypeError, ValueError, IndexError):
        pass
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=fuso)
    except ValueError:
        pass
    m = re.search(r"(\d{1,2}) de ([a-záéíóúç]+) de (\d{4})", v.lower())
    if m and m.group(2) in MESES_NUM:
        try:
            return datetime(int(m.group(3)), MESES_NUM[m.group(2)], int(m.group(1)), tzinfo=fuso)
        except ValueError:
            return None
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})(?:\D{1,20}?(\d{1,2})[h:](\d{2}))?", v)
    if m:
        d, mo, a, h, mi = m.groups()
        try:
            return datetime(int(a), int(mo), int(d), int(h or 0), int(mi or 0), tzinfo=fuso)
        except ValueError:
            return None
    return None


def _texto(el, *nomes):
    for nome in nomes:
        x = el.find(nome)
        if x is not None and (x.text or "").strip():
            return x.text
    return ""


def ler_feed(conteudo):
    conteudo = conteudo.lstrip(b"\xef\xbb\xbf \t\r\n")
    raiz = ET.fromstring(conteudo)
    itens = []
    for it in list(raiz.iter("item")) + list(raiz.iter(f"{RSS1}item")):
        itens.append({
            "titulo": _texto(it, "title", f"{RSS1}title"),
            "link": _texto(it, "link", f"{RSS1}link", "guid"),
            "resumo": _texto(it, "description", f"{RSS1}description", f"{DC}description"),
            "data": _texto(it, "pubDate", f"{DC}date"),
        })
    for en in raiz.iter(f"{ATOM}entry"):
        link = ""
        for ln in en.findall(f"{ATOM}link"):
            if ln.get("rel", "alternate") == "alternate":
                link = ln.get("href", "")
                break
        itens.append({
            "titulo": _texto(en, f"{ATOM}title"),
            "link": link,
            "resumo": _texto(en, f"{ATOM}summary", f"{ATOM}content"),
            "data": _texto(en, f"{ATOM}published", f"{ATOM}updated"),
        })
    return itens


ARTIGO = re.compile(r"<article[^>]*tileItem[^>]*>(.*?)</article>", re.S | re.I)
ANCORA = re.compile(r"<a\s[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.S | re.I)


def ler_plone(conteudo, base, padrao):
    corpo = conteudo.decode("utf-8", "replace")
    itens = []
    for bloco in ARTIGO.findall(corpo):
        link = titulo = ""
        for href, txt in ANCORA.findall(bloco):
            if padrao in href and limpar(txt):
                link, titulo = urllib.parse.urljoin(base, html.unescape(href)), txt
                break
        if not link:
            continue
        sub = re.search(r"class=[\"']subtitle[\"'][^>]*>(.*?)</span>", bloco, re.S)
        desc = re.search(r"class=[\"']description[\"'][^>]*>(.*?)</(?:span|p|div)>", bloco, re.S)
        data = re.search(r"\d{2}/\d{2}/\d{4}(?:\D{1,20}?\d{1,2}[h:]\d{2})?", bloco)
        itens.append({
            "titulo": titulo,
            "link": link,
            "resumo": desc.group(1) if desc else "",
            "data": data.group(0) if data else "",
            "rotulo": limpar(sub.group(1)) if sub else "",
        })
    return itens


LI = re.compile(r"<li[\s>](.*?)</li>", re.S | re.I)


def ler_lista_govbr(conteudo, base, padrao):
    corpo = conteudo.decode("utf-8", "replace")
    ini = corpo.find("listagem-noticias")
    if ini < 0:
        return []
    fim = corpo.find("</ul>", ini)
    trecho = corpo[ini:fim] if fim > 0 else corpo[ini:]
    itens = []
    for bloco in LI.findall(trecho):
        link = titulo = ""
        for href, txt in ANCORA.findall(bloco):
            if padrao in href and limpar(txt):
                link, titulo = urllib.parse.urljoin(base, html.unescape(href)), txt
                break
        if not link:
            continue
        md = re.search(r"class=[\"']data[\"'][^>]*>(.*?)</span>", bloco, re.S)
        data = limpar(md.group(1)) if md else ""
        if not data:
            mm = re.search(r"\d{2}/\d{2}/\d{4}(?:\D{1,20}?\d{1,2}[h:]\d{2})?", bloco)
            data = mm.group(0) if mm else ""
        sem_data = re.sub(r"<span class=[\"']data[\"'][^>]*>.*?</span>", " ", bloco, flags=re.S)
        desc = re.search(r"class=[\"']descricao[\"'][^>]*>(.*?)</span>", sem_data, re.S)
        sub = re.search(r"class=[\"'](?:subtitulo-noticia|categoria-noticia)[\"'][^>]*>(.*?)</div>", bloco, re.S)
        itens.append({
            "titulo": titulo,
            "link": link,
            "resumo": desc.group(1) if desc else "",
            "data": data,
            "rotulo": limpar(sub.group(1)) if sub else "",
        })
    return itens


DATA_NUMERICA = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")


def ler_links(conteudo, base, padrao, min_titulo=25):
    """Leitor generico para paginas sem feed.
    - aceita links cujo endereco JA RESOLVIDO contem PADRAO;
    - titulo = cabecalho (h1-h6/strong) dentro do link, se houver; senao o texto do link;
    - data: por extenso dentro do link; se nao houver, a primeira data (por extenso ou dd/mm/aaaa)
      no trecho logo APOS o link, ate o proximo link da lista (formato titulo -> data -> resumo);
    - resumo: restante do texto do link ou o texto que segue a data."""
    corpo = conteudo.decode("utf-8", "replace")
    alvo_lista = urllib.parse.urlsplit(base).path.rstrip("/")
    candidatos = []
    for m in ANCORA.finditer(corpo):
        link = urllib.parse.urljoin(base, html.unescape(m.group(1).strip())).split("#")[0]
        caminho = urllib.parse.urlsplit(link).path
        if padrao in caminho + "/" and caminho.rstrip("/") != alvo_lista:
            candidatos.append((m, link))
    itens, vistos = [], set()
    for i, (m, link) in enumerate(candidatos):
        if link in vistos:
            continue
        txt = m.group(2)
        texto = limpar(txt)
        cab = re.search(r"<(h[1-6]|strong)[^>]*>(.*?)</\1>", txt, re.S | re.I)
        titulo = limpar(cab.group(2)) if cab else ""
        if len(titulo) < min_titulo:
            cab, titulo = None, texto
        titulo = re.sub(r"\s+", " ", DATA_TEXTO.sub(" ", titulo)).strip(" -|:>·")
        if len(titulo) < min_titulo:
            continue
        md = DATA_TEXTO.search(texto)
        data = md.group(0) if md else ""
        resumo = limpar(DATA_TEXTO.sub(" ", texto.replace(limpar(cab.group(2)), " "))) if cab else ""
        if not data:
            limite = candidatos[i + 1][0].start() if i + 1 < len(candidatos) else m.end() + 800
            depois = limpar(corpo[m.end():min(limite, m.end() + 800)])
            md2 = DATA_TEXTO.search(depois) or DATA_NUMERICA.search(depois)
            if md2:
                data = md2.group(0)
                if not resumo:
                    resumo = depois[md2.end():]
        vistos.add(link)
        itens.append({"titulo": titulo, "link": link, "resumo": resumo.strip(" -|:>·"), "data": data})
    return itens

def data_do_artigo(link):
    """Abre a noticia e devolve a primeira data encontrada no texto (por extenso ou dd/mm/aaaa), ou ''.
    Usado so em fontes com data_no_artigo=true (testado: a 1a data da pagina e a de publicacao)."""
    texto = limpar(baixar(link)[0].decode("utf-8", "replace"))
    m = DATA_TEXTO.search(texto) or DATA_NUMERICA.search(texto)
    return m.group(0) if m else ""


def ler_fonte(fonte):
    conteudo, final = baixar(fonte["url"])
    if fonte["tipo"] == "feed":
        return ler_feed(conteudo)
    if fonte["tipo"] == "html-plone":
        return ler_plone(conteudo, final, fonte["padrao_link"])
    if fonte["tipo"] == "html-links":
        return ler_links(conteudo, final, fonte["padrao_link"], fonte.get("min_titulo", 25))
    if fonte["tipo"] == "html-govbr":
        return ler_lista_govbr(conteudo, final, fonte["padrao_link"])
    raise ValueError(f"tipo de fonte desconhecido: {fonte['tipo']}")


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent
    cfg = json.loads((raiz / "fontes" / f"{sys.argv[1]}.json").read_text(encoding="utf-8"))
    fuso = timezone(timedelta(hours=cfg["pais"].get("fuso_horas", 0)))
    for f in cfg["fontes"]:
        try:
            itens = ler_fonte(f)
        except Exception as e:
            print(f"[ERRO] {f['id']}: {e}")
            continue
        datas = [ler_data(i["data"], fuso) for i in itens]
        validas = [d for d in datas if d]
        recente = max(validas).isoformat() if validas else "SEM DATA"
        print(f"[OK] {f['id']}: {len(itens)} itens | com data: {len(validas)} | mais recente: {recente}")
        if itens:
            print(f"     1o: {limpar(itens[0]['titulo'], 70)}")
