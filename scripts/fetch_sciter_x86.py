"""Fetch the pinned upstream legacy engine without modifying its identity or signature."""
from pathlib import Path
import hashlib,json,urllib.request

root=Path(__file__).resolve().parents[1]
engine=json.loads((root/'branding/sciter-x86.json').read_text())
url=f'https://raw.githubusercontent.com/c-smile/sciter-sdk/{engine["revision"]}/{engine["path"]}'
with urllib.request.urlopen(url,timeout=60) as response:body=response.read()
if len(body)!=engine['bytes'] or hashlib.sha256(body).hexdigest()!=engine['sha256']:
    raise RuntimeError('Sciter engine hash or size differs from pinned source')
license_path=root/engine['license_file']
if hashlib.sha256(license_path.read_bytes()).hexdigest()!=engine['license_sha256']:
    raise RuntimeError('Sciter original license differs')
(root/'dist/sciter.dll').write_bytes(body)
print('Original x86 Sciter engine and redistribution notice verified')
