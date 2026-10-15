// The Horizon world: a dark mirror orb over a night sea, whose edge is a live equaliser.
// The scenery changes with each chapter of the call. It reads one Signal object every
// frame; the view writes that object from the live call or the recorded sample.

import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { Reflector } from "three/examples/jsm/objects/Reflector.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";

export type Signal = {
  started: boolean;
  ended: boolean;
  who: "agent" | "lead" | null;
  agent: number; // voice loudness 0..1
  lead: number;
  bands: Float32Array; // 32 log bands of whoever speaks, 0..1
  chapter: number; // index in CHAPTERS
  laugh: number; // set to 1 on a laugh; the world lets it fade
};

export const newSignal = (): Signal => ({
  started: false,
  ended: false,
  who: null,
  agent: 0,
  lead: 0,
  bands: new Float32Array(32),
  chapter: 0,
  laugh: 0,
});

type Place = "near" | "wide" | "under" | "sky" | "dawn";
export const CHAPTERS: { label: string; title: string; mtn: number; sub: number; aur: number; dawn: number; place: Place }[] = [
  { label: "I", title: "Night sea", mtn: 0, sub: 0, aur: 0, dawn: 0, place: "near" },
  { label: "II", title: "The mountains rise", mtn: 1, sub: 0, aur: 0, dawn: 0, place: "wide" },
  { label: "III", title: "Under the surface", mtn: 1, sub: 1, aur: 0, dawn: 0, place: "under" },
  { label: "IV", title: "The sky answers", mtn: 1, sub: 0, aur: 1, dawn: 0, place: "sky" },
  { label: "V", title: "First light", mtn: 1, sub: 0, aur: 0.45, dawn: 0.4, place: "near" },
  { label: "VI", title: "Morning", mtn: 1, sub: 0, aur: 0.15, dawn: 1, place: "dawn" },
];

const LIME = new THREE.Color(0xd8ff36);

const SKY_FS = `uniform float time, aur, dawn; uniform vec3 hz; varying vec3 vD;
  float h(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
  void main(){ vec3 d = normalize(vD); float y = d.y; float az = atan(d.x, -d.z);
    vec3 zen = mix(vec3(.0,.0,.004), vec3(.004,.012,.02), dawn);
    vec3 col = mix(hz, zen, smoothstep(.0, .5, y));
    vec2 g = vec2(az * 260., asin(clamp(y, -1., 1.)) * 260.); vec2 c = floor(g); float r = h(c);
    vec2 off = vec2(h(c + 3.1), h(c + 7.3)) * .5 + .25;
    float st = step(.992, r) * smoothstep(.16, .0, length(fract(g) - off)) * (.6 + .4*sin(time*(1.+r*3.) + r*40.));
    col += vec3(.9, 1., .85) * st * smoothstep(.02, .2, y) * (1. - dawn*.9);
    float band = .26 + .07*sin(az*2.3 + time*.06) + .03*sin(az*7.1 - time*.11);
    float cur = exp(-pow((y - band) * 9., 2.)) * smoothstep(band - .08, band + .02, y);
    float streak = .78 + .22*sin(az*26. + sin(az*4. + time*.2)*3.);
    vec3 ac = mix(vec3(.62,.78,.16), vec3(.22,.3,.85), smoothstep(band - .03, band + .1, y));
    ac = mix(ac, vec3(1.,.25,.65), smoothstep(band + .1, band + .2, y) * .6);
    col += ac * cur * streak * aur * .45 * smoothstep(-1.4, .1, -abs(az));
    vec3 sd = normalize(vec3(0., mix(-.06, .07, dawn), -1.));
    float sdot = max(dot(d, sd), 0.);
    col += vec3(.85, 1., .4) * pow(sdot, 1400.) * 1.6 * dawn + vec3(.8,1.,.3) * pow(sdot, 30.) * .1 * dawn;
    col += vec3(.85,1.,.21) * exp(-abs(y) * 160.) * .3 * dawn + vec3(.6,.75,.2) * exp(-max(y, 0.) * 9.) * .05 * dawn;
    col = mix(col, vec3(.004), smoothstep(.0, -.08, y));
    gl_FragColor = vec4(col, 1.);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }`;

const MTN_FS = `uniform vec3 lime, hz, camPos; uniform float glow, dawn; varying vec3 vW; varying vec3 vN;
  void main(){ vec3 n = normalize(vN); vec3 v = normalize(camPos - vW);
    float rimL = pow(1. - max(dot(n, v), 0.), 3.);
    vec3 col = vec3(.006) + vec3(.012,.014,.012) * max(dot(n, normalize(vec3(-.3,.8,.4))), 0.);
    col += lime * rimL * (.03 + .08*dawn);
    float f = vW.y * .32; float fw = max(fwidth(f), 1e-4); float dl = abs(fract(f) - .5) / fw;
    float line = (1. - smoothstep(.3, 1.3, dl)) * smoothstep(.0, 1.5, vW.y) * smoothstep(.45, .12, fw);
    col += lime * line * glow * .52;
    col += vec3(.8,1.,.3) * pow(max(dot(n, normalize(vec3(0., .2, -1.))), 0.), 4.) * dawn * .06;
    float dist = length(camPos - vW);
    col = mix(col, hz, smoothstep(160., 520., dist) * .6);
    gl_FragColor = vec4(col, 1.);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }`;

const SEA_FS = `uniform vec3 color; uniform sampler2D tDiffuse; uniform float time, level; uniform vec2 center; uniform vec3 tint; varying vec4 vUv; varying vec2 vP;
  void main(){ vec2 d = vP - center; float r = length(d);
    float w = sin(r*2.4 - time*2.4) * exp(-r*.16) * (.002 + level*.03);
    float n = (sin(vP.x*.7 + time*.5) * sin(vP.y*.9 - time*.4) + .5*sin(vP.x*2.1 - vP.y*1.3 + time*.9)) * .0022;
    vec4 uv = vUv; uv.xy += (normalize(d + 1e-4)*w + n) * uv.w;
    vec3 base = texture2DProj(tDiffuse, uv).rgb;
    float glint = pow(max(0., sin(r*2.4 - time*2.4)), 30.) * exp(-r*.2) * level * .6;
    gl_FragColor = vec4(mix(tint, base, .7) + vec3(.85,1.,.3) * glint * .65, 1.);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }`;

const FILM_FS = `uniform sampler2D tDiffuse; uniform float time, sub, aspect; varying vec2 vUv;
  float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)))*43758.5453); }
  void main(){ vec2 uv = vUv; vec2 c = uv - .5;
    float wl = mix(-.12, 1.14, sub) + .014*sin(uv.x*13. + time*1.5) + .007*sin(uv.x*31. - time*2.2);
    float under = smoothstep(wl + .003, wl - .003, uv.y);
    vec2 wob = vec2(sin(uv.y*26. + time*1.4), cos(uv.x*21. + time*1.1)) * .0045 * under;
    vec3 col = texture2D(tDiffuse, uv + wob).rgb;
    vec2 p = vec2(uv.x * aspect, uv.y) * 7.;
    float ca = abs(sin(p.x*1.3 + sin(p.y*1.7 + time*.7)*1.6) * sin(p.y*1.5 + sin(p.x*1.1 - time*.6)*1.6));
    ca = pow(1. - ca, 10.);
    float rays = pow(.5 + .5*sin(uv.x*18. + sin(uv.x*4. + time*.25)*2.5), 10.) * smoothstep(.15, 1., uv.y);
    vec2 sp = vec2(uv.x * aspect * 60., uv.y * 60. - time * 2.5); float sk = step(.993, h(floor(sp))) * smoothstep(.5, .1, length(fract(sp) - .5));
    vec3 deep = col * vec3(.13, .3, .29) + vec3(.0, .022, .024) + vec3(.6,1.,.3) * ca * .045 * smoothstep(.0, 1., uv.y) + vec3(.55,1.,.4) * rays * .045 + vec3(.8,1.,.7) * sk * .28;
    col = mix(col, deep, under);
    col += vec3(.85,1.,.5) * exp(-abs(uv.y - wl) * 500.) * .3 * step(.001, sub) * step(sub, .999);
    col += (h(uv*vec2(1440.,900.) + fract(time)*91.) - .5) * .045;
    col *= 1. - dot(c, c) * .75;
    gl_FragColor = vec4(col, 1.); }`;

const VS_UV = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`;

function hash(x: number, y: number) {
  const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return s - Math.floor(s);
}
function noise(x: number, y: number) {
  const ix = Math.floor(x), iy = Math.floor(y), fx = x - ix, fy = y - iy;
  const ux = fx * fx * (3 - 2 * fx), uy = fy * fy * (3 - 2 * fy);
  const a = hash(ix, iy), b = hash(ix + 1, iy), c = hash(ix, iy + 1), d = hash(ix + 1, iy + 1);
  return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy;
}
function ridged(x: number, y: number) {
  let s = 0, a = 0.5;
  for (let i = 0; i < 5; i++) {
    s += a * (1 - Math.abs(noise(x, y) * 2 - 1));
    x *= 2.03;
    y *= 2.03;
    a *= 0.5;
  }
  return s;
}

/** Mounts the world on a canvas and runs it until dispose(). */
export function createWorld(canvas: HTMLCanvasElement, signal: Signal): { dispose: () => void } {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const W = () => canvas.clientWidth || window.innerWidth;
  const H = () => canvas.clientHeight || window.innerHeight;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.setSize(W(), H(), false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.95;
  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;
  const camera = new THREE.PerspectiveCamera(42, W() / H(), 0.1, 800);

  // ---- sky ----
  const horizon = new THREE.Color();
  const skyU = { time: { value: 0 }, aur: { value: 0 }, dawn: { value: 0 }, hz: { value: horizon } };
  scene.add(
    new THREE.Mesh(
      new THREE.SphereGeometry(500, 64, 32),
      new THREE.ShaderMaterial({
        side: THREE.BackSide,
        depthWrite: false,
        uniforms: skyU,
        vertexShader: `varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
        fragmentShader: SKY_FS,
      }),
    ),
  );

  // ---- mountains that rise out of the water ----
  const mtnU = { lime: { value: LIME }, glow: { value: 0.5 }, dawn: { value: 0 }, hz: { value: horizon }, camPos: { value: camera.position } };
  const mtnMat = new THREE.ShaderMaterial({
    uniforms: mtnU,
    vertexShader: `varying vec3 vW; varying vec3 vN; void main(){ vec4 w = modelMatrix*vec4(position,1.); vW = w.xyz; vN = normalize(mat3(modelMatrix)*normal); gl_Position = projectionMatrix*viewMatrix*w; }`,
    fragmentShader: MTN_FS,
  });
  const range = (w: number, d: number, sx: number, sz: number, peaks: [number, number, number][], seed: number) => {
    const g = new THREE.PlaneGeometry(w, d, sx, sz);
    g.rotateX(-Math.PI / 2);
    const p = g.attributes.position as THREE.BufferAttribute;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), z = p.getZ(i);
      let hgt = 0;
      for (const [px, ph, pw] of peaks) hgt += ph * Math.exp(-((x - px) ** 2) / (2 * pw * pw));
      const fall = Math.exp(-(z * z) / (2 * (d * 0.22) ** 2));
      p.setY(i, hgt * 0.5 * fall * (0.55 + 0.7 * ridged(x * 0.025 + seed, z * 0.025 + seed)) - 4);
    }
    g.computeVertexNormals();
    return new THREE.Mesh(g, mtnMat);
  };
  const mountains = [
    { m: range(560, 110, 260, 60, [[-120, 70, 70], [10, 95, 60], [140, 60, 80], [240, 40, 50]], 3.1), x: 0, z: -330, delay: 0 },
    { m: range(180, 60, 140, 40, [[-20, 38, 30], [40, 26, 28]], 7.7), x: -150, z: -190, delay: 0.18 },
    { m: range(160, 60, 140, 40, [[0, 30, 26], [-50, 18, 22]], 11.3), x: 160, z: -175, delay: 0.3 },
  ];
  for (const o of mountains) {
    o.m.position.set(o.x, -60, o.z);
    scene.add(o.m);
  }

  // ---- the sea ----
  const seaU = { time: { value: 0 }, level: { value: 0 }, center: { value: new THREE.Vector2() }, tint: { value: new THREE.Color(0x050605) } };
  const water = new Reflector(new THREE.PlaneGeometry(1200, 1200), {
    textureWidth: W() * 0.6,
    textureHeight: H() * 0.6,
    color: 0x777777,
    shader: {
      name: "HoplonSea",
      uniforms: { color: { value: null }, tDiffuse: { value: null }, textureMatrix: { value: null }, ...seaU },
      vertexShader: `uniform mat4 textureMatrix; varying vec4 vUv; varying vec2 vP;
        void main(){ vUv = textureMatrix*vec4(position,1.); vP = position.xy; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
      fragmentShader: SEA_FS,
    },
  });
  water.rotation.x = -Math.PI / 2;
  scene.add(water);
  const Wu = (water.material as THREE.ShaderMaterial).uniforms;

  // ---- the orb and its equaliser edge ----
  const ORB_Y = 2.7;
  const orb = new THREE.Mesh(
    new THREE.SphereGeometry(1.15, 96, 64),
    new THREE.MeshPhysicalMaterial({ color: 0x050505, metalness: 0.7, roughness: 0.14, clearcoat: 1, clearcoatRoughness: 0.04, envMapIntensity: 0.9 }),
  );
  orb.position.set(0, ORB_Y, 0);
  scene.add(orb);
  const rimMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    uniforms: { c: { value: LIME.clone() }, k: { value: 0.3 } },
    vertexShader: `varying vec3 vN; varying vec3 vV; void main(){ vec4 mv = modelViewMatrix*vec4(position,1.); vN = normalize(normalMatrix*normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix*mv; }`,
    fragmentShader: `uniform vec3 c; uniform float k; varying vec3 vN; varying vec3 vV; void main(){ float f = pow(1. - max(dot(vN, vV), 0.), 3.); gl_FragColor = vec4(c * f * k * 1.6, f * k); }`,
  });
  orb.add(new THREE.Mesh(new THREE.SphereGeometry(1.17, 64, 48), rimMat));
  const BARS = 180;
  const eq = new THREE.Group();
  scene.add(eq);
  const barGeo = new THREE.PlaneGeometry(0.022, 1);
  barGeo.translate(0, 0.5, 0);
  const barMat = new THREE.MeshBasicMaterial({ color: LIME.clone(), transparent: true, opacity: 0.72, toneMapped: false, depthWrite: false });
  const bars = new THREE.InstancedMesh(barGeo, barMat, BARS);
  eq.add(bars);
  const ringPts: THREE.Vector3[] = [];
  for (let i = 0; i <= 256; i++) {
    const a = (i / 256) * Math.PI * 2;
    ringPts.push(new THREE.Vector3(Math.cos(a) * 1.25, Math.sin(a) * 1.25, 0));
  }
  const ringMat = new THREE.LineBasicMaterial({ color: LIME, transparent: true, opacity: 0.2, toneMapped: false });
  eq.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(ringPts), ringMat));
  const glowCanvas = document.createElement("canvas");
  glowCanvas.width = glowCanvas.height = 128;
  const gctx = glowCanvas.getContext("2d")!;
  const grad = gctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.25, "rgba(255,255,255,.35)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  gctx.fillStyle = grad;
  gctx.fillRect(0, 0, 128, 128);
  const glowTex = new THREE.CanvasTexture(glowCanvas);
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: LIME, transparent: true, opacity: 0.06, depthWrite: false, blending: THREE.AdditiveBlending }));
  halo.scale.setScalar(5);
  scene.add(halo);
  const dummy = new THREE.Object3D();
  const barLen = new Float32Array(BARS);

  // ---- sparks drifting up around the orb ----
  const M = 800;
  const mg = new THREE.BufferGeometry();
  const mp = new Float32Array(M * 3);
  const ms = new Float32Array(M);
  for (let i = 0; i < M; i++) {
    mp.set([(Math.random() - 0.5) * 22, Math.random() * 10, -12 + Math.random() * 16], i * 3);
    ms[i] = Math.random();
  }
  mg.setAttribute("position", new THREE.BufferAttribute(mp, 3));
  const motesMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    uniforms: { opacity: { value: 0.3 }, px: { value: renderer.getPixelRatio() } },
    vertexShader: `uniform float px; void main(){ vec4 mv = modelViewMatrix*vec4(position,1.); gl_Position = projectionMatrix*mv; gl_PointSize = min(5., 22. / -mv.z) * px; }`,
    fragmentShader: `uniform float opacity; void main(){ float d = length(gl_PointCoord - .5); gl_FragColor = vec4(.9, 1., .7, pow(smoothstep(.5, 0., d), 2.) * opacity); }`,
  });
  scene.add(new THREE.Points(mg, motesMat));

  // ---- finish: bloom, grain, the waterline ----
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(W(), H()), 0.42, 0.4, 0.78);
  composer.addPass(bloom);
  const film = new ShaderPass({
    uniforms: { tDiffuse: { value: null }, time: { value: 0 }, sub: { value: 0 }, aspect: { value: W() / H() } },
    vertexShader: VS_UV,
    fragmentShader: FILM_FS,
  });
  composer.addPass(film);
  composer.addPass(new OutputPass());

  // ---- motion ----
  const PLACES: Record<Place | "intro", { pos: THREE.Vector3; look: THREE.Vector3 }> = {
    near: { pos: new THREE.Vector3(0, 3.0, 8.4), look: new THREE.Vector3(0, 3.4, -30) },
    wide: { pos: new THREE.Vector3(4, 3.4, 15), look: new THREE.Vector3(-2, 6, -120) },
    under: { pos: new THREE.Vector3(0.6, 1.6, 9.5), look: new THREE.Vector3(0, 2.6, -10) },
    sky: { pos: new THREE.Vector3(0, 1.4, 11), look: new THREE.Vector3(0, 26, -120) },
    dawn: { pos: new THREE.Vector3(0, 3.4, 18), look: new THREE.Vector3(0, 9, -160) },
    intro: { pos: new THREE.Vector3(0, 6, 30), look: new THREE.Vector3(0, 3, -40) },
  };
  const cur = { mtn: 0, sub: 0, aur: 0, dawn: 0 };
  const look = PLACES.intro.look.clone();
  camera.position.copy(PLACES.intro.pos);
  camera.lookAt(look);
  const NIGHT_HZ = new THREE.Color(0x060706), DAWN_HZ = new THREE.Color(0x161d0c), AUR_HZ = new THREE.Color(0x0a0f1a);
  const tmpC = new THREE.Color(), want = new THREE.Vector3(), orbPos = new THREE.Vector3(0, ORB_Y, 0);
  const clock = new THREE.Clock();
  let orbLift = 0, last = performance.now(), raf = 0, laugh = 0;

  const frame = () => {
    raf = requestAnimationFrame(frame);
    const now = performance.now();
    const f = Math.min(4, (now - last) / 16.67); // frames at 60 fps, so pace holds on slow machines
    last = now;
    const ease = (k: number) => 1 - Math.pow(1 - k, f);
    const t = clock.getElapsedTime();
    const s = signal;
    const a = s.agent, l = s.lead;
    if (s.laugh > laugh) laugh = s.laugh;
    s.laugh = 0;
    laugh *= Math.pow(0.985, f);
    const C = CHAPTERS[Math.max(0, Math.min(CHAPTERS.length - 1, s.chapter))]!;
    const on = s.started ? 1 : 0;
    cur.mtn += (C.mtn * on - cur.mtn) * ease(0.006);
    cur.sub += (C.sub * on - cur.sub) * ease(0.012);
    cur.aur += (C.aur * on - cur.aur) * ease(0.01) + laugh * 0.01 * f;
    cur.dawn += ((s.ended ? 1 : C.dawn * on) - cur.dawn) * ease(0.005);

    for (const o of mountains) {
      const r = Math.min(1, Math.max(0, (cur.mtn - o.delay) / (1 - o.delay)));
      o.m.position.y = -60 + 60 * (1 - Math.pow(1 - r, 3));
    }
    horizon.copy(NIGHT_HZ).lerp(DAWN_HZ, cur.dawn).lerp(AUR_HZ, cur.aur * 0.4 * (1 - cur.dawn));
    skyU.time.value = t;
    skyU.aur.value = Math.min(1.4, cur.aur);
    skyU.dawn.value = cur.dawn;
    mtnU.dawn.value = cur.dawn;
    mtnU.glow.value = 0.3 + (a + l) * 0.45 + cur.aur * 0.12;
    Wu.time!.value = t;
    Wu.level!.value += (Math.max(a, l * 0.6) - Wu.level!.value) * ease(0.2);

    // the camera: each chapter has a place; the agent draws you toward the orb, the Lead lets you drift back
    const P = s.started ? PLACES[s.ended ? "dawn" : C.place] : PLACES.intro;
    want.copy(P.pos);
    if (!reduced && !s.ended) {
      if (s.who === "agent") want.lerp(orbPos, 0.18);
      else if (s.who === "lead") want.sub(orbPos).multiplyScalar(1.15).add(orbPos);
    }
    camera.position.lerp(want, ease(0.008));
    look.lerp(P.look, ease(0.008));
    if (!reduced) camera.position.y += Math.sin(t * 0.4) * 0.002;
    camera.lookAt(look);

    if (s.ended) orbLift = Math.min(1, orbLift + 0.003 * f);
    else orbLift = Math.max(0, orbLift - 0.01 * f);
    orb.position.set(0, ORB_Y + Math.sin(t * 0.6) * 0.06 + orbLift * orbLift * 1.2, 0);
    orb.rotation.y += 0.003 * f;
    eq.position.copy(orb.position);
    eq.quaternion.copy(camera.quaternion);
    halo.position.copy(orb.position);
    halo.material.opacity = 0.06 + (a + l) * 0.09 + laugh * 0.07;
    const lvl = Math.max(a, l);
    const col = s.who === "lead" ? tmpC.setRGB(0.74, 0.77, 0.8) : LIME;
    barMat.color.lerp(col, ease(0.08));
    rimMat.uniforms.c!.value.lerp(col, ease(0.08));
    rimMat.uniforms.k!.value = 0.28 + lvl * 0.4 + laugh * 0.2;
    for (let i = 0; i < BARS; i++) {
      const j = i < BARS / 2 ? i : BARS - 1 - i; // mirrored: lows at the top, highs at the bottom
      const b = s.bands[Math.min(31, 2 + Math.floor((j / (BARS / 2)) * 26))] ?? 0;
      const target = 0.04 + 0.02 * Math.sin(t * 2.2 + i * 0.45) + Math.pow(b, 1.3) * (0.3 + lvl * 1.1);
      barLen[i]! += (target - barLen[i]!) * ease(target > barLen[i]! ? 0.5 : 0.12);
      const ang = (i / BARS) * Math.PI * 2 + Math.PI / 2;
      dummy.position.set(Math.cos(ang) * 1.27, Math.sin(ang) * 1.27, 0);
      dummy.rotation.set(0, 0, ang - Math.PI / 2);
      dummy.scale.set(1, Math.min(0.5, barLen[i]!), 1);
      dummy.updateMatrix();
      bars.setMatrixAt(i, dummy.matrix);
    }
    bars.instanceMatrix.needsUpdate = true;
    ringMat.opacity = 0.14 + lvl * 0.22;
    Wu.center!.value.set(orb.position.x, -orb.position.z);
    if (!reduced) {
      for (let i = 0; i < M; i++) {
        mp[i * 3 + 1]! += (0.004 + ms[i]! * 0.006 * (1 + l * 3 + laugh * 3)) * f;
        mp[i * 3]! += Math.sin(t + ms[i]! * 20) * 0.002 * f;
        if (mp[i * 3 + 1]! > 10) mp[i * 3 + 1] = 0;
      }
      mg.attributes.position!.needsUpdate = true;
    }
    motesMat.uniforms.opacity!.value = 0.28 + l * 0.35 + cur.sub * 0.25 + laugh * 0.18;
    bloom.strength = 0.4 + laugh * 0.18 + cur.aur * 0.08 + lvl * 0.08;
    film.uniforms.time!.value = t;
    film.uniforms.sub!.value = cur.sub < 0.002 ? 0 : cur.sub;
    composer.render();
  };
  raf = requestAnimationFrame(frame);

  const onResize = () => {
    camera.aspect = W() / H();
    camera.updateProjectionMatrix();
    renderer.setSize(W(), H(), false);
    composer.setSize(W(), H());
    film.uniforms.aspect!.value = W() / H();
  };
  window.addEventListener("resize", onResize);

  return {
    dispose() {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      scene.traverse((o) => {
        const m = o as THREE.Mesh;
        m.geometry?.dispose();
        const mat = m.material as THREE.Material | THREE.Material[] | undefined;
        if (Array.isArray(mat)) mat.forEach((x) => x.dispose());
        else mat?.dispose();
      });
      water.dispose();
      glowTex.dispose();
      pmrem.dispose();
      composer.dispose();
      renderer.dispose();
    },
  };
}
