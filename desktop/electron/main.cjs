// Electron main process: starts the Python engine (API server) and opens the
// React UI. In dev it loads the Vite dev server; in production it loads the
// built files and spawns the bundled phonexe.exe with the `serve` command.

const { app, BrowserWindow } = require("electron");
const { spawn } = require("node:child_process");
const path = require("node:path");
const http = require("node:http");

const API_PORT = 8765;
const isDev = !app.isPackaged;
let engine = null;

function startEngine() {
  if (isDev) {
    // dev: use the Python source (requires Python + deps installed)
    engine = spawn("python3", ["-m", "phonexe", "serve", "--port", String(API_PORT)], {
      cwd: path.resolve(__dirname, "..", ".."),
      stdio: "inherit",
    });
  } else {
    // prod: spawn the bundled engine executable
    const exe = path.join(process.resourcesPath, "engine", "phonexe.exe");
    engine = spawn(exe, ["serve", "--port", String(API_PORT)], { stdio: "ignore" });
  }
  engine.on("error", (e) => console.error("engine failed:", e));
}

function waitForApi(cb, tries = 0) {
  http
    .get(`http://127.0.0.1:${API_PORT}/api/health`, (res) => {
      res.resume();
      cb();
    })
    .on("error", () => {
      if (tries > 60) return cb();
      setTimeout(() => waitForApi(cb, tries + 1), 250);
    });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1920,
    height: 1080,
    minWidth: 1280,
    minHeight: 800,
    backgroundColor: "#050B12",
    autoHideMenuBar: true,
    webPreferences: { contextIsolation: true },
  });
  if (isDev) {
    win.loadURL("http://localhost:5173");
  } else {
    win.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }
}

app.whenReady().then(() => {
  startEngine();
  waitForApi(() => createWindow());
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (engine) try { engine.kill(); } catch (_) {}
  if (process.platform !== "darwin") app.quit();
});
