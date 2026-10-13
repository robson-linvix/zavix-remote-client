"""Select a trusted Windows edition before compilation; archive all transformed build inputs."""
from pathlib import Path
import argparse,json,shutil
ROOT=Path(__file__).resolve().parents[1]
FILES=['Cargo.toml','src/platform/windows.rs','src/zavix.rs','src/ui.rs','src/ui/cm.tis','src/ui/index.tis',
 'flutter/windows/CMakeLists.txt','flutter/windows/runner/Runner.rc','flutter/windows/runner/main.cpp',
 'flutter/lib/desktop/pages/desktop_home_page.dart','flutter/lib/desktop/pages/server_page.dart',
 'flutter/lib/desktop/pages/desktop_setting_page.dart','flutter/lib/desktop/widgets/tabbar_widget.dart',
 'scripts/build_msi.py','scripts/build_bundle.py','scripts/package_release.py','scripts/validate_config.py',
 'scripts/test_windows.ps1','scripts/test_msi.ps1','scripts/test_bundle.ps1','scripts/test_sciter_startup.ps1','scripts/test_installer_ui.ps1',
 'res/zavix-bundle/pt-BR.wxl','res/zavix-msi/License.rtf']
def prepare(edition):
 if edition=='zavix':
  assert json.loads((ROOT/'branding/zavix.json').read_text(encoding='utf-8'))['app_name']=='ZAVIXRemote'
  return
 brand=json.loads((ROOT/'branding/linvix.json').read_text(encoding='utf-8'));assert brand['app_name']=='LinvixRemote' and brand['product_name']=='Linvix Remote'
 assert json.loads((ROOT/'branding/zavix.json').read_text(encoding='utf-8'))['app_name']=='ZAVIXRemote','Use a clean checkout for each brand'
 for name in FILES:
  p=ROOT/name;s=p.read_text(encoding='utf-8')
  if name=='flutter/windows/runner/Runner.rc':
   s=s.replace('VALUE "CompanyName", "ZAVIX"', 'VALUE "CompanyName", "LINVIX SOFTWARES LTDA"')
  if name=='flutter/lib/desktop/pages/desktop_setting_page.dart':
   s=s.replace('ZAVIX Remote 1.5.0.1', 'Linvix Remote '+brand['version']).replace('Modificações ZAVIX © 2026', 'Modificações LINVIX © 2026')
  s=s.replace('ZAVIXRemote','LinvixRemote').replace('ZAVIX Remote','Linvix Remote')
  s=s.replace('A3F6A58C-1994-4DA7-909D-380DE3D52BB9','51B0F725-6EC7-4182-9CFD-544510B9881C')
  s=s.replace('5F8EA9B9-D7D4-44A4-9A18-2C54010A4E3F','4D0D41CF-FC23-4E69-AF03-957A57A958DF')
  p.write_text(s,encoding='utf-8')
 shutil.copyfile(ROOT/'branding/linvix.json',ROOT/'branding/zavix.json')
 for name in ['res/icon.ico','res/tray-icon.ico','flutter/assets/icon.ico','flutter/windows/runner/resources/app_icon.ico']:
  shutil.copyfile(ROOT/'branding/linvix/icon.ico',ROOT/name)
 shutil.copyfile(ROOT/'branding/linvix/icon.png',ROOT/'branding/zavix-icon.png')
 for mode in ['light','dark']:
  shutil.copyfile(ROOT/f'branding/linvix/logo-{mode}.png',ROOT/f'flutter/assets/remote-logo-{mode}.png')
 shutil.copyfile(ROOT/'branding/linvix/logo-light.png',ROOT/'branding/remote-logo.png')
 for name in ['icon.png','icon.svg']:
  shutil.copyfile(ROOT/'branding/linvix'/name,ROOT/'flutter/assets'/name)
 # Preserve original upstream copyright and notices; identify the selected edition explicitly.
 for name in ['NOTICE-ZAVIX.md','PRIVACY.md']:
  p=ROOT/name;p.write_text('Edição Linvix Remote — LINVIX SOFTWARES LTDA. Usa a infraestrutura ZAVIX Remote.\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
 print('Linvix Remote: native app, Windows resources, own service/MSI/bundle identity and icon selected')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('edition',choices=['zavix','linvix']);prepare(p.parse_args().edition)
