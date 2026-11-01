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


def ate_frase_completa(texto):
    """Se o texto foi cortado (termina em ... ou sem pontuacao final), corta na ultima frase completa."""
    texto = texto.strip()
    if texto and (texto.endswith(("...", "…")) or texto[-1] not in ".!?"):
        texto = texto.rstrip(".… ")
        corte = max(texto.rfind(". "), texto.rfind("! "), texto.rfind("? "))
        texto = texto[:corte + 1] if corte > 40 else ""
    return texto


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
    if re.search(r"\b[A-Z]{3,}(?: [A-Z]{3,})*:", resumo):
        resumo = ""  # transcricao (MODERATOR:, SECRETARY X:): le so o titulo
    partes = [f"{nome_fonte(nome_da_fonte)}.", f"{titulo}."]
    if resumo:
        partes.append(resumo)
    return " ".join(partes)
