const modeSelect = document.querySelector("[data-main-mode]");
const modeList = document.querySelector("[data-mode-list]");
const modePanel = document.querySelector("[data-mode-panel]");
const saveState = document.querySelector("[data-save-state]");
const sharedFields = document.querySelectorAll("[data-main-field]");
const versionBadge = document.querySelector("[data-app-version]");
const minimizeButton = document.querySelector("[data-window-minimize]");
const maximizeButton = document.querySelector("[data-window-maximize]");
const closeButton = document.querySelector("[data-window-close]");
const smokeCanvas = document.querySelector(".smoke-background");

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

const modes = [
  { id: "story", label: "Story" },
  { id: "bounty", label: "Bounty" },
  { id: "boss-rush", label: "Boss Rush" },
  { id: "challenge", label: "Challenge" },
  { id: "legend", label: "Legend Stage" },
  { id: "infinite", label: "Infinite" },
  { id: "rift", label: "Rift" },
  { id: "raid", label: "Raid" },
  { id: "portal", label: "Portal" },
  { id: "odyssey", label: "Odyssey" },
  { id: "dungeon", label: "Dungeon" },
  { id: "worldline", label: "Worldline" },
  { id: "event", label: "Event" }
];

const teams = ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6"];
const hourlyChallengeTypes = ["Story", "Legend Stage", "Bosses", "Double Dungeon"];
const riftCards = ["Fisticuffs", "King's Burden", "Money Surge", "Warding Off Evil"];
const raidMounts = ["Mount", "Sprint", "Cid Mount", "Default Mount"];
const dungeonMainModifiers = ["Fisticuffs", "King's Burden", "Money Surge", "Warding Off Evil"];
const dungeonModifiers = ["Harvest", "Common Loot", "Uncommon Loot", "Take It", "Damage", "Range", "Slayer", "Champion", "Dodge", "Speed"];
const priorityOptions = ["Highest", "Lowest", "First Available", "Skip"];

let userConfig = {
  mainSettings: {
    activeMode: "story",
    team: "Team 1",
    webhook: false,
    modes: {}
  }
};

const defaultsByMode = {
  story: { nightmare: false },
  bounty: { cooldownCheck: true, cooldownMinutes: 30 },
  "boss-rush": { enabled: true },
  challenge: { weekly: true, daily: true, hourly: ["Story", "Legend Stage", "Bosses", "Double Dungeon"] },
  legend: { nightmare: false },
  infinite: { leaveAtWave: 0 },
  rift: { card: "Money Surge", resetTimer: 0 },
  raid: { mount: "Mount" },
  portal: { tier: "Highest Available" },
  odyssey: { enabled: true },
  dungeon: {
    mainModifier: "Fisticuffs",
    cards: dungeonModifiers.map((modifier, index) => ({
      modifier,
      priority: priorityOptions[Math.min(index, priorityOptions.length - 1)],
      limit: 9999
    }))
  },
  worldline: { enabled: true },
  event: { event: "Anniversary" }
};

if (smokeCanvas) {
  const smokeRenderer = new SmokeRenderer(smokeCanvas);
  window.addEventListener("resize", () => smokeRenderer.resize());
  smokeRenderer.render();
}

const modeConfig = (mode = userConfig.mainSettings.activeMode) => {
  userConfig.mainSettings.modes ||= {};
  userConfig.mainSettings.modes[mode] ||= structuredClone(defaultsByMode[mode] || {});
  return userConfig.mainSettings.modes[mode];
};

const scheduleSave = (() => {
  let timer;
  return () => {
    clearTimeout(timer);
    saveState?.classList.add("saving");
    if (saveState) saveState.textContent = "Saving";
    timer = setTimeout(async () => {
      await window.openAVAuto?.config?.saveUserConfig?.(userConfig);
      saveState?.classList.remove("saving");
      if (saveState) saveState.textContent = "Saved";
    }, 120);
  };
})();

const optionHtml = (values, selected) => values.map((value) => (
  `<option value="${value}" ${value === selected ? "selected" : ""}>${value}</option>`
)).join("");

const checkboxGrid = (name, values, selectedValues = [], compact = false) => `
  <div class="choice-grid ${compact ? "compact" : ""}">
    ${values.map((value) => `
      <label class="choice-chip">
        <input type="checkbox" data-list-field="${name}" value="${value}" ${selectedValues.includes(value) ? "checked" : ""} />
        ${value}
      </label>
    `).join("")}
  </div>
`;

const renderGenericPanel = (title, fields = "") => `
  <div class="panel-grid">
    <section class="panel-card wide">
      <h2>${title}</h2>
      <div class="field-grid">${fields}</div>
    </section>
  </div>
`;

const renderPanel = () => {
  const activeMode = userConfig.mainSettings.activeMode;
  const config = modeConfig(activeMode);
  const mode = modes.find((item) => item.id === activeMode);

  if (!modePanel) return;

  if (activeMode === "bounty") {
    modePanel.innerHTML = renderGenericPanel("Bounty", `
      <label class="inline-toggle"><input type="checkbox" data-mode-field="cooldownCheck" ${config.cooldownCheck ? "checked" : ""} />Cooldown check</label>
      <label>Cooldown Minutes<input type="number" min="0" data-mode-field="cooldownMinutes" value="${config.cooldownMinutes ?? 30}" /></label>
    `);
    return;
  }

  if (activeMode === "challenge") {
    modePanel.innerHTML = `
      <div class="panel-grid">
        <section class="panel-card">
          <h2>Challenge</h2>
          <label class="inline-toggle"><input type="checkbox" data-mode-field="weekly" ${config.weekly !== false ? "checked" : ""} />Weekly challenge</label>
          <label class="inline-toggle"><input type="checkbox" data-mode-field="daily" ${config.daily !== false ? "checked" : ""} />Daily challenge</label>
        </section>
        <section class="panel-card">
          <h2>Hourly Rotation</h2>
          ${checkboxGrid("hourly", hourlyChallengeTypes, config.hourly || [])}
        </section>
      </div>
    `;
    return;
  }

  if (activeMode === "rift") {
    modePanel.innerHTML = renderGenericPanel("Rift", `
      <label>Dadadan Card
        <select data-mode-field="card">${optionHtml(riftCards, config.card)}</select>
      </label>
      <label>Rift Reset Timer<input type="number" min="0" data-mode-field="resetTimer" value="${config.resetTimer ?? 0}" /></label>
    `);
    return;
  }

  if (activeMode === "raid") {
    modePanel.innerHTML = renderGenericPanel("Raid", `
      <label>Cid Mount
        <select data-mode-field="mount">${optionHtml(raidMounts, config.mount)}</select>
      </label>
    `);
    return;
  }

  if (activeMode === "dungeon") {
    config.cards ||= defaultsByMode.dungeon.cards;
    modePanel.innerHTML = `
      <div class="panel-grid">
        <section class="panel-card wide">
          <h2>Dungeon</h2>
          <div class="field-grid">
            <label>Main Modifier
              <select data-mode-field="mainModifier">${optionHtml(dungeonMainModifiers, config.mainModifier)}</select>
            </label>
          </div>
        </section>
        <section class="panel-card wide">
          <h2>Cards</h2>
          <div class="modifier-grid">
            ${config.cards.map((card, index) => `
              <div class="modifier-row">
                <label>Modifier #${index + 1}
                  <select data-card-index="${index}" data-card-field="modifier">${optionHtml(dungeonModifiers, card.modifier)}</select>
                </label>
                <label>Priority
                  <select data-card-index="${index}" data-card-field="priority">${optionHtml(priorityOptions, card.priority)}</select>
                </label>
                <label>Limit
                  <input type="number" min="0" data-card-index="${index}" data-card-field="limit" value="${card.limit ?? 9999}" />
                </label>
              </div>
            `).join("")}
          </div>
        </section>
      </div>
    `;
    return;
  }

  modePanel.innerHTML = renderGenericPanel(mode?.label || "Main", `
    <label class="inline-toggle"><input type="checkbox" data-mode-field="enabled" ${config.enabled !== false ? "checked" : ""} />Enabled</label>
    ${["story", "legend"].includes(activeMode) ? `<label class="inline-toggle"><input type="checkbox" data-mode-field="nightmare" ${config.nightmare ? "checked" : ""} />Nightmare</label>` : ""}
    ${activeMode === "infinite" ? `<label>Leave At Wave<input type="number" min="0" data-mode-field="leaveAtWave" value="${config.leaveAtWave ?? 0}" /></label>` : ""}
    ${activeMode === "event" ? `<label>Event<select data-mode-field="event">${optionHtml(["Anniversary", "Spring Event"], config.event)}</select></label>` : ""}
  `);
};

const renderModeControls = () => {
  if (!modeSelect || !modeList) return;

  modeSelect.innerHTML = optionHtml(modes.map((mode) => mode.label), "");
  Array.from(modeSelect.options).forEach((option, index) => {
    option.value = modes[index].id;
    option.selected = modes[index].id === userConfig.mainSettings.activeMode;
  });

  modeList.innerHTML = modes.map((mode) => `
    <button class="${mode.id === userConfig.mainSettings.activeMode ? "active" : ""}" type="button" data-mode-id="${mode.id}">
      ${mode.label}
    </button>
  `).join("");
};

const renderSharedFields = () => {
  sharedFields.forEach((field) => {
    const key = field.dataset.mainField;
    if (field.type === "checkbox") {
      field.checked = Boolean(userConfig.mainSettings[key]);
    } else {
      field.value = userConfig.mainSettings[key] || "Team 1";
    }
  });
};

const setActiveMode = (mode) => {
  userConfig.mainSettings.activeMode = mode;
  renderModeControls();
  renderPanel();
  scheduleSave();
};

const hydrate = async () => {
  const savedConfig = await window.openAVAuto?.config?.loadUserConfig?.();
  userConfig = {
    ...userConfig,
    ...savedConfig,
    mainSettings: {
      ...userConfig.mainSettings,
      ...savedConfig?.mainSettings,
      modes: {
        ...userConfig.mainSettings.modes,
        ...savedConfig?.mainSettings?.modes
      }
    }
  };

  if (!teams.includes(userConfig.mainSettings.team)) {
    userConfig.mainSettings.team = "Team 1";
  }

  renderModeControls();
  renderSharedFields();
  renderPanel();
};

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

modeSelect?.addEventListener("change", () => setActiveMode(modeSelect.value));

modeList?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-mode-id]");
  if (!button) return;
  setActiveMode(button.dataset.modeId);
});

sharedFields.forEach((field) => {
  field.addEventListener("change", () => {
    const key = field.dataset.mainField;
    userConfig.mainSettings[key] = field.type === "checkbox" ? field.checked : field.value;
    scheduleSave();
  });
});

modePanel?.addEventListener("input", (event) => {
  const field = event.target.closest("[data-mode-field], [data-list-field], [data-card-field]");
  if (!field) return;
  const config = modeConfig();

  if (field.dataset.modeField) {
    const key = field.dataset.modeField;
    config[key] = field.type === "checkbox" ? field.checked : field.type === "number" ? Number(field.value) : field.value;
  }

  if (field.dataset.listField) {
    const key = field.dataset.listField;
    config[key] = Array.from(modePanel.querySelectorAll(`[data-list-field="${key}"]:checked`)).map((input) => input.value);
  }

  if (field.dataset.cardField) {
    const index = Number(field.dataset.cardIndex);
    const key = field.dataset.cardField;
    config.cards ||= structuredClone(defaultsByMode.dungeon.cards);
    config.cards[index][key] = field.type === "number" ? Number(field.value) : field.value;
  }

  scheduleSave();
});

modePanel?.addEventListener("change", (event) => {
  if (event.target.matches("select, input")) {
    event.target.dispatchEvent(new Event("input", { bubbles: true }));
  }
});

hydrate();
