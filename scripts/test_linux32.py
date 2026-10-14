"""Verify the i386 package, actual process architecture and GTK startup."""
import json, os, signal, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def command(*args):
    return subprocess.check_output(args,text=True,timeout=90).strip()

def main():
    out=ROOT/'Linux32Release'
    subprocess.run(['apt-get','install','-y',str(next(out.glob('*.deb')))],check=True)
    exe=Path('/opt/zavixremote/zavixremote')
    try:
        assert command('dpkg-query','-W','-f=${Architecture}','zavixremote')=='i386'
        assert 'ELF 32-bit' in command('file',str(exe))
        data=json.loads(next(line for line in command(str(exe),'--zavix-diagnostics').splitlines() if line.startswith('{')))
        assert data['architecture']=='x86' and data['platform']=='linux'
        assert data['approve_mode']=='click' and data['incoming_only'] and data['updater']=='N'
        assert data['app_name']=='ZAVIXRemote' and data['api']=='https://remote.zavix.app'
        assert 'not found' not in command('ldd',str(exe))
        with (out/'linux32-gui.log').open('w') as log:
            p=subprocess.Popen([str(exe),'--no-server'],stdout=log,stderr=log,start_new_session=True)
            try:
                window=''
                for _ in range(30):
                    assert p.poll() is None,'GTK exited before opening'
                    r=subprocess.run(['xdotool','search','--onlyvisible','--name','ZAVIX Remote'],capture_output=True,text=True)
                    if r.returncode==0 and r.stdout.strip():
                        window=r.stdout.strip().splitlines()[-1]
                        break
                    time.sleep(1)
                assert window,'GTK window was not visible'
                time.sleep(2)
                command('import','-window','root',str(out/'linux32-gui.png'))
                command('xdotool','key','--window',window,'alt+s')
                p.wait(timeout=10)
                assert p.returncode==0,'Application did not exit cleanly'
            finally:
                if p.poll() is None:
                    os.killpg(p.pid,signal.SIGTERM)
                    p.wait(timeout=10)
        evidence={'result':'passed','configuration':data,'executable':'ELF 32-bit Intel 80386','gui':'GTK3 visible X11 window','lifecycle':'install/open/exit/remove','remote_session':'pending real desktop validation','channel':'candidate'}
        (out/'linux32-validation.json').write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps(evidence,indent=2))
    finally:
        subprocess.run(['apt-get','remove','-y','zavixremote'],check=True)
    assert not exe.exists()
if __name__=='__main__':main()
