# Cliente ZAVIX Remote para Linux

## Escopo implementado

Cliente nativo x86_64 com interface Flutter, identidade ZAVIX Remote e perfil assistido compilado no binário. A configuração externa `custom.txt` não substitui servidor, chave pública ou política. Atualizações upstream ficam bloqueadas neste perfil.

O workflow `.github/workflows/linux-client.yml` gera:

- `ZAVIXRemote-<versão>-linux-x64.deb` para Ubuntu 22.04 x64, com dependências declaradas;
- `ZAVIXRemote-<versão>-linux-x64.tar.gz`, bundle portátil com bibliotecas Flutter e bibliotecas adicionais necessárias;
- fontes correspondentes, incluindo o submódulo e a bridge efetivamente usados na compilação;
- manifesto, SHA256 e evidência dos testes de instalação, configuração, abertura gráfica X11 e remoção.

O `.deb` instala em `/opt/zavixremote`, com comando `zavixremote` e atalho no menu. Não instala nem habilita serviço de sistema. O usuário deve abrir o aplicativo para receber atendimento e aprovar a conexão. O bundle portátil ainda depende das bibliotecas do sistema listadas no pacote; não é um AppImage nem um binário estático.

## Instalação do candidato

```sh
sudo apt install ./ZAVIXRemote-1.5.0.6-linux-x64.deb
zavixremote
```

Para remover o pacote:

```sh
sudo apt remove zavixremote
```

## Estado de distribuição

O manifesto nasce com `channel: candidate`. Build e abertura gráfica não comprovam captura, teclado, mouse e aceite em atendimento real. A promoção para estável exige essa homologação e a conferência de hashes/fontes; só então o pacote entra em https://remote.zavix.app/download. Wayland e outras distribuições não são declarados homologados por um teste em Xvfb/Ubuntu 22.04.

## Linux 32 bits

O pedido de 32 bits permanece pendente. Flutter não oferece alvo desktop Linux x86/i686. O Sciter legado usado pelo cliente Windows x86 não fornece o runtime Linux x86 correspondente. O SDK inclui ARM32, que é outra arquitetura e não funciona em computadores x86 de 32 bits.

- Plataformas oficiais Flutter: https://docs.flutter.dev/reference/supported-platforms
- Runtimes oficiais Sciter: https://github.com/c-smile/sciter-sdk/tree/master/bin.lnx
- Discussão específica do runtime x86 ausente: https://github.com/c-smile/sciter-sdk/issues/222

É necessário confirmar distribuição, versão e arquitetura dos equipamentos. Um sistema operacional de 32 bits pode estar instalado em uma CPU capaz de executar 64 bits; isso não permite executar este pacote enquanto o sistema continuar em 32 bits. Suporte nativo i686 exige outra interface/engine e homologação própria, sem renomear um pacote x64 como x86.

## Superfície de regressão

As alterações em `Cargo.toml`, `src/lib.rs`, `src/common.rs` e `src/core_main.rs` apenas registram e acionam o perfil sob `target_os=linux` e feature `zavix-linux`. Com a feature desligada, o Linux anterior e o gateway mantêm o caminho existente. Windows, macOS, Android, protocolos e submódulos não são alterados.

O preparo da marca transforma somente arquivos de interface no checkout isolado do build Linux. A lógica nova fica em `src/zavix_linux.rs` e nos scripts Linux. Os workflows existentes permanecem intactos.
