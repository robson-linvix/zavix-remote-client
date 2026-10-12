"""ZAVIX modifications, 2026-10-12: archive actual build inputs and hash final unsigned packages."""
from pathlib import Path
import hashlib, json, subprocess, tarfile

root = Path(__file__).resolve().parents[1]
out = root / 'SignOutput'
brand = json.loads((root / 'branding/zavix.json').read_text())
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
sources = out / f'ZAVIXRemote-{brand["version"]}-source.tar.gz'
with tarfile.open(sources, 'w:gz') as archive:
    for folder, prefix in [(root, ''), (root / 'libs/hbb_common', 'libs/hbb_common/')]:
        files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=folder).decode().split('\0')
        for name in files:
            p = folder / name
            if name and (p.is_file() or p.is_symlink()):
                archive.add(p, arcname='ZAVIXRemote-source/' + prefix + name, recursive=False)
    for name in ['src/bridge_generated.rs','src/bridge_generated.io.rs','flutter/lib/generated_bridge.dart','flutter/lib/generated_bridge.freezed.dart','flutter/pubspec.lock']:
        p = root / name
        if p.is_file(): archive.add(p, arcname='ZAVIXRemote-source/' + name, recursive=False)
files = []
for ext in ('exe','msi'):
    p = out / f'ZAVIXRemote-{brand["version"]}.{ext}'
    if not p.is_file() or p.stat().st_size < 1000000: raise RuntimeError(f'Missing Windows {ext} artifact')
    files.append(p)
files.append(sources)
manifest = {'product':brand['product_name'],'version':brand['version'],'upstream':'1.5.0','revision':revision,'signed':False,'mode':'assisted','files':[{ 'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
(out / 'SHA256SUMS.txt').write_text(''.join(f'{f["sha256"]}  {f["name"]}\n' for f in manifest['files']))
(out / 'windows-runtime-evidence.json').write_bytes((root / 'windows-runtime-evidence.json').read_bytes())
print(json.dumps(manifest, indent=2))
