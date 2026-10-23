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
  const dia = d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
  if (item.precisao === "hora") return dia + ", " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  if (item.precisao === "estimada") return dia + " (data estimada)";
  return dia;
}

function cartao(item) {
  const art = el("article", "cartao");
  const meta = el("div", "meta");
  meta.append(el("span", "selo", CATEGORIAS[item.categoria] || item.categoria));
  if (item.rotulo) meta.append(el("span", "rotulo", item.rotulo));
  art.append(meta);
  const h = el("h2", "titulo");
  const href = linkSeguro(item.link);
  if (href) {
    const a = el("a", null, item.titulo);
    a.href = href; a.target = "_blank"; a.rel = "noopener noreferrer";
    h.append(a);
  } else {
    h.textContent = item.titulo;
  }
  art.append(h);
  if (item.resumo) art.append(el("p", "resumo", item.resumo));
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
}

async function abrirPais(codigo) {
  estado = novoEstado(codigo);
  $("feed").replaceChildren();
  $("sentinela").textContent = "Carregando...";
  for (const b of $("paises").children) b.setAttribute("aria-pressed", String(b.dataset.pais === codigo));
  for (const b of $("categorias").children) b.setAttribute("aria-pressed", String(b.dataset.cat === "todas"));
  try {
    const indice = await obterJSON(codigo + "/indice.json");
    estado.totalPaginas = indice.paginas;
    estado.total = indice.total;
    renderizarPainel(indice);
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
  for (const [codigo, p] of Object.entries(paises)) {
    const b = el("button", null, p.nome + (p.completo ? "" : " *"));
    b.type = "button"; b.dataset.pais = codigo.toLowerCase();
    b.addEventListener("click", () => { location.hash = codigo.toLowerCase(); });
    $("paises").append(b);
  }
  const inicial = location.hash.slice(1) || Object.keys(paises)[0].toLowerCase();
  window.addEventListener("hashchange", () => abrirPais(location.hash.slice(1)));
  new IntersectionObserver((e) => { if (e[0].isIntersecting) carregarProxima(); }, { rootMargin: "600px" }).observe($("sentinela"));
  abrirPais(inicial);
}

iniciar();

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch((e) => console.warn("Service worker nao registrado:", e));
}
