#!/usr/bin/env python3
"""GIN - gera o boletim em audio de um pais.
Piper (GPL) roda como PROGRAMA SEPARADO; ffmpeg converte para Opus.
Reaproveita o audio ja publicado quando as noticias nao mudaram.
Uso: python3 coletor/boletim.py br [--so-texto]
Variaveis: PIPER_PY (python do ambiente do Piper), VOZES_DIR (pasta dos modelos)."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import wave
from datetime import datetime, timezone
from pathlib import Path

from fala import texto_item

RAIZ = Path(__file__).resolve().parent.parent
SITE = "https://techally96.github.io/gin/dados/"
MAX_NOTICIAS = 30
PAUSA_S = 0.7
VOZ_PADRAO = {"pt": "pt_BR-faber-medium", "es": "es_AR-daniela-high", "en": "en_US-lessac-medium"}
ABERTURA = {"pt": "Boletim GIN. {nome}.", "es": "Boletín GIN. {nome}.", "en": "GIN bulletin. {nome}."}
FECHO = {"pt": "Fim do boletim.", "es": "Fin del boletín.", "en": "End of the bulletin."}


def ler(caminho, padrao=None):
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else padrao


def baixar_publicado(codigo, arquivo, destino):
    try:
        req = urllib.request.Request(SITE + f"{codigo}/{arquivo}", headers={"User-Agent": "GIN-boletim"})
        with urllib.request.urlopen(req, timeout=60) as r:
            destino.write_bytes(r.read())
        return destino.stat().st_size > 0
    except Exception:
        return False


def segmentos_do_pais(codigo):
    cfg = ler(RAIZ / "fontes" / f"{codigo}.json")
    pais, pasta = cfg["pais"], RAIZ / "dados" / codigo
    idioma = pais.get("idioma", "pt")
    nomes = {f["id"]: f["nome"] for f in ler(pasta / "indice.json", {"fontes": []})["fontes"]}
    itens = [i for i in ler(pasta / "todos.json", []) if i["precisao"] != "desconhecida"][:MAX_NOTICIAS]
    segs = [{"id": "abertura", "texto": ABERTURA[idioma].format(nome=pais.get("nome_falado", pais["nome"])),
             "titulo": "Abertura", "fonte": ""}]
    for i in itens:
        fonte = nomes.get(i["fonte"], i["fonte_nome"])
        segs.append({"id": i["id"], "texto": texto_item(i, fonte), "titulo": i["titulo"], "fonte": fonte})
    segs.append({"id": "fim", "texto": FECHO[idioma], "titulo": "Fim", "fonte": ""})
    return cfg.get("voz") or VOZ_PADRAO[idioma], segs, pasta


def main(codigo):
    voz, segs, pasta = segmentos_do_pais(codigo)
    assinatura = hashlib.sha1((voz + "\n" + "\n".join(s["texto"] for s in segs)).encode("utf-8")).hexdigest()[:12]
    arquivo = f"boletim-{assinatura}.ogg"
    if "--so-texto" in sys.argv:
        total = sum(len(s["texto"]) for s in segs)
        print(f"{codigo}: voz {voz} | {len(segs) - 2} noticias | {total} caracteres (~{total / 15 / 60:.0f} min) | arquivo {arquivo}")
        for s in segs[:3] + segs[-1:]:
            print(f"   [{s['id']}] {s['texto'][:110]}")
        return 0
    anterior = ler(pasta / "boletim.json", {})
    destino = pasta / arquivo
    if anterior.get("assinatura") == assinatura and (destino.exists() or baixar_publicado(codigo, arquivo, destino)):
        print(f"{codigo}: noticias sem mudanca, audio reaproveitado ({arquivo})")
        return 0
    piper_py = os.environ.get("PIPER_PY", sys.executable)
    vozes = Path(os.environ.get("VOZES_DIR", "vozes"))
    vozes.mkdir(parents=True, exist_ok=True)
    onnx = vozes / f"{voz}.onnx"
    if not onnx.exists():
        subprocess.run([piper_py, "-m", "piper.download_voices", voz], cwd=vozes, check=True)
    capitulos, quadros, params, t, falhas = [], [], None, 0.0, 0
    with tempfile.TemporaryDirectory() as tmp:
        for n, s in enumerate(segs):
            wav = Path(tmp) / f"{n:03d}.wav"
            r = subprocess.run([piper_py, "-m", "piper", "-m", str(onnx), "-f", str(wav)],
                               input=s["texto"], capture_output=True, text=True, timeout=300)
            if r.returncode != 0 or not wav.exists():
                falhas += 1
                continue
            with wave.open(str(wav)) as w:
                params = params or w.getparams()
                dados = w.readframes(w.getnframes())
            dur = len(dados) / (params.sampwidth * params.nchannels) / params.framerate
            capitulos.append({"id": s["id"], "inicio": round(t, 2), "fim": round(t + dur, 2),
                              "titulo": s["titulo"], "fonte": s["fonte"]})
            quadros.append(dados)
            quadros.append(b"\x00" * int(params.framerate * PAUSA_S) * params.sampwidth * params.nchannels)
            t += dur + PAUSA_S
        if not quadros:
            raise SystemExit(f"{codigo}: nenhum trecho sintetizado ({falhas} falhas)")
        junto = Path(tmp) / "boletim.wav"
        with wave.open(str(junto), "wb") as w:
            w.setparams(params)
            w.writeframes(b"".join(quadros))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(junto), "-c:a", "libopus",
                        "-b:a", "32k", "-ac", "1", "-application", "voip", str(destino)], check=True)
    for velho in pasta.glob("boletim-*.ogg"):
        if velho.name != arquivo:
            velho.unlink()
    (pasta / "boletim.json").write_text(json.dumps({
        "pais": codigo.upper(), "gerado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "voz": voz, "arquivo": arquivo, "assinatura": assinatura, "duracao": round(t, 1),
        "noticias": len(capitulos) - 2, "falhas": falhas, "capitulos": capitulos,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{codigo}: boletim gerado | {t / 60:.1f} min | {destino.stat().st_size // 1024} KB | falhas {falhas} | {arquivo}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
