"""Collect original license notices alongside the actual Windows payload."""
import argparse, json, os, shutil, subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dist = root / 'dist'
legal = dist / 'legal'
legal.mkdir(exist_ok=True)
for name in ['LICENCE','NOTICE-ZAVIX.md','THIRD-PARTY-LICENSES.md','PRIVACY.md','CODE_SIGNING_POLICY.md']:
    shutil.copyfile(root / name, dist / name)
shutil.copyfile(root / 'branding/WindowInjection-LICENSE.txt', legal / 'WindowInjection-LICENSE.txt')
metadata = json.loads(subprocess.check_output(['cargo','metadata','--locked','--format-version','1'],cwd=root))
inventory = []
for package in metadata['packages']:
    entry = {'name':package['name'],'version':package['version'],'license':package.get('license') or 'UNSPECIFIED','repository':package.get('repository')}
    inventory.append(entry)
    folder = Path(package['manifest_path']).parent
    matches = [p for p in folder.iterdir() if p.is_file() and p.name.lower().startswith(('license','licence','copyright','notice')) and p.stat().st_size < 1000000]
    if matches:
        target = legal / 'cargo' / (package['name'] + '-' + package['version'])
        target.mkdir(parents=True,exist_ok=True)
        for p in matches: shutil.copyfile(p,target / p.name)
parser = argparse.ArgumentParser()
parser.add_argument('--arch', choices=['x86','x64'], default='x64')
args = parser.parse_args()
vcpkg = Path(os.environ['VCPKG_ROOT']) / 'installed' / (args.arch+'-windows-static') / 'share'
if args.arch == 'x86':
    shutil.copyfile(root / 'branding/Sciter-LICENSE.htm', legal / 'Sciter-LICENSE.htm')
for p in vcpkg.glob('*/copyright'):
    target = legal / 'vcpkg' / p.parent.name
    target.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,target / 'copyright')
(legal / 'cargo-inventory.json').write_text(json.dumps(inventory,indent=2))
print(f'Original notices collected for {len(inventory)} Cargo packages and installed vcpkg ports')
