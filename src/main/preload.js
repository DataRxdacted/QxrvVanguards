const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("openAVAuto", {
  getVersion: () => ipcRenderer.invoke("app:get-version"),
  config: {
    open: () => ipcRenderer.send("config:open"),
    listMapImages: () => ipcRenderer.invoke("config:list-map-images"),
    loadUserConfig: () => ipcRenderer.invoke("config:load-user-config"),
    saveUserConfig: (config) => ipcRenderer.invoke("config:save-user-config", config)
  },
  roblox: {
    align: () => ipcRenderer.invoke("roblox:align"),
    setSlotBounds: (bounds) => ipcRenderer.send("roblox:set-slot-bounds", bounds)
  },
  macro: {
    start: (options) => ipcRenderer.invoke("macro:start", options),
    onLog: (callback) => {
      const listener = (_event, message) => callback(message);
      ipcRenderer.on("macro:log", listener);
      return () => ipcRenderer.removeListener("macro:log", listener);
    }
  },
  window: {
    minimize: () => ipcRenderer.send("window:minimize"),
    maximizeToggle: () => ipcRenderer.send("window:maximize-toggle"),
    close: () => ipcRenderer.send("window:close")
  }
});
