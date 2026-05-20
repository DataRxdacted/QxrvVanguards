const navItems = document.querySelectorAll(".nav-item");
const toolButtons = document.querySelectorAll(".segmented-control button");
const menuButtons = document.querySelectorAll(".menu-list button");
const versionBadge = document.querySelector("[data-app-version]");
const smokeCanvas = document.querySelector(".smoke-background");
const robloxSlot = document.querySelector(".roblox-slot");
const minimizeButton = document.querySelector("[data-window-minimize]");
const maximizeButton = document.querySelector("[data-window-maximize]");
const closeButton = document.querySelector("[data-window-close]");

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
  };

  window.addEventListener("resize", () => {
    smokeRenderer.resize();
    updateBackgroundHole();
  });
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
