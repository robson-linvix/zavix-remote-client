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

O manifesto nasce com `channel: candidate`. Build e abertura gráfica não comprovam captura, teclado, mouse e aceite em atendimento real. A promoção para estável exige essa homologação e a conferência de hashes/fontes; só então o pacote pode ser anunciado como estável em https://remote.zavix.app/download. Wayland e outras distribuições não são declarados homologados por um teste em Xvfb/Ubuntu 22.04.

## Linux 32 bits

O pedido de 32 bits permanece pendente. Flutter não oferece alvo desktop Linux x86/i686. O Sciter legado usado pelo cliente Windows x86 não fornece o runtime Linux x86 correspondente. O SDK inclui ARM32, que é outra arquitetura e não funciona em computadores x86 de 32 bits.

- Plataformas oficiais Flutter: https://docs.flutter.dev/reference/supported-platforms
- Runtimes oficiais Sciter: https://github.com/c-smile/sciter-sdk/tree/master/bin.lnx
- Discussão específica do runtime x86 ausente: https://github.com/c-smile/sciter-sdk/issues/222

É necessário confirmar distribuição, versão e arquitetura dos equipamentos. Um sistema operacional de 32 bits pode estar instalado em uma CPU capaz de executar 64 bits; isso não permite executar este pacote enquanto o sistema continuar em 32 bits. Suporte nativo i686 exige outra interface/engine e homologação própria, sem renomear um pacote x64 como x86.

## Superfície de regressão

As alterações em `Cargo.toml`, `src/lib.rs`, `src/common.rs` e `src/core_main.rs` apenas registram e acionam o perfil sob `target_os=linux` e feature `zavix-linux`. Com a feature desligada, o Linux anterior e o gateway mantêm o caminho existente. Windows, macOS, Android, protocolos e submódulos não são alterados.

O preparo da marca transforma somente arquivos de interface no checkout isolado do build Linux. A lógica nova fica em `src/zavix_linux.rs` e nos scripts Linux. Os workflows existentes permanecem intactos.

## Validação em ambiente limpo (14/10/2026)

O primeiro teste fora do runner encontrou duas dependências mascaradas pelo ambiente de desenvolvimento: o carregador não procurava `libyuv.so.0` ao lado de `librustdesk.so`, e o pacote não declarava `libegl1`. O empacotamento agora define RUNPATH `$ORIGIN` em `librustdesk.so` e `libyuv.so.0`, declara `libegl1`/`libgl1`, e o teste verifica que libyuv e libjpeg são resolvidas dentro do pacote instalado.

Com essas correções, o cliente abriu e ficou online em um contêiner Ubuntu 22.04/Xvfb isolado. A conexão de laboratório chegou ao cliente pelo relay, mas o diálogo de aceite não foi iniciado nesse ambiente sem loginctl/sessão gráfica registrada. O caminho existente de `is_prelogin()` não deve ser alterado apenas para contornar a ausência de uma sessão real no laboratório. Captura, teclado, mouse e aceite continuam pendentes em desktop Linux com usuário logado. Não há promoção para estável baseada nesse teste parcial.

## Disponibilização autorizada no portal

Em 14/10/2026, após receber o resultado da homologação parcial, o usuário solicitou disponibilizar esta build na central oficial. O pacote foi publicado em https://remote.zavix.app/download#linux-edition com identificação explícita de versão candidata para testes, Ubuntu 22.04/x86_64/X11 e limitações. O manifesto continua candidate, Linux 32 bits continua indisponível e não houve promoção para estável. Código-fonte e SHA256 acompanham o instalador. Publicação do portal: commit 377a987.
