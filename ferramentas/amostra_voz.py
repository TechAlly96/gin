#!/usr/bin/env python3
"""GIN - amostras de voz do boletim com noticias reais publicadas.
O Piper (GPL) roda como PROGRAMA SEPARADO (subprocess), nunca importado pelo GIN.
Uso: python3 ferramentas/amostra_voz.py PASTA_SAIDA [--so-texto]
Variavel PIPER_PY: python do ambiente isolado onde o Piper esta instalado."""
import json
import os
import subprocess
import sys
import time
import urllib.request
import wave
from pathlib import Path

SITE = "https://techally96.github.io/gin/dados/"
CANDIDATAS = {
    "br": ["pt_BR-faber-medium", "pt_BR-cadu-medium", "pt_BR-jeff-medium"],
    "ar": ["es_AR-daniela-high", "es_MX-claude-high", "es_ES-davefx-medium"],
    "us": ["en_US-lessac-medium", "en_US-ryan-high"],
}
FALA = {
    "br": ("Boletim GIN. Notícias do Brasil.",
           {"governo": "Governo", "chancelaria": "Relações exteriores", "defesa": "Defesa",
            "parlamento": "Congresso", "agencia": "Agência pública"}),
    "ar": ("Boletín GIN. Noticias de Argentina.",
           {"governo": "Gobierno", "chancelaria": "Cancillería", "defesa": "Defensa",
            "parlamento": "Congreso", "agencia": "Agencia pública"}),
    "us": ("GIN bulletin. News from the United States.",
           {"governo": "Government", "chancelaria": "Foreign affairs", "defesa": "Defense",
            "parlamento": "Congress", "agencia": "Public broadcaster"}),
}


def obter(caminho):
    req = urllib.request.Request(SITE + caminho, headers={"User-Agent": "GIN-amostra-voz"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def texto_do_pais(pais):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "coletor"))
    from fala import texto_item
    abertura = FALA[pais][0]
    indice = obter(f"{pais}/indice.json")
    nomes = {f["id"]: f["nome"] for f in indice["fontes"]}
    itens = [i for i in obter(f"{pais}/pagina-1.json")["itens"] if i["precisao"] in ("hora", "dia")][:2]
    return "\n".join([abertura] + [texto_item(i, nomes.get(i["fonte"], i["fonte_nome"])) for i in itens])


def gerar(voz, texto, saida, piper_py):
    pasta_voz = Path("vozes")
    pasta_voz.mkdir(exist_ok=True)
    if not (pasta_voz / f"{voz}.onnx").exists():
        r = subprocess.run([piper_py, "-m", "piper.download_voices", voz], cwd=pasta_voz, capture_output=True, text=True)
        if not (pasta_voz / f"{voz}.onnx").exists():
            return f"voz indisponivel ({(r.stderr or r.stdout).strip()[-80:]})"
    wav = saida / f"{voz}.wav"
    t0 = time.monotonic()
    r = subprocess.run([piper_py, "-m", "piper", "-m", str(pasta_voz / f"{voz}.onnx"), "-f", str(wav)],
                       input=texto, capture_output=True, text=True)
    gasto = time.monotonic() - t0
    if r.returncode != 0 or not wav.exists():
        return f"falha na sintese ({r.stderr.strip()[-80:]})"
    with wave.open(str(wav)) as w:
        dur = w.getnframes() / w.getframerate()
    ogg = saida / f"{voz}.ogg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libopus", "-b:a", "32k", "-ac", "1", str(ogg)], check=True)
    wav.unlink()
    return f"OK | audio {dur:.0f} s | gerado em {gasto:.1f} s ({dur / max(gasto, 0.01):.0f}x tempo real) | {ogg.stat().st_size // 1024} KB"


saida = Path(sys.argv[1])
saida.mkdir(parents=True, exist_ok=True)
for pais, vozes in CANDIDATAS.items():
    texto = texto_do_pais(pais)
    print(f"\n===== {pais.upper()} =====\n{texto}\n")
    if "--so-texto" in sys.argv:
        continue
    for voz in vozes:
        print(f"  {voz:<24} {gerar(voz, texto, saida, os.environ.get('PIPER_PY', sys.executable))}", flush=True)
