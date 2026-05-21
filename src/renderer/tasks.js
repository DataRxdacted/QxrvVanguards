const taskRows = document.querySelector("[data-task-rows]");
const addTaskButton = document.querySelector("[data-add-task]");
const clearTasksButton = document.querySelector("[data-clear-tasks]");
const startOverToggle = document.querySelector("[data-start-over]");
const saveState = document.querySelector("[data-save-state]");
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

const teams = ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6"];
const storyMaps = ["Planet Namak", "Sand Village", "Double Dungeon", "Shibuya Station", "Underground Church", "Spirit Society", "Martial Island", "Edge of Heaven", "Lebereo Raid", "Hill of Swords", "Frozen Port", "Downtown Tokyo", "Hidden Village"];
const legendMaps = ["Sand Village", "Double Dungeon", "Shibuya Aftermath", "Golden Castle", "Kuinshi Palace", "Land of the Gods", "Shining Castle", "Crystal Chapel", "Burning Spirit Tree", "Imprisoned Island", "Tokyo Railway", "Destroyed Hidden Village"];

const modeCatalog = [
  { id: "story", label: "Story", maps: storyMaps, acts: ["Act 1", "Act 2", "Act 3", "Act 4", "Act 5", "Act 6", "Infinite"] },
  { id: "legend", label: "Legend", maps: legendMaps, acts: ["Act 1", "Act 2", "Act 3"] },
  { id: "infinite", label: "Infinite", maps: storyMaps, acts: ["Infinite"] },
  { id: "challenge", label: "Challenge", maps: ["Weekly", "Daily", "Story", "Legend Stage", "Bosses", "Double Dungeon"], acts: ["Default"] },
  { id: "rift", label: "Rift", maps: ["Current Rift"], acts: ["Default"] },
  { id: "raid", label: "Raid", maps: ["Tracks at the Edge of the World", "Ruined City", "HAPPY Factory"], acts: ["Default"] },
  { id: "dungeon", label: "Dungeon", maps: ["Underworld", "Frozen Volcano"], acts: ["Default"] },
  { id: "bounty", label: "Bounty", maps: ["Bounty Board"], acts: ["Default"] },
  { id: "event", label: "Event", maps: ["Spring", "Anniversary"], acts: ["Default"] }
];

let userConfig = {
  tasks: {
    startOver: false,
    items: []
  }
};

const defaultTask = () => ({
  id: crypto.randomUUID(),
  priority: 10,
  mode: "story",
  repeat: 0,
  map: "Planet Namak",
  act: "Act 1",
  team: "Team 1"
});

if (smokeCanvas) {
  const smokeRenderer = new SmokeRenderer(smokeCanvas);
  window.addEventListener("resize", () => smokeRenderer.resize());
  smokeRenderer.render();
}

const modeInfo = (mode) => modeCatalog.find((item) => item.id === mode) || modeCatalog[0];

const optionHtml = (values, selected) => values.map((value) => (
  `<option value="${value}" ${value === selected ? "selected" : ""}>${value}</option>`
)).join("");

const modeOptionHtml = (selected) => modeCatalog.map((mode) => (
  `<option value="${mode.id}" ${mode.id === selected ? "selected" : ""}>${mode.label}</option>`
)).join("");

const normalizeTask = (task, index = 0) => {
  const next = { ...defaultTask(), ...task };
  const mode = modeInfo(next.mode);
  next.priority = Number.isFinite(Number(next.priority)) ? Number(next.priority) : (index + 1) * 10;
  next.repeat = Math.max(0, Number(next.repeat || 0));
  if (!mode.maps.includes(next.map)) next.map = mode.maps[0] || "";
  if (!mode.acts.includes(next.act)) next.act = mode.acts[0] || "Default";
  if (!teams.includes(next.team)) next.team = "Team 1";
  return next;
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

const renderTasks = () => {
  if (!taskRows) return;
  userConfig.tasks.items = userConfig.tasks.items.map(normalizeTask);
  taskRows.innerHTML = userConfig.tasks.items.map((task, index) => {
    const mode = modeInfo(task.mode);
    return `
      <article class="task-row" data-task-index="${index}">
        <input type="number" min="1" data-task-field="priority" value="${task.priority}" title="Higher numbers interrupt lower priority repeats." />
        <select data-task-field="mode">${modeOptionHtml(task.mode)}</select>
        <input type="number" min="0" data-task-field="repeat" value="${task.repeat}" title="0 repeats forever until a higher priority available task interrupts it." />
        <select data-task-field="map">${optionHtml(mode.maps, task.map)}</select>
        <select data-task-field="act">${optionHtml(mode.acts, task.act)}</select>
        <select data-task-field="team">${optionHtml(teams, task.team)}</select>
        <div class="row-actions">
          <button class="danger-button" type="button" data-remove-task>Remove</button>
          <button class="icon-button" type="button" data-move-task="-1" aria-label="Move task up">^</button>
          <button class="icon-button" type="button" data-move-task="1" aria-label="Move task down">v</button>
        </div>
      </article>
    `;
  }).join("");
};

const updateTask = (row, field, value) => {
  const index = Number(row.dataset.taskIndex);
  const task = userConfig.tasks.items[index];
  if (!task) return;

  task[field] = field === "priority" || field === "repeat" ? Number(value) : value;

  if (field === "mode") {
    const mode = modeInfo(task.mode);
    task.map = mode.maps[0] || "";
    task.act = mode.acts[0] || "Default";
    renderTasks();
  }

  scheduleSave();
};

const moveTask = (index, direction) => {
  const target = index + direction;
  if (target < 0 || target >= userConfig.tasks.items.length) return;
  const [task] = userConfig.tasks.items.splice(index, 1);
  userConfig.tasks.items.splice(target, 0, task);
  renderTasks();
  scheduleSave();
};

const hydrate = async () => {
  const savedConfig = await window.openAVAuto?.config?.loadUserConfig?.();
  userConfig = {
    ...userConfig,
    ...savedConfig,
    tasks: {
      ...userConfig.tasks,
      ...savedConfig?.tasks,
      items: savedConfig?.tasks?.items?.length ? savedConfig.tasks.items.map(normalizeTask) : [defaultTask()]
    }
  };
  if (startOverToggle) startOverToggle.checked = Boolean(userConfig.tasks.startOver);
  renderTasks();
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

startOverToggle?.addEventListener("change", () => {
  userConfig.tasks.startOver = startOverToggle.checked;
  scheduleSave();
});

addTaskButton?.addEventListener("click", () => {
  userConfig.tasks.items.push({
    ...defaultTask(),
    priority: (userConfig.tasks.items.length + 1) * 10
  });
  renderTasks();
  scheduleSave();
});

clearTasksButton?.addEventListener("click", () => {
  userConfig.tasks.items = [defaultTask()];
  renderTasks();
  scheduleSave();
});

taskRows?.addEventListener("input", (event) => {
  const field = event.target.closest("[data-task-field]");
  const row = event.target.closest("[data-task-index]");
  if (!field || !row) return;
  updateTask(row, field.dataset.taskField, field.value);
});

taskRows?.addEventListener("change", (event) => {
  const field = event.target.closest("[data-task-field]");
  const row = event.target.closest("[data-task-index]");
  if (!field || !row) return;
  updateTask(row, field.dataset.taskField, field.value);
});

taskRows?.addEventListener("click", (event) => {
  const row = event.target.closest("[data-task-index]");
  if (!row) return;
  const index = Number(row.dataset.taskIndex);

  if (event.target.closest("[data-remove-task]")) {
    userConfig.tasks.items.splice(index, 1);
    if (!userConfig.tasks.items.length) userConfig.tasks.items = [defaultTask()];
    renderTasks();
    scheduleSave();
    return;
  }

  const moveButton = event.target.closest("[data-move-task]");
  if (moveButton) {
    moveTask(index, Number(moveButton.dataset.moveTask));
  }
});

hydrate();
