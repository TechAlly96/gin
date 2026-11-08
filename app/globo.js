"use strict";
// GIN - globo 3D. globe.gl (MIT); textura NASA Blue Marble e contornos Natural Earth (dominio publico).
// Independente do app.js: le a lista de paises, destaca os cobertos, abre o pais ao tocar
// e voa ate o pais do boletim em reproducao (window.GINGlobo.focar, chamado em tocarPais).
(function () {
  const VENDOR = "vendor/";
  const EXCECOES = { FRA: "FR", NOR: "NO", KOS: "XK" }; // Natural Earth marca alguns paises com ISO_A2 = -99
  const MARCADORES = { SG: [1.35, 103.82] };             // pequenos demais para o mapa 1:110m
  const caixa = document.getElementById("globo");
  let globo = null, centros = {}, cobertos = {}, atual = null, retomar = null;

  function suportaWebGL() {
    try {
      const c = document.createElement("canvas");
      return !!(window.WebGLRenderingContext && (c.getContext("webgl") || c.getContext("experimental-webgl")));
    } catch (e) { return false; }
  }
  function codigoDe(p) {
    if (p.ISO_A2 && p.ISO_A2 !== "-99") return String(p.ISO_A2).toUpperCase();
    return EXCECOES[p.ADM0_A3] || EXCECOES[p.ISO_A3] || "";
  }
  function centro(geometria) { // media esferica do contorno principal (vale ate para quem cruza a linha de data)
    const poligonos = geometria.type === "Polygon" ? [geometria.coordinates] : geometria.coordinates;
    let maior = poligonos[0][0];
    poligonos.forEach((pg) => { if (pg[0].length > maior.length) maior = pg[0]; });
    let x = 0, y = 0, z = 0;
    maior.forEach(([lng, lat]) => {
      const a = lat * Math.PI / 180, b = lng * Math.PI / 180;
      x += Math.cos(a) * Math.cos(b); y += Math.cos(a) * Math.sin(b); z += Math.sin(a);
    });
    return [Math.atan2(z, Math.hypot(x, y)) * 180 / Math.PI, Math.atan2(y, x) * 180 / Math.PI];
  }
  function carregarScript(src) {
    return new Promise((ok, falha) => {
      const s = document.createElement("script");
      s.src = src; s.onload = ok; s.onerror = falha;
      document.head.appendChild(s);
    });
  }
  function nomeDe(c, f) { return (cobertos[c] && cobertos[c].nome) || (f && f.properties.NAME) || c; }
  function redesenhar() {
    globo.polygonCapColor((f) => {
      const c = f.properties._codigo;
      if (c === atual) return "rgba(251, 191, 36, 0.85)";
      return cobertos[c] ? "rgba(56, 189, 248, 0.55)" : "rgba(255, 255, 255, 0.03)";
    }).polygonAltitude((f) => {
      const c = f.properties._codigo;
      return c === atual ? 0.05 : (cobertos[c] ? 0.012 : 0.004);
    }).pointsData(Object.keys(MARCADORES).filter((c) => cobertos[c])
      .map((c) => ({ codigo: c, lat: MARCADORES[c][0], lng: MARCADORES[c][1] })));
  }
  function focar(codigo) {
    atual = String(codigo || "").toUpperCase();
    if (!globo) return;
    redesenhar();
    const c = centros[atual] || MARCADORES[atual];
    if (!c) return;
    globo.controls().autoRotate = false;
    globo.pointOfView({ lat: c[0], lng: c[1], altitude: 1.6 }, 1800);
    clearTimeout(retomar);
    retomar = setTimeout(() => { if (globo) globo.controls().autoRotate = true; }, 45000);
  }
  function abrir(codigo) { if (codigo && cobertos[codigo]) location.hash = codigo.toLowerCase(); }
  function doHash() { return location.hash.slice(1).toUpperCase(); }

  async function iniciar() {
    if (!caixa) return;
    if (!suportaWebGL()) { caixa.hidden = true; return; }
    try {
      const [, geo, lista] = await Promise.all([
        carregarScript(VENDOR + "globe.gl.min.js"),
        fetch(VENDOR + "paises-110m.geojson").then((r) => r.json()),
        fetch("../dados/paises.json", { cache: "no-cache" }).then((r) => r.json()),
      ]);
      cobertos = lista;
      geo.features.forEach((f) => {
        const c = codigoDe(f.properties);
        f.properties._codigo = c;
        if (c) centros[c] = centro(f.geometry);
      });
      globo = Globe({ animateIn: true })(caixa)
        .globeImageUrl(VENDOR + "terra-blue-marble.jpg")
        .backgroundColor("rgba(0,0,0,0)")
        .showAtmosphere(true).atmosphereColor("#7dd3fc").atmosphereAltitude(0.15)
        .polygonsData(geo.features)
        .polygonSideColor(() => "rgba(56, 189, 248, 0.15)")
        .polygonStrokeColor(() => "rgba(255, 255, 255, 0.25)")
        .polygonLabel((f) => {
          const c = f.properties._codigo;
          return cobertos[c] ? nomeDe(c, f) + " · tocar para abrir" : nomeDe(c, f);
        })
        .onPolygonClick((f) => abrir(f.properties._codigo))
        .pointColor(() => "#38bdf8").pointAltitude(0.02).pointRadius(0.6)
        .pointLabel((p) => nomeDe(p.codigo) + " · tocar para abrir")
        .onPointClick((p) => abrir(p.codigo))
        .width(caixa.clientWidth).height(caixa.clientHeight);
      globo.renderer().setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
      globo.controls().autoRotate = true;
      globo.controls().autoRotateSpeed = 0.4;
      globo.controls().enableZoom = false; // a rolagem da pagina continua normal
      redesenhar();
      if (cobertos[doHash()]) focar(doHash());
      else if (atual) focar(atual);
      window.addEventListener("hashchange", () => { if (cobertos[doHash()]) focar(doHash()); });
      window.addEventListener("resize", () => globo.width(caixa.clientWidth).height(caixa.clientHeight));
      new IntersectionObserver(([e]) => { if (e.isIntersecting) globo.resumeAnimation(); else globo.pauseAnimation(); }).observe(caixa);
      document.addEventListener("visibilitychange", () => { if (document.hidden) globo.pauseAnimation(); else globo.resumeAnimation(); });
    } catch (e) {
      caixa.hidden = true;
      console.warn("GIN: globo indisponivel", e);
    }
  }
  window.GINGlobo = { focar };
  if (document.readyState === "complete") iniciar(); else window.addEventListener("load", iniciar);
})();
