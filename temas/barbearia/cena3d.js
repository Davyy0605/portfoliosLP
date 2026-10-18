/* Cena 3D da capa (three.js) — melhoria progressiva, só em desktop.
 *
 * Padrão reaproveitável em outros sites de cliente:
 * 1. Gate: só carrega com tela >= 1024px E ponteiro fino (mouse/trackpad), sem prefers-reduced-motion
 *    e sem navigator.connection.saveData. Fora disso nada é baixado e fica a versão CSS/estática.
 * 2. Carregamento: import() dinâmico, depois do "load" e com a página ociosa (requestIdleCallback,
 *    com setTimeout de reserva). Nunca <script src> estático: o celular não baixa nada do three.
 * 3. CDN com versão fixa: o import map da página aponta "three" e "three/addons/" para
 *    cdn.jsdelivr.net/npm/three@0.160.0 (mudar a versão só lá, testando antes).
 * 4. Custo: devicePixelRatio limitado a 2; o laço de render para fora da tela (IntersectionObserver)
 *    e com a aba oculta (visibilitychange); tudo é descartado (dispose) no pagehide.
 * 5. Acessibilidade: o canvas é decorativo (aria-hidden) e só aparece quando o 1º quadro está pronto;
 *    se o import falhar, o poste em CSS continua no lugar.
 * Este arquivo é incluído inline pelo landing.html (o build só copia tema.css do tema).
 */
const LARGO = "(min-width: 1024px) and (pointer: fine)";
const pode = () =>
  matchMedia(LARGO).matches &&
  !matchMedia("(prefers-reduced-motion: reduce)").matches &&
  !(navigator.connection && navigator.connection.saveData);

function quandoOcioso(fn) {
  const agendar = () =>
    "requestIdleCallback" in window ? requestIdleCallback(fn, { timeout: 3000 }) : setTimeout(fn, 1200);
  if (document.readyState === "complete") agendar();
  else addEventListener("load", agendar, { once: true });
}

async function iniciar() {
  const capa = document.querySelector(".capa");
  if (!capa || !pode()) return;
  let THREE, RoomEnvironment;
  try {
    THREE = await import("three");
    ({ RoomEnvironment } = await import("three/addons/environments/RoomEnvironment.js"));
  } catch (e) {
    return; // sem rede ou CDN fora: fica o poste em CSS
  }

  const canvas = document.createElement("canvas");
  canvas.className = "cena3d";
  canvas.setAttribute("aria-hidden", "true");
  capa.append(canvas);

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: "low-power" });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.95;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const cena = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  const ambiente = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  cena.environment = ambiente;

  const camera = new THREE.PerspectiveCamera(26, 1, 0.1, 50);
  camera.position.set(0, 0.1, 9.6);

  // Luz de tarde vinda da janela (esquerda, quente) + contraluz fria e suave.
  cena.add(new THREE.HemisphereLight(0xfff1dc, 0x3a3129, 0.55));
  const sol = new THREE.DirectionalLight(0xffd9a8, 2.4);
  sol.position.set(-3.5, 2.5, 3.5);
  sol.castShadow = true;
  sol.shadow.mapSize.set(1024, 1024);
  sol.shadow.radius = 6;
  Object.assign(sol.shadow.camera, { left: -2, right: 2, top: 2.5, bottom: -2.5, near: 0.5, far: 12 });
  cena.add(sol);
  const recorte = new THREE.DirectionalLight(0xe8eef5, 0.8);
  recorte.position.set(3, 1, -2);
  cena.add(recorte);

  // Listra em hélice: textura com faixas a 45° que fecham emenda; repeat.y deixa o ângulo certo no cilindro.
  const tela = document.createElement("canvas");
  tela.width = tela.height = 256;
  const ctx = tela.getContext("2d");
  const img = ctx.createImageData(256, 256);
  const cores = [[162, 64, 28], [251, 246, 238], [43, 36, 30], [251, 246, 238]];
  const cortes = [44, 64, 108, 128];
  for (let y = 0; y < 256; y++) {
    for (let x = 0; x < 256; x++) {
      const v = (x + y) % 128;
      const c = cores[cortes.findIndex((k) => v < k)];
      const i = (y * 256 + x) * 4;
      img.data[i] = c[0]; img.data[i + 1] = c[1]; img.data[i + 2] = c[2]; img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  const listra = new THREE.CanvasTexture(tela);
  listra.colorSpace = THREE.SRGBColorSpace;
  listra.wrapS = listra.wrapT = THREE.RepeatWrapping;
  listra.anisotropy = 4;
  const R = 0.36, H = 2.5;
  listra.repeat.set(1, H / (2 * Math.PI * R));

  const poste = new THREE.Group();
  const geos = [], mats = [];
  const malha = (geo, mat) => { geos.push(geo); mats.push(mat); const m = new THREE.Mesh(geo, mat); m.castShadow = true; return m; };

  const miolo = malha(new THREE.CylinderGeometry(R, R, H, 64, 1, true),
    new THREE.MeshStandardMaterial({ map: listra, roughness: 0.42, metalness: 0 }));
  poste.add(miolo);
  const vidro = malha(new THREE.CylinderGeometry(R + 0.05, R + 0.05, H + 0.02, 64, 1, true),
    new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.04, metalness: 0, transparent: true, opacity: 0.16, clearcoat: 1, envMapIntensity: 1.4 }));
  vidro.castShadow = false;
  poste.add(vidro);

  const cromo = new THREE.MeshStandardMaterial({ color: 0xf2ece2, roughness: 0.22, metalness: 1, envMapIntensity: 1.6 });
  mats.push(cromo);
  const tampa = (sinal) => {
    const g = new THREE.Group();
    const aro = malha(new THREE.CylinderGeometry(R + 0.1, R + 0.1, 0.16, 48), cromo);
    aro.position.y = sinal * (H / 2 + 0.08);
    const cupula = malha(new THREE.SphereGeometry(R + 0.1, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2), cromo);
    cupula.scale.y = 0.55;
    cupula.position.y = sinal * (H / 2 + 0.16);
    if (sinal < 0) cupula.rotation.x = Math.PI;
    const bola = malha(new THREE.SphereGeometry(0.11, 24, 16), cromo);
    bola.position.y = sinal * (H / 2 + 0.16 + (R + 0.1) * 0.55 + 0.07);
    g.add(aro, cupula, bola);
    return g;
  };
  poste.add(tampa(1), tampa(-1));
  cena.add(poste);

  // Parede invisível que só recebe sombra: a sombra do poste cai sobre a foto.
  const paredeGeo = new THREE.PlaneGeometry(8, 8);
  const paredeMat = new THREE.ShadowMaterial({ opacity: 0.22 });
  geos.push(paredeGeo); mats.push(paredeMat);
  const parede = new THREE.Mesh(paredeGeo, paredeMat);
  parede.position.z = -0.95;
  parede.receiveShadow = true;
  cena.add(parede);

  function medir() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  const ro = new ResizeObserver(medir);
  ro.observe(canvas);
  medir();

  // Ponteiro: o poste inclina de leve na direção do mouse (suavizado no laço, sem trabalho no evento).
  const alvo = { x: 0, y: 0 }, atual = { x: 0, y: 0 };
  const mover = (e) => {
    const r = capa.getBoundingClientRect();
    alvo.x = ((e.clientX - r.left) / r.width) * 2 - 1;
    alvo.y = ((e.clientY - r.top) / r.height) * 2 - 1;
  };
  const sair = () => { alvo.x = 0; alvo.y = 0; };
  capa.addEventListener("pointermove", mover);
  capa.addEventListener("pointerleave", sair);

  let visivel = true, rodando = false, quadro = 0, antes = performance.now(), primeiro = true;
  const relogio = { t: 0 };
  function laco(agora) {
    if (!rodando) return;
    const dt = Math.min((agora - antes) / 1000, 0.05);
    antes = agora;
    relogio.t += dt;
    listra.offset.y -= dt * 0.22;
    atual.x += (alvo.x - atual.x) * Math.min(dt * 4, 1);
    atual.y += (alvo.y - atual.y) * Math.min(dt * 4, 1);
    poste.rotation.z = -atual.x * 0.14 + Math.sin(relogio.t * 0.7) * 0.02;
    poste.rotation.x = atual.y * 0.12;
    poste.rotation.y = Math.sin(relogio.t * 0.4) * 0.25 + atual.x * 0.35;
    renderer.render(cena, camera);
    if (primeiro) { primeiro = false; document.documentElement.classList.add("cena3d-pronta"); }
    quadro = requestAnimationFrame(laco);
  }
  const ligar = () => {
    if (rodando || !visivel || document.hidden || !matchMedia(LARGO).matches) return;
    rodando = true;
    antes = performance.now();
    quadro = requestAnimationFrame(laco);
  };
  const desligar = () => { rodando = false; cancelAnimationFrame(quadro); };

  const io = new IntersectionObserver(([e]) => { visivel = e.isIntersecting; visivel ? ligar() : desligar(); });
  io.observe(canvas);
  const aba = () => (document.hidden ? desligar() : ligar());
  document.addEventListener("visibilitychange", aba);
  // janela estreitada abaixo de 1024px: o CSS esconde o canvas e o laço para
  const largura = matchMedia(LARGO);
  const trocou = () => (largura.matches ? ligar() : desligar());
  largura.addEventListener("change", trocou);

  addEventListener("pagehide", () => {
    desligar();
    io.disconnect(); ro.disconnect();
    document.removeEventListener("visibilitychange", aba);
    largura.removeEventListener("change", trocou);
    capa.removeEventListener("pointermove", mover);
    capa.removeEventListener("pointerleave", sair);
    geos.forEach((g) => g.dispose());
    mats.forEach((m) => m.dispose());
    listra.dispose(); ambiente.dispose(); pmrem.dispose();
    renderer.dispose();
    canvas.remove(); // se a página voltar do cache (bfcache), o poste em CSS reaparece
    document.documentElement.classList.remove("cena3d-pronta");
  }, { once: true });

  ligar();
}

if (pode()) quandoOcioso(iniciar);
