#!/usr/bin/env python3
"""GIN - coletor por pais.
Uso: python3 coletor/coletar.py br
Le fontes/<pais>.json, coleta as fontes, normaliza, remove duplicados (pelo link), mescla com o
historico (nunca apaga) e grava dados/<pais>/: todos.json, pagina-N.json e indice.json; atualiza
dados/paises.json. Imprime relatorio de cobertura por categoria."""
import hashlib
import json
import re
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from leitores import data_do_artigo, ler_data, ler_fonte, limpar

RAIZ = Path(__file__).resolve().parent.parent
POR_PAGINA = 50
ALERTA_DIAS_PADRAO = 7
HORA = re.compile(r"\d{1,2}[h:]\d{2}|T\d{2}")
RANK = {"hora": 2, "dia": 1, "estimada": 0}


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def de_iso(texto):
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def chave_link(link):
    p = urllib.parse.urlsplit(link.strip())
    return f"{p.netloc.lower()}{p.path.rstrip('/')}" + (f"?{p.query}" if p.query else "")


def id_do_link(link):
    return hashlib.sha1(chave_link(link).encode("utf-8")).hexdigest()[:16]


def ler_json(caminho, padrao):
    if not caminho.exists():
        return padrao
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"ABORTADO: {caminho} corrompido ({e}). Historico preservado, nada foi gravado.")


def gravar(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(caminho)


def normalizar(bruto, fonte, pais, fuso, agora, posicao):
    titulo = limpar(bruto.get("titulo"), 300)
    link = (bruto.get("link") or "").strip()
    if not titulo or not link.startswith(("http://", "https://")):
        return None
    texto_data = bruto.get("data") or ""
    dt = ler_data(texto_data, fuso)
    estimada = dt is None or dt > agora + timedelta(days=1)
    if estimada:
        dt = agora
    item = {
        "id": id_do_link(link),
        "pais": pais,
        "fonte": fonte["id"],
        "fonte_nome": fonte["nome"],
        "categoria": fonte["categoria"],
        "natureza": fonte["natureza"],
        "titulo": titulo,
        "resumo": limpar(bruto.get("resumo"), 400),
        "link": link,
        "publicado": iso(dt),
        "precisao": "estimada" if estimada else ("hora" if HORA.search(texto_data) else "dia"),
        "ordem": posicao,
        "coletado": iso(agora),
    }
    if bruto.get("rotulo"):
        item["rotulo"] = bruto["rotulo"]
    return item


def mesclar(atual, novo):
    if novo["fonte"] == atual["fonte"] and novo["titulo"] != atual["titulo"]:
        atual.setdefault("titulos_anteriores", []).append(atual["titulo"])
        atual["titulo"] = novo["titulo"]
        atual["atualizado"] = novo["coletado"]
    if RANK[novo["precisao"]] > RANK[atual["precisao"]]:
        for campo in ("publicado", "precisao", "fonte", "fonte_nome", "ordem"):
            atual[campo] = novo[campo]
    if novo["resumo"] and not atual.get("resumo"):
        atual["resumo"] = novo["resumo"]
    return atual


def main(codigo):
    cfg = json.loads((RAIZ / "fontes" / f"{codigo}.json").read_text(encoding="utf-8"))
    pais = cfg["pais"]
    fuso = timezone(timedelta(hours=pais.get("fuso_horas", 0)))
    alerta_dias = cfg.get("alerta_dias_sem_publicar", ALERTA_DIAS_PADRAO)
    agora = datetime.now(timezone.utc).replace(microsecond=0)
    pasta = RAIZ / "dados" / codigo
    historico = {i["id"]: i for i in ler_json(pasta / "todos.json", [])}
    total_antes = len(historico)

    lidos, status = {}, []
    for fonte in cfg["fontes"]:
        st = {k: fonte[k] for k in ("id", "nome", "categoria", "tipo", "url")}
        try:
            brutos = ler_fonte(fonte)
        except Exception as e:
            st.update(ok=False, erro=str(e)[:200], lidos=0, validos=0, novos=0)
            status.append(st)
            print(f"[ERRO  ] {fonte['id']}: {st['erro']}")
            continue
        total_lidos, buscados, adiados = len(brutos), 0, 0
        if fonte.get("data_no_artigo"):
            limite = fonte.get("max_artigos_por_execucao", 20)
            filtrados = []
            for b in brutos:
                link = (b.get("link") or "").strip()
                if b.get("data") or not link.startswith(("http://", "https://")) or id_do_link(link) in historico:
                    filtrados.append(b)
                    continue
                if buscados >= limite:
                    adiados += 1
                    continue
                try:
                    b["data"] = data_do_artigo(link)
                except Exception:
                    adiados += 1
                    continue
                buscados += 1
                filtrados.append(b)
            brutos = filtrados
        validos = novos = 0
        recente = None
        for pos, b in enumerate(brutos):
            item = normalizar(b, fonte, pais["codigo"], fuso, agora, pos)
            if not item:
                continue
            validos += 1
            if item["precisao"] != "estimada":
                recente = max(recente or item["publicado"], item["publicado"])
            if item["id"] not in historico and item["id"] not in lidos:
                novos += 1
            ja = lidos.get(item["id"])
            if ja is None or RANK[item["precisao"]] > RANK[ja["precisao"]]:
                lidos[item["id"]] = item
        dias = (agora - de_iso(recente)).days if recente else None
        alerta = ""
        if validos == 0:
            alerta = "nenhum item válido"
        elif dias is not None and dias > alerta_dias:
            alerta = f"sem publicar há {dias} dias"
        st.update(ok=True, lidos=total_lidos, buscadas=buscados, adiadas=adiados, validos=validos, novos=novos,
                  mais_recente=recente, dias_sem_publicar=dias, alerta=alerta)
        status.append(st)
        marca = "ALERTA" if alerta else "OK"
        extra = f" | {alerta}" if alerta else ""
        if buscados or adiados:
            extra += f" | datas buscadas {buscados}, adiadas {adiados}"
        print(f"[{marca:<6}] {fonte['id']}: lidos {total_lidos} | validos {validos} | novos {novos} | ultima {(recente or '-')[:10]}{extra}")

    for id_, item in lidos.items():
        historico[id_] = mesclar(historico[id_], item) if id_ in historico else item

    itens = sorted(historico.values(), key=lambda i: (i["publicado"], -i["ordem"]), reverse=True)
    paginas = max(1, -(-len(itens) // POR_PAGINA))
    gravar(pasta / "todos.json", itens)
    for n in range(paginas):
        gravar(pasta / f"pagina-{n + 1}.json",
               {"pagina": n + 1, "total_paginas": paginas, "itens": itens[n * POR_PAGINA:(n + 1) * POR_PAGINA]})
    for velha in pasta.glob("pagina-*.json"):
        if int(velha.stem.split("-")[1]) > paginas:
            velha.unlink()

    cobertura = {}
    for cat in cfg["categorias_obrigatorias"]:
        fontes_ok = [s for s in status if s["categoria"] == cat and s["ok"] and s["validos"]]
        datas = [i["publicado"] for i in itens if i["categoria"] == cat and i["precisao"] != "estimada"]
        cobertura[cat] = {"fontes_ok": len(fontes_ok), "ultima": max(datas) if datas else None}
        if cat in cfg.get("lacunas", {}):
            cobertura[cat]["lacuna"] = cfg["lacunas"][cat]
    completo = all(c["fontes_ok"] > 0 or c.get("lacuna") for c in cobertura.values())

    gravar(pasta / "indice.json", {
        "pais": pais["codigo"], "nome": pais["nome"], "idioma": pais.get("idioma"),
        "atualizado": iso(agora), "total": len(itens), "por_pagina": POR_PAGINA,
        "paginas": paginas, "completo": completo, "cobertura": cobertura, "fontes": status,
    })
    paises = ler_json(RAIZ / "dados" / "paises.json", {})
    paises[pais["codigo"]] = {"nome": pais["nome"], "atualizado": iso(agora),
                              "total": len(itens), "completo": completo}
    gravar(RAIZ / "dados" / "paises.json", paises)

    print(f"\nHistorico: {total_antes} -> {len(itens)} (novos nesta coleta: {len(itens) - total_antes}) | paginas: {paginas}")
    for cat, c in cobertura.items():
        lacuna = f" | LACUNA: {c['lacuna'][:70]}" if c.get("lacuna") else ""
        print(f"  {cat:<12} fontes ok: {c['fontes_ok']} | ultima: {(c['ultima'] or '-')[:10]}{lacuna}")
    print(f"PAIS COMPLETO: {'SIM' if completo else 'NAO'}")
    return 0 if any(s["ok"] for s in status) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
