"use strict";
const DADOS = "../dados/";
const CATEGORIAS = { todas: "Todas", governo: "Governo", chancelaria: "Chancelaria", defesa: "Defesa", parlamento: "Parlamento", agencia: "Agência" };
const $ = (id) => document.getElementById(id);
let estado;
let nomesFontes = {};

function novoEstado(pais) {
  return { pais, pagina: 0, totalPaginas: 1, carregando: false, vistos: new Set(), itens: [], categoria: "todas", total: 0 };
}

async function obterJSON(caminho) {
  const r = await fetch(DADOS + caminho, { cache: "no-cache" });
  if (!r.ok) throw new Error(caminho + ": HTTP " + r.status);
  return r.json();
}

function el(tag, classe, texto) {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  if (texto != null) e.textContent = texto;
  return e;
}

function linkSeguro(url) {
  try {
    const u = new URL(url);
    return (u.protocol === "https:" || u.protocol === "http:") ? u.href : null;
  } catch { return null; }
}

function formatarData(item) {
  const d = new Date(item.publicado);
  if (Number.isNaN(d.getTime())) return "";
  if (item.precisao === "dia" && item.data_local) {
    const [ano, mes, dia] = item.data_local.split("-").map(Number);
    return new Date(ano, mes - 1, dia).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
  }
  const dia = d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
  if (item.precisao === "hora") return dia + ", " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  if (item.precisao === "desconhecida") return "data não informada pela fonte (anterior ao início da coleta)";
  if (item.precisao === "estimada") return dia + " (data estimada)";
  return dia;
}

function cartao(item) {
  const art = el("article", "cartao");
  art.dataset.id = item.id;
  const meta = el("div", "meta");
  meta.append(el("span", "selo", CATEGORIAS[item.categoria] || item.categoria));
  if (item.rotulo) meta.append(el("span", "rotulo", item.rotulo));
  if (item.titulo_pt) meta.append(el("span", "traducao", "tradução automática"));
  art.append(meta);
  const traduzido = !!item.titulo_pt;
  const titulo = traduzido ? item.titulo_pt : item.titulo;
  const resumo = traduzido ? (item.resumo_pt || item.resumo || "") : (item.resumo || "");
  const h = el("h2", "titulo");
  const href = linkSeguro(item.link);
  if (href) {
    const a = el("a", null, titulo);
    a.href = href; a.target = "_blank"; a.rel = "noopener noreferrer";
    h.append(a);
  } else {
    h.textContent = titulo;
  }
  art.append(h);
  const pResumo = resumo && /\p{L}/u.test(resumo) ? el("p", "resumo", resumo) : null;
  if (pResumo) art.append(pResumo);
  if (traduzido) {
    const botao = el("button", "ver-original", "Ver original");
    botao.type = "button";
    let original = false;
    botao.addEventListener("click", () => {
      original = !original;
      (h.querySelector("a") || h).textContent = original ? item.titulo : titulo;
      if (pResumo) pResumo.textContent = original ? (item.resumo || "") : resumo;
      botao.textContent = original ? "Ver tradução" : "Ver original";
    });
    art.append(botao);
  }
  if (item.titulos_anteriores) art.append(el("p", "corrigido", "Título atualizado pela fonte"));
  art.append(el("p", "rodape", (nomesFontes[item.fonte] || item.fonte_nome) + " · " + formatarData(item)));
  return art;
}

const visivel = (item) => estado.categoria === "todas" || item.categoria === estado.categoria;

function sentinelaPerto() {
  return $("sentinela").getBoundingClientRect().top < window.innerHeight + 600;
}

function atualizarSentinela() {
  const mostrados = $("feed").childElementCount;
  if (estado.pagina >= estado.totalPaginas) {
    $("sentinela").textContent = mostrados ? "Fim - " + mostrados + " notícias exibidas" : "Nenhuma notícia nesta categoria";
  } else {
    $("sentinela").textContent = "Carregando...";
  }
}

async function carregarProxima() {
  if (!estado || estado.carregando || estado.pagina >= estado.totalPaginas) return;
  estado.carregando = true;
  const meu = estado;
  try {
    const p = await obterJSON(meu.pais + "/pagina-" + (meu.pagina + 1) + ".json");
    if (meu !== estado) return;
    meu.pagina = p.pagina;
    meu.totalPaginas = p.total_paginas;
    for (const item of p.itens) {
      if (meu.vistos.has(item.id)) continue;
      meu.vistos.add(item.id);
      meu.itens.push(item);
      if (visivel(item)) $("feed").append(cartao(item));
    }
  } catch (e) {
    $("sentinela").textContent = "Erro ao carregar: " + e.message;
    meu.carregando = false;
    return;
  }
  meu.carregando = false;
  atualizarSentinela();
  if (meu.pagina < meu.totalPaginas && sentinelaPerto()) carregarProxima();
}

function renderizarFiltro() {
  $("feed").replaceChildren();
  for (const item of estado.itens) if (visivel(item)) $("feed").append(cartao(item));
  for (const b of $("categorias").children) b.setAttribute("aria-pressed", String(b.dataset.cat === estado.categoria));
  atualizarSentinela();
  if (sentinelaPerto()) carregarProxima();
}

function renderizarPainel(indice) {
  nomesFontes = Object.fromEntries(indice.fontes.map((f) => [f.id, f.nome]));
  const alertas = indice.fontes.filter((f) => !f.ok || f.alerta).length;
  const quando = new Date(indice.atualizado).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
  $("resumo-status").textContent = (navigator.onLine ? "" : "Offline · ") + "Atualizado " + quando + " · " + indice.total + " notícias · " +
    (alertas ? alertas + " alerta(s)" : "todas as fontes OK");
  const lista = $("lista-fontes");
  lista.replaceChildren();
  for (const f of indice.fontes) {
    const li = el("li");
    const classe = !f.ok ? "erro" : (f.alerta ? "alerta" : "ok");
    const sinal = !f.ok ? "[ERRO]" : (f.alerta ? "[ALERTA]" : "[OK]");
    li.append(el("span", classe, sinal + " "));
    let texto = f.nome;
    if (f.mais_recente) texto += " · última: " + new Date(f.mais_recente).toLocaleDateString("pt-BR");
    if (!f.ok) texto += " - " + f.erro;
    else if (f.alerta) texto += " - " + f.alerta;
    li.append(document.createTextNode(texto));
    lista.append(li);
  }
  for (const [cat, c] of Object.entries(indice.cobertura || {})) {
    if (!c.lacuna) continue;
    const li = el("li");
    li.append(el("span", "lacuna", "[LACUNA] "));
    li.append(document.createTextNode((CATEGORIAS[cat] || cat) + ": " + c.lacuna));
    lista.append(li);
  }
}

async function abrirPais(codigo) {
  estado = novoEstado(codigo);
  $("feed").replaceChildren();
  $("sentinela").textContent = "Carregando...";
  for (const b of $("paises").children) b.setAttribute("aria-pressed", String(b.dataset.pais === codigo));
  $("btn-pais").textContent = (nomesPaises[codigo] || codigo.toUpperCase()) + " ▾";
  if (window.GINGlobo) window.GINGlobo.focar(codigo);
  if ($("dlg-paises").open) $("dlg-paises").close();
  for (const b of $("categorias").children) b.setAttribute("aria-pressed", String(b.dataset.cat === "todas"));
  try {
    const indice = await obterJSON(codigo + "/indice.json");
    estado.totalPaginas = indice.paginas;
    estado.total = indice.total;
    renderizarPainel(indice);
    infoBoletim(codigo);
  } catch (e) {
    $("resumo-status").textContent = "Índice indisponível: " + e.message;
  }
  carregarProxima();
}

async function iniciar() {
  for (const [cat, nome] of Object.entries(CATEGORIAS)) {
    const b = el("button", null, nome);
    b.type = "button"; b.dataset.cat = cat;
    b.addEventListener("click", () => { estado.categoria = cat; renderizarFiltro(); });
    $("categorias").append(b);
  }
  let paises = {};
  try { paises = await obterJSON("paises.json"); } catch (e) {
    $("resumo-status").textContent = "Lista de países indisponível: " + e.message;
    $("sentinela").textContent = "";
    return;
  }
  for (const [codigo, p] of Object.entries(paises).sort((a, b) => a[1].nome.localeCompare(b[1].nome, "pt"))) {
    nomesPaises[codigo.toLowerCase()] = p.nome;
    const b = el("button", null, p.nome + (p.completo ? "" : " *"));
    b.type = "button"; b.dataset.pais = codigo.toLowerCase();
    b.addEventListener("click", () => { location.hash = codigo.toLowerCase(); });
    $("paises").append(b);
  }
  const dlg = $("dlg-paises"), busca = $("busca-pais");
  const semAcento = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  busca.addEventListener("input", () => {
    const q = semAcento(busca.value.trim());
    for (const b of $("paises").children) b.hidden = Boolean(q) && !semAcento(b.textContent).includes(q);
  });
  $("btn-pais").addEventListener("click", () => { busca.value = ""; busca.dispatchEvent(new Event("input")); dlg.showModal(); });
  $("fechar-paises").addEventListener("click", () => dlg.close());
  dlg.addEventListener("click", (ev) => { if (ev.target === dlg) dlg.close(); });
  for (const b of $("paises").children) b.addEventListener("click", () => dlg.close());
  const inicial = location.hash.slice(1) || Object.keys(paises)[0].toLowerCase();
  window.addEventListener("hashchange", () => abrirPais(location.hash.slice(1)));
  new IntersectionObserver((e) => { if (e[0].isIntersecting) carregarProxima(); }, { rootMargin: "600px" }).observe($("sentinela"));
  abrirPais(inicial);
}

// ===== Boletim em audio: toca com a tela apagada (Media Session) =====
const VELOCIDADES = [1, 1.25, 1.5, 1.75, 2];
const player = { boletim: null, pais: null, nome: "", fila: [], cap: -1, velocidade: 1, ultimaPosicao: 0 };
let nomesPaises = {};
const audio = () => $("audio");

async function infoBoletim(codigo) {
  try {
    const b = await obterJSON(codigo + "/boletim.json");
    const quando = new Date(b.gerado).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    const off = await estaOffline(new URL(DADOS + codigo + "/" + b.arquivo, location.href).href);
    $("info-boletim").textContent = b.noticias + " notícias · " + Math.round(b.duracao / 60) + " min · " + quando + (off ? " · offline ✓" : "");
    $("btn-ouvir").disabled = false;
  } catch {
    $("info-boletim").textContent = "boletim em áudio indisponível";
    $("btn-ouvir").disabled = true;
  }
}

async function guardarOffline(codigo, url) {
  if (!("caches" in window)) return;
  try {
    const cache = await caches.open("gin-audio-v1");
    if (await cache.match(url)) return;
    const r = await fetch(url);
    if (r.status !== 200) return;
    for (const req of await cache.keys()) {
      if (req.url.includes("/" + codigo + "/boletim-")) await cache.delete(req);
    }
    await cache.put(url, r);
    if (estado && estado.pais === codigo) infoBoletim(codigo);
  } catch {}
}

async function estaOffline(url) {
  try { return "caches" in window && !!(await (await caches.open("gin-audio-v1")).match(url)); } catch { return false; }
}

async function tocarPais(codigo, fila) {
  try {
    const b = await obterJSON(codigo + "/boletim.json");
    if (window.GINGlobo) window.GINGlobo.focar(codigo);
    Object.assign(player, { boletim: b, pais: codigo, nome: nomesPaises[codigo] || codigo.toUpperCase(), fila: fila || [], cap: -1 });
    const a = audio();
    a.src = DADOS + codigo + "/" + b.arquivo;
    a.playbackRate = player.velocidade;
    $("player").hidden = false;
    document.body.classList.add("com-player");
    $("player-pais").textContent = "GIN · " + player.nome;
    $("player-titulo").textContent = "Carregando...";
    await a.play();
    guardarOffline(codigo, new URL(a.src, location.href).href);
  } catch (e) {
    $("player").hidden = false;
    $("player-titulo").textContent = "Não foi possível tocar: " + e.message;
    if (player.fila.length) tocarPais(player.fila.shift(), player.fila);
  }
}

function capituloEm(t) {
  const caps = player.boletim ? player.boletim.capitulos : [];
  let i = 0;
  while (i + 1 < caps.length && caps[i + 1].inicio <= t + 0.05) i++;
  return i;
}

function aoMudarCapitulo(i) {
  player.cap = i;
  const c = player.boletim.capitulos[i];
  if (!c) return;
  $("player-titulo").textContent = c.titulo;
  if ("mediaSession" in navigator) {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: c.titulo, artist: c.fonte || "GIN", album: "GIN · " + player.nome,
      artwork: [{ src: "icone-512.png", sizes: "512x512", type: "image/png" }],
    });
  }
  document.querySelectorAll(".cartao.tocando").forEach((x) => x.classList.remove("tocando"));
  if (document.visibilityState === "visible" && estado && player.pais === estado.pais) {
    const card = document.querySelector('.cartao[data-id="' + c.id + '"]');
    if (card) {
      card.classList.add("tocando");
      card.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }
}

function irPara(i) {
  const caps = player.boletim ? player.boletim.capitulos : [];
  if (!caps.length) return;
  audio().currentTime = caps[Math.max(0, Math.min(i, caps.length - 1))].inicio;
}
function anterior() {
  if (!player.boletim) return;
  const t = audio().currentTime, i = capituloEm(t);
  irPara(t - player.boletim.capitulos[i].inicio > 3 ? i : i - 1);
}
function proxima() {
  if (player.boletim) irPara(capituloEm(audio().currentTime) + 1);
}
function alternar() {
  const a = audio();
  if (a.paused) a.play(); else a.pause();
}

$("btn-ouvir").addEventListener("click", () => tocarPais(estado.pais, []));
$("btn-tudo").addEventListener("click", () => {
  const todos = Object.keys(nomesPaises), i = todos.indexOf(estado.pais);
  const ordem = i >= 0 ? todos.slice(i).concat(todos.slice(0, i)) : todos;
  if (ordem.length) tocarPais(ordem[0], ordem.slice(1));
});
$("p-tocar").addEventListener("click", alternar);
$("p-anterior").addEventListener("click", anterior);
$("p-proxima").addEventListener("click", proxima);
$("p-velocidade").addEventListener("click", () => {
  player.velocidade = VELOCIDADES[(VELOCIDADES.indexOf(player.velocidade) + 1) % VELOCIDADES.length];
  audio().playbackRate = player.velocidade;
  $("p-velocidade").textContent = String(player.velocidade).replace(".", ",") + "×";
});
$("p-fechar").addEventListener("click", () => {
  audio().pause();
  $("player").hidden = true;
  document.body.classList.remove("com-player");
  document.querySelectorAll(".cartao.tocando").forEach((x) => x.classList.remove("tocando"));
});
$("player-barra").addEventListener("click", (ev) => {
  const a = audio(), r = ev.currentTarget.getBoundingClientRect();
  if (isFinite(a.duration)) a.currentTime = ((ev.clientX - r.left) / r.width) * a.duration;
});

audio().addEventListener("timeupdate", () => {
  const a = audio();
  if (!player.boletim) return;
  if (isFinite(a.duration)) $("player-progresso").style.width = (100 * a.currentTime / a.duration) + "%";
  const i = capituloEm(a.currentTime);
  if (i !== player.cap) aoMudarCapitulo(i);
  if ("mediaSession" in navigator && navigator.mediaSession.setPositionState && isFinite(a.duration)
      && Math.abs(a.currentTime - player.ultimaPosicao) > 5) {
    player.ultimaPosicao = a.currentTime;
    try { navigator.mediaSession.setPositionState({ duration: a.duration, playbackRate: a.playbackRate, position: a.currentTime }); } catch {}
  }
});
audio().addEventListener("play", () => {
  $("p-tocar").textContent = "⏸";
  if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "playing";
});
audio().addEventListener("pause", () => {
  $("p-tocar").textContent = "▶";
  if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "paused";
});
audio().addEventListener("ended", () => {
  if (player.fila.length) tocarPais(player.fila.shift(), player.fila);
  else $("player-titulo").textContent = "Fim dos boletins";
});
audio().addEventListener("error", () => {
  $("player-titulo").textContent = "Erro ao carregar o áudio";
});
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && player.cap >= 0) aoMudarCapitulo(player.cap);
});
if ("mediaSession" in navigator) {
  const a = audio();
  const acoes = {
    play: () => a.play(), pause: () => a.pause(), previoustrack: anterior, nexttrack: proxima,
    seekbackward: (d) => { a.currentTime = Math.max(0, a.currentTime - (d.seekOffset || 10)); },
    seekforward: (d) => { a.currentTime = a.currentTime + (d.seekOffset || 10); },
    seekto: (d) => { a.currentTime = d.seekTime; },
  };
  for (const [acao, f] of Object.entries(acoes)) {
    try { navigator.mediaSession.setActionHandler(acao, f); } catch {}
  }
}

iniciar();

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch((e) => console.warn("Service worker nao registrado:", e));
}
