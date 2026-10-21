#!/usr/bin/env python3
"""Upload GMGN intel static site to Cloudflare Pages Direct Upload.

IMPORTANT: use bare blake3 hashes (32 hex) as asset keys AND in the deployment
manifest. Uploading as hash.ext while deploying with bare hashes causes HTTP 500.

Usage:
  PAGES_UPLOAD_JWT=... python3 pages-direct-upload.py [/workspace/gmgn-intel]
Writes /tmp/gmgn-pages-manifest.json for the create-deployment step.
"""
import base64, json, mimetypes, os, sys, urllib.request
from pathlib import Path
import blake3

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/workspace/gmgn-intel")
JWT = os.environ["PAGES_UPLOAD_JWT"]
SKIP_NAMES = {"server.log", "server.pid", "build.py", "README.md", ".gitignore"}

def collect():
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if any(part.startswith(".") and part not in (".nojekyll",) for part in rel.parts):
            continue
        if rel.name in SKIP_NAMES or "server." in rel.name:
            continue
        if "__pycache__" in rel.parts:
            continue
        out.append(p)
    return out

def api(method, url, body=None):
    hdrs = {"Authorization": f"Bearer {JWT}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        print("HTTP", e.code, raw[:800], file=sys.stderr)
        raise

files = collect()
manifest = {}
by_key = {}
for p in files:
    data = p.read_bytes()
    h = blake3.blake3(data).hexdigest()[:32]
    path_key = "/" + p.relative_to(ROOT).as_posix()
    ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    if path_key.endswith(".json"):
        ctype = "application/json"
    elif path_key.endswith(".html"):
        ctype = "text/html; charset=utf-8"
    elif path_key.endswith(".txt") or p.name == ".nojekyll":
        ctype = "text/plain"
    manifest[path_key] = h
    by_key[h] = (p, data, path_key, ctype)
    print(f"  {path_key} -> {h} ({len(data)}b {ctype})")

hashes = list(by_key.keys())
_, missing_resp = api("POST", "https://api.cloudflare.com/client/v4/pages/assets/check-missing", {"hashes": hashes})
missing = missing_resp.get("result") or []
print(f"check-missing ok; missing={len(missing)}")

BATCH = 15
for i in range(0, len(missing), BATCH):
    batch = missing[i:i+BATCH]
    payload = []
    for k in batch:
        p, data, path_key, ctype = by_key[k]
        payload.append({
            "key": k,
            "value": base64.b64encode(data).decode(),
            "metadata": {"contentType": ctype},
            "base64": True,
        })
    _, up = api("POST", "https://api.cloudflare.com/client/v4/pages/assets/upload", payload)
    print(f"upload {i}: success={up.get('success')}")

_, uph = api("POST", "https://api.cloudflare.com/client/v4/pages/assets/upsert-hashes", {"hashes": hashes})
print("upsert", uph.get("success"), uph.get("errors"))
Path("/tmp/gmgn-pages-manifest.json").write_text(json.dumps(manifest, separators=(",", ":")))
print("MANIFEST_OK", len(manifest))
print(json.dumps(manifest, indent=2))
