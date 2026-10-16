"""Verify the i386 package, actual process architecture and GTK startup."""
import json, os, signal, socket, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def command(*args):
    return subprocess.check_output(args,text=True,timeout=90).strip()

def send(peer, kind, content=None):
    value={'t':kind}
    if content is not None:value['c']=content
    payload=json.dumps(value).encode()
    size=next(n for n in range(1,5) if len(payload)<(1<<(8*n-2)))
    peer.sendall(((len(payload)<<2)|(size-1)).to_bytes(size,'little')+payload)

def receive(peer):
    def exact(length):
        value=b''
        while len(value)<length:
            part=peer.recv(length-len(value))
            assert part,'IPC closed unexpectedly'
            value+=part
        return value
    first=exact(1)
    header=first+exact(first[0]&3)
    return json.loads(exact(int.from_bytes(header,'little')>>2))

def consent(window, out):
    """Drive the real CM socket and GTK controls, without a production test hook."""
    path=f'/tmp/ZAVIXRemote-{os.geteuid()}/ipc_cm'
    for _ in range(50):
        if Path(path).exists():break
        time.sleep(.1)
    assert Path(path).exists(),'Connection manager socket missing'
    for connection, accept in [(901,True),(902,False)]:
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as peer:
            peer.connect(path)
            login={key:False for key in ['is_file_transfer','is_view_camera','is_terminal','authorized','clipboard','audio','file','file_transfer_enabled','restart','recording','block_input','privacy_mode','from_switch']}
            login.update(id=connection,peer_id='123456789',name='Validação local',avatar='',port_forward='',keyboard=True)
            send(peer,'Login',login)
            peer.settimeout(.8)
            try:
                value=receive(peer)
                raise AssertionError(f'Unexpected action before local consent: {value}')
            except socket.timeout:pass
            command('xdotool','windowfocus',window)
            if accept:
                command('import','-window','root',str(out/'linux32-consent.png'))
                command('xdotool','key','--window',window,'alt+a')
                peer.settimeout(5)
                assert receive(peer)['t']=='ClickTime'
                send(peer,'ClickTime',0)
                assert receive(peer)['t']=='Authorize','Local acceptance did not authorize'
            command('xdotool','key','--window',window,'alt+r')
            peer.settimeout(5)
            assert receive(peer)['t']=='Close','Refuse/end did not close the connection'
            send(peer,'Close')
        time.sleep(.5)

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
                consent(window,out)
                command('xdotool','key','--window',window,'alt+s')
                p.wait(timeout=10)
                assert p.returncode==0,'Application did not exit cleanly'
            finally:
                if p.poll() is None:
                    os.killpg(p.pid,signal.SIGTERM)
                    p.wait(timeout=10)
        evidence={'result':'passed','configuration':data,'executable':'ELF 32-bit Intel 80386','gui':'GTK3 visible X11 window','local_consent':'no implicit authorization; accept, refuse and end verified through real CM IPC and GTK controls','lifecycle':'install/open/exit/remove','remote_session':'pending real desktop validation','channel':'candidate'}
        (out/'linux32-validation.json').write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps(evidence,indent=2))
    finally:
        subprocess.run(['apt-get','remove','-y','zavixremote'],check=True)
    assert not exe.exists()
if __name__=='__main__':main()
