"""Verify the actual universal PKG in an ephemeral macOS runner."""
from pathlib import Path
import argparse,json,os,plistlib,subprocess,time

def command(*args,check=True):
    return subprocess.run(list(map(str,args)),text=True,capture_output=True,timeout=120,check=check)

p=argparse.ArgumentParser();p.add_argument('--release',type=Path,required=True);p.add_argument('--arch',choices=['x86_64','arm64'],required=True)
a=p.parse_args();manifest=json.loads((a.release/'manifest.json').read_text());app_name=manifest['app_name']
pkg=a.release/next(f['name'] for f in manifest['files'] if f['name'].endswith('.pkg'))
app=Path('/Applications')/(app_name+'.app');exe=app/'Contents/MacOS'/app_name
labels={k:f'com.carriez.{app_name}_{k}' for k in ['service','server']}
console_uid=command('/usr/bin/stat','-f','%u','/dev/console').stdout.strip()
result={'product':manifest['product'],'version':manifest['version'],'architecture':a.arch,'environment':'macOS 15 ephemeral CI','developer_id_signed':False,'notarized':False}
try:
    signature=command('pkgutil','--check-signature',pkg,check=False)
    assert 'no signature' in (signature.stdout+signature.stderr).lower() or 'unsigned' in (signature.stdout+signature.stderr).lower()
    command('sudo','/usr/sbin/installer','-pkg',pkg,'-target','/')
    info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
    assert info['CFBundleIdentifier']==manifest['bundle_id'] and info['CFBundleDisplayName']==manifest['product']
    assert set(command('lipo','-archs',exe).stdout.split())=={'x86_64','arm64'}
    command('codesign','--verify','--deep','--strict',app)
    signed_identity=command('codesign','-d','--verbose=2',app).stderr
    assert 'Identifier='+manifest['bundle_id'] in signed_identity
    runtime=command(exe,'--zavix-diagnostics')
    data=json.loads(next(line for line in reversed(runtime.stdout.splitlines()) if line.startswith('{')))
    assert data['app_name']==app_name and data['product_name']==manifest['product'] and data['version']==manifest['version'] and data['installed']
    assert data['architecture']==('aarch64' if a.arch=='arm64' else 'x86_64')
    assert data['server']=='187.77.241.190:21116' and data['relay']=='187.77.241.190:21117' and data['api']=='https://remote.zavix.app'
    assert data['approve_mode']=='click' and data['incoming_only'] and data['updater']=='N'
    service=command('sudo','launchctl','print','system/'+labels['service']).stdout
    assert 'state = running' in service or 'pid = ' in service
    for kind,folder in [('service','LaunchDaemons'),('server','LaunchAgents')]:
        plist=plistlib.loads((Path('/Library')/folder/(labels[kind]+'.plist')).read_bytes())
        assert plist['RunAtLoad'] and plist['AssociatedBundleIdentifiers']==manifest['bundle_id']
    command('/usr/bin/open','-n','-a',app)
    deadline=time.monotonic()+20
    gui=False
    while time.monotonic()<deadline:
        processes=command('/bin/ps','-axo','pid=,command=').stdout.splitlines()
        gui=any(str(exe) in line and not any(flag in line for flag in ['--server','--cm','--tray','--zavix-diagnostics']) for line in processes)
        if gui:break
        time.sleep(1)
    assert gui,'Installed Flutter application did not remain running'
    time.sleep(5)
    assert any(str(exe) in line and not any(flag in line for flag in ['--server','--cm','--tray','--zavix-diagnostics']) for line in command('/bin/ps','-axo','pid=,command=').stdout.splitlines())
    # Tampered external configuration never overrides the compiled assisted profile.
    custom=app/'Contents/Resources/custom.txt'
    command('sudo','/bin/sh','-c','printf %s hostile-external-config > "$1"','test',custom)
    try:
        tampered=command(exe,'--zavix-diagnostics');second=json.loads(next(line for line in reversed(tampered.stdout.splitlines()) if line.startswith('{')))
        assert second==data
    finally:command('sudo','/bin/rm',custom)
    command('codesign','--verify','--deep','--strict',app)
    result.update({'result':'passed','configuration':data,'service':'running','gui_startup':'passed','launchd_run_at_load':True,'universal_macho':'passed','external_configuration':'ignored','screen_control_permissions':'require client approval; not granted by test'})
finally:
    command('sudo','launchctl','bootout','system/'+labels['service'],check=False)
    command('sudo','launchctl','bootout','gui/'+console_uid+'/'+labels['server'],check=False)
    command('sudo','/usr/bin/pkill','-x',app_name,check=False)
    for path in [app,Path('/Library/LaunchDaemons')/(labels['service']+'.plist'),Path('/Library/LaunchAgents')/(labels['server']+'.plist')]:
        command('sudo','/bin/rm','-rf',path,check=False)
    command('sudo','pkgutil','--forget',manifest['bundle_id']+'.installer',check=False)
(a.release/('macos-runtime-'+a.arch+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
