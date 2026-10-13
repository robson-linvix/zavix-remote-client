import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from validate_android import ROOT, validate


class ManagedAndroidProfileTest(unittest.TestCase):
    def test_administrative_enrollment_is_restricted_to_shell_or_system(self):
        import xml.etree.ElementTree as ET
        ns = '{http://schemas.android.com/apk/res/android}'
        tree = ET.parse(ROOT/'flutter/android/app/src/main/AndroidManifest.xml')
        receiver = next(r for r in tree.findall('./application/receiver')
                        if r.get(ns+'name') == '.ZavixProvisionReceiver')
        self.assertEqual(receiver.get(ns+'permission'), 'android.permission.DUMP')
        self.assertEqual(receiver.find('intent-filter/action').get(ns+'name'), 'app.zavix.remote.MDM_PREPARE')

    def test_current_managed_profile(self):
        validate()

    def rejected_profile(self, modify):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "branding").mkdir()
            brand = json.loads((ROOT / "branding/zavix-android.json").read_text())
            modify(brand)
            (root / "branding/zavix-android.json").write_text(json.dumps(brand))
            (root / "branding/zavix.json").write_bytes((ROOT / "branding/zavix.json").read_bytes())
            with self.assertRaises(ValueError):
                validate(root)

    def test_invalid_approval_and_upstream_server_are_rejected(self):
        for value in ("approve-mode", "custom-rendezvous-server"):
            with self.subTest(value=value):
                self.rejected_profile(lambda brand: brand["settings"].update({value: "invalid"}))

    def test_permanent_password_and_recording_are_rejected(self):
        for value, setting in (("preset-password", "unsafe"), ("allow-auto-record-incoming", "Y")):
            with self.subTest(value=value):
                self.rejected_profile(lambda brand: brand["settings"].update({value: setting}))


if __name__ == "__main__":
    unittest.main()
