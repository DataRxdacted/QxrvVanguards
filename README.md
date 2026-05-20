# OpenAVAuto

OpenAVAuto is a desktop-first vision macro studio for Roblox tower defense strategies.

This project is intentionally designed around normal desktop input automation and screen reading. It does not inject into Roblox, modify game memory, intercept traffic, or bypass anticheat.

## Run The App

```powershell
npm.cmd install
npm.cmd run dev
```

PowerShell may block the `npm` shim on some systems. Use `npm.cmd` on Windows if that happens.

## Project Shape

```text
src/main      Electron main process
src/renderer  Desktop UI
```

The current build is a static Electron shell so the product direction can be designed before wiring the vision service.
