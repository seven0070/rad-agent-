//! RAD Desktop backend lifecycle. Fixed `rad serve` argv only — no arbitrary shell.

use serde::Serialize;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

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
    if let Ok(h) = std::env::var("RAD_HOME") {
        return PathBuf::from(h);
    }
    #[cfg(windows)]
    if let Some(profile) = std::env::var_os("USERPROFILE") {
        return PathBuf::from(profile).join(".rad");
    }
    if let Some(home) = std::env::var_os("HOME") {
        return PathBuf::from(home).join(".rad");
    }
    PathBuf::from(".rad")
}

fn python_bin() -> String {
    std::env::var("RAD_PYTHON").unwrap_or_else(|_| {
        if cfg!(windows) {
            "python".into()
        } else {
            "python3".into()
        }
    })
}

enum RadProgram {
    PythonModule,
    Direct(PathBuf),
}

fn target_triple() -> Option<&'static str> {
    match (std::env::consts::OS, std::env::consts::ARCH) {
        ("windows", "x86_64") => Some("x86_64-pc-windows-msvc"),
        ("macos", "aarch64") => Some("aarch64-apple-darwin"),
        ("macos", "x86_64") => Some("x86_64-apple-darwin"),
        ("linux", "x86_64") => Some("x86_64-unknown-linux-gnu"),
        ("linux", "aarch64") => Some("aarch64-unknown-linux-gnu"),
        _ => None,
    }
}

fn rad_program() -> RadProgram {
    if let Ok(bin) = std::env::var("RAD_BIN") {
        return RadProgram::Direct(PathBuf::from(bin));
    }
    if let Some(triple) = target_triple() {
        let exe_dir = std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(PathBuf::from));
        let name = if cfg!(windows) {
            format!("rad-{triple}.exe")
        } else {
            format!("rad-{triple}")
        };
        if let Some(mut candidate) = exe_dir {
            candidate.push(name);
            if candidate.is_file() {
                return RadProgram::Direct(candidate);
            }
        }
    }
    RadProgram::PythonModule
}

fn token_path(home: &Path) -> PathBuf {
    home.join("api.token")
}

#[tauri::command]
fn default_home() -> String {
    default_rad_home().display().to_string()
}

#[tauri::command]
fn api_token(home: Option<String>) -> Result<String, String> {
    let root = home
        .map(PathBuf::from)
        .unwrap_or_else(default_rad_home);
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
    let program = rad_program();
    let mut cmd = match &program {
        RadProgram::PythonModule => {
            let mut c = Command::new(python_bin());
            c.args(["-m", "rad", "serve", "--host", "127.0.0.1", "--port", &port.to_string()]);
            c
        }
        RadProgram::Direct(p) => {
            let mut c = Command::new(p);
            c.args(["serve", "--host", "127.0.0.1", "--port", &port.to_string()]);
            c
        }
    };
    cmd.env("RAD_HOME", &home)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    let label = match &program {
        RadProgram::PythonModule => python_bin(),
        RadProgram::Direct(p) => p.display().to_string(),
    };
    let child = cmd
        .spawn()
        .map_err(|e| format!("failed to start rad serve via {label}: {e}"))?;
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
