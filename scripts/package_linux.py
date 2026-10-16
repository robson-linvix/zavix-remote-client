"""Package the Linux x64 client without enabling a system service or unattended access."""
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(*args, **kwargs):
    return subprocess.check_output(args, cwd=ROOT, text=True, **kwargs).strip()

def package():
    brand = json.loads((ROOT / 'branding/linux.json').read_text())
    version = brand['version']
    bundle = ROOT / 'flutter/build/linux/x64/release/bundle'
    executable = bundle / 'zavixremote'
    assert executable.is_file() and 'x86-64' in run('file', str(executable))
    for library in ['librustdesk.so', 'libyuv.so.0']:
        run('patchelf', '--set-rpath', '$ORIGIN', str(bundle / 'lib' / library))
    output = ROOT / 'LinuxRelease'
    output.mkdir(exist_ok=True)
    legal = bundle / 'Legal'
    legal.mkdir(exist_ok=True)
    for name in ['LICENCE', 'NOTICE-ZAVIX.md', 'THIRD-PARTY-LICENSES.md', 'PRIVACY.md']:
        shutil.copyfile(ROOT / name, legal / name)
    flutter_root = Path(shutil.which('flutter')).resolve().parents[1]
    shutil.copyfile(flutter_root / 'LICENSE', legal / 'Flutter-LICENSE.txt')
    for package_name in ['libyuv0', 'libjpeg-turbo8']:
        shutil.copyfile(Path('/usr/share/doc') / package_name / 'copyright', legal / (package_name + '-copyright'))
    metadata = json.loads(run('cargo', 'metadata', '--locked', '--features', 'flutter,linux-pkg-config,zavix-linux', '--format-version', '1'))
    inventory = []
    for item in metadata['packages']:
        inventory.append({key: item.get(key) for key in ['name', 'version', 'license', 'repository']})
        for source in Path(item['manifest_path']).parent.iterdir():
            if source.is_file() and source.name.lower().startswith(('license', 'licence', 'notice', 'copyright')) and source.stat().st_size < 1000000:
                destination = legal / 'Cargo' / (item['name'] + '-' + item['version'])
                destination.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination / source.name)
    (legal / 'Cargo-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    stem = f'ZAVIXRemote-{version}-linux-x64'
    with tarfile.open(output / (stem + '.tar.gz'), 'w:gz') as archive:
        archive.add(bundle, arcname='ZAVIXRemote')
    deb = ROOT / 'linux-build/deb'
    assert not deb.exists(), 'Use a clean package directory'
    shutil.copytree(bundle, deb / 'opt/zavixremote')
    (deb / 'DEBIAN').mkdir()
    (deb / 'DEBIAN/control').write_text(
        f'Package: zavixremote\nVersion: {version}\nArchitecture: amd64\n'
        'Maintainer: LINVIX SOFTWARES LTDA\nSection: net\nPriority: optional\n'
        'Depends: libc6 (>= 2.35), libgtk-3-0, libegl1, libgl1, libayatana-appindicator3-1, libasound2, libpulse0, libxdo3, libxfixes3, libxcb-randr0, libxcb-shape0, libxcb-xfixes0, libgstreamer1.0-0, libgstreamer-plugins-base1.0-0, libssl3, libdbus-1-3, libopus0, libvpx7, libaom3, libva2, libstdc++6\n'
        'Description: ZAVIX Remote assisted support client\n'
        ' Incoming remote support with local approval; no unattended service is installed.\n')
    (deb / 'usr/bin').mkdir(parents=True)
    (deb / 'usr/bin/zavixremote').symlink_to('/opt/zavixremote/zavixremote')
    applications = deb / 'usr/share/applications'
    applications.mkdir(parents=True)
    (applications / 'app.zavix.remote.linux.desktop').write_text(
        '[Desktop Entry]\nType=Application\nName=ZAVIX Remote\n'
        'Comment=Receber suporte remoto com sua autorização\nExec=zavixremote\n'
        'Icon=zavixremote\nTerminal=false\nCategories=Network;RemoteAccess;\n')
    icons = deb / 'usr/share/icons/hicolor/256x256/apps'
    icons.mkdir(parents=True)
    shutil.copyfile(ROOT / 'branding/zavix/icon.png', icons / 'zavixremote.png')
    run('dpkg-deb', '--root-owner-group', '--build', str(deb), str(output / (stem + '.deb')))
    source_name = f'ZAVIXRemote-{version}-linux-source.tar.gz'
    with tarfile.open(output / source_name, 'w:gz') as archive:
        for folder, prefix in [(ROOT, ''), (ROOT / 'libs/hbb_common', 'libs/hbb_common/')]:
            names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=folder).decode().split('\0')
            for name in names:
                path = folder / name
                if name and (path.is_file() or path.is_symlink()):
                    archive.add(path, arcname='source/' + prefix + name, recursive=False)
        for name in ['src/bridge_generated.rs', 'src/bridge_generated.io.rs', 'flutter/lib/generated_bridge.dart', 'flutter/lib/generated_bridge.freezed.dart', 'flutter/pubspec.lock']:
            path = ROOT / name
            assert path.is_file(), 'Missing build input: ' + name
            archive.add(path, arcname='source/' + name, recursive=False)
    files = []
    for name in [stem + '.deb', stem + '.tar.gz', source_name]:
        path = output / name
        files.append({'name': name, 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest = {'product': 'ZAVIX Remote', 'version': version, 'platform': 'linux', 'architecture': 'x86_64',
                'minimum_glibc': '2.35', 'tested_distribution': 'Ubuntu 22.04', 'channel': 'candidate',
                'mode': 'assisted', 'revision': run('git', 'rev-parse', 'HEAD'), 'files': files}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'SHA256SUMS.txt').write_text(''.join(item['sha256'] + '  ' + item['name'] + '\n' for item in files))
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    package()
