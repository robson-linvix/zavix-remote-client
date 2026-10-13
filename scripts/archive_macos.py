"""Archive the actual native macOS bundle and corresponding build inputs."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, tarfile

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--arch',choices=['x86_64','arm64'],required=True)
args=parser.parse_args();brand=json.loads((root/'macos-build/brand.json').read_text())
app=root/f'flutter/build/macos/Build/Products/Release/{brand["app_name"]}.app'
assert app.is_dir() and (app/'Contents/MacOS/service').is_file()
legal=app/'Contents/Resources/Legal';legal.mkdir(exist_ok=True)
for name in ['LICENCE','NOTICE-ZAVIX.md','THIRD-PARTY-LICENSES.md','PRIVACY.md','CODE_SIGNING_POLICY.md']:
    shutil.copyfile(root/name,legal/name)
flutter_root=Path(shutil.which('flutter')).resolve().parents[1]
shutil.copyfile(flutter_root/'LICENSE',legal/'Flutter-LICENSE.txt')
metadata=json.loads(subprocess.check_output(['cargo','metadata','--locked','--features','flutter,zavix-macos','--format-version','1'],cwd=root))
inventory=[]
for package in metadata['packages']:
    inventory.append({k:package.get(k) for k in ['name','version','license','repository']})
    folder=Path(package['manifest_path']).parent
    for p in folder.iterdir():
        if p.is_file() and p.name.lower().startswith(('license','licence','copyright','notice')) and p.stat().st_size<1000000:
            dest=legal/'Cargo'/(package['name']+'-'+package['version']);dest.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest/p.name)
vcpkg=Path(os.environ['VCPKG_ROOT'])/'installed'/('x64-osx' if args.arch=='x86_64' else 'arm64-osx')/'share'
for p in vcpkg.glob('*/copyright'):
    dest=legal/'vcpkg'/p.parent.name;dest.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest/'copyright')
(legal/'Cargo-inventory.json').write_text(json.dumps(inventory,indent=2))
subprocess.run(['bash',str(root/'.github/scripts/sign-macos-app.sh'),str(app),'-',str(root/'flutter/macos/Runner/Release.entitlements')],check=True)
out=root/'MacNative';out.mkdir(exist_ok=True)
with tarfile.open(out/'app.tar.gz','w:gz') as archive:archive.add(app,arcname=app.name)
with tarfile.open(out/'source.tar.gz','w:gz') as archive:
    for folder,prefix in [(root,''),(root/'libs/hbb_common','libs/hbb_common/')]:
        names=subprocess.check_output(['git','ls-files','-z'],cwd=folder).decode().split('\0')
        for name in names:
            p=folder/name
            if name and (p.is_file() or p.is_symlink()):archive.add(p,arcname='source/'+prefix+name,recursive=False)
    for name in ['src/bridge_generated.rs','src/bridge_generated.io.rs','flutter/lib/generated_bridge.dart','flutter/lib/generated_bridge.freezed.dart','flutter/macos/Runner/bridge_generated.h','flutter/pubspec.lock','macos-build/brand.json','macos-build/vcpkg.json']:
        p=root/name
        if p.is_file():archive.add(p,arcname='source/'+name,recursive=False)
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
result={'product':brand['product_name'],'app_name':brand['app_name'],'bundle_id':brand['bundle_id'],'version':brand['version'],'architecture':args.arch,'revision':revision,'minimum_macos':brand['minimum_macos'],'developer_id_signed':False,'notarized':False,'code_signature':'ad-hoc','files':[]}
for name in ['app.tar.gz','source.tar.gz']:
    p=out/name;result['files'].append({'name':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(out/'native-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
