#!/usr/bin/env python3
"""GIN - traducao automatica para portugues com os modelos do Argos Translate
(CTranslate2 + SentencePiece, sem PyTorch). Tenta o par direto; senao, passa pelo ingles.
Uso: python coletor/traduzir.py ar            (traduz o historico do pais)
     python coletor/traduzir.py --teste ar us (mostra exemplos reais, nao grava nada)
Variavel ARGOS_MODELOS: pasta dos modelos (cache)."""
import json
import os
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fala import suavizar_maiusculas  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
SITE = "https://techally96.github.io/gin/dados/"
INDICE = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"
MODELOS = Path(os.environ.get("ARGOS_MODELOS", "argos-modelos"))
MAX_POR_EXECUCAO = 80
FRASES = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑÜ¿¡\"“(0-9])")
_tradutores = {}


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "GIN-traducao"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def pasta_do_par(origem, destino):
    alvo = MODELOS / f"{origem}_{destino}"
    if (alvo / "pronto").exists():
        return alvo
    indice = json.loads(baixar(INDICE))
    pacote = next((p for p in indice if p.get("from_code") == origem and p.get("to_code") == destino), None)
    if not pacote:
        return None
    alvo.mkdir(parents=True, exist_ok=True)
    arquivo = alvo / "pacote.zip"
    arquivo.write_bytes(baixar(pacote["links"][0]))
    with zipfile.ZipFile(arquivo) as z:
        z.extractall(alvo)
    arquivo.unlink()
    (alvo / "pronto").write_text(str(pacote.get("package_version", "?")), encoding="utf-8")
    return alvo


def carregar(origem, destino):
    chave = (origem, destino)
    if chave not in _tradutores:
        import ctranslate2
        import sentencepiece
        base = pasta_do_par(origem, destino)
        if base is None:
            _tradutores[chave] = None
        else:
            modelo = next(base.rglob("model.bin")).parent
            sp = next(base.rglob("sentencepiece.model"))
            _tradutores[chave] = (ctranslate2.Translator(str(modelo), device="cpu"),
                                  sentencepiece.SentencePieceProcessor(model_file=str(sp)))
    return _tradutores[chave]


def traduzir_par(texto, origem, destino):
    par = carregar(origem, destino)
    if par is None:
        raise LookupError(f"sem modelo {origem}->{destino}")
    tradutor, sp = par
    frases = [f for f in FRASES.split(texto.strip()) if f]
    resultado = tradutor.translate_batch([sp.encode(f, out_type=str) for f in frases],
                                         beam_size=2, max_decoding_length=256)
    return " ".join(sp.decode(r.hypotheses[0]) for r in resultado).strip()


def traduzir(texto, origem):
    texto = (texto or "").strip()
    if not texto:
        return ""
    try:
        return traduzir_par(texto, origem, "pt")
    except LookupError:
        return traduzir_par(traduzir_par(texto, origem, "en"), "en", "pt")


def idioma_do_pais(codigo):
    cfg = json.loads((RAIZ / "fontes" / f"{codigo}.json").read_text(encoding="utf-8"))
    return cfg["pais"].get("idioma", "pt")


def teste(paises):
    for codigo in paises:
        origem = idioma_do_pais(codigo)
        itens = json.loads(baixar(f"{SITE}{codigo}/pagina-1.json"))["itens"][:3]
        print(f"\n===== {codigo.upper()} ({origem} -> pt) =====")
        for i in itens:
            for campo in ("titulo", "resumo"):
                original = suavizar_maiusculas(i.get(campo) or "")[:300]
                if not original:
                    continue
                t0 = time.monotonic()
                pt = traduzir(original, origem)
                print(f"  [{time.monotonic() - t0:4.1f}s] {campo}: {original[:90]}")
                print(f"           -> {pt[:120]}")


if __name__ == "__main__":
    paises = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--teste" in sys.argv:
        teste(paises)
    else:
        raise SystemExit("modo de gravacao ainda nao ativado (sera ligado apos aprovacao do teste)")
