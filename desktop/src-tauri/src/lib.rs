//! RAD Desktop backend lifecycle. Fixed `rad serve` argv only — no arbitrary shell.

use serde::Serialize;
use std::ffi::OsString;
use std::net::{SocketAddr, TcpStream};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::{Duration, Instant};
use tauri::Manager;

#[derive(Serialize, Clone)]
pub struct BackendInfo {
    running: bool,
    port: u16,
    home: String,
    pid: Option<u32>,
    managed: bool,
}

struct Backend {
    child: Child,
    port: u16,
    home: PathBuf,
}

struct State {
    backend: Mutex<Option<Backend>>,
}

fn default_rad_home() -> PathBuf {
    if let Ok(h) = std::env::var("RAD_HOME") {
        return PathBuf::from(h);
    }
    dirs_fallback()
}

fn dirs_fallback() -> PathBuf {
    if let Some(home) = std::env::var_os("HOME") {
        return PathBuf::from(home).join(".rad");
    }
    PathBuf::from(".rad")
}

fn python_bin() -> String {
    std::env::var("RAD_PYTHON").unwrap_or_else(|_| "python3".into())
}

fn bundled_backend_root(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    if let Ok(root) = std::env::var("RAD_DESKTOP_SOURCE_ROOT") {
        let p = PathBuf::from(root);
        if p.join("rad").exists() {
            return Ok(p);
        }
    }
    if let Ok(dir) = app.path().resource_dir() {
        if dir.join("rad").exists() {
            return Ok(dir);
        }
    }
    let dev = PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/../.."));
    if dev.join("rad").exists() {
        return Ok(dev);
    }
    Err("bundled RAD backend sources not found".into())
}

fn python_path(root: &PathBuf) -> Result<OsString, String> {
    let mut paths = vec![root.clone()];
    if let Some(existing) = std::env::var_os("PYTHONPATH") {
        paths.extend(std::env::split_paths(&existing));
    }
    std::env::join_paths(paths).map_err(|e| format!("cannot set PYTHONPATH: {e}"))
}

fn wait_for_backend_ready(child: &mut Child, port: u16, home: &PathBuf) -> Result<(), String> {
    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    let tok = token_path(home);
    let deadline = Instant::now() + Duration::from_secs(15);
    while Instant::now() < deadline {
        if let Some(status) = child.try_wait().map_err(|e| e.to_string())? {
            return Err(format!("rad serve exited before ready: {status}"));
        }
        let port_ready = TcpStream::connect_timeout(&addr, Duration::from_millis(250)).is_ok();
        if port_ready && tok.exists() {
            return Ok(());
        }
        thread::sleep(Duration::from_millis(200));
    }
    Err(format!(
        "timed out waiting for RAD backend on http://127.0.0.1:{port}"
    ))
}

fn token_path(home: &PathBuf) -> PathBuf {
    home.join("api.token")
}

#[tauri::command]
fn default_home() -> String {
    default_rad_home().display().to_string()
}

#[tauri::command]
fn api_token(home: Option<String>) -> Result<String, String> {
    let root = home.map(PathBuf::from).unwrap_or_else(default_rad_home);
    let p = token_path(&root);
    std::fs::read_to_string(&p)
        .map(|s| s.trim().to_string())
        .map_err(|e| format!("cannot read {}: {e}", p.display()))
}

#[tauri::command]
fn backend_info(state: tauri::State<State>) -> BackendInfo {
    let guard = state.backend.lock().ok();
    if let Some(ref slot) = guard {
        if let Some(b) = slot.as_ref() {
            return BackendInfo {
                running: true,
                port: b.port,
                home: b.home.display().to_string(),
                pid: Some(b.child.id()),
                managed: true,
            };
        }
    }
    BackendInfo {
        running: false,
        port: 7331,
        home: default_rad_home().display().to_string(),
        pid: None,
        managed: false,
    }
}

#[tauri::command]
fn backend_start(
    app: tauri::AppHandle,
    state: tauri::State<State>,
    port: Option<u16>,
    home: Option<String>,
) -> Result<BackendInfo, String> {
    let port = port.unwrap_or(7331);
    let home = home.map(PathBuf::from).unwrap_or_else(default_rad_home);
    {
        let guard = state.backend.lock().map_err(|e| e.to_string())?;
        if let Some(b) = guard.as_ref() {
            return Ok(BackendInfo {
                running: true,
                port: b.port,
                home: b.home.display().to_string(),
                pid: Some(b.child.id()),
                managed: true,
            });
        }
    }
    // Fixed argv: never interpolate a user command string.
    let backend_root = bundled_backend_root(&app)?;
    let python = python_bin();
    let mut cmd = Command::new(&python);
    cmd.args([
        "-m",
        "rad",
        "serve",
        "--host",
        "127.0.0.1",
        "--port",
        &port.to_string(),
    ])
    .current_dir(&backend_root)
    .env("RAD_HOME", &home)
    .env("PYTHONPATH", python_path(&backend_root)?)
    .stdin(Stdio::null())
    .stdout(Stdio::null())
    .stderr(Stdio::null());
    let mut child = cmd
        .spawn()
        .map_err(|e| format!("failed to start bundled rad serve via {python}: {e}"))?;
    wait_for_backend_ready(&mut child, port, &home)?;
    let pid = child.id();
    let mut guard = state.backend.lock().map_err(|e| e.to_string())?;
    *guard = Some(Backend {
        child,
        port,
        home: home.clone(),
    });
    Ok(BackendInfo {
        running: true,
        port,
        home: home.display().to_string(),
        pid: Some(pid),
        managed: true,
    })
}

#[tauri::command]
fn backend_stop(state: tauri::State<State>) -> Result<(), String> {
    let mut guard = state.backend.lock().map_err(|e| e.to_string())?;
    if let Some(mut b) = guard.take() {
        let _ = b.child.kill();
        let _ = b.child.wait();
    }
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(State {
            backend: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            default_home,
            api_token,
            backend_info,
            backend_start,
            backend_stop
        ])
        .run(tauri::generate_context!())
        .expect("error while running RAD Desktop");
}
