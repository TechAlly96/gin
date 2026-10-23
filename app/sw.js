"use strict";
// GIN - service worker: rede primeiro (nunca mostra versao velha quando ha internet),
// copia guardada de tudo o que foi aberto (funciona offline com as ultimas noticias baixadas).
const CACHE_APP = "gin-app-v1";
const CACHE_DADOS = "gin-dados-v1";
const CASCA = ["./", "./index.html", "./app.js", "./estilo.css", "./manifest.json",
  "./icone-192.png", "./icone-512.png", "./icone-maskable-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE_APP).then((c) => c.addAll(CASCA)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((chaves) => Promise.all(chaves.filter((k) => k !== CACHE_APP && k !== CACHE_DADOS).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  e.respondWith(redePrimeiro(req, url.pathname.includes("/dados/") ? CACHE_DADOS : CACHE_APP));
});

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
