"""Assemble one x86 Burn installer from verified ZAVIX x86/x64 MSI builds."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,tarfile
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
NS='http://wixtoolset.org/schemas/v4/wxs'
BAL=NS+'/bal'
E.register_namespace('',NS);E.register_namespace('bal',BAL)
def node(parent,name,**attrs):return E.SubElement(parent,'{'+NS+'}'+name,attrs)
def checked(folder,arch):
    m=json.loads((folder/'manifest.json').read_text())
    v=m['version'];suffix='-x86' if arch=='x86' else ''
    assert m['product']=='ZAVIX Remote' and m['package']=='msi' and m['signed'] is False and m['architecture']==arch
    expected={f'ZAVIXRemote-{v}{suffix}.msi',f'ZAVIXRemote-{v}{suffix}-source.tar.gz'}
    assert len(m['files'])==2 and {f['name'] for f in m['files']}==expected
    for item in m['files']:
        p=folder/item['name'];assert p.is_file() and not p.is_symlink() and p.stat().st_size==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
    provenance=json.loads((folder/'build-provenance.json').read_text())
    assert provenance['conclusion']=='success' and provenance['head_sha']==m['revision'] and provenance['repository']['full_name']=='robson-linvix/zavix-remote-client'
    runtime=json.loads((folder/'windows-runtime-evidence.json').read_text(encoding='utf-8-sig'))
    assert len(runtime)==3
    for item in runtime:
        c=item['configuration']
        assert item['result']=='passed' and c['architecture']==arch and c['version']==v and c['approve_mode']=='click' and c['incoming_only'] and not c['filename_configuration'] and c['updater']=='N' and c['server']=='187.77.241.190:21116' and c['api']=='https://remote.zavix.app'
    if arch=='x86':
        startup=json.loads((folder/'sciter-startup-evidence.json').read_text(encoding='utf-8-sig'))
        assert startup['result']=='passed'
    lifecycle=json.loads((folder/'windows-msi-evidence.json').read_text(encoding='utf-8-sig'))
    assert {'previous-version-install','upgrade-to-release','downgrade blocked','repair missing file','uninstall and legacy sentinel preservation'} <= {item['case'] for item in lifecycle}
    for item in lifecycle:
        if 'result' in item:assert item['result']=='passed'
        if item['case'] in ('previous-version-install','upgrade-to-release','repair missing file'):assert item['exit_code'] in (0,3010)
        if item['case']=='downgrade blocked':assert item['exit_code']!=0
    return m,provenance

def build(x86,x64,wix):
    a,pa=checked(x86,'x86');b,pb=checked(x64,'x64')
    brand=json.loads((ROOT/'branding/zavix.json').read_text())
    assert a['version']==b['version']==brand['version']
    revisions={'x86':a['revision'],'x64':b['revision']}
    v=a['version'];out=ROOT/'UniversalOutput';out.mkdir(exist_ok=True)
    for arch,folder,m in [('x86',x86,a),('x64',x64,b)]:
        item=next(f for f in m['files'] if f['name'].endswith('.msi'))
        shutil.copyfile(folder/item['name'],out/f'ZAVIXRemote-{v}-{arch}.msi')
    root=E.Element('{'+NS+'}Wix')
    bundle=node(root,'Bundle',Name='ZAVIX Remote',Manufacturer='LINVIX SOFTWARES LTDA',Version=v,
                UpgradeCode='5F8EA9B9-D7D4-44A4-9A18-2C54010A4E3F',Compressed='yes',IconSourceFile=str(ROOT/'res/icon.ico'),
                AboutUrl='https://remote.zavix.app',HelpUrl='https://remote.zavix.app/download')
    ba=node(bundle,'BootstrapperApplication')
    E.SubElement(ba,'{'+BAL+'}WixStandardBootstrapperApplication',{'Theme':'hyperlinkLicense','LicenseUrl':'https://remote.zavix.app/privacidade',
        'LocalizationFile':str(ROOT/'res/zavix-bundle/pt-BR.wxl'),'ShowVersion':'yes','SuppressOptionsUI':'yes'})
    condition=E.SubElement(bundle,'{'+BAL+'}Condition',{'Message':'O ZAVIX Remote requer Windows 7 SP1, Windows 8/8.1, Windows 10 ou Windows 11.'})
    condition.set('Condition','VersionNT >= v6.1 AND (VersionNT <> v6.1 OR ServicePackLevel >= 1)')
    chain=node(bundle,'Chain')
    node(chain,'MsiPackage',Id='ZavixX86',SourceFile=str(out/f'ZAVIXRemote-{v}-x86.msi'),Visible='no',Vital='yes',
        InstallCondition='NOT VersionNT64 OR WindowsBuildNumber < 10240')
    node(chain,'MsiPackage',Id='ZavixX64',SourceFile=str(out/f'ZAVIXRemote-{v}-x64.msi'),Visible='no',Vital='yes',
        InstallCondition='VersionNT64 AND WindowsBuildNumber >= 10240')
    source=out/'bundle.wxs';E.indent(root);E.ElementTree(root).write(source,encoding='utf-8',xml_declaration=True)
    exe=out/f'ZAVIXRemote-{v}.exe'
    subprocess.run([str(wix),'build',str(source),'-arch','x86','-ext','WixToolset.Bal.wixext','-o',str(exe)],check=True)
    package_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    report={'product':'ZAVIX Remote','version':v,'compiled_revision':a['revision'],'compiled_revisions':revisions,'package_revision':package_revision,
        'builds':{'x86':{'id':pa['id'],'revision':pa['head_sha']},'x64':{'id':pb['id'],'revision':pb['head_sha']}},
        'selection':{'x86':'Windows 7/8 on x86 or x64; Windows 10 x86','x64':'Windows 10/11 x64'},
        'old_windows_real_validation':'pending','signed':False}
    (out/'build-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    archive=out/f'ZAVIXRemote-{v}-source.tar.gz'
    with tarfile.open(archive,'w:gz') as t:
        for arch,folder,m in [('x86',x86,a),('x64',x64,b)]:
            source_item=next(f for f in m['files'] if f['name'].endswith('-source.tar.gz'))
            t.add(folder/source_item['name'],arcname=f'ZAVIXRemote-source/{arch}-build-inputs.tar.gz')
            for name in ['manifest.json','build-provenance.json','windows-runtime-evidence.json','windows-msi-evidence.json']:
                t.add(folder/name,arcname=f'ZAVIXRemote-source/evidence/{arch}/{name}')
            if arch=='x86':
                t.add(folder/'sciter-startup-evidence.json',arcname='ZAVIXRemote-source/evidence/x86/sciter-startup-evidence.json')
        tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT,text=True).split('\0')
        for name in tracked:
            p=ROOT/name
            if name and p.is_file() and (name.startswith(('scripts/','res/zavix-bundle/','.github/workflows/','branding/','res/zavix-msi/')) or name.endswith('.md') or name=='LICENCE'):
                t.add(p,arcname='ZAVIXRemote-source/packaging/'+name)
        t.add(out/'build-provenance.json',arcname='ZAVIXRemote-source/build-provenance.json')
    files=[exe,out/f'ZAVIXRemote-{v}-x86.msi',out/f'ZAVIXRemote-{v}-x64.msi',archive]
    manifest={'product':'ZAVIX Remote','version':v,'upstream':'1.5.0','revision':a['revision'],'compiled_revisions':revisions,'package_revision':package_revision,
        'signed':False,'mode':'assisted','package':'exe','installer':True,'architectures':['x86','x64'],
        'files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'SHA256SUMS.txt').write_text(''.join(f'{f["sha256"]}  {f["name"]}\n' for f in manifest['files']))
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--x86',type=Path,required=True);p.add_argument('--x64',type=Path,required=True);p.add_argument('--wix',type=Path,required=True)
    args=p.parse_args();build(args.x86.resolve(),args.x64.resolve(),args.wix.resolve())
