const navItems = document.querySelectorAll(".nav-item");
const toolButtons = document.querySelectorAll(".segmented-control button");
const menuButtons = document.querySelectorAll(".menu-list button");
const versionBadge = document.querySelector("[data-app-version]");
const smokeCanvas = document.querySelector(".smoke-background");
const robloxSlot = document.querySelector(".roblox-slot");
const logFeed = document.querySelector("[data-log-feed]");
const minimizeButton = document.querySelector("[data-window-minimize]");
const maximizeButton = document.querySelector("[data-window-maximize]");
const closeButton = document.querySelector("[data-window-close]");
const alignRobloxButton = document.querySelector("[data-align-roblox]");
const startMacroButton = document.querySelector("[data-start-macro]");
const openMainSettingsButton = document.querySelector("[data-open-main-settings]");
const openConfigButton = document.querySelector("[data-open-config]");
const openTasksButton = document.querySelector("[data-open-tasks]");
const modeSelect = document.querySelector("[data-mode-select]");
const mapSelect = document.querySelector("[data-map-select]");
const actSelect = document.querySelector("[data-act-select]");
const mapField = document.querySelector("[data-map-field]");
const actField = document.querySelector("[data-act-field]");

const appendLog = (message, muted = false) => {
  if (!logFeed) return;
  const entry = document.createElement("p");
  entry.textContent = message;
  entry.classList.toggle("muted", muted);
  logFeed.append(entry);
  while (logFeed.children.length > 80) {
    logFeed.firstElementChild?.remove();
  }
  logFeed.scrollTop = logFeed.scrollHeight;
};

const gameModes = [
  {
    id: "spring-event",
    label: "Spring Event",
    selector: "fixed",
    fixedMap: "Eternal Tyrant",
    acts: ["Default"],
    source: "https://wiki.vanguards.gg/Eternal_Tyrant_Gamemode"
  },
  {
    id: "story",
    label: "Story",
    selector: "map",
    acts: ["Act 1", "Act 2", "Act 3", "Act 4", "Act 5", "Act 6"],
    maps: [
      "Planet Namak",
      "Sand Village",
      "Double Dungeon",
      "Shibuya Station",
      "Underground Church",
      "Spirit Society",
      "Martial Island",
      "Edge of Heaven",
      "Lebereo Raid",
      "Hill of Swords",
      "Frozen Port",
      "Downtown Tokyo",
      "Hidden Village"
    ],
    source: "https://wiki.vanguards.gg/Story"
  },
  {
    id: "legend",
    label: "Legend Stages",
    selector: "map",
    acts: ["Stage 1", "Stage 2", "Stage 3", "EX"],
    maps: [
      "Sand Village",
      "Double Dungeon",
      "Shibuya Aftermath",
      "Golden Castle",
      "Kuinshi Palace",
      "Land of the Gods",
      "Shining Castle",
      "Crystal Chapel",
      "Burning Spirit Tree",
      "Imprisoned Island",
      "Tokyo Railway",
      "Destroyed Hidden Village"
    ],
    source: "https://wiki.vanguards.gg/Legend_Stages"
  },
  {
    id: "infinite",
    label: "Infinite Mode",
    selector: "map",
    acts: ["Infinite"],
    maps: [
      "Planet Namak",
      "Sand Village",
      "Double Dungeon",
      "Shibuya Station",
      "Underground Church",
      "Spirit Society",
      "Martial Island",
      "Edge of Heaven",
      "Lebereo Raid",
      "Hill of Swords",
      "Frozen Port",
      "Downtown Tokyo",
      "Hidden Village"
    ],
    source: "https://wiki.vanguards.gg/Infinite_Mode"
  },
  {
    id: "challenges",
    label: "Challenges",
    selector: "rotating",
    fixedMap: "Rotating Story / Legend stage",
    acts: ["Current Rotation"],
    source: "https://wiki.vanguards.gg/Challenges"
  },
  {
    id: "raids",
    label: "Raids",
    selector: "map",
    acts: ["Default"],
    maps: ["Tracks at the Edge of the World", "Ruined City", "HAPPY Factory"],
    source: "https://wiki.vanguards.gg/Raids"
  },
  {
    id: "boss-events",
    label: "Boss Events",
    selector: "boss",
    acts: ["Default"],
    maps: ["Igros", "The Blood-Red Commander", "Sukono", "King of Curses", "Dark-Tainted Tyrant", "Saber (Alternate)", "The Founder", "Arin"],
    source: "https://wiki.vanguards.gg/Boss_Events"
  },
  {
    id: "world-destroyer",
    label: "World Destroyer",
    selector: "fixed",
    fixedMap: "Frozen Port",
    acts: ["Default"],
    source: "https://wiki.vanguards.gg/World_Destroyer_Gamemode"
  },
  {
    id: "portals",
    label: "Portals",
    selector: "portal",
    acts: ["Tier 1-10"],
    maps: ["Boo Portal", "Lfelt Portal"],
    source: "https://wiki.vanguards.gg/Portals"
  }
];

const smokeFragmentShader = `#version 300 es
precision highp float;
out vec4 O;
uniform float time;
uniform vec2 resolution;
uniform vec3 u_color;

#define FC gl_FragCoord.xy
#define R resolution
#define T (time+660.)

float rnd(vec2 p){p=fract(p*vec2(12.9898,78.233));p+=dot(p,p+34.56);return fract(p.x*p.y);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p),u=f*f*(3.-2.*f);return mix(mix(rnd(i),rnd(i+vec2(1,0)),u.x),mix(rnd(i+vec2(0,1)),rnd(i+1.),u.x),u.y);}
float fbm(vec2 p){float t=.0,a=1.;for(int i=0;i<5;i++){t+=a*noise(p);p*=mat2(1,-1.2,.2,1.2)*2.;a*=.5;}return t;}

void main(){
  vec2 uv=(FC-.5*R)/R.y;
  vec3 col=vec3(1);
  uv.x+=.25;
  uv*=vec2(2,1);

  float n=fbm(uv*.28-vec2(T*.01,0));
  n=noise(uv*3.+n*2.);

  col.r-=fbm(uv+vec2(0,T*.015)+n);
  col.g-=fbm(uv*1.003+vec2(0,T*.015)+n+.003);
  col.b-=fbm(uv*1.006+vec2(0,T*.015)+n+.006);
  col=mix(col, u_color, dot(col,vec3(.21,.71,.07)));
  col=mix(vec3(.02),col,min(time*.1,1.));
  col=clamp(col,.02,.22);
  O=vec4(col,1);
}`;

class SmokeRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.gl = canvas.getContext("webgl2", { alpha: false });
    this.color = [0.08, 0.09, 0.11];
    this.vertexSource = `#version 300 es
precision highp float;
in vec4 position;
void main(){gl_Position=position;}`;

    if (!this.gl) return;
    this.setup();
    this.resize();
  }

  compile(type, source) {
    const shader = this.gl.createShader(type);
    this.gl.shaderSource(shader, source);
    this.gl.compileShader(shader);
    if (!this.gl.getShaderParameter(shader, this.gl.COMPILE_STATUS)) {
      console.error(this.gl.getShaderInfoLog(shader));
      return null;
    }
    return shader;
  }

  setup() {
    const gl = this.gl;
    const vertexShader = this.compile(gl.VERTEX_SHADER, this.vertexSource);
    const fragmentShader = this.compile(gl.FRAGMENT_SHADER, smokeFragmentShader);
    const program = gl.createProgram();

    if (!vertexShader || !fragmentShader || !program) return;

    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error(gl.getProgramInfoLog(program));
      return;
    }

    this.program = program;
    this.buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, 1, -1, -1, 1, 1, 1, -1]), gl.STATIC_DRAW);

    const position = gl.getAttribLocation(program, "position");
    gl.enableVertexAttribArray(position);
    gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);

    this.uniforms = {
      resolution: gl.getUniformLocation(program, "resolution"),
      time: gl.getUniformLocation(program, "time"),
      color: gl.getUniformLocation(program, "u_color")
    };
  }

  resize() {
    if (!this.gl) return;
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    this.canvas.width = Math.floor(window.innerWidth * dpr);
    this.canvas.height = Math.floor(window.innerHeight * dpr);
    this.gl.viewport(0, 0, this.canvas.width, this.canvas.height);
  }

  render = (now = 0) => {
    if (!this.gl || !this.program) return;
    const gl = this.gl;
    gl.useProgram(this.program);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.buffer);
    gl.uniform2f(this.uniforms.resolution, this.canvas.width, this.canvas.height);
    gl.uniform1f(this.uniforms.time, now * 0.001);
    gl.uniform3fv(this.uniforms.color, this.color);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    requestAnimationFrame(this.render);
  };
}

if (smokeCanvas) {
  const smokeRenderer = new SmokeRenderer(smokeCanvas);
  const updateBackgroundHole = () => {
    if (!robloxSlot) return;
    const rect = robloxSlot.getBoundingClientRect();
    smokeCanvas.style.setProperty("--hole-left", `${rect.left}px`);
    smokeCanvas.style.setProperty("--hole-top", `${rect.top}px`);
    smokeCanvas.style.setProperty("--hole-width", `${rect.width}px`);
    smokeCanvas.style.setProperty("--hole-height", `${rect.height}px`);
    window.openAVAuto?.roblox?.setSlotBounds({
      x: rect.left,
      y: rect.top,
      width: rect.width,
      height: rect.height
    });
  };

  window.addEventListener("resize", () => {
    smokeRenderer.resize();
    updateBackgroundHole();
  });
  new ResizeObserver(updateBackgroundHole).observe(robloxSlot);
  updateBackgroundHole();
  smokeRenderer.render();
}

navItems.forEach((item) => {
  item.addEventListener("click", () => {
    navItems.forEach((navItem) => navItem.classList.remove("active"));
    item.classList.add("active");
  });
});

toolButtons.forEach((button) => {
  button.addEventListener("click", () => {
    toolButtons.forEach((toolButton) => toolButton.classList.remove("active"));
    button.classList.add("active");
  });
});

menuButtons.forEach((button) => {
  button.addEventListener("click", () => {
    menuButtons.forEach((menuButton) => menuButton.classList.remove("active"));
    button.classList.add("active");
  });
});

if (versionBadge && window.openAVAuto) {
  window.openAVAuto.getVersion().then((version) => {
    versionBadge.textContent = `v${version}`;
  });
}

if (window.openAVAuto?.window) {
  minimizeButton?.addEventListener("click", () => window.openAVAuto.window.minimize());
  maximizeButton?.addEventListener("click", () => window.openAVAuto.window.maximizeToggle());
  closeButton?.addEventListener("click", () => window.openAVAuto.window.close());
}

window.openAVAuto?.macro?.onLog?.((message) => appendLog(message));

const fillSelect = (select, values) => {
  if (!select) return;
  select.innerHTML = "";
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.append(option);
  });
};

const updateModeFields = () => {
  if (!modeSelect) return;
  const selectedMode = gameModes.find((mode) => mode.id === modeSelect.value) || gameModes[0];
  const mapValues = selectedMode.maps || [selectedMode.fixedMap].filter(Boolean);
  const actValues = selectedMode.acts || ["Default"];
  const usesMapChoice = selectedMode.selector === "map" || selectedMode.selector === "boss" || selectedMode.selector === "portal";
  const usesActChoice = actValues.length > 1;

  fillSelect(mapSelect, mapValues);
  fillSelect(actSelect, actValues);
  mapField?.classList.toggle("is-hidden", !usesMapChoice);
  actField?.classList.toggle("is-hidden", !usesActChoice);
};

if (modeSelect) {
  fillSelect(modeSelect, gameModes.map((mode) => mode.label));
  Array.from(modeSelect.options).forEach((option, index) => {
    option.value = gameModes[index].id;
  });
  modeSelect.value = "story";
  modeSelect.addEventListener("change", updateModeFields);
  updateModeFields();
  mapSelect.value = "Lebereo Raid";
  actSelect.value = "Act 2";
}

alignRobloxButton?.addEventListener("click", () => {
  window.openAVAuto?.roblox?.align();
});

startMacroButton?.addEventListener("click", () => {
  appendLog("Starting macro...");
  window.openAVAuto?.macro?.start({
    mode: modeSelect?.value,
    map: mapSelect?.value,
    act: actSelect?.value
  });
});

openConfigButton?.addEventListener("click", () => {
  window.openAVAuto?.config?.open();
});

openMainSettingsButton?.addEventListener("click", () => {
  window.openAVAuto?.mainSettings?.open();
});

openTasksButton?.addEventListener("click", () => {
  window.openAVAuto?.tasks?.open();
});
