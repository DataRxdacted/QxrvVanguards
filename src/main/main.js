const path = require("node:path");
const fs = require("node:fs");
const { pathToFileURL } = require("node:url");
const { execFile, spawn } = require("node:child_process");
const { app, BrowserWindow, ipcMain, globalShortcut } = require("electron");

let mainWindow;
let configWindow;
let mainSettingsWindow;
let tasksWindow;
let slotBounds = null;
let robloxAttached = false;
let alignInFlight = false;
let pendingAlign = false;
let macroInFlight = false;
let movementRecorder = null;

const alignScript = path.join(__dirname, "align_roblox.py");
const startStoryScript = path.join(__dirname, "start_story.py");
const userConfigPath = path.join(app.getAppPath(), "data", "config", "user-config.json");
const logPath = path.join(app.getAppPath(), "data", "logs", "openavauto.log");
const movementStopFlagPath = path.join(app.getAppPath(), "data", "vision", "movement", "planetnamek.stop");

const getRobloxTargetBounds = () => {
  if (!mainWindow || !slotBounds) return null;
  const windowBounds = mainWindow.getBounds();

  return {
    x: Math.round(windowBounds.x + slotBounds.x),
    y: Math.round(windowBounds.y + slotBounds.y),
    width: Math.round(slotBounds.width),
    height: Math.round(slotBounds.height)
  };
};

const applyMainWindowShape = () => {
  if (!mainWindow || !slotBounds || typeof mainWindow.setShape !== "function") return;
  const bounds = mainWindow.getBounds();
  const slot = {
    x: Math.max(0, Math.round(slotBounds.x)),
    y: Math.max(0, Math.round(slotBounds.y)),
    width: Math.max(0, Math.round(slotBounds.width)),
    height: Math.max(0, Math.round(slotBounds.height))
  };
  const rightX = slot.x + slot.width;
  const bottomY = slot.y + slot.height;
  const shape = [
    { x: 0, y: 0, width: bounds.width, height: slot.y },
    { x: 0, y: slot.y, width: slot.x, height: slot.height },
    { x: rightX, y: slot.y, width: Math.max(0, bounds.width - rightX), height: slot.height },
    { x: 0, y: bottomY, width: bounds.width, height: Math.max(0, bounds.height - bottomY) }
  ].filter((rect) => rect.width > 0 && rect.height > 0);

  mainWindow.setShape(shape);
};

const alignRobloxWindow = () => {
  const target = getRobloxTargetBounds();
  if (!target) return Promise.resolve({ ok: false, error: "Roblox slot is not ready." });

  if (alignInFlight) {
    pendingAlign = true;
    return Promise.resolve({ ok: true, pending: true });
  }

  alignInFlight = true;

  return new Promise((resolve) => {
    execFile(
      "py",
      [
        "-3",
        alignScript,
        "--x",
        String(target.x),
        "--y",
        String(target.y),
        "--width",
        String(target.width),
        "--height",
        String(target.height)
      ],
      { windowsHide: true },
      (error, stdout, stderr) => {
        alignInFlight = false;

        if (pendingAlign) {
          pendingAlign = false;
          alignRobloxWindow();
        }

        if (error) {
          resolve({ ok: false, error: stderr.trim() || error.message });
          return;
        }

        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.setAlwaysOnTop(true, "screen-saver");
          mainWindow.moveTop();
        }

        resolve({ ok: true, message: stdout.trim(), target });
      }
    );
  });
};

const attachRobloxWindow = async () => {
  robloxAttached = true;
  return alignRobloxWindow();
};

const sendMainLog = (message) => {
  const timestamp = new Date().toISOString();
  try {
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    fs.appendFileSync(logPath, `[${timestamp}] ${message}\n`, "utf8");
  } catch (error) {
    console.error("Failed to write log:", error);
  }

  mainWindow?.webContents?.send("macro:log", message);
};

const runStartMacro = async (options = {}) => {
  if (macroInFlight) {
    return { ok: false, error: "Macro is already running." };
  }

  sendMainLog("Aligning Roblox...");
  const alignResult = await attachRobloxWindow();
  if (!alignResult.ok) {
    sendMainLog(`Align failed: ${alignResult.error}`);
    return alignResult;
  }

  const target = alignResult.target || getRobloxTargetBounds();
  if (!target) return { ok: false, error: "Roblox slot is not ready." };

  macroInFlight = true;
  applyMainWindowShape();
  mainWindow?.setAlwaysOnTop(true, "screen-saver");
  mainWindow?.moveTop();
  const mode = options.mode || "story";
  const map = options.map || "Planet Namak";
  const act = options.act || "Act 1";
  sendMainLog(`Starting ${mode}: ${map} / ${act}...`);

  return new Promise((resolve) => {
    const child = spawn(
      "py",
      [
        "-3",
        startStoryScript,
        "--x",
        String(target.x),
        "--y",
        String(target.y),
        "--width",
        String(target.width),
        "--height",
        String(target.height),
        "--mode",
        mode,
        "--map",
        map,
        "--act",
        act
      ],
      { windowsHide: true }
    );
    let stderr = "";
    let stdout = "";

    const handleLines = (chunk, onLine) => {
      chunk
        .toString()
        .split(/\r?\n/)
        .filter(Boolean)
        .forEach(onLine);
    };

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
      handleLines(chunk, sendMainLog);
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (error) => {
      macroInFlight = false;
      applyMainWindowShape();
      mainWindow?.setAlwaysOnTop(true, "screen-saver");
      mainWindow?.moveTop();
      sendMainLog(`Macro failed: ${error.message}`);
      resolve({ ok: false, error: error.message });
    });

    child.on("close", (code) => {
        macroInFlight = false;
        applyMainWindowShape();
        mainWindow?.setAlwaysOnTop(true, "screen-saver");
        mainWindow?.moveTop();

        if (code !== 0) {
          const errorMessage = stderr.trim() || `Macro exited with code ${code}`;
          sendMainLog(`Macro failed: ${errorMessage}`);
          resolve({ ok: false, error: errorMessage });
          return;
        }

        if (!stdout.trim()) {
          sendMainLog("Macro finished.");
        }
        resolve({ ok: true, message: stdout.trim() });
    });
  });
};

const runNamekHelper = async ({ flag, extraArgs = [], startMessage, failureLabel, emptySuccessMessage }) => {
  if (macroInFlight) {
    return { ok: false, error: "Macro is already running." };
  }

  const target = getRobloxTargetBounds();
  if (!target) {
    const error = "Roblox slot is not ready.";
    sendMainLog(`${failureLabel} failed: ${error}`);
    return { ok: false, error };
  }

  macroInFlight = true;
  applyMainWindowShape();
  mainWindow?.setAlwaysOnTop(true, "screen-saver");
  mainWindow?.moveTop();
  sendMainLog(startMessage);

  return new Promise((resolve) => {
    const child = spawn(
      "py",
      [
        "-3",
        startStoryScript,
        "--x",
        String(target.x),
        "--y",
        String(target.y),
        "--width",
        String(target.width),
        "--height",
        String(target.height),
        "--spawn-template-map",
        "planet-namek",
        flag,
        ...extraArgs
      ],
      { windowsHide: true }
    );
    let stderr = "";
    let stdout = "";

    const handleLines = (chunk, onLine) => {
      chunk
        .toString()
        .split(/\r?\n/)
        .filter(Boolean)
        .forEach(onLine);
    };

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
      handleLines(chunk, sendMainLog);
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (error) => {
      macroInFlight = false;
      applyMainWindowShape();
      mainWindow?.setAlwaysOnTop(true, "screen-saver");
      mainWindow?.moveTop();
      sendMainLog(`${failureLabel} failed: ${error.message}`);
      resolve({ ok: false, error: error.message });
    });

    child.on("close", (code) => {
      macroInFlight = false;
      applyMainWindowShape();
      mainWindow?.setAlwaysOnTop(true, "screen-saver");
      mainWindow?.moveTop();

      if (code !== 0) {
        const errorMessage = stderr.trim() || `${failureLabel} exited with code ${code}`;
        sendMainLog(`${failureLabel} failed: ${errorMessage}`);
        resolve({ ok: false, error: errorMessage });
        return;
      }

      if (!stdout.trim()) {
        sendMainLog(emptySuccessMessage);
      }
      resolve({ ok: true, message: stdout.trim() });
    });
  });
};

const runNamekCameraNormalization = () =>
  runNamekHelper({
    flag: "--normalize-namek-camera",
    startMessage: "Normalizing Planet Namek camera...",
    failureLabel: "Camera normalization",
    emptySuccessMessage: "Camera normalization finished."
  });

const captureNamekSpawnAnchor = () =>
  runNamekHelper({
    flag: "--capture-namek-spawn-anchor",
    startMessage: "Capturing Planet Namek spawn anchor...",
    failureLabel: "Spawn anchor capture",
    emptySuccessMessage: "Spawn anchor capture finished."
  });

const testNamekSpawnDetector = () =>
  runNamekHelper({
    flag: "--test-namek-spawn-detector",
    extraArgs: ["--spawn-test-attempts", "100"],
    startMessage: "Testing Planet Namek spawn detector...",
    failureLabel: "Spawn detector test",
    emptySuccessMessage: "Spawn detector test finished."
  });

const playNamekMovement = () =>
  runNamekHelper({
    flag: "--play-movement",
    startMessage: "Playing saved Planet Namek movement...",
    failureLabel: "Movement playback",
    emptySuccessMessage: "Movement playback finished."
  });

const toggleMovementRecording = () => {
  if (movementRecorder) {
    fs.mkdirSync(path.dirname(movementStopFlagPath), { recursive: true });
    fs.writeFileSync(movementStopFlagPath, "stop", "utf8");
    sendMainLog("Stopping movement recording...");
    return;
  }

  if (macroInFlight) {
    sendMainLog("Movement recording failed: Macro is already running.");
    return;
  }

  const target = getRobloxTargetBounds();
  if (!target) {
    sendMainLog("Movement recording failed: Roblox slot is not ready.");
    return;
  }

  try {
    if (fs.existsSync(movementStopFlagPath)) {
      fs.unlinkSync(movementStopFlagPath);
    }
  } catch (error) {
    sendMainLog(`Movement recording cleanup failed: ${error.message}`);
  }

  macroInFlight = true;
  applyMainWindowShape();
  mainWindow?.setAlwaysOnTop(true, "screen-saver");
  mainWindow?.moveTop();
  sendMainLog("Starting movement recording...");

  movementRecorder = spawn(
    "py",
    [
      "-3",
      startStoryScript,
      "--x",
      String(target.x),
      "--y",
      String(target.y),
      "--width",
      String(target.width),
      "--height",
      String(target.height),
      "--spawn-template-map",
      "planet-namek",
      "--record-movement"
    ],
    { windowsHide: true }
  );
  let stderr = "";

  const handleLines = (chunk, onLine) => {
    chunk
      .toString()
      .split(/\r?\n/)
      .filter(Boolean)
      .forEach(onLine);
  };

  movementRecorder.stdout.on("data", (chunk) => {
    handleLines(chunk, sendMainLog);
  });

  movementRecorder.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });

  movementRecorder.on("error", (error) => {
    movementRecorder = null;
    macroInFlight = false;
    applyMainWindowShape();
    mainWindow?.setAlwaysOnTop(true, "screen-saver");
    mainWindow?.moveTop();
    sendMainLog(`Movement recording failed: ${error.message}`);
  });

  movementRecorder.on("close", (code) => {
    movementRecorder = null;
    macroInFlight = false;
    applyMainWindowShape();
    mainWindow?.setAlwaysOnTop(true, "screen-saver");
    mainWindow?.moveTop();

    if (code !== 0) {
      const errorMessage = stderr.trim() || `Movement recording exited with code ${code}`;
      sendMainLog(`Movement recording failed: ${errorMessage}`);
    }
  });
};

const alignIfAttached = () => {
  if (robloxAttached) {
    alignRobloxWindow();
  }
};

const getMapImages = () => {
  const searchDirs = [
    path.join(app.getAppPath(), "data", "map"),
    path.join(app.getAppPath(), "data", "maps"),
    path.join(app.getAppPath(), "map"),
    path.join(app.getAppPath(), "maps"),
    path.join(__dirname, "../renderer/map"),
    path.join(__dirname, "../renderer/maps")
  ];
  const extensions = new Set([".png", ".jpg", ".jpeg", ".webp"]);

  return searchDirs.flatMap((directory) => {
    if (!fs.existsSync(directory)) return [];

    return fs
      .readdirSync(directory, { withFileTypes: true })
      .filter((entry) => entry.isFile() && extensions.has(path.extname(entry.name).toLowerCase()))
      .map((entry) => {
        const filePath = path.join(directory, entry.name);
        return {
          name: path.basename(entry.name, path.extname(entry.name)),
          url: pathToFileURL(filePath).toString()
        };
      });
  });
};

const readUserConfig = () => {
  try {
    if (!fs.existsSync(userConfigPath)) return {};
    return JSON.parse(fs.readFileSync(userConfigPath, "utf8"));
  } catch (error) {
    console.error("Failed to read user config:", error);
    return {};
  }
};

const writeUserConfig = (_event, config) => {
  try {
    fs.mkdirSync(path.dirname(userConfigPath), { recursive: true });
    fs.writeFileSync(userConfigPath, `${JSON.stringify(config, null, 2)}\n`, "utf8");
    return { ok: true };
  } catch (error) {
    console.error("Failed to save user config:", error);
    return { ok: false, error: error.message };
  }
};

const openConfigWindow = () => {
  if (configWindow && !configWindow.isDestroyed()) {
    configWindow.focus();
    return;
  }

  configWindow = new BrowserWindow({
    width: 1320,
    height: 720,
    minWidth: 1080,
    minHeight: 640,
    title: "OpenAVAuto Configs",
    backgroundColor: "#070a10",
    frame: false,
    minimizable: true,
    skipTaskbar: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  configWindow.setMenuBarVisibility(false);
  configWindow.setAlwaysOnTop(true, "screen-saver");
  configWindow.loadFile(path.join(__dirname, "../renderer/config.html"));
  configWindow.on("closed", () => {
    configWindow = null;
  });
};

const openMainSettingsWindow = () => {
  if (mainSettingsWindow && !mainSettingsWindow.isDestroyed()) {
    mainSettingsWindow.focus();
    return;
  }

  mainSettingsWindow = new BrowserWindow({
    width: 1180,
    height: 700,
    minWidth: 980,
    minHeight: 620,
    title: "OpenAVAuto Main Settings",
    backgroundColor: "#070a10",
    frame: false,
    minimizable: true,
    skipTaskbar: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  mainSettingsWindow.setMenuBarVisibility(false);
  mainSettingsWindow.setAlwaysOnTop(true, "screen-saver");
  mainSettingsWindow.loadFile(path.join(__dirname, "../renderer/main-settings.html"));
  mainSettingsWindow.on("closed", () => {
    mainSettingsWindow = null;
  });
};

const openTasksWindow = () => {
  if (tasksWindow && !tasksWindow.isDestroyed()) {
    tasksWindow.focus();
    return;
  }

  tasksWindow = new BrowserWindow({
    width: 980,
    height: 520,
    minWidth: 820,
    minHeight: 430,
    title: "OpenAVAuto Tasks",
    backgroundColor: "#070a10",
    frame: false,
    minimizable: true,
    skipTaskbar: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  tasksWindow.setMenuBarVisibility(false);
  tasksWindow.setAlwaysOnTop(true, "screen-saver");
  tasksWindow.loadFile(path.join(__dirname, "../renderer/tasks.html"));
  tasksWindow.on("closed", () => {
    tasksWindow = null;
  });
};

const createMainWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1348,
    height: 710,
    minWidth: 1120,
    minHeight: 690,
    backgroundColor: "#00000000",
    frame: false,
    transparent: true,
    hasShadow: true,
    title: "OpenAVAuto",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  mainWindow.setMenuBarVisibility(false);
  mainWindow.setAlwaysOnTop(true, "screen-saver");
  mainWindow.loadFile(path.join(__dirname, "../renderer/index.html"));
  mainWindow.on("move", alignIfAttached);
  mainWindow.on("resize", () => {
    applyMainWindowShape();
    alignIfAttached();
  });
};

app.whenReady().then(() => {
  ipcMain.handle("app:get-version", () => app.getVersion());
  ipcMain.handle("config:list-map-images", () => getMapImages());
  ipcMain.handle("config:load-user-config", () => readUserConfig());
  ipcMain.handle("config:save-user-config", writeUserConfig);
  ipcMain.on("main-settings:open", () => openMainSettingsWindow());
  ipcMain.on("tasks:open", () => openTasksWindow());
  ipcMain.on("config:open", () => openConfigWindow());
  ipcMain.handle("roblox:align", () => attachRobloxWindow());
  ipcMain.handle("macro:start", (_event, options) => runStartMacro(options));
  ipcMain.on("roblox:set-slot-bounds", (_event, bounds) => {
    slotBounds = bounds;
    applyMainWindowShape();
    alignIfAttached();
  });
  ipcMain.on("window:minimize", (event) => {
    BrowserWindow.fromWebContents(event.sender)?.minimize();
  });
  ipcMain.on("window:maximize-toggle", (event) => {
    const window = BrowserWindow.fromWebContents(event.sender);
    if (!window) return;
    if (window.isMaximized()) {
      window.unmaximize();
    } else {
      window.maximize();
    }
  });
  ipcMain.on("window:close", (event) => {
    BrowserWindow.fromWebContents(event.sender)?.close();
  });
  createMainWindow();
  globalShortcut.register("F1", () => {
    attachRobloxWindow();
  });
  globalShortcut.register("F2", () => {
    runStartMacro();
  });
  globalShortcut.register("F8", () => {
    runNamekCameraNormalization();
  });
  globalShortcut.register("F9", () => {
    captureNamekSpawnAnchor();
  });
  globalShortcut.register("F10", () => {
    testNamekSpawnDetector();
  });
  globalShortcut.register("F11", () => {
    toggleMovementRecording();
  });
  globalShortcut.register("Insert", () => {
    playNamekMovement();
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
