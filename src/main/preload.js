const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("openAVAuto", {
  getVersion: () => ipcRenderer.invoke("app:get-version"),
  window: {
    minimize: () => ipcRenderer.send("window:minimize"),
    maximizeToggle: () => ipcRenderer.send("window:maximize-toggle"),
    close: () => ipcRenderer.send("window:close")
  }
});
