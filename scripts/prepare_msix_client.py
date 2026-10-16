"""Prepare an isolated Store build; never run this in an EXE/MSI release job."""
import argparse
import json
from pathlib import Path
import prepare_brand

ROOT = Path(__file__).resolve().parents[1]

def prepare(edition):
    prepare_brand.prepare(edition)
    brand = json.loads((ROOT / 'branding/zavix.json').read_text(encoding='utf-8'))
    app = brand['app_name']
    if app not in ('ZAVIXRemote', 'LinvixRemote'):
        raise ValueError('Use a clean checkout for each Store build')
    store_app = app + 'Store'
    for name in prepare_brand.FILES:
        if name.startswith(('scripts/', 'res/')):
            continue
        path = ROOT / name
        path.write_text(path.read_text(encoding='utf-8').replace(app, store_app), encoding='utf-8')
    cargo = ROOT / 'Cargo.toml'
    source = cargo.read_text(encoding='utf-8')
    old = 'default = ["use_dasp"]'
    if source.count(old) != 1:
        raise ValueError('Cargo default feature declaration changed')
    cargo.write_text(source.replace(old, 'default = ["use_dasp", "zavix-msix"]'), encoding='utf-8')
    brand['app_name'] = store_app
    brand['hard'].update({'disable-installation': 'Y', 'disable-settings': 'Y'})
    brand['builtin'].update({'store-assisted': 'Y', 'hide-elevate-button-in-accept-window': 'Y'})
    (ROOT / 'branding/zavix.json').write_text(json.dumps(brand, indent=2), encoding='utf-8')
    profile = {'edition': edition, 'app_name': store_app, 'product_name': brand['product_name'],
               'version': brand['version'], 'profile': 'store-assisted', 'architecture': 'x64'}
    (ROOT / 'branding/msix-profile.json').write_text(json.dumps(profile, indent=2), encoding='utf-8')
    for name in ['PRIVACY.md', 'NOTICE-ZAVIX.md']:
        path = ROOT / name
        path.write_text('Edição Microsoft Store: acesso assistido enquanto o app estiver aberto; '
                        'sem serviço, elevação, acesso à tela UAC ou instalação de drivers. '
                        'Fechar a janela principal encerra o aplicativo.\n\n' +
                        path.read_text(encoding='utf-8'), encoding='utf-8')
    print(json.dumps(profile))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('edition', choices=['zavix', 'linvix'])
    prepare(parser.parse_args().edition)
