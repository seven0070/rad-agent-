"""Cloud mind — Google Drive as Rad's serverless server.

Drive holds the MIND, not the compute:
  long-term memory · DNA generations · model weight bundles ·
  faded-memory archive · web/voice caches.

Not the inference disk — inference stays on local SSD (Drive is far too
latency-hungry for expert streaming).

Requires: `rad install cloud` (pip extras).
"""
from __future__ import annotations

import io
import json
import time
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rad.home import RadHome
from rad.ui import col, fail, ok, warn

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
OAUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _deps() -> Tuple[Optional[Any], str]:
    try:
        from google.auth.transport.requests import Request  # type: ignore
        from google.oauth2.credentials import Credentials  # type: ignore
        from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
        from googleapiclient.discovery import build  # type: ignore
        from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload  # type: ignore
        return {"Request": Request, "Credentials": Credentials, "InstalledAppFlow": InstalledAppFlow,
                "build": build, "MediaIoBaseDownload": MediaIoBaseDownload, "MediaIoBaseUpload": MediaIoBaseUpload}, ""
    except ImportError as e:
        return None, f"missing dependency ({e.name}) — run: pip install google-auth google-auth-oauthlib google-api-python-client   (or `rad install cloud`)"


class Drive:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.state_path = home.root / "keys" / "drive.json"

    # ------------------------------------------------------------ credentials
    def state(self) -> Dict[str, Any]:
        try:
            return json.loads(self.state_path.read_text())
        except Exception:
            return {}

    def credentials(self):
        deps, err = _deps()
        if deps is None:
            fail(err)
            return None
        st = self.state()
        if not st.get("client_id"):
            fail("no OAuth client configured — run `rad drive connect --client-id <id> --client-secret <secret>` "
                 "(create a Desktop app in Google Cloud Console, enable Drive API)")
            return None
        creds = deps["Credentials"](
            client_id=st["client_id"], client_secret=st["client_secret"],
            refresh_token=st.get("refresh_token"),
            token=st.get("token"), token_uri=TOKEN_URI, scopes=[DRIVE_SCOPE])
        if creds and (creds.valid or creds.expired):
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(deps["Request"]())
                    st["token"] = creds.token
                    self.state_path.write_text(json.dumps(st))
                except Exception as e:
                    fail(f"token refresh failed: {e}")
                    return None
            return creds
        if creds and creds.expired and not creds.refresh_token:
            fail("stored token expired without refresh — re-run `rad drive connect`")
            return None
        return creds

    def connect(self, client_id: Optional[str], client_secret: Optional[str]) -> None:
        deps, err = _deps()
        if deps is None:
            fail(err)
            return
        st = self.state()
        if client_id:
            st["client_id"] = client_id
        if client_secret:
            st["client_secret"] = client_secret
        if not st.get("client_id") or not st.get("client_secret"):
            fail("need --client-id and --client-secret (Google Cloud Console → OAuth consent → Desktop app)")
            return
        st.pop("token", None)
        st.pop("refresh_token", None)
        self.state_path.write_text(json.dumps(st))
        flow = deps["InstalledAppFlow"].from_client_config(
            {"web": {"client_id": st["client_id"], "client_secret": st["client_secret"]}},
            scopes=[DRIVE_SCOPE])
        print(col.bold("\n  Open this URL, authorize Rad, then paste the code back here:\n"))
        webbrowser.open(flow.authorization_url)
        print(flow.authorization_url)
        code = input("  paste code> ").strip()
        flow.fetch_token(code=code)
        st["token"] = flow.credentials.token
        st["refresh_token"] = flow.credentials.refresh_token
        st["expires_at"] = time.time() + 3600
        self.state_path.write_text(json.dumps(st))
        ok("Google Drive connected")

    def _api(self):
        creds = self.credentials()
        if not creds:
            return None
        deps, _ = _deps()
        return deps["build"]("drive", "v3", credentials=creds, cache_discovery=False)

    def _folder_id(self, service) -> Optional[str]:
        deps, _ = _deps()
        q = f"name='{self.home.cfg.get('drive_folder', 'RadAgent')}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        res = service.files().list(q=q, spaces="drive", fields="files(id, name)", pageSize=5).execute()
        files = res.get("files", [])
        if files:
            return files[0]["id"]
        created = service.files().create(
            body={"name": self.home.cfg.get("drive_folder", "RadAgent"),
                  "mimeType": "application/vnd.google-apps.folder"},
            fields="id").execute()
        return created["id"]

    # ------------------------------------------------------------ sync
    SYNC_PATHS = [
        ("rad.json", "config/rad.json"),
        ("cost.json", "config/cost.json"),
        ("dna/current.json", "dna/current.json"),
    ]

    def _local_files(self) -> List[Tuple[Path, str]]:
        out = []
        for local, remote in self.SYNC_PATHS:
            p = self.home.root / local
            if p.exists():
                out.append((p, remote))
        for p in sorted((self.home.root / "memory" / "long").rglob("*.md")):
            out.append((p, "memory/" + str(p.relative_to(self.home.root / "memory" / "long"))))
        for gen in sorted((self.home.root / "dna").glob("gen*.json")):
            out.append((gen, f"dna/{gen.name}"))
        return out

    def push(self) -> str:
        service = self._api()
        if service is None:
            return "drive unavailable"
        deps, _ = _deps()
        folder = self._folder_id(service)
        if not folder:
            return "no folder"
        n = 0
        for p, remote in self._local_files():
            try:
                service.files().create(
                    body={"name": Path(remote).name, "parents": [folder], "mimeType": "text/markdown" if p.suffix == ".md" else "application/json"},
                    media_body=deps["MediaIoBaseUpload"](io.BytesIO(p.read_bytes()), mimetype=None, resumable=False),
                    fields="id").execute()
                n += 1
            except Exception as e:
                warn(f"skip {remote}: {str(e)[:100]}")
        self.state_path.write_text(json.dumps({**self.state(), "last_push": time.time()}))
        return f"pushed {n} file(s) to Drive/{self.home.cfg.get('drive_folder', 'RadAgent')}"

    def pull(self) -> str:
        service = self._api()
        if service is None:
            return "drive unavailable"
        deps, _ = _deps()
        folder = self._folder_id(service)
        if not folder:
            return "no folder on drive"
        res = service.files().list(q=f"'{folder}' in parents and trashed=false",
                                   fields="files(id, name, mimeType)", pageSize=1000).execute()
        n = 0
        for f in res.get("files", []):
            name = f["name"]
            # map flat names back to safe relative paths (no path traversal)
            local = (self.home.root / "memory" / "long" / name).resolve()
            if not str(local).startswith(str((self.home.root / "memory" / "long").resolve())):
                continue
            if f["mimeType"] != "application/vnd.google-apps.folder":
                try:
                    local.parent.mkdir(parents=True, exist_ok=True)
                    req = service.files().get_media(fileId=f["id"])
                    deps["MediaIoBaseDownload"](io.BytesIO(), req).close()
                    with open(local, "wb") as fh:
                        req = service.files().get_media(fileId=f["id"])
                        deps["MediaIoBaseDownload"](fh, req).close()
                    n += 1
                except Exception as e:
                    warn(f"skip {name}: {str(e)[:100]}")
        self.state_path.write_text(json.dumps({**self.state(), "last_pull": time.time()}))
        return f"pulled {n} file(s) from Drive"

    def status(self) -> str:
        st = self.state()
        if not st.get("client_id"):
            return "  not connected — `rad drive connect --client-id <id> --client-secret <secret>`"
        last = st.get("last_push") or st.get("last_pull")
        out = "  connected ✓"
        if last:
            out += f"  last sync: {time.strftime('%Y-%m-%d %H:%M', time.localtime(last))}"
        return out
