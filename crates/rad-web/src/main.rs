//! rad-web: High-performance Rust HTTP server & reverse proxy for RAD Agent Web UI.
//! Zero external dependencies: builds instantly with rustc / cargo.

use std::fs;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

struct Config {
    port: u16,
    api_port: u16,
    dist_dir: PathBuf,
    token: Option<String>,
}

fn resolve_dist_dir() -> PathBuf {
    // Candidates: relative to current exe or working dir
    let mut candidates = vec![
        PathBuf::from("desktop/dist"),
        PathBuf::from("../desktop/dist"),
        PathBuf::from("../../desktop/dist"),
    ];
    if let Ok(exe) = std::env::current_exe() {
        if let Some(parent) = exe.parent() {
            candidates.push(parent.join("dist"));
            candidates.push(parent.join("../../desktop/dist"));
        }
    }
    for c in candidates {
        if c.join("index.html").exists() {
            return c.canonicalize().unwrap_or(c);
        }
    }
    PathBuf::from("desktop/dist")
}

fn resolve_api_token() -> Option<String> {
    if let Ok(tok) = std::env::var("RAD_TOKEN") {
        let t = tok.trim().to_string();
        if !t.is_empty() {
            return Some(t);
        }
    }
    let home: Option<PathBuf> = std::env::var("RAD_HOME")
        .ok()
        .map(PathBuf::from)
        .or_else(|| std::env::var_os("USERPROFILE").map(|p| PathBuf::from(p).join(".rad")))
        .or_else(|| std::env::var_os("HOME").map(|p| PathBuf::from(p).join(".rad")));

    if let Some(h) = home {
        let p = h.join("api.token");
        if let Ok(content) = fs::read_to_string(&p) {
            let t = content.trim().to_string();
            if !t.is_empty() {
                return Some(t);
            }
        }
    }
    None
}

fn mime_type(path: &Path) -> &'static str {
    match path.extension().and_then(|s| s.to_str()).unwrap_or("") {
        "html" | "htm" => "text/html; charset=utf-8",
        "js" | "mjs" => "application/javascript; charset=utf-8",
        "css" => "text/css; charset=utf-8",
        "json" => "application/json; charset=utf-8",
        "svg" => "image/svg+xml",
        "png" => "image/png",
        "jpg" | "jpeg" => "image/jpeg",
        "ico" => "image/x-icon",
        "woff" => "font/woff",
        "woff2" => "font/woff2",
        "ttf" => "font/ttf",
        _ => "application/octet-stream",
    }
}

fn handle_proxy(
    client_stream: &mut TcpStream,
    config: &Config,
    raw_request: &[u8],
    headers_text: &str,
) {
    let api_addr = format!("127.0.0.1:{}", config.api_port);
    let mut backend_stream = match TcpStream::connect_timeout(
        &api_addr.parse().unwrap(),
        Duration::from_millis(3000),
    ) {
        Ok(s) => s,
        Err(e) => {
            let body = format!(
                r#"{{"error":"Cannot connect to RAD backend at {}: {}"}}"#,
                api_addr, e
            );
            let resp = format!(
                "HTTP/1.1 502 Bad Gateway\r\n\
                 Content-Type: application/json\r\n\
                 Access-Control-Allow-Origin: *\r\n\
                 Content-Length: {}\r\n\r\n{}",
                body.len(),
                body
            );
            let _ = client_stream.write_all(resp.as_bytes());
            return;
        }
    };

    let _ = backend_stream.set_read_timeout(Some(Duration::from_secs(60)));

    // Inject Authorization header if missing and local token is available
    let has_auth = headers_text
        .lines()
        .any(|line| line.to_lowercase().starts_with("authorization:"));

    if !has_auth && config.token.is_some() {
        let tok = config.token.as_ref().unwrap();
        // Insert Authorization header right after request line
        if let Some(pos) = headers_text.find("\r\n") {
            let (req_line, rest) = headers_text.split_at(pos + 2);
            let new_headers = format!("{}Authorization: Bearer {}\r\n{}", req_line, tok, rest);
            // Replace header section of raw_request
            if let Some(header_end) = find_header_end(raw_request) {
                let body = &raw_request[header_end..];
                let _ = backend_stream.write_all(new_headers.as_bytes());
                let _ = backend_stream.write_all(body);
            } else {
                let _ = backend_stream.write_all(new_headers.as_bytes());
            }
        } else {
            let _ = backend_stream.write_all(raw_request);
        }
    } else {
        let _ = backend_stream.write_all(raw_request);
    }

    // Pipe response back to client
    let mut buf = [0u8; 8192];
    loop {
        match backend_stream.read(&mut buf) {
            Ok(0) => break,
            Ok(n) => {
                if client_stream.write_all(&buf[..n]).is_err() {
                    break;
                }
            }
            Err(_) => break,
        }
    }
}

fn find_header_end(data: &[u8]) -> Option<usize> {
    for i in 0..data.len().saturating_sub(3) {
        if &data[i..i + 4] == b"\r\n\r\n" {
            return Some(i + 4);
        }
    }
    None
}

fn handle_connection(mut stream: TcpStream, config: Arc<Config>) {
    let _ = stream.set_read_timeout(Some(Duration::from_secs(30)));
    let mut buf = vec![0u8; 16384];
    let n = match stream.read(&mut buf) {
        Ok(n) if n > 0 => n,
        _ => return,
    };
    buf.truncate(n);

    let header_end = match find_header_end(&buf) {
        Some(pos) => pos,
        None => return,
    };

    let headers_str = String::from_utf8_lossy(&buf[..header_end]);
    let first_line = match headers_str.lines().next() {
        Some(l) => l,
        None => return,
    };

    let mut parts = first_line.split_whitespace();
    let method = parts.next().unwrap_or("");
    let path = parts.next().unwrap_or("/");

    // CORS preflight
    if method == "OPTIONS" {
        let resp = "HTTP/1.1 204 No Content\r\n\
                    Access-Control-Allow-Origin: *\r\n\
                    Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS\r\n\
                    Access-Control-Allow-Headers: Authorization, Content-Type, Accept, X-Requested-With\r\n\
                    Access-Control-Max-Age: 86400\r\n\r\n";
        let _ = stream.write_all(resp.as_bytes());
        return;
    }

    // Proxy API requests directly to RAD backend
    if path.starts_with("/v1/") || path.starts_with("/api/") {
        handle_proxy(&mut stream, &config, &buf, &headers_str);
        return;
    }

    // Health endpoint
    if path == "/health" {
        let payload = format!(
            r#"{{"ok":true,"server":"rad-web","version":"0.2.0","port":{},"api_port":{}}}"#,
            config.port, config.api_port
        );
        let resp = format!(
            "HTTP/1.1 200 OK\r\n\
             Content-Type: application/json\r\n\
             Access-Control-Allow-Origin: *\r\n\
             Content-Length: {}\r\n\r\n{}",
            payload.len(),
            payload
        );
        let _ = stream.write_all(resp.as_bytes());
        return;
    }

    // Static file serving from dist_dir with SPA fallback
    let clean_path = path.split('?').next().unwrap_or("/").trim_start_matches('/');
    let target_file = if clean_path.is_empty() {
        config.dist_dir.join("index.html")
    } else {
        config.dist_dir.join(clean_path)
    };

    let (content, content_type) = if target_file.is_file() {
        match fs::read(&target_file) {
            Ok(bytes) => (bytes, mime_type(&target_file)),
            Err(_) => (b"File read error".to_vec(), "text/plain"),
        }
    } else {
        // SPA Fallback: serve index.html for unknown routes
        let index_file = config.dist_dir.join("index.html");
        match fs::read(&index_file) {
            Ok(bytes) => (bytes, "text/html; charset=utf-8"),
            Err(_) => (
                format!(
                    "RAD Web UI assets not found at {}. Run `npm run build` in desktop/ first.",
                    config.dist_dir.display()
                )
                .into_bytes(),
                "text/plain",
            ),
        }
    };

    let resp = format!(
        "HTTP/1.1 200 OK\r\n\
         Content-Type: {}\r\n\
         Access-Control-Allow-Origin: *\r\n\
         Cache-Control: public, max-age=3600\r\n\
         Content-Length: {}\r\n\r\n",
        content_type,
        content.len()
    );

    let _ = stream.write_all(resp.as_bytes());
    let _ = stream.write_all(&content);
}

fn main() {
    let mut port = 3000u16;
    let mut api_port = 7331u16;
    let mut custom_dist: Option<PathBuf> = None;

    let args: Vec<String> = std::env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--port" => {
                if i + 1 < args.len() {
                    port = args[i + 1].parse().unwrap_or(3000);
                    i += 1;
                }
            }
            "--api-port" => {
                if i + 1 < args.len() {
                    api_port = args[i + 1].parse().unwrap_or(7331);
                    i += 1;
                }
            }
            "--dist" => {
                if i + 1 < args.len() {
                    custom_dist = Some(PathBuf::from(&args[i + 1]));
                    i += 1;
                }
            }
            _ => {}
        }
        i += 1;
    }

    let dist_dir = custom_dist.unwrap_or_else(resolve_dist_dir);
    let token = resolve_api_token();

    println!("============================================================");
    println!("  RAD Web UI Server (Rust) v0.2.0");
    println!("  Serving Web UI:  http://127.0.0.1:{}", port);
    println!("  Agent API Proxy: http://127.0.0.1:{} -> /v1/*", api_port);
    println!("  Static Assets:   {}", dist_dir.display());
    if token.is_some() {
        println!("  Auto-Auth Token: [configured from ~/.rad/api.token]");
    } else {
        println!("  Auto-Auth Token: [none found; web client will prompt]");
    }
    println!("============================================================");

    let config = Arc::new(Config {
        port,
        api_port,
        dist_dir,
        token,
    });

    let listener = match TcpListener::bind(("127.0.0.1", port)) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("Failed to bind to 127.0.0.1:{}: {}", port, e);
            std::process::exit(1);
        }
    };

    for stream in listener.incoming() {
        match stream {
            Ok(s) => {
                let cfg = Arc::clone(&config);
                thread::spawn(move || handle_connection(s, cfg));
            }
            Err(e) => {
                eprintln!("Connection error: {}", e);
            }
        }
    }
}
