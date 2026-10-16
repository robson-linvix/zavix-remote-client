"""Prepare an isolated macOS build without changing Windows or Android profiles."""
from pathlib import Path
import argparse, json, plistlib, shutil

ROOT = Path(__file__).resolve().parents[1]

def prepare(edition):
    brand = json.loads((ROOT / f'branding/{edition}.json').read_text())
    assert brand['app_name'] == {'zavix':'ZAVIXRemote','linvix':'LinvixRemote'}[edition]
    assert brand['settings']['approve-mode'] == 'click' and brand['hard']['conn-type'] == 'incoming'
    (ROOT / 'branding/macos.json').write_text(json.dumps(brand, indent=2)+'\n')
    app, product = brand['app_name'], brand['product_name']
    bundle = {'zavix':'app.zavix.remote.macos','linvix':'app.linvix.remote.macos'}[edition]
    runner = ROOT / 'flutter/macos/Runner'
    (runner / 'Configs/AppInfo.xcconfig').write_text(
        f'PRODUCT_NAME = {app}\nPRODUCT_MODULE_NAME = {app}\nPRODUCT_BUNDLE_IDENTIFIER = {bundle}\n'
        'PRODUCT_COPYRIGHT = Copyright © 2026 Purslane Tech Pte. Ltd.; modificações LINVIX SOFTWARES LTDA.\n')
    p = runner / 'Info.plist'
    info = plistlib.loads(p.read_bytes())
    info['CFBundleDisplayName'] = product
    info['CFBundleName'] = product
    info['NSMicrophoneUsageDescription'] = f'O {product} usa o microfone somente quando você habilita áudio no atendimento.'
    info['CFBundleURLTypes'][0]['CFBundleURLName'] = bundle
    info['CFBundleURLTypes'][0]['CFBundleURLSchemes'] = [app.lower()]
    p.write_bytes(plistlib.dumps(info))
    p = runner / 'Base.lproj/MainMenu.xib'
    p.write_text(p.read_text().replace('customModule="RustDesk"',f'customModule="{app}"').replace('title="APP_NAME"',f'title="{product}"'))
    p = ROOT / 'flutter/macos/Runner.xcodeproj/project.pbxproj'
    p.write_text(p.read_text().replace('RustDesk.app',app+'.app').replace('MACOSX_DEPLOYMENT_TARGET = 10.14','MACOSX_DEPLOYMENT_TARGET = 11.0'))
    p = ROOT / 'flutter/macos/Podfile'
    p.write_text(p.read_text().replace("platform :osx, '10.14'", "platform :osx, '11.0'"))
    shutil.copyfile(ROOT/f'branding/{edition}/mac-icon.icns',runner/'AppIcon.icns')
    shutil.copyfile(ROOT/f'branding/{edition}/mac-tray.png',ROOT/'res/mac-tray-dark-x2.png')
    for mode in ['light','dark']:
        shutil.copyfile(ROOT/f'branding/{edition}/logo-{mode}.png',ROOT/f'flutter/assets/remote-logo-{mode}.png')
    for name in ['icon.png','icon.svg']:
        shutil.copyfile(ROOT/f'branding/{edition}/{name}',ROOT/f'flutter/assets/{name}')
    if edition == 'linvix':
        for name in ['flutter/lib/common.dart','flutter/lib/desktop/pages/desktop_home_page.dart',
                     'flutter/lib/desktop/pages/server_page.dart','flutter/lib/desktop/pages/desktop_setting_page.dart',
                     'flutter/lib/desktop/widgets/tabbar_widget.dart']:
            p = ROOT / name
            p.write_text(p.read_text().replace('ZAVIXRemote',app).replace('ZAVIX Remote',product))
    out = ROOT / 'macos-build'
    out.mkdir(exist_ok=True)
    manifest = json.loads((ROOT/'vcpkg.json').read_text())
    manifest['dependencies'] = ['aom','libjpeg-turbo','opus','libvpx','libyuv']
    manifest['vcpkg-configuration']['overlay-ports'] = [str(ROOT/'res/vcpkg')]
    manifest['vcpkg-configuration']['overlay-triplets'] = [str(ROOT/'res/zavix-macos-triplets')]
    (out/'vcpkg.json').write_text(json.dumps(manifest,indent=2))
    (out/'brand.json').write_text(json.dumps({**brand,'bundle_id':bundle,'minimum_macos':'11.0'},indent=2))
    print(f'{product}: macOS branding, native configuration, bundle and dependencies prepared')

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('edition',choices=['zavix','linvix'])
    prepare(parser.parse_args().edition)
