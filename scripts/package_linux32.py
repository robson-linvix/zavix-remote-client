"""Package the GTK i686 client and exact corresponding source as a candidate."""
import hashlib, json, shutil, subprocess, tarfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()

def main():
    version = json.loads((ROOT/'branding/linux.json').read_text())['version']
    executable = ROOT/'target/i686-unknown-linux-gnu/release/zavixremote-gtk'
    assert 'ELF 32-bit' in run('file', str(executable))
    out = ROOT/'Linux32Release'
    out.mkdir(exist_ok=True)
    deb = ROOT/'linux32-build/deb'
    assert not deb.exists(), 'Use a clean packaging directory'
    app = deb/'opt/zavixremote'
    app.mkdir(parents=True)
    shutil.copy2(executable, app/'zavixremote')
    shutil.copyfile(ROOT/'branding/zavix/icon.png', app/'zavix.png')
    legal = app/'Legal'
    legal.mkdir()
    for name in ['LICENCE','NOTICE-ZAVIX.md','THIRD-PARTY-LICENSES.md','PRIVACY.md']:
        shutil.copyfile(ROOT/name,legal/name)
    metadata = json.loads(run('cargo','metadata','--locked','--features','zavix-linux-gtk,linux-pkg-config','--format-version','1'))
    inventory = []
    for item in metadata['packages']:
        inventory.append({k:item.get(k) for k in ['name','version','license','repository']})
        for source in Path(item['manifest_path']).parent.iterdir():
            if source.is_file() and source.name.lower().startswith(('license','licence','notice','copyright')) and source.stat().st_size < 1000000:
                folder=legal/'Cargo'/(item['name']+'-'+item['version'])
                folder.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,folder/source.name)
    (legal/'Cargo-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    (deb/'DEBIAN').mkdir()
    (deb/'DEBIAN/control').write_text(f'Package: zavixremote\nVersion: {version}\nArchitecture: i386\nMaintainer: LINVIX SOFTWARES LTDA\nSection: net\nPriority: optional\n'
        'Depends: libc6 (>= 2.36), libgtk-3-0, libayatana-appindicator3-1, libasound2, libpulse0, libxdo3, libxfixes3, libxcb-randr0, libxcb-shape0, libxcb-xfixes0, libgstreamer1.0-0, libgstreamer-plugins-base1.0-0, libssl3, libdbus-1-3, libopus0, libvpx7, libyuv0, libaom3, libva2, libstdc++6, libgcc-s1\n'
        'Description: ZAVIX Remote native GTK assisted client for Linux i386\n Incoming support with local approval. Candidate for Debian 12 X11.\n')
    (deb/'usr/bin').mkdir(parents=True)
    (deb/'usr/bin/zavixremote').symlink_to('/opt/zavixremote/zavixremote')
    desktop=deb/'usr/share/applications'
    desktop.mkdir(parents=True)
    (desktop/'app.zavix.remote.linux32.desktop').write_text('[Desktop Entry]\nType=Application\nName=ZAVIX Remote (32 bits)\nExec=zavixremote\nIcon=zavixremote\nTerminal=false\nCategories=Network;RemoteAccess;\n')
    icons=deb/'usr/share/icons/hicolor/256x256/apps'
    icons.mkdir(parents=True)
    shutil.copyfile(ROOT/'branding/zavix/icon.png',icons/'zavixremote.png')
    stem=f'ZAVIXRemote-{version}-linux-x86'
    run('dpkg-deb','--root-owner-group','--build',str(deb),str(out/(stem+'.deb')))
    with tarfile.open(out/(stem+'.tar.gz'),'w:gz') as archive:
        archive.add(app,arcname='ZAVIXRemote')
    source_name=f'ZAVIXRemote-{version}-linux-x86-source.tar.gz'
    with tarfile.open(out/source_name,'w:gz') as archive:
        for folder,prefix in [(ROOT,''),(ROOT/'libs/hbb_common','libs/hbb_common/')]:
            for name in subprocess.check_output(['git','ls-files','-z'],cwd=folder).decode().split('\0'):
                p=folder/name
                if name and (p.is_file() or p.is_symlink()):archive.add(p,arcname='source/'+prefix+name,recursive=False)
        for name in ['src/bridge_generated.rs','src/bridge_generated.io.rs']:
            archive.add(ROOT/name,arcname='source/'+name,recursive=False)
    files=[]
    for name in [stem+'.deb',stem+'.tar.gz',source_name]:
        p=out/name
        files.append({'name':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    manifest={'product':'ZAVIX Remote','version':version,'platform':'linux','architecture':'x86','debian_architecture':'i386','minimum_cpu':'i686 with SSE2','ui':'GTK3','minimum_glibc':'2.36','tested_distribution':'Debian 12','channel':'candidate','mode':'assisted','revision':run('git','rev-parse','HEAD'),'files':files}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'SHA256SUMS.txt').write_text(''.join(f['sha256']+'  '+f['name']+'\n' for f in files))
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
