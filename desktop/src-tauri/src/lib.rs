//! RAD Desktop backend lifecycle.
//!
//! The desktop owns the UX around the RAD backend; the backend stays authoritative:
//!
//!     Launch Desktop → start/locate RAD backend → health check → connect → operate
//!                      → disconnect cleanly (no silent failure)
//!
//! The backend is the packaged `rad-backend` sidecar (a PyInstaller build of
//! `rad/sidecar.py`, placed via `bundle.externalBin`). It is launched with a
//! FIXED argv — `serve --host 127.0.0.1 --port <n>` — and only these lifecycle
//! commands exist. There is no arbitrary command execution: no user-supplied
//! command string ever reaches a process spawn, and the sidecar itself only
//! binds loopback.
//!
//! In `tauri dev` (no packaged sidecar present) the lifecycle falls back to
//! `RAD_PYTHON` (or `python3 -m rad`), which is what the developer has checked
//! out. Production builds always use the sidecar.

use serde::Serialize;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;

const DEFAULT_PORT: u16 = 7331;
const HEALTH_TIMEOUT_MS: u64 = 3000;
const STARTUP_WAIT_SECS: u64 = 20;

#[derive(Serialize, Clone)]
pub struct BackendInfo {
    running: bool,
    port: u16,
    home: String,
    pid: Option<u32>,
    managed: bool,
    sidecar: bool,
}

#[derive(Serialize, Clone)]
pub struct HealthReport {
    ok: bool,
    port: u16,
    version: Option<String>,
    error: Option<String>,
}

struct Backend {
    child: Child,
    port: u16,
    home: PathBuf,
    sidecar: bool,
}

struct State {
    backend: Mutex<Option<Backend>>,
}

fn default_rad_home() -> PathBuf {
    if let Ok(h) = std::env::var("RAD_HOME") {
        return PathBuf::from(h);
    }
    if let Some(home) = std::env::var_os("HOME") {
        return PathBuf::from(home).join(".rad");
    }
    if let Ok(pf) = std::env::var("USERPROFILE") {
        return PathBuf::from(pf).join(".rad");
    }
    PathBuf::from(".rad")
}

/// Target triple of *this* build (matches the Tauri sidecar naming).
fn target_triple() -> Option<&'static str> {
    match (std::env::consts::OS, std::env::consts::ARCH) {
        ("linux", "x86_64") => Some("x86_64-unknown-linux-gnu"),
        ("linux", "aarch64") => Some("aarch64-unknown-linux-gnu"),
        ("macos", "aarch64") => Some("aarch64-apple-darwin"),
        ("macos", "x86_64") => Some("x86_64-apple-darwin"),
        ("windows", "x86_64") => Some("x86_64-pc-windows-msvc"),
        _ => None,
    }
}

fn sidecar_name(triple: &str) -> String {
    if cfg!(windows) {
        format!("rad-backend-{}.exe", triple)
    } else {
        format!("rad-backend-{}", triple)
    }
}

/// File names for the packaged backend, preferred first.
///
/// Installers (MSI/NSIS) ship the **short** name (`rad-backend[.exe]`) next to
/// `rad-desktop`. The build tree and `tauri dev` keep the **triple-suffixed**
/// name (`rad-backend-<triple>[.exe]`) under `src-tauri/binaries/`. Short name
/// first so an installed build never falls through to the compile-time path.
fn sidecar_names() -> Vec<String> {
    let short = if cfg!(windows) {
        "rad-backend.exe"
    } else {
        "rad-backend"
    };
    let mut names = vec![short.to_string()];
    if let Some(triple) = target_triple() {
        let n = sidecar_name(triple);
        if !names.iter().any(|x| x == &n) {
            names.push(n);
        }
    }
    names
}

/// Resolve the packaged sidecar binary. Tauri places externalBin next to the
/// main executable (linux/windows) or in the app bundle's resources dir
/// (macOS), under the short name. In `tauri dev` the checkout's
/// `src-tauri/binaries/` holds the triple-suffixed name. Install-dir layout is
/// always tried before the compile-time manifest path (clean machine must not
/// depend on the repo). Size gate: >1024 bytes (rejects 0-byte placeholders).
fn resolve_sidecar() -> Option<PathBuf> {
    let names = sidecar_names();
    let mut dirs: Vec<PathBuf> = Vec::new();
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            dirs.push(dir.to_path_buf());
            dirs.push(dir.join("binaries"));
            dirs.push(dir.join("Resources"));
            dirs.push(dir.join("../Resources"));
        }
    }
    dirs.push(std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("binaries"));
    dirs.push(std::path::Path::new("binaries").to_path_buf());

    for dir in &dirs {
        for name in &names {
            let p = dir.join(name);
            if p.is_file() && p.metadata().map(|m| m.len() > 1024).unwrap_or(false) {
                return Some(p);
            }
        }
    }
    None
}

fn python_bin() -> String {
    std::env::var("RAD_PYTHON")
        .ok()
        .or_else(which_python)
        .unwrap_or_else(|| {
            if cfg!(windows) {
                "python".into()
            } else {
                "python3".into()
            }
        })
}

fn which_python() -> Option<String> {
    if let Ok(p) = std::env::var("RAD_PYTHON") {
        return Some(p);
    }
    let candidates = if cfg!(windows) {
        vec!["python", "python3", "py"]
    } else {
        vec!["python3", "python"]
    };
    for c in candidates {
        if let Ok(status) = Command::new(c)
            .arg("--version")
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
        {
            if status.success() {
                return Some(c.into());
            }
        }
    }
    None
}

fn token_path(home: &PathBuf) -> PathBuf {
    home.join("api.token")
}

fn read_token(home: &PathBuf) -> Option<String> {
    std::fs::read_to_string(token_path(home))
        .ok()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
}

fn backend_log_path(home: &PathBuf) -> PathBuf {
    home.join("logs").join("backend.log")
}

fn append_backend_log(home: &PathBuf, line: &str) {
    let p = backend_log_path(home);
    if let Ok(mut f) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&p)
    {
        use std::io::Write;
        let _ = writeln!(f, "{} {}", chrono_free_now(), line);
    }
}

fn chrono_free_now() -> String {
    // no chrono dep: SystemTime is enough for log lines
    let s = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    format!("t={}", s)
}

/// Minimal HTTP GET against loopback with a bearer token (no HTTP client crate:
/// the desktop is a surface, not a proxy, and one fixed path is all it needs).
fn http_health(port: u16, token: Option<&str>) -> HealthReport {
    use std::io::{Read, Write};
    use std::net::TcpStream;
    let addr_str = format!("127.0.0.1:{}", port);
    let addr: std::net::SocketAddr = match addr_str.parse() {
        Ok(a) => a,
        Err(e) => {
            return HealthReport {
                ok: false,
                port,
                version: None,
                error: Some(format!("addr parse error: {}", e)),
            };
        }
    };
    let mut stream = match TcpStream::connect_timeout(&addr, Duration::from_millis(HEALTH_TIMEOUT_MS)) {
        Ok(s) => s,
        Err(e) => {
            return HealthReport {
                ok: false,
                port,
                version: None,
                error: Some(format!("connect {}: {}", addr_str, e)),
            };
        }
    };
    let _ = stream.set_read_timeout(Some(Duration::from_millis(HEALTH_TIMEOUT_MS)));
    let auth = token.map(|t| format!("Authorization: Bearer {}\r\n", t)).unwrap_or_default();
    let req = format!(
        "GET /v1/health HTTP/1.1\r\nHost: 127.0.0.1:{}\r\n{}\r\n\r\n",
        port, auth
    );
    if stream.write_all(req.as_bytes()).is_err() {
        return HealthReport {
            ok: false,
            port,
            version: None,
            error: Some("write failed".into()),
        };
    }
    let mut buf = Vec::new();
    if stream.read_to_end(&mut buf).is_err() {
        return HealthReport {
            ok: false,
            port,
            version: None,
            error: Some("read failed".into()),
        };
    }
    let text = String::from_utf8_lossy(&buf).to_string();
    let body = text.split("\r\n\r\n").nth(1).unwrap_or("").to_string();
    let v: serde_json::Value = match serde_json::from_str(&body) {
        Ok(v) => v,
        Err(_) => {
            return HealthReport {
                ok: false,
                port,
                version: None,
                error: Some(format!("unhealthy response: {}", body.chars().take(160).collect::<String>())),
            }
        }
    };
    HealthReport {
        ok: v.get("ok").and_then(|x| x.as_bool()).unwrap_or(false),
        port,
        version: v.get("version").and_then(|x| x.as_str()).map(|s| s.to_string()),
        error: if v.get("ok").and_then(|x| x.as_bool()).unwrap_or(false) {
            None
        } else {
            Some(body.chars().take(160).collect())
        },
    }
}

/// Wait for the backend to become healthy. Returns the report; the tail of the
/// backend log is attached to the error so a failed start is never silent.
fn wait_healthy(home: &PathBuf, port: u16) -> HealthReport {
    let deadline = std::time::Instant::now() + Duration::from_secs(STARTUP_WAIT_SECS);
    let mut last = HealthReport {
        ok: false,
        port,
        version: None,
        error: Some("starting".into()),
    };
    while std::time::Instant::now() < deadline {
        if let Some(tok) = read_token(home) {
            last = http_health(port, Some(&tok));
            if last.ok {
                return last;
            }
        } else if std::net::TcpStream::connect(format!("127.0.0.1:{}", port)).is_err() {
            // no token yet — the sidecar writes it on first serve
            last = HealthReport {
                ok: false,
                port,
                version: None,
                error: Some("waiting for backend to bind".into()),
            };
        }
        std::thread::sleep(Duration::from_millis(250));
    }
    if !last.ok {
        if let Some(e) = &last.error {
            append_backend_log(
                home,
                &format!("unhealthy after {}s: {}", STARTUP_WAIT_SECS, e),
            );
        }
        let tail = std::fs::read_to_string(backend_log_path(home))
            .map(|s| {
                s.lines()
                    .rev()
                    .take(5)
                    .collect::<Vec<_>>()
                    .into_iter()
                    .rev()
                    .collect::<Vec<_>>()
                    .join(" | ")
            })
            .unwrap_or_default();
        last.error = Some(format!(
            "{}{}{}",
            last.error.as_deref().unwrap_or("unhealthy"),
            if tail.is_empty() { "" } else { " — backend log: " },
            tail
        ));
    }
    last
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
    let mut guard = state.backend.lock().ok();
    if let Some(ref mut g) = guard {
        if let Some(b) = g.as_mut() {
            let alive = b.child.try_wait().ok().flatten().is_none();
            if alive {
                return BackendInfo {
                    running: true,
                    port: b.port,
                    home: b.home.display().to_string(),
                    pid: Some(b.child.id()),
                    managed: true,
                    sidecar: b.sidecar,
                };
            }
        }
    }
    BackendInfo {
        running: false,
        port: DEFAULT_PORT,
        home: default_rad_home().display().to_string(),
        pid: None,
        managed: false,
        sidecar: false,
    }
}

fn probe_foreign(port: u16) -> Option<String> {
    // Something is already listening. With no token a live RAD answers 401
    // ("bearer token"); any other live response means a foreign process.
    let rep = http_health(port, None);
    if rep.version.is_some() {
        return Some(format!("a RAD backend is already listening (v{})", rep.version.unwrap()));
    }
    if let Some(e) = &rep.error {
        if e.contains("bearer") {
            return Some("an existing RAD backend is listening (token mismatch or stale process)".into());
        }
    }
    None
}

#[tauri::command]
fn backend_start(
    state: tauri::State<State>,
    port: Option<u16>,
    home: Option<String>,
) -> Result<BackendInfo, String> {
    let port = port.unwrap_or(DEFAULT_PORT);
    let home = home.map(PathBuf::from).unwrap_or_else(default_rad_home);
    {
        let mut guard = state.backend.lock().map_err(|e| e.to_string())?;
        if let Some(b) = guard.as_mut() {
            if b.child.try_wait().ok().flatten().is_none() {
                return Ok(BackendInfo {
                    running: true,
                    port: b.port,
                    home: b.home.display().to_string(),
                    pid: Some(b.child.id()),
                    managed: true,
                    sidecar: b.sidecar,
                });
            }
        }
    }

    // Pre-flight: a stale/foreign process on the port must be surfaced, not swallowed.
    if let Some(note) = probe_foreign(port) {
        append_backend_log(&home, &format!("start refused: {}", note));
        return Err(format!(
            "cannot start: {} (port {}). Stop the stale process or use another port.",
            note, port
        ));
    }

    let mut sidecar: Option<std::path::PathBuf> = None;
    let mut python = None;
    if let Some(p) = resolve_sidecar() {
        sidecar = Some(p);
    } else if which_python().is_some() {
        python = Some(python_bin());
    }
    let (bin, args): (String, Vec<String>) = match sidecar {
        Some(ref p) => (
            p.to_string_lossy().to_string(),
            vec!["serve".into(), "--host".into(), "127.0.0.1".into(), "--port".into(), port.to_string(), "--home".into(), home.to_string_lossy().to_string()],
        ),
        None => {
            let py = python.ok_or("no sidecar binary and no RAD_PYTHON/python3 found")?;
            // Fixed argv — never a user command string.
            (
                py,
                vec!["-m".into(), "rad".into(), "serve".into(), "--host".into(), "127.0.0.1".into(), "--port".into(), port.to_string()],
            )
        }
    };

    let mut cmd = Command::new(&bin);
    cmd.args(&args)
        .env("RAD_HOME", &home)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    // --- Process-group orphan reaping (T4 hardening) ---
    // Ensures no orphan rad-backend children survive desktop quit: new pgid on spawn,
    // backend_stop kills the whole group (taskkill /T on Windows, killpg on Unix).
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NEW_PROCESS_GROUP: u32 = 0x00000200;
        cmd.creation_flags(CREATE_NEW_PROCESS_GROUP);
    }
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        cmd.process_group(0);
    }
    let mut child = cmd
        .spawn()
        .map_err(|e| format!("failed to start backend ({bin}): {e}"))?;
    // Pump stdout/stderr into the backend log (the sidecar speaks JSON lines).
    let home_log = home.clone();
    if let Some(mut out) = child.stdout.take() {
        std::thread::spawn(move || {
            use std::io::Read;
            let mut buf = [0u8; 4096];
            loop {
                match out.read(&mut buf) {
                    Ok(0) => break,
                    Ok(n) => append_backend_log(&home_log, &String::from_utf8_lossy(&buf[..n]).trim()),
                    Err(_) => break,
                }
            }
        });
    }
    if let Some(mut err) = child.stderr.take() {
        let home_err = home.clone();
        std::thread::spawn(move || {
            use std::io::Read;
            let mut buf = [0u8; 4096];
            loop {
                match err.read(&mut buf) {
                    Ok(0) => break,
                    Ok(n) => append_backend_log(&home_err, &format!("stderr: {}", String::from_utf8_lossy(&buf[..n]).trim())),
                    Err(_) => break,
                }
            }
        });
    }
    let is_sidecar = sidecar.is_some();
    let pid = child.id();

    let report = wait_healthy(&home, port);
    if !report.ok {
        let _ = child.kill();
        let _ = child.wait();
        return Err(format!(
            "backend did not become healthy: {}",
            report.error.unwrap_or_else(|| "unknown".into())
        ));
    }
    let info = BackendInfo {
        running: true,
        port,
        home: home.display().to_string(),
        pid: Some(pid),
        managed: true,
        sidecar: is_sidecar,
    };
    {
        let mut guard = state.backend.lock().map_err(|e| e.to_string())?;
        *guard = Some(Backend { child, port, home, sidecar: is_sidecar });
    }
    Ok(info)
}

/// Reap process-group orphans: kill the whole group, not just the parent.
fn reap_orphans(pid: u32) {
    #[cfg(windows)]
    {
        let _ = std::process::Command::new("taskkill")
            .args(["/PID", &pid.to_string(), "/T", "/F"])
            .stdin(std::process::Stdio::null())
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status();
    }
    #[cfg(unix)]
    {
        // group kill via killpg — best-effort, ignore errors if already dead
        unsafe {
            // libc::killpg without new dep — raw syscall via libc crate if present,
            // fallback to just killing pid
            let pid_i32 = pid as i32;
            // use nix-style: kill(-pgid, SIGTERM) where pgid == pid
            extern "C" { fn kill(pid: i32, sig: i32) -> i32; }
            const SIGTERM: i32 = 15;
            const SIGKILL: i32 = 9;
            let _ = kill(-pid_i32, SIGTERM);
            std::thread::sleep(std::time::Duration::from_millis(200));
            let _ = kill(-pid_i32, SIGKILL);
        }
    }
}

#[tauri::command]
fn backend_stop(state: tauri::State<State>) -> Result<(), String> {
    let mut guard = state.backend.lock().map_err(|e| e.to_string())?;
    if let Some(mut b) = guard.take() {
        let pid = b.child.id();
        let _ = b.child.kill();
        let _ = b.child.wait();
        reap_orphans(pid);
        Ok(())
    } else {
        Ok(())
    }
}

#[tauri::command]
fn backend_restart(
    state: tauri::State<State>,
    port: Option<u16>,
    home: Option<String>,
) -> Result<BackendInfo, String> {
    backend_stop(state.clone()).map_err(|e| e)?;
    backend_start(state, port, home)
}

#[tauri::command]
fn backend_health(port: Option<u16>, home: Option<String>) -> HealthReport {
    let port = port.unwrap_or(DEFAULT_PORT);
    let home = home.map(PathBuf::from).unwrap_or_else(default_rad_home);
    http_health(port, read_token(&home).as_deref())
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
            backend_stop,
            backend_restart,
            backend_health
        ])
        .run(tauri::generate_context!())
        .expect("error while running RAD Desktop");
}
