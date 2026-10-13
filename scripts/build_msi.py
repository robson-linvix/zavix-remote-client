"""Build the ZAVIX x64 MSI from the actual Windows application bundle."""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, uuid
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://wixtoolset.org/schemas/v4/wxs'
UI = 'http://wixtoolset.org/schemas/v4/wxs/ui'
UPGRADE = 'A3F6A58C-1994-4DA7-909D-380DE3D52BB9'
E.register_namespace('', NS)
E.register_namespace('ui', UI)

def node(parent, name, **attributes):
    return E.SubElement(parent, '{'+NS+'}'+name, attributes)

def build(bundle, output, wix, fixture=False, arch='x64'):
    brand = json.loads((ROOT/'branding/zavix.json').read_text())
    app = brand['app_name']
    exe = bundle/(app+'.exe')
    if not exe.is_file(): raise ValueError('The compiled ZAVIX application is missing')
    version = [int(x) for x in brand['version'].split('.')]
    msi_version = f'{version[0]}.{version[1]}.{version[2]*1000+version[3]}'
    if fixture: msi_version = f'{version[0]}.{version[1]}.{version[2]*1000+version[3]-1}'
    build_date = subprocess.check_output([str(exe), '--build-date'],text=True).strip()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', build_date): raise ValueError('Invalid native build date')
    root = E.Element('{'+NS+'}Wix')
    package = node(root,'Package',Name=brand['product_name'],Manufacturer='LINVIX SOFTWARES LTDA',
        Version=msi_version,Language='1046',UpgradeCode=UPGRADE,Scope='perMachine',InstallerVersion='500')
    node(package,'SummaryInformation',Description='Instalador ZAVIX Remote para Windows x64',Codepage='1252')
    node(package,'MediaTemplate',EmbedCab='yes',CompressionLevel='high')
    node(package,'MajorUpgrade',Schedule='afterInstallInitialize',AllowSameVersionUpgrades='yes',DowngradeErrorMessage='Uma versão mais recente do ZAVIX Remote já está instalada.')
    if arch == 'x64':
        os_build=node(package,'Property',Id='WINDOWS_BUILD')
        node(os_build,'RegistrySearch',Id='WindowsBuildSearch',Root='HKLM',Key='SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion',Name='CurrentBuildNumber',Type='raw',Bitness='always64')
        node(package,'Launch',Condition='VersionNT64 AND WINDOWS_BUILD >= 10240',Message='O ZAVIX Remote requer Windows 10 ou superior, 64 bits.')
    else:
        node(package,'Launch',Condition='VersionNT >= 601 AND (VersionNT <> 601 OR ServicePackLevel >= 1)',Message='O ZAVIX Remote de 32 bits requer Windows 7 SP1 ou superior.')
    for key,value in {'ARPPRODUCTICON':'ZavixIcon','ARPHELPLINK':'https://remote.zavix.app/download',
        'ARPURLINFOABOUT':'https://remote.zavix.app','ARPCONTACT':'robson@linvix.com.br','ARPINSTALLLOCATION':'[INSTALLFOLDER]'}.items():
        node(package,'Property',Id=key,Value=value)
    node(package,'Icon',Id='ZavixIcon',SourceFile=str(ROOT/'res/icon.ico'))
    node(package,'WixVariable',Id='WixUILicenseRtf',Value=str(ROOT/'res/zavix-msi/License.rtf'))
    E.SubElement(package,'{'+UI+'}WixUI',{'Id':'WixUI_InstallDir','InstallDirectory':'INSTALLFOLDER'})
    pf = node(package,'StandardDirectory',Id='ProgramFiles64Folder' if arch == 'x64' else 'ProgramFilesFolder')
    directory = node(pf,'Directory',Id='INSTALLFOLDER',Name=app)
    feature = node(package,'Feature',Id='Client',Title=brand['product_name'],Level='1')
    directories = {'.':directory}
    def get_directory(relative):
        key=relative.as_posix()
        if key not in directories:
            parent=get_directory(relative.parent)
            directories[key]=node(parent,'Directory',Id='D'+hashlib.sha256(key.encode()).hexdigest()[:24],Name=relative.name)
        return directories[key]
    for path in sorted(bundle.rglob('*')):
        if path.is_symlink(): raise ValueError('Symlinks are not accepted in the Windows payload')
        if not path.is_file(): continue
        relative=path.relative_to(bundle)
        key=relative.as_posix()
        identity=hashlib.sha256(key.lower().encode()).hexdigest()[:24]
        guid_key=key.lower() if arch == 'x64' else 'x86/'+key.lower()
        component=node(get_directory(relative.parent),'Component',Id='C'+identity,
            Guid=str(uuid.uuid5(uuid.UUID(UPGRADE),guid_key)).upper(),Bitness='always64' if arch == 'x64' else 'always32')
        file_id='AppExe' if path==exe else 'F'+identity
        node(component,'File',Id=file_id,Source=str(path),KeyPath='yes')
        node(feature,'ComponentRef',Id='C'+identity)
        if path==exe:
            node(component,'ServiceInstall',Id='ClientService',Name=app,DisplayName=brand['product_name']+' Service',
                Description='Atendimento remoto assistido ZAVIX Remote',Type='ownProcess',Start='auto',
                ErrorControl='normal',Account='LocalSystem',Arguments='--service',Vital='yes')
            node(component,'ServiceControl',Id='ClientServiceControl',Name=app,Start='install',Stop='both',Remove='uninstall',Wait='yes')
            node(component,'RemoveFile',Id='RemoveRuntimeBroker',Name='RuntimeBroker_rustdesk.exe',On='uninstall')
            state=node(component,'RegistryKey',Root='HKLM',Key=f'Software\\{app}\\InstallState\\{app}',ForceDeleteOnUninstall='yes')
            for name,value,typ in [('InstallLocation','[INSTALLFOLDER]','string'),('WindowsInstaller','1','integer'),
                ('MsiProductCode','[ProductCode]','string'),('BuildDate',build_date,'string')]:
                node(state,'RegistryValue',Name=name,Value=value,Type=typ)
            node(component,'Shortcut',Id='DesktopShortcut',Directory='DesktopFolder',Name=brand['product_name'],
                Advertise='yes',Icon='ZavixIcon',WorkingDirectory='INSTALLFOLDER')
            node(component,'Shortcut',Id='StartMenuShortcut',Directory='ProgramMenuFolder',Name=brand['product_name'],
                Advertise='yes',Icon='ZavixIcon',WorkingDirectory='INSTALLFOLDER')
    node(package,'StandardDirectory',Id='DesktopFolder')
    node(package,'StandardDirectory',Id='ProgramMenuFolder')
    output.parent.mkdir(parents=True,exist_ok=True)
    source=output.with_suffix('.wxs')
    E.indent(root)
    E.ElementTree(root).write(source,encoding='utf-8',xml_declaration=True)
    subprocess.run([str(wix),'build',str(source),'-arch',arch,'-culture','pt-BR','-ext','WixToolset.UI.wixext','-o',str(output)],check=True)
    return msi_version

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--bundle',type=Path,default=ROOT/'dist')
    parser.add_argument('--wix',type=Path,required=True)
    parser.add_argument('--arch',choices=['x86','x64'],default='x64')
    args=parser.parse_args()
    brand=json.loads((ROOT/'branding/zavix.json').read_text())
    suffix='-x86' if args.arch == 'x86' else ''
    output=ROOT/'SignOutput'/f'ZAVIXRemote-{brand["version"]}{suffix}.msi'
    build(args.bundle.resolve(),output,args.wix.resolve(),arch=args.arch)
    build(args.bundle.resolve(),ROOT/'msi-test'/'previous-version.msi',args.wix.resolve(),fixture=True,arch=args.arch)
