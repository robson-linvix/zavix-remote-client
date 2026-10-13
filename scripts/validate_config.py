"""ZAVIX modifications, 2026-10-12: fail builds with unsafe or incomplete embedded settings."""
from pathlib import Path
import base64, json, re

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

assert re.fullmatch(r'[0-9]+(?:\.[0-9]+){3}', b['version'])
parts = [int(x) for x in b['version'].split('.')]
assert parts[0] <= 255 and parts[1] <= 255 and parts[2]*1000+parts[3] <= 65535
