"use strict";
// GIN - service worker: rede primeiro (nunca mostra versao velha quando ha internet),
// copia guardada de tudo o que foi aberto (funciona offline com as ultimas noticias baixadas).
const CACHE_APP = "gin-app-v6";
const CACHE_AUDIO = "gin-audio-v1";
const CACHE_DADOS = "gin-dados-v1";
const CASCA = ["./", "./index.html", "./app.js", "./estilo.css", "./manifest.json",
  "./icone-192.png", "./icone-512.png", "./icone-maskable-512.png", "./globo.js"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE_APP).then((c) => c.addAll(CASCA)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((chaves) => Promise.all(chaves.filter((k) => k !== CACHE_APP && k !== CACHE_DADOS && k !== CACHE_AUDIO).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.endsWith(".ogg")) {
    e.respondWith(audioComReserva(req));
    return;
  }
  e.respondWith(redePrimeiro(req, url.pathname.includes("/dados/") ? CACHE_DADOS : CACHE_APP));
});

// Audio: rede primeiro; sem internet, entrega a copia guardada (inclusive em pedacos, para pular noticias)
async function audioComReserva(req) {
  const guardado = async () => (await caches.open(CACHE_AUDIO)).match(req.url);
  let resp;
  try {
    resp = await fetch(req);
    if (resp.status !== 404) return resp;
  } catch (erro) {
    resp = null;
  }
  const salvo = await guardado();
  if (!salvo) {
    if (resp) return resp;
    throw new Error("audio indisponivel offline");
  }
  const faixa = req.headers.get("range");
  if (!faixa) return salvo;
  const buf = await salvo.arrayBuffer();
  const m = /bytes=(\d*)-(\d*)/.exec(faixa) || [];
  const ini = m[1] ? parseInt(m[1], 10) : 0;
  const fim = Math.min(m[2] ? parseInt(m[2], 10) : buf.byteLength - 1, buf.byteLength - 1);
  return new Response(buf.slice(ini, fim + 1), {
    status: 206,
    headers: {
      "Content-Type": "audio/ogg", "Accept-Ranges": "bytes",
      "Content-Range": "bytes " + ini + "-" + fim + "/" + buf.byteLength,
      "Content-Length": String(fim - ini + 1),
    },
  });
}

async function redePrimeiro(req, nomeCache) {
  const cache = await caches.open(nomeCache);
  try {
    const resp = await fetch(req);
    if (resp.ok) cache.put(req, resp.clone());
    return resp;
  } catch (erro) {
    const salvo = await cache.match(req, { ignoreSearch: true });
    if (salvo) return salvo;
    throw erro;
  }
}
