"""Merge both tested native slices and build one branded macOS Installer package."""
from pathlib import Path
import argparse, hashlib, json, plistlib, shutil, subprocess, tarfile
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]

def run(*args):
    return subprocess.check_output(list(map(str,args)),text=True).strip()

def build(native,out,edition):
    app_name={'zavix':'ZAVIXRemote','linvix':'LinvixRemote'}[edition]
    manifests={}
    stage=out/'work';stage.mkdir(parents=True,exist_ok=False)
    for arch in ['x86_64','arm64']:
        source=native/arch;manifest=json.loads((source/'native-manifest.json').read_text());manifests[arch]=manifest
        assert manifest['app_name']==app_name and manifest['architecture']==arch and manifest['developer_id_signed'] is False and manifest['notarized'] is False
        for item in manifest['files']:
            assert item['name'] in ['app.tar.gz','source.tar.gz']
            p=source/item['name'];assert p.stat().st_size==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
        extracted=stage/arch;extracted.mkdir()
        with tarfile.open(source/'app.tar.gz') as archive:archive.extractall(extracted,filter='data')
        assert (extracted/(app_name+'.app')).is_dir()
    left,right=manifests['x86_64'],manifests['arm64']
    assert all(left[k]==right[k] for k in ['app_name','product','bundle_id','version','revision','minimum_macos'])
    payload=stage/'payload';apps=payload/'Applications';apps.mkdir(parents=True)
    app=apps/(app_name+'.app');shutil.copytree(stage/'x86_64'/app.name,app,symlinks=True)
    arm=stage/'arm64'/app.name
    merged=[]
    for p in sorted(app.rglob('*')):
        if p.is_symlink() or not p.is_file():continue
        relative=p.relative_to(app)
        if 'Mach-O' not in run('file','-b',p):continue
        other=arm/relative;assert other.is_file() and 'Mach-O' in run('file','-b',other)
        thin=[]
        for arch,binary in [('x86_64',p),('arm64',other)]:
            assert arch in run('lipo','-archs',binary).split()
            dest=stage/(arch+'-slice')
            if len(run('lipo','-archs',binary).split())==1:shutil.copyfile(binary,dest)
            else:run('lipo','-thin',arch,binary,'-output',dest)
            thin.append(dest)
        original_mode=p.stat().st_mode
        run('lipo','-create',*thin,'-output',p)
        p.chmod(original_mode)
        assert set(run('lipo','-archs',p).split())=={'arm64','x86_64'}
        merged.append(str(relative))
    assert len(merged)>=3 and f'Contents/MacOS/{app_name}' in merged and 'Contents/MacOS/service' in merged
    info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
    assert info['CFBundleIdentifier'] in [left['bundle_id'],'com.carriez.rustdesk'] and info['CFBundleExecutable']==app_name
    info['CFBundleIdentifier']=left['bundle_id']
    assert info.get('CFBundleDisplayName')==left['product']
    info['LSMinimumSystemVersion']='11.0';info['LSArchitecturePriority']=['arm64','x86_64']
    (app/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
    resources=stage/'resources';resources.mkdir()
    shutil.copyfile(ROOT/f'branding/{edition}/logo-light.png',resources/'logo.png')
    color='#2563EB' if edition=='zavix' else '#405E7B'
    product=escape(left['product'])
    welcome=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>body{{font:14px -apple-system,Helvetica,sans-serif;color:#172b48;margin:28px}}img{{width:230px;height:auto}}h1{{font-size:24px;color:{color};margin-top:26px}}p{{line-height:1.65}}.note{{background:#f1f5fc;border-left:4px solid {color};padding:14px;border-radius:5px}}</style></head><body><img src="logo.png" alt="{product}"><h1>Suporte remoto para seu Mac</h1><p>Este instalador prepara o {product} para Macs Intel e Apple Silicon, com o servidor da nossa equipe já configurado.</p><p class="note">Acesso assistido: o atendente só se conecta quando você aceita a solicitação no aplicativo.</p><p>Ao concluir, abra o aplicativo, autorize Gravação de Tela e Acessibilidade em Privacidade e Segurança e informe seu ID ao atendente.</p><p>Versão {left['version']} · macOS 11 ou posterior.</p></body></html>'''
    (resources/'Welcome.html').write_text(welcome)
    (resources/'ReadMe.html').write_text('<html><meta charset="utf-8"><body><h2>Permissões e segurança</h2><p>O macOS exige sua autorização de Gravação de Tela e Acessibilidade. Monitoramento de Entrada poderá ser solicitado. Essas permissões não são concedidas pelo instalador.</p><p>Este pacote não tem assinatura Developer ID nem notarização Apple. Mantenha as proteções do macOS ativas; aprove a abertura somente se você solicitou este suporte.</p><p>O serviço inicia com o Mac e o componente de atendimento inicia na entrada do usuário. O acesso continua exigindo aprovação do cliente.</p></body></html>')
    shutil.copyfile(ROOT/'LICENCE',resources/'License.txt')
    scripts=stage/'scripts';scripts.mkdir()
    labels={kind:f'com.carriez.{app_name}_{kind}' for kind in ['service','server']}
    for kind,template,folder in [('service','daemon.plist','LaunchDaemons'),('server','agent.plist','LaunchAgents')]:
        text=(ROOT/'src/platform/privileges_scripts'/template).read_text().replace('com.carriez.rustdesk',left['bundle_id']).replace('RustDesk',app_name).replace('rustdesk',app_name.lower())
        dest=payload/'Library'/folder/(labels[kind]+'.plist');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
        assert plistlib.loads(dest.read_bytes())['Label']==labels[kind]
    pre=f'''#!/bin/bash
set -eu
/bin/launchctl bootout system/{labels['service']} 2>/dev/null || true
console_uid=$(/usr/bin/stat -f %u /dev/console)
if [ "$console_uid" -ge 500 ]; then /bin/launchctl bootout gui/"$console_uid"/{labels['server']} 2>/dev/null || true; fi
exit 0
'''
    post=f'''#!/bin/bash
set -eu
daemon=/Library/LaunchDaemons/{labels['service']}.plist
agent=/Library/LaunchAgents/{labels['server']}.plist
/usr/sbin/chown root:wheel "$daemon" "$agent"
/bin/chmod 644 "$daemon" "$agent"
/bin/launchctl bootstrap system "$daemon"
/bin/launchctl kickstart system/{labels['service']}
console_user=$(/usr/bin/stat -f %Su /dev/console)
console_uid=$(/usr/bin/stat -f %u /dev/console)
if [ "$console_uid" -ge 500 ] && [ "$console_user" != loginwindow ]; then
  /bin/launchctl bootstrap gui/"$console_uid" "$agent" || true
  /bin/launchctl asuser "$console_uid" /usr/bin/sudo -u "$console_user" /usr/bin/open -n -a /Applications/{app_name}.app --args --no-server || true
fi
exit 0
'''
    for name,text in [('preinstall',pre),('postinstall',post)]:
        p=scripts/name;p.write_text(text);p.chmod(0o755)
    # Finder can add cosmetic bundle metadata while extracting frameworks.
    for attribute in ['com.apple.FinderInfo','com.apple.ResourceFork']:
        subprocess.run(['xattr','-r','-d',attribute,str(app)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(['bash',str(ROOT/'.github/scripts/sign-macos-app.sh'),str(app),'-',str(ROOT/'flutter/macos/Runner/Release.entitlements')],check=True)
    run('codesign','--force','--options','runtime','--sign','-','--identifier',left['bundle_id'],'--generate-entitlement-der','--entitlements',ROOT/'flutter/macos/Runner/Release.entitlements',app)
    run('codesign','--verify','--deep','--strict',app)
    component=stage/'component.pkg';identifier=left['bundle_id']+'.installer'
    run('pkgbuild','--root',payload,'--scripts',scripts,'--identifier',identifier,'--version',left['version'],'--install-location','/',component)
    distribution=stage/'Distribution.xml'
    distribution.write_text(f'''<?xml version="1.0" encoding="utf-8"?><installer-gui-script minSpecVersion="2"><title>{product}</title><welcome file="Welcome.html"/><readme file="ReadMe.html"/><license file="License.txt"/><options customize="never" require-scripts="true" hostArchitectures="x86_64,arm64"/><domains enable_localSystem="true" enable_currentUserHome="false" enable_anywhere="false"/><script>function checkSystem() {{ if (system.compareVersions(system.version.ProductVersion,"11.0") &lt; 0) {{ my.result.type="Fatal"; my.result.message="Este instalador exige macOS 11 ou posterior."; return false; }} return true; }}</script><installation-check script="checkSystem()"/><choices-outline><line choice="default"/></choices-outline><choice id="default" visible="false"><pkg-ref id="{identifier}"/></choice><pkg-ref id="{identifier}" version="{left['version']}" onConclusion="none">component.pkg</pkg-ref></installer-gui-script>''')
    pkg=out/f'{app_name}-{left["version"]}-macos-universal.pkg'
    run('productbuild','--distribution',distribution,'--resources',resources,'--package-path',stage,pkg)
    source=out/f'{app_name}-{left["version"]}-macos-source.tar.gz'
    with tarfile.open(source,'w:gz') as archive:
        for arch in ['x86_64','arm64']:
            archive.add(native/arch/'source.tar.gz',arcname=arch+'/source.tar.gz')
            archive.add(native/arch/'native-manifest.json',arcname=arch+'/native-manifest.json')
        archive.add(ROOT/'scripts/build_macos.py',arcname='build_macos.py')
    manifest={**left,'package_revision':run('git','rev-parse','HEAD'),'architecture':'universal','architectures':['x86_64','arm64'],'mode':'assisted','package':'pkg','merged_macho':merged,'files':[]}
    for p in [pkg,source]:manifest['files'].append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'SHA256SUMS.txt').write_text(''.join(f'{f["sha256"]}  {f["name"]}\n' for f in manifest['files']))
    shutil.rmtree(stage)
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--edition',choices=['zavix','linvix'],required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);build(a.native,a.out,a.edition)
