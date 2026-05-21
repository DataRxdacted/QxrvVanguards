const tabButtons = document.querySelectorAll("[data-tab-button]");
const tabPanels = document.querySelectorAll("[data-tab-panel]");
const activeSlotSelect = document.querySelector("[data-active-slot]");
const coordinateUnits = document.querySelector("[data-coordinate-units]");
const mapPreview = document.querySelector("[data-map-preview]");
const mapCanvas = document.querySelector(".map-canvas");
const markerLayer = document.querySelector("[data-marker-layer]");
const addActionButton = document.querySelector("[data-add-action]");
const deleteActionButton = document.querySelector("[data-delete-action]");
const resetAllCoordinatesButton = document.querySelector("[data-reset-all-coordinates]");
const resetSlotCoordinatesButton = document.querySelector("[data-reset-slot-coordinates]");
const actionFields = document.querySelectorAll("[data-action-field]");
const actionList = document.querySelector("[data-action-list]");
const selectedActionTitle = document.querySelector("[data-selected-action-title]");
const modeSelect = document.querySelector("[data-config-mode-select]");
const mapSelect = document.querySelector("[data-config-map-select]");
const strategyModeSelect = document.querySelector("[data-strategy-mode-select]");
const strategyMapSelect = document.querySelector("[data-strategy-map-select]");
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

const storyMaps = ["Planet Namak", "Sand Village", "Double Dungeon", "Shibuya Station", "Underground Church", "Spirit Society", "Martial Island", "Edge of Heaven", "Lebereo Raid", "Hill of Swords", "Frozen Port", "Downtown Tokyo", "Hidden Village"];
const legendMaps = ["Sand Village", "Double Dungeon", "Shibuya Aftermath", "Golden Castle", "Kuinshi Palace", "Land of the Gods", "Shining Castle", "Crystal Chapel", "Burning Spirit Tree", "Imprisoned Island", "Tokyo Railway", "Destroyed Hidden Village"];
const raidMaps = ["Tracks at the Edge of the World", "Ruined City", "HAPPY Factory"];
const bossMaps = ["Blood Red Chamber", "Dark Tainted Tyrant", "Frozen Volcano", "Jeju Island", "Jojo", "Jojo 2", "Mountain Shrine", "Rumbling Event", "Spider Forest", "Sun Temple", "Underworld", "Winter Bleach", "Winter Bleach Regular"];
const portalMaps = ["Boo Portal", "Lfelt Portal"];
const extraImageMaps = ["Dried Lake", "HAPPY Factory 2", "Lich King's Throne", "Old Lobby", "Old Namek", "Planet Namak Spring"];

const gameModes = [
  { id: "default", label: "Default", maps: [...new Set([...storyMaps, ...legendMaps, ...raidMaps, ...bossMaps, ...portalMaps, ...extraImageMaps])] },
  { id: "spring-event", label: "Spring Event", maps: ["Eternal Tyrant", "Spring", "Planet Namak Spring"] },
  { id: "story", label: "Story", maps: storyMaps },
  { id: "legend", label: "Legend Stages", maps: legendMaps },
  { id: "infinite", label: "Infinite Mode", maps: storyMaps },
  { id: "challenges", label: "Challenges", maps: [...storyMaps, ...legendMaps] },
  { id: "raids", label: "Raids", maps: raidMaps },
  { id: "boss-events", label: "Boss Events", maps: bossMaps },
  { id: "world-destroyer", label: "World Destroyer", maps: ["Frozen Port"] },
  { id: "portals", label: "Portals", maps: portalMaps }
];

const strategyModes = [
  { id: "story", label: "Story", maps: ["All Story Maps", ...storyMaps] },
  { id: "legend", label: "Legend Stages", maps: ["All Legend Maps", ...legendMaps] },
  { id: "infinite", label: "Infinite Mode", maps: ["All Infinite Maps", ...storyMaps] },
  { id: "challenges", label: "Challenges", maps: ["Current Rotation"] },
  { id: "raids", label: "Raids", maps: ["All Raids", ...raidMaps] },
  { id: "portals", label: "Portals", maps: ["All Portals", ...portalMaps] }
];

const defaultAction = () => ({
  type: "Place",
  slot: "Slot 1",
  unit: "Unit 1",
  upgrade: "0",
  priority: "None",
  wave: 0,
  money: 0,
  delay: 0
});

let mapImages = [];
let selectedActionIndex = 0;
let pendingCoordinateTarget = null;
let userConfig = {
  coordinate: {
    mode: "default",
    map: "Planet Namak",
    activeSlot: "Slot 1",
    maps: {}
  },
  strategy: {
    mode: "story",
    map: "All Story Maps",
    page: "Page 1",
    actions: [defaultAction()]
  }
};

const normalizeName = (value = "") => value.toLowerCase().replace(/&/g, "and").replace(/[^a-z0-9]/g, "");

const mapAliases = new Map([
  ["planetnamak", "planetnamek"],
  ["planetnamakspring", "planetnamekspring"],
  ["landofthegods", "thelandofthegods"],
  ["tracksattheedgeoftheworld", "happyfactory"],
  ["eternaltyrant", "spring"],
  ["booportal", "driedlake"],
  ["lfeltportal", "winterbleachregular"]
]);

if (smokeCanvas) {
  const smokeRenderer = new SmokeRenderer(smokeCanvas);
  window.addEventListener("resize", () => smokeRenderer.resize());
  smokeRenderer.render();
}

const fillSelect = (select, values, getValue = (value) => value, getLabel = (value) => value) => {
  if (!select) return;
  select.innerHTML = "";
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = getValue(value);
    option.textContent = getLabel(value);
    select.append(option);
  });
};

const configKey = (mode = modeSelect?.value, map = mapSelect?.value) => `${mode}:${normalizeName(map)}`;
const getCurrentCoordinateSet = () => {
  const key = configKey();
  userConfig.coordinate.maps[key] ||= { mode: modeSelect.value, map: mapSelect.value, slots: {} };
  const mapConfig = userConfig.coordinate.maps[key];
  mapConfig.mode = modeSelect.value;
  mapConfig.map = mapSelect.value;
  mapConfig.slots ||= {};
  mapConfig.slots[activeSlotSelect.value] ||= {};
  return mapConfig;
};

const scheduleSave = (() => {
  let timer;
  return () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      window.openAVAuto?.config?.saveUserConfig?.(userConfig);
    }, 120);
  };
})();

const getContainedImageRect = () => {
  if (!mapPreview?.naturalWidth || !mapPreview?.naturalHeight || !mapCanvas) return null;
  const canvasRect = mapCanvas.getBoundingClientRect();
  const imageRatio = mapPreview.naturalWidth / mapPreview.naturalHeight;
  const canvasRatio = canvasRect.width / canvasRect.height;
  let width = canvasRect.width;
  let height = canvasRect.height;

  if (canvasRatio > imageRatio) {
    width = height * imageRatio;
  } else {
    height = width / imageRatio;
  }

  return {
    left: (canvasRect.width - width) / 2,
    top: (canvasRect.height - height) / 2,
    width,
    height
  };
};

const coordinateFromPointer = (event) => {
  const rect = getContainedImageRect();
  if (!rect) return null;
  const canvasRect = mapCanvas.getBoundingClientRect();
  const xInImage = event.clientX - canvasRect.left - rect.left;
  const yInImage = event.clientY - canvasRect.top - rect.top;
  if (xInImage < 0 || yInImage < 0 || xInImage > rect.width || yInImage > rect.height) return null;

  return {
    x: Math.round((xInImage / rect.width) * mapPreview.naturalWidth),
    y: Math.round((yInImage / rect.height) * mapPreview.naturalHeight)
  };
};

const renderCoordinateRows = () => {
  if (!coordinateUnits) return;
  const mapConfig = getCurrentCoordinateSet();
  const slotConfig = mapConfig.slots[activeSlotSelect.value];

  coordinateUnits.innerHTML = Array.from({ length: 6 }, (_, index) => {
    const unit = `Unit ${index + 1}`;
    const point = slotConfig[unit] || { x: 0, y: 0 };
    return `
      <article class="unit-card">
        <h3>${unit}</h3>
        <div class="xy-grid">
          <label>x<input data-coordinate-x="${unit}" type="number" value="${point.x}" /></label>
          <label>y<input data-coordinate-y="${unit}" type="number" value="${point.y}" /></label>
          <button class="secondary-button" type="button" data-pos-unit="${unit}">Pos</button>
        </div>
      </article>
    `;
  }).join("");
};

const renderMarkers = () => {
  if (!markerLayer) return;
  markerLayer.innerHTML = "";
  const rect = getContainedImageRect();
  if (!rect) return;
  const mapConfig = getCurrentCoordinateSet();
  const slotConfig = mapConfig.slots[activeSlotSelect.value] || {};

  Object.entries(slotConfig).forEach(([unit, point]) => {
    if (!point || point.x <= 0 || point.y <= 0) return;
    const left = rect.left + (point.x / mapPreview.naturalWidth) * rect.width;
    const top = rect.top + (point.y / mapPreview.naturalHeight) * rect.height;
    const marker = document.createElement("div");
    marker.className = "coordinate-marker";
    marker.style.left = `${left}px`;
    marker.style.top = `${top}px`;
    marker.innerHTML = `<span></span><strong>SL${activeSlotSelect.value.replace("Slot ", "")}/UN${unit.replace("Unit ", "")}</strong>`;
    markerLayer.append(marker);
  });
};

const setCoordinate = (unit, point, shouldRenderRows = true) => {
  const mapConfig = getCurrentCoordinateSet();
  mapConfig.slots[activeSlotSelect.value][unit] = point;
  if (shouldRenderRows) {
    renderCoordinateRows();
  }
  renderMarkers();
  scheduleSave();
};

const updateModeMaps = () => {
  const selectedMode = gameModes.find((mode) => mode.id === modeSelect?.value) || gameModes[0];
  fillSelect(mapSelect, selectedMode.maps);
  if (selectedMode.maps.includes(userConfig.coordinate.map)) {
    mapSelect.value = userConfig.coordinate.map;
  }
  userConfig.coordinate.mode = modeSelect.value;
  userConfig.coordinate.map = mapSelect.value;
  updateMapPreview();
  renderCoordinateRows();
  scheduleSave();
};

const updateMapPreview = () => {
  if (!mapPreview || !mapCanvas || !mapSelect) return;
  const selectedMap = normalizeName(mapSelect.value);
  const alias = mapAliases.get(selectedMap);
  const image = mapImages.find((item) => {
    const imageName = normalizeName(item.name);
    return imageName === selectedMap || imageName === alias;
  });

  userConfig.coordinate.map = mapSelect.value;

  if (!image) {
    mapPreview.removeAttribute("src");
    mapCanvas.classList.remove("has-image");
    renderMarkers();
    scheduleSave();
    return;
  }

  mapPreview.src = image.url;
  mapCanvas.classList.add("has-image");
  scheduleSave();
};

const updateStrategyMaps = () => {
  const selectedMode = strategyModes.find((mode) => mode.id === strategyModeSelect?.value) || strategyModes[0];
  fillSelect(strategyMapSelect, selectedMode.maps);
  if (selectedMode.maps.includes(userConfig.strategy.map)) {
    strategyMapSelect.value = userConfig.strategy.map;
  }
  userConfig.strategy.mode = strategyModeSelect.value;
  userConfig.strategy.map = strategyMapSelect.value;
  scheduleSave();
};

const renderActionList = () => {
  if (!actionList) return;
  userConfig.strategy.actions ||= [defaultAction()];
  actionList.innerHTML = userConfig.strategy.actions.map((action, index) => `
    <button class="${index === selectedActionIndex ? "active" : ""}" type="button" data-action-index="${index}">
      <strong>#${index + 1}</strong>
      <span>${action.type} - ${action.slot} / ${action.unit}</span>
      <span>Wave ${action.wave || 0}</span>
    </button>
  `).join("");
};

const renderActionEditor = () => {
  const action = userConfig.strategy.actions[selectedActionIndex] || userConfig.strategy.actions[0];
  if (!action) return;
  selectedActionTitle.textContent = `Action ${selectedActionIndex + 1}`;
  actionFields.forEach((field) => {
    field.value = action[field.dataset.actionField] ?? "";
  });
};

const saveActionEditor = () => {
  const action = userConfig.strategy.actions[selectedActionIndex];
  if (!action) return;
  actionFields.forEach((field) => {
    const key = field.dataset.actionField;
    action[key] = field.type === "number" ? Number(field.value) : field.value;
  });
  renderActionList();
  scheduleSave();
};

const hydrateConfig = async () => {
  const savedConfig = await window.openAVAuto?.config?.loadUserConfig?.();
  userConfig = {
    ...userConfig,
    ...savedConfig,
    coordinate: {
      ...userConfig.coordinate,
      ...savedConfig?.coordinate,
      maps: savedConfig?.coordinate?.maps || {}
    },
    strategy: {
      ...userConfig.strategy,
      ...savedConfig?.strategy,
      actions: savedConfig?.strategy?.actions?.length ? savedConfig.strategy.actions : [defaultAction()]
    }
  };

  fillSelect(activeSlotSelect, ["Slot 1", "Slot 2", "Slot 3", "Slot 4", "Slot 5", "Slot 6"]);
  activeSlotSelect.value = userConfig.coordinate.activeSlot || "Slot 1";
  fillSelect(modeSelect, gameModes, (mode) => mode.id, (mode) => mode.label);
  modeSelect.value = userConfig.coordinate.mode || "default";
  updateModeMaps();
  fillSelect(strategyModeSelect, strategyModes, (mode) => mode.id, (mode) => mode.label);
  strategyModeSelect.value = userConfig.strategy.mode || "story";
  updateStrategyMaps();
  renderActionList();
  renderActionEditor();
};

tabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const tab = button.dataset.tabButton;
    tabButtons.forEach((item) => item.classList.toggle("active", item === button));
    tabPanels.forEach((panel) => panel.classList.toggle("active", panel.dataset.tabPanel === tab));
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

modeSelect?.addEventListener("change", updateModeMaps);
mapSelect?.addEventListener("change", () => {
  userConfig.coordinate.map = mapSelect.value;
  updateMapPreview();
  renderCoordinateRows();
});
activeSlotSelect?.addEventListener("change", () => {
  userConfig.coordinate.activeSlot = activeSlotSelect.value;
  pendingCoordinateTarget = null;
  renderCoordinateRows();
  renderMarkers();
  scheduleSave();
});
strategyModeSelect?.addEventListener("change", updateStrategyMaps);
strategyMapSelect?.addEventListener("change", () => {
  userConfig.strategy.map = strategyMapSelect.value;
  scheduleSave();
});

coordinateUnits?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-pos-unit]");
  if (!button) return;
  pendingCoordinateTarget = button.dataset.posUnit;
  coordinateUnits.querySelectorAll("[data-pos-unit]").forEach((item) => item.classList.toggle("active", item === button));
});

coordinateUnits?.addEventListener("input", (event) => {
  const xInput = event.target.closest("[data-coordinate-x]");
  const yInput = event.target.closest("[data-coordinate-y]");
  if (!xInput && !yInput) return;
  const unit = xInput?.dataset.coordinateX || yInput?.dataset.coordinateY;
  const card = event.target.closest(".unit-card");
  const x = Number(card.querySelector("[data-coordinate-x]").value);
  const y = Number(card.querySelector("[data-coordinate-y]").value);
  setCoordinate(unit, { x, y }, false);
});

mapCanvas?.addEventListener("click", (event) => {
  if (!pendingCoordinateTarget || !mapCanvas.classList.contains("has-image")) return;
  const point = coordinateFromPointer(event);
  if (!point) return;
  setCoordinate(pendingCoordinateTarget, point);
  pendingCoordinateTarget = null;
  coordinateUnits.querySelectorAll("[data-pos-unit]").forEach((item) => item.classList.remove("active"));
});

mapPreview?.addEventListener("load", renderMarkers);
window.addEventListener("resize", renderMarkers);

addActionButton?.addEventListener("click", () => {
  userConfig.strategy.actions.push(defaultAction());
  selectedActionIndex = userConfig.strategy.actions.length - 1;
  renderActionList();
  renderActionEditor();
  scheduleSave();
});

deleteActionButton?.addEventListener("click", () => {
  if (userConfig.strategy.actions.length <= 1) {
    userConfig.strategy.actions = [defaultAction()];
    selectedActionIndex = 0;
  } else {
    userConfig.strategy.actions.splice(selectedActionIndex, 1);
    selectedActionIndex = Math.min(selectedActionIndex, userConfig.strategy.actions.length - 1);
  }

  renderActionList();
  renderActionEditor();
  scheduleSave();
});

resetSlotCoordinatesButton?.addEventListener("click", () => {
  const mapConfig = getCurrentCoordinateSet();
  mapConfig.slots[activeSlotSelect.value] = {};
  pendingCoordinateTarget = null;
  renderCoordinateRows();
  renderMarkers();
  scheduleSave();
});

resetAllCoordinatesButton?.addEventListener("click", () => {
  const mapConfig = getCurrentCoordinateSet();
  mapConfig.slots = {};
  pendingCoordinateTarget = null;
  renderCoordinateRows();
  renderMarkers();
  scheduleSave();
});

actionList?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-action-index]");
  if (!button) return;
  selectedActionIndex = Number(button.dataset.actionIndex);
  renderActionList();
  renderActionEditor();
});

actionFields.forEach((field) => {
  field.addEventListener("input", saveActionEditor);
  field.addEventListener("change", saveActionEditor);
});

const loadMapImages = async () => {
  mapImages = await window.openAVAuto?.config?.listMapImages?.() || [];
  updateMapPreview();
};

hydrateConfig().then(loadMapImages);
