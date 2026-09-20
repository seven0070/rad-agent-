# Sidecar binaries

Tauri resolves the `externalBin` entry `binaries/rad` to a file named
`rad-<target-triple>` (`.exe` on Windows) in this directory. The bundler ships
that file beside the app executable, and the Rust bootstrap locates it with the
same naming scheme next to `current_exe()`.

| Platform      | Triple                    | File                                     |
| ------------- | ------------------------- | ---------------------------------------- |
| Windows x64   | x86_64-pc-windows-msvc    | rad-x86_64-pc-windows-msvc.exe           |
| macOS arm64   | aarch64-apple-darwin      | rad-aarch64-apple-darwin                 |
| macOS x64     | x86_64-apple-darwin       | rad-x86_64-apple-darwin                  |
| Linux x64     | x86_64-unknown-linux-gnu  | rad-x86_64-unknown-linux-gnu             |
| Linux arm64   | aarch64-unknown-linux-gnu | rad-aarch64-unknown-linux-gnu            |

The binary is a PyInstaller onefile build of the `rad` CLI, produced by
`scripts/build-sidecar.ps1` in Phase 5. Until then the app falls back to the
Python module launcher (`python3 -m rad serve ...`).

Note: `rad-x86_64-pc-windows-gnu.exe` is a 0-byte build placeholder. This dev
machine uses a GNU (MinGW) toolchain, so tauri-build validates the sidecar file
for the host triple `x86_64-pc-windows-gnu` at compile time. Phase 5 replaces it
with the real PyInstaller binary (or it can be deleted once builds stop needing it).