"""Validate the Android pilot's public configuration, not device compatibility."""
import base64
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "flutter/android/app"
NS = "{http://schemas.android.com/apk/res/android}"


def validate(root=ROOT):
    brand = json.loads((root / "branding/zavix-android.json").read_text())
    windows = json.loads((root / "branding/zavix.json").read_text())
    settings = brand["settings"]
    for name in ("custom-rendezvous-server", "relay-server", "key", "api-server"):
        if settings[name] != windows["settings"][name]:
            raise ValueError(f"Android and Windows infrastructure differ: {name}")
    if len(base64.b64decode(settings["key"], validate=True)) != 32:
        raise ValueError("Invalid public server key")
    if settings["approve-mode"] != "password" or settings["allow-auto-update"] != "N":
        raise ValueError("The Android pilot must use credential-based unattended access without an upstream updater")
    if settings["verification-method"] != "use-permanent-password":
        raise ValueError("A per-device permanent credential is required")
    if brand["hard"]["conn-type"] != "incoming":
        raise ValueError("The Android pilot must receive support only")
    if settings["allow-auto-record-incoming"] != "N":
        raise ValueError("Recording must remain disabled")
    if any("password" in key and key not in ("verification-method", "temporary-password-length") for key in settings):
        raise ValueError("A permanent password must not be embedded")
    app = root / "flutter/android/app"
    gradle = (app / "build.gradle").read_text()
    for pattern in ('applicationId "app.zavix.remote"', 'applicationIdSuffix ".pilot.t2mini"', 'minSdkVersion 24', 'targetSdkVersion 36'):
        if pattern not in gradle:
            raise ValueError(f"Missing Android build setting: {pattern}")
    manifest = ET.parse(app / "src/main/AndroidManifest.xml").getroot()
    receiver = manifest.find("application/receiver")
    if receiver.get(NS + "enabled") != "true":
        raise ValueError("Managed boot receiver must be present")
    if not any(p.get(NS + "name") == "android.permission.RECEIVE_BOOT_COMPLETED" for p in manifest.findall("uses-permission")):
        raise ValueError("Managed boot permission is missing")
    accessibility = ET.parse(app / "src/main/res/xml/accessibility_service_config.xml").getroot()
    if accessibility.get(NS + "isAccessibilityTool") == "true":
        raise ValueError("Remote support is not a disability accessibility tool")
    for file in ("src/lib.rs", "src/flutter_ffi.rs"):
        content = (root / file).read_text()
        if not re.search(r'#\[cfg\(target_os = "android"\)\].*?zavix_android', content, re.S):
            raise ValueError("Android startup must not change the Windows runtime")
    print("Android pilot configuration validated; compilation and real-device acceptance remain required")


if __name__ == "__main__":
    validate()
