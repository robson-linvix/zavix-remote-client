"""Archive corresponding build sources without keystores or local credentials."""
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "AndroidPilot"
apks = sorted(out.glob("*.apk"))
if len(apks) != 1:
    raise RuntimeError("Expected exactly one verified pilot APK")
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
source = out / "ZAVIXRemote-Android-piloto-source.tar.gz"
tracked = subprocess.check_output(["git", "ls-files", "--recurse-submodules", "-z"], cwd=root).decode().split("\0")
generated = ["src/bridge_generated.rs", "src/bridge_generated.io.rs", "flutter/lib/generated_bridge.dart", "flutter/lib/generated_bridge.freezed.dart", "flutter/pubspec.lock"]
with tarfile.open(source, "w:gz") as archive:
    for name in sorted(set(tracked + generated)):
        if not name:
            continue
        path = root / name
        if path.suffix in (".jks", ".keystore", ".pfx", ".p12") or path.name in ("key.properties", "local.properties", ".env"):
            raise RuntimeError("Credentials must not enter the source archive")
        if name in generated and not path.is_file():
            raise RuntimeError(f"Missing build source: {name}")
        if path.is_file():
            archive.add(path, arcname="ZAVIXRemote-Android-source/" + name, recursive=False)
files = apks + [source]
manifest = {
    "product": "Zavix Remote Sunmi",
    "revision": revision,
    "package": "app.zavix.remote.pilot.t2mini",
    "version": "1.2.3-piloto",
    "default_mode": "unattended",
    "distribution": "pilot-only",
    "signing": "stable-protected-test-key-not-for-google-play",
    "min_android": "7.0 (API 24)",
    "target_sdk": 36,
    "device_homologation": "pending-SUNMI-T2-Mini-S",
    "google_play_ready": False,
    "files": [{"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size} for p in files],
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
(out / "SHA256SUMS.txt").write_text("".join(f'{p["sha256"]}  {p["name"]}\n' for p in manifest["files"]))
print("Packaged Android pilot and corresponding sources; not a Google Play release")
