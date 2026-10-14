"""Select the Linux client profile in an isolated build checkout."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def prepare():
    brand = json.loads((ROOT / 'branding/linux.json').read_text())
    assert brand['app_name'] == 'ZAVIXRemote'
    assert brand['settings']['approve-mode'] == 'click'
    assert brand['hard']['conn-type'] == 'incoming'
    cmake = ROOT / 'flutter/linux/CMakeLists.txt'
    text = cmake.read_text()
    assert 'set(BINARY_NAME "rustdesk")' in text, 'Use a clean checkout'
    cmake.write_text(text.replace('set(BINARY_NAME "rustdesk")', 'set(BINARY_NAME "zavixremote")')
                    .replace('com.carriez.flutter_hbb', 'app.zavix.remote.linux'))
    runner = ROOT / 'flutter/linux/my_application.cc'
    text = runner.read_text().replace('"rustdesk"', '"ZAVIX Remote"')
    text = text.replace('gtk_icon_theme_load_icon(theme, "ZAVIX Remote"',
                        'gtk_icon_theme_load_icon(theme, "zavixremote"')
    runner.write_text(text)
    print('Linux client: assisted profile, dedicated app identity and desktop branding')

if __name__ == '__main__':
    prepare()
