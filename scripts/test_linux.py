"""Exercise the installed Linux package, embedded profile and visible X11 window."""
import json
import os
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def command(*args, **kwargs):
    return subprocess.check_output(args, text=True, timeout=60, **kwargs).strip()

def diagnostics(executable):
    output = command(str(executable), '--zavix-diagnostics')
    return json.loads(next(line for line in reversed(output.splitlines()) if line.startswith('{')))

def main():
    output = ROOT / 'LinuxRelease'
    manifest = json.loads((output / 'manifest.json').read_text())
    package = next(output.glob('*.deb'))
    command('sudo', 'apt-get', 'install', '-y', str(package))
    executable = Path('/opt/zavixremote/zavixremote')
    try:
        assert command('dpkg-query', '-W', '-f=${Architecture}', 'zavixremote') == 'amd64'
        assert command('dpkg-query', '-W', '-f=${Version}', 'zavixremote') == manifest['version']
        data = diagnostics(executable)
        assert data['architecture'] == 'x86_64' and data['platform'] == 'linux'
        assert data['app_name'] == 'ZAVIXRemote' and data['version'] == manifest['version']
        assert data['server'] == '187.77.241.190:21116' and data['relay'] == '187.77.241.190:21117'
        assert data['api'] == 'https://remote.zavix.app'
        assert data['approve_mode'] == 'click' and data['updater'] == 'N' and data['incoming_only']
        custom = executable.parent / 'custom.txt'
        command('sudo', 'sh', '-c', 'printf %s hostile-test-config > "$1"', 'test', str(custom))
        try:
            assert diagnostics(executable) == data
        finally:
            command('sudo', 'rm', str(custom))
        for path in [executable, *executable.parent.glob('lib/*.so*')]:
            result = subprocess.run(['ldd', str(path)], text=True, capture_output=True)
            assert 'not found' not in result.stdout + result.stderr, str(path) + result.stdout + result.stderr
        dependencies = command('ldd', str(executable.parent / 'lib/librustdesk.so'))
        assert 'libyuv.so.0 => /opt/zavixremote/lib/libyuv.so.0' in dependencies, dependencies
        dependencies = command('ldd', str(executable.parent / 'lib/libyuv.so.0'))
        assert 'libjpeg.so.8 => /opt/zavixremote/lib/libjpeg.so.8' in dependencies, dependencies
        with (output / 'linux-gui.log').open('w') as log:
            process = subprocess.Popen([str(executable), '--no-server'], stdout=log, stderr=log, start_new_session=True)
            try:
                deadline = time.monotonic() + 40
                found = False
                while time.monotonic() < deadline:
                    assert process.poll() is None, 'GUI exited before a window appeared'
                    windows = subprocess.run(['xdotool', 'search', '--onlyvisible', '--pid', str(process.pid)], capture_output=True, text=True)
                    if windows.returncode == 0 and windows.stdout.strip():
                        found = True
                        break
                    time.sleep(1)
                assert found, 'No visible application window'
                time.sleep(5)
                assert process.poll() is None, 'GUI exited after opening'
                command('import', '-window', 'root', str(output / 'linux-gui.png'))
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=15)
        evidence = {'result': 'passed', 'configuration': data, 'gui_startup': 'visible X11 window',
                    'external_configuration': 'ignored', 'lifecycle': 'install/remove',
                    'remote_session': 'not tested', 'wayland': 'not tested', 'channel': 'candidate'}
        (output / 'linux-validation.json').write_text(json.dumps(evidence, indent=2) + '\n')
    finally:
        command('sudo', 'apt-get', 'remove', '-y', 'zavixremote')
    assert not executable.exists(), 'Package removal left executable installed'
    print(json.dumps(evidence, indent=2))

if __name__ == '__main__':
    main()
