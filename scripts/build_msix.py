"""Package the compiled Store-only client; no installer execution or publication."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as E
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://schemas.microsoft.com/appx/manifest/foundation/windows10'
UAP = 'http://schemas.microsoft.com/appx/manifest/uap/windows10'
RESCAP = 'http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities'
for prefix, namespace in [('', NS), ('uap', UAP), ('rescap', RESCAP)]:
    E.register_namespace(prefix, namespace)

def checksum(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def assets(folder, edition):
    icon = ROOT / ('branding/zavix-icon.png' if edition == 'zavix' else 'branding/linvix/icon.png')
    image = Image.open(icon).convert('RGBA')
    folder.mkdir()
    for name, size in [('StoreLogo', 50), ('Square44x44Logo', 44), ('Square150x150Logo', 150)]:
        for scale in [100, 200, 400]:
            pixels = size * scale // 100
            tile = Image.new('RGBA', (pixels, pixels), (0, 0, 0, 0))
            logo = image.copy()
            logo.thumbnail((pixels * 4 // 5, pixels * 4 // 5), Image.Resampling.LANCZOS)
            tile.alpha_composite(logo, ((pixels-logo.width)//2, (pixels-logo.height)//2))
            tile.save(folder / (name + ('' if scale == 100 else f'.scale-{scale}') + '.png'))

def build(bundle, output, makeappx, identity_path=None):
    profile = json.loads((ROOT / 'branding/msix-profile.json').read_text(encoding='utf-8'))
    app, edition = profile['app_name'], profile['edition']
    if app not in ('ZAVIXRemoteStore', 'LinvixRemoteStore') or profile['profile'] != 'store-assisted':
        raise ValueError('Only the compiled isolated Store profile can be packaged')
    for name in [app+'.exe', 'librustdesk.dll', 'flutter_windows.dll', 'LICENCE', 'PRIVACY.md']:
        if not (bundle / name).is_file():
            raise ValueError('Missing compiled payload: '+name)
    diagnostic = subprocess.check_output([str(bundle / (app+'.exe')), '--msix-diagnostics'], text=True)
    runtime = json.loads(next(line for line in diagnostic.splitlines() if line.startswith('{')))
    if (runtime['profile'] != 'store-assisted' or runtime['app_name'] != app or
        not runtime['installation_disabled'] or runtime['can_elevate'] or not runtime['close_exits'] or
        runtime['approve_mode'] != 'click' or not runtime['incoming_only']):
        raise ValueError('Compiled client does not enforce assisted Store behavior')
    identity = {'name': 'LinvixSoftware.'+app, 'publisher': 'CN=LINVIX SOFTWARES LTDA',
                'publisher_display_name': 'LINVIX SOFTWARES LTDA', 'confirmed': False}
    if identity_path:
        identity = json.loads(identity_path.read_text(encoding='utf-8'))
        if not identity.get('confirmed') or not identity.get('partner_center_product_id'):
            raise ValueError('Store identity must come from the reserved Partner Center product')
    if not re.fullmatch(r'[A-Za-z0-9.-]{3,50}', identity['name']) or not identity['publisher'].startswith('CN='):
        raise ValueError('Invalid package identity')
    major, minor, patch, revision = map(int, profile['version'].split('.'))
    version = f'{major}.{minor}.{patch*1000+revision}.0'
    output.mkdir(parents=True, exist_ok=False)
    stage = output / 'payload'
    shutil.copytree(bundle, stage, ignore=shutil.ignore_patterns('*.pdb', 'custom.txt'))
    assets(stage / 'Assets', edition)
    root = E.Element('{'+NS+'}Package', {'IgnorableNamespaces': 'uap rescap'})
    def node(parent, name, **attrs):
        return E.SubElement(parent, '{'+NS+'}'+name, attrs)
    node(root, 'Identity', Name=identity['name'], Publisher=identity['publisher'],
         Version=version, ProcessorArchitecture='x64')
    properties = node(root, 'Properties')
    for name, value in [('DisplayName', profile['product_name']),
                        ('PublisherDisplayName', identity['publisher_display_name']),
                        ('Logo', 'Assets\\StoreLogo.png'),
                        ('Description', 'Suporte remoto assistido enquanto o aplicativo estiver aberto.')]:
        node(properties, name).text = value
    resources = node(root, 'Resources')
    node(resources, 'Resource', Language='pt-BR')
    dependencies = node(root, 'Dependencies')
    node(dependencies, 'TargetDeviceFamily', Name='Windows.Desktop',
         MinVersion='10.0.19041.0', MaxVersionTested='10.0.26100.0')
    application = node(node(root, 'Applications'), 'Application', Id='Remote',
                       Executable=app+'.exe', EntryPoint='Windows.FullTrustApplication')
    E.SubElement(application, '{'+UAP+'}VisualElements', {
        'DisplayName': profile['product_name'],
        'Description': 'Abra o aplicativo, informe seu ID e aceite a solicitação do atendente.',
        'Square150x150Logo': 'Assets\\Square150x150Logo.png',
        'Square44x44Logo': 'Assets\\Square44x44Logo.png', 'BackgroundColor': 'transparent'})
    capabilities = node(root, 'Capabilities')
    node(capabilities, 'Capability', Name='internetClient')
    E.SubElement(capabilities, '{'+RESCAP+'}Capability', {'Name': 'runFullTrust'})
    E.indent(root)
    E.ElementTree(root).write(stage / 'AppxManifest.xml', encoding='utf-8', xml_declaration=True)
    package = output / f'{app}-{version}-x64.msix'
    subprocess.run([str(makeappx), 'pack', '/d', str(stage), '/p', str(package), '/o'], check=True)
    sources = output / f'{app}-{version}-source.tar.gz'
    with tarfile.open(sources, 'w:gz') as archive:
        for folder, prefix in [(ROOT, ''), (ROOT/'libs/hbb_common', 'libs/hbb_common/')]:
            names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=folder).decode().split('\0')
            for name in names:
                path = folder / name
                if name and (path.is_file() or path.is_symlink()):
                    archive.add(path, arcname=app+'-source/'+prefix+name, recursive=False)
        for name in ['branding/msix-profile.json', 'src/bridge_generated.rs', 'src/bridge_generated.io.rs',
                     'flutter/lib/generated_bridge.dart', 'flutter/lib/generated_bridge.freezed.dart', 'flutter/pubspec.lock']:
            path = ROOT / name
            if path.is_file():
                archive.add(path, arcname=app+'-source/'+name, recursive=False)
    files = [{'name': path.name, 'sha256': checksum(path), 'bytes': path.stat().st_size} for path in [package, sources]]
    manifest = {**profile, 'package_version': version, 'identity': identity, 'signed': False,
        'store_submission_ready': False, 'release_candidate': True,
        'minimum_windows_build': 19041, 'service': False, 'elevation': False,
        'revision': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        'pending': ['Partner Center identity association' if not identity['confirmed'] else 'Store certification',
                    'Windows 10/11 real assisted session and Store certification'],
        'runtime': runtime, 'files': files}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'SHA256SUMS.txt').write_text(''.join(f'{f["sha256"]}  {f["name"]}\n' for f in files), encoding='utf-8')
    shutil.copyfile(stage / 'AppxManifest.xml', output / 'AppxManifest.xml')
    shutil.rmtree(stage)
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, default=ROOT/'dist')
    parser.add_argument('--out', type=Path, default=ROOT/'MSIXOutput')
    parser.add_argument('--makeappx', type=Path, required=True)
    parser.add_argument('--identity', type=Path)
    args = parser.parse_args()
    build(args.bundle.resolve(), args.out.resolve(), args.makeappx.resolve(), args.identity)
