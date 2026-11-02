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
    audio = pais.get("idioma_audio", idioma)
    traduzido = audio != idioma
    nomes = {f["id"]: f["nome"] for f in ler(pasta / "indice.json", {"fontes": []})["fontes"]}
    candidatos = [i for i in ler(pasta / "todos.json", []) if i["precisao"] != "desconhecida"]
    if traduzido:
        candidatos = [dict(i, titulo=i["titulo_pt"], resumo=i.get("resumo_pt", ""))
                      for i in candidatos if i.get("titulo_pt")]
    abertura = ABERTURA[audio].format(nome=pais.get("nome_falado", pais["nome"]) if not traduzido else pais["nome"])
    if traduzido:
        abertura += " Notícias traduzidas automaticamente."
    segs = [{"id": "abertura", "texto": abertura, "titulo": "Abertura", "fonte": ""}]
    for i in candidatos[:MAX_NOTICIAS]:
        fonte = nomes.get(i["fonte"], i["fonte_nome"])
        segs.append({"id": i["id"], "texto": texto_item(i, fonte), "titulo": i["titulo"], "fonte": fonte})
    segs.append({"id": "fim", "texto": FECHO[audio], "titulo": "Fim", "fonte": ""})
    return cfg.get("voz") or VOZ_PADRAO[audio], segs, pasta

def main(codigo):
    voz, segs, pasta = segmentos_do_pais(codigo)
    assinatura = hashlib.sha1(("v2\n" + voz + "\n" + "\n".join(s["texto"] for s in segs)).encode("utf-8")).hexdigest()[:12]
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
    cache = Path(os.environ.get("AUDIO_CACHE", "audio-cache")) / codigo
    cache.mkdir(parents=True, exist_ok=True)
    capitulos, quadros, params, t, falhas, novas, usados = [], [], None, 0.0, 0, 0, set()
    with tempfile.TemporaryDirectory() as tmp:
        for n, s in enumerate(segs):
            chave = hashlib.sha1((voz + "\n" + s["texto"]).encode("utf-8")).hexdigest()[:16]
            item_ogg = cache / f"{chave}.ogg"
            usados.add(item_ogg.name)
            if not item_ogg.exists():
                novo_wav = Path(tmp) / "novo.wav"
                r = subprocess.run([piper_py, "-m", "piper", "-m", str(onnx), "-f", str(novo_wav)],
                                   input=s["texto"], capture_output=True, text=True, timeout=300)
                if r.returncode != 0 or not novo_wav.exists():
                    falhas += 1
                    continue
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(novo_wav), "-c:a", "libopus",
                                "-b:a", "48k", "-ac", "1", str(item_ogg)], check=True)
                novas += 1
            wav = Path(tmp) / f"{n:03d}.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(item_ogg), "-ar", "22050",
                            "-ac", "1", "-c:a", "pcm_s16le", str(wav)], check=True)
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
    for velho in cache.glob("*.ogg"):
        if velho.name not in usados:
            velho.unlink()
    for velho in pasta.glob("boletim-*.ogg"):
        if velho.name != arquivo:
            velho.unlink()
    (pasta / "boletim.json").write_text(json.dumps({
        "pais": codigo.upper(), "gerado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "voz": voz, "arquivo": arquivo, "assinatura": assinatura, "duracao": round(t, 1),
        "noticias": len(capitulos) - 2, "falhas": falhas, "capitulos": capitulos,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{codigo}: boletim gerado | {t / 60:.1f} min | {destino.stat().st_size // 1024} KB | falhas {falhas} | narradas {novas} novas, {len(capitulos) - novas} do cache | {arquivo}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
