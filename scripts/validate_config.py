"""ZAVIX modifications, 2026-10-12: fail builds with unsafe or incomplete embedded settings."""
from pathlib import Path
import base64, json

root = Path(__file__).resolve().parents[1]
b = json.loads((root / 'branding/zavix.json').read_text())
s = b['settings']
assert b['app_name'] == 'ZAVIXRemote'
assert s['custom-rendezvous-server'] == '187.77.241.190'
assert s['relay-server'] == '187.77.241.190:21117'
assert s['api-server'] == 'https://remote.zavix.app'
assert len(base64.b64decode(s['key'], validate=True)) == 32
assert s['allow-auto-update'] == 'N' and s['approve-mode'] == 'click'
assert s['verification-method'] == 'use-temporary-password'
assert b['hard']['conn-type'] == 'incoming'
assert b['builtin']['allow-deep-link-server-settings'] == 'N'
assert not any('password' in k and k != 'temporary-password-length' and k != 'verification-method' for k in s)
assert (root / 'res/icon.ico').stat().st_size > 1000
print('Validated ZAVIX brand, HTTPS API, server public key and assisted defaults')
