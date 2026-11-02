#!/usr/bin/env python3
"""GIN - prepara o TEXTO FALADO do boletim em audio (limpeza para sintese de voz).
Nao altera os dados guardados nem a tela; so o que e enviado para a voz. Sem dependencias."""
import re

RODAPES = [
    r"Not[ií]cias relacionadas\s*:.*$", r"Leia (mais|tamb[eé]m)\s*:?.*$", r"Saiba mais\s*:?.*$",
    r"Lee (m[aá]s|tambi[eé]n)\s*:?.*$", r"Read more\s*:?.*$", r"Continue reading.*$",
    r"The post .* appeared first.*$", r"\[(…|\.\.\.)\].*$",
]
MOEDAS = [(r"R\$\s?([\d.,]+)", r"\1 reais"), (r"US\$\s?([\d.,]+)", r"\1 dólares"),
          (r"€\s?([\d.,]+)", r"\1 euros")]


def nome_fonte(nome):
    nome = re.sub(r"\s*\([^)]*\)", "", nome or "")
    return nome.split(" - ")[0].strip()


def suavizar_maiusculas(texto):
    letras = [c for c in texto if c.isalpha()]
    if letras and sum(c.isupper() for c in letras) / len(letras) > 0.7:
        texto = texto.lower()
        texto = texto[:1].upper() + texto[1:]
    return texto


def limpar_fala(texto):
    texto = re.sub(r"\s+", " ", texto or "").strip()
    for padrao in RODAPES:
        texto = re.sub(padrao, "", texto, flags=re.I).strip()
    for padrao, troca in MOEDAS:
        texto = re.sub(padrao, troca, texto)
    return texto


CONECTORES = set("a o e de do da dos das em no na nos nas que com para por um uma os as ao "
                 "and or the of to in for with an by on at "
                 "y el la los las del en con un una al".split())
TRANSCRICAO = re.compile(r"\b[A-Z]{3,}(?: [A-Z]{3,})*:")


def ate_frase_completa(texto):
    """Texto cortado: termina na ultima frase completa; se nao houver nenhuma, aproveita o trecho
    ate a ultima virgula (ou palavra inteira), sem conectores soltos no fim, e fecha com ponto."""
    texto = texto.strip()
    if not texto or (not texto.endswith(("...", "…")) and texto[-1] in ".!?"):
        return texto
    texto = texto.rstrip(".… ")
    corte = max(texto.rfind(". "), texto.rfind("! "), texto.rfind("? "))
    if corte > 15:
        return texto[:corte + 1]
    if len(texto) < 25:
        return ""
    virgula = max(texto.rfind(", "), texto.rfind("; "))
    palavras = (texto[:virgula] if virgula > len(texto) * 0.6 else texto).split()
    while palavras and palavras[-1].lower().strip(",;:-") in CONECTORES:
        palavras.pop()
    trecho = " ".join(palavras).rstrip(",;:- ")
    return trecho + "." if trecho else ""


def texto_item(item, nome_da_fonte):
    titulo = suavizar_maiusculas(limpar_fala(item.get("titulo", "")))
    if titulo.endswith(("...", "…")):
        titulo = titulo.rstrip(".… ")
        corte = max(titulo.rfind(". "), titulo.rfind("; "), titulo.rfind(", "))
        if corte > 60:
            titulo = titulo[:corte]
    titulo = titulo.rstrip(".… ")
    resumo = ate_frase_completa(limpar_fala(item.get("resumo", "")))
    if resumo.lower().startswith(titulo.lower()[:40]):
        resumo = ate_frase_completa(resumo[len(titulo):].lstrip(" .:-"))
    if not re.search(r"[^\W\d_]", resumo):
        resumo = ""  # resumo sem nenhuma letra (ex.: "-")
    if TRANSCRICAO.search(resumo):
        resumo = ""  # transcricao (MODERATOR:, SECRETARY X:): le so o titulo
    partes = [f"{nome_fonte(nome_da_fonte)}.", f"{titulo}."]
    if resumo:
        partes.append(resumo)
    return " ".join(partes)
