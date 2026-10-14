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

O perfil `zavix-linux-gtk` adiciona uma interface GTK3 nativa para x86/i686, compilada pelo workflow `linux32-client.yml`. O alvo inicial é Debian 12 i386 com X11 e glibc 2.36. Distribuição e CPU dos equipamentos do usuário ainda precisam ser confirmadas. O pacote de 64 bits continua separado, com interface Flutter e alvo Ubuntu 22.04.

O cliente GTK mostra ID e estado de conexão, permite aceitar, recusar e encerrar um atendimento e fecha a sessão ao sair. Só admite um atendimento assistido por vez; não oferece acesso não supervisionado, transferência de arquivos, área de transferência, terminal, áudio ou câmera. Reutiliza o protocolo e o gerenciador de conexões existentes. A feature `flutter` seleciona o backend Rust moderno, mas o executável GTK não carrega Flutter nem Sciter.

O pipeline gera `.deb`, `.tar.gz`, fontes correspondentes e SHA256 com sufixo `linux-x86`. O teste executa o ELF de 32 bits, confere a configuração, instala, abre GTK em X11, exercita os botões com o IPC real do gerenciador e remove o pacote. Isso não substitui a homologação de imagem, teclado e mouse em um computador de 32 bits com sessão gráfica real.

```sh
sudo apt install ./ZAVIXRemote-1.5.0.6-linux-x86.deb
zavixremote
```

O mesmo nome de pacote `zavixremote` é usado nas duas arquiteturas; instale a variante compatível com o sistema. O pacote portátil também depende das bibliotecas listadas no `.deb`.

## Superfície de regressão

As alterações em `Cargo.toml`, `src/lib.rs`, `src/common.rs` e `src/core_main.rs` apenas registram e acionam o perfil sob `target_os=linux` e feature `zavix-linux`. Com a feature desligada, o Linux anterior e o gateway mantêm o caminho existente. Windows, macOS, Android, protocolos e submódulos não são alterados.

O preparo da marca transforma somente arquivos de interface no checkout isolado do build Linux. A lógica nova fica em `src/zavix_linux.rs` e nos scripts Linux. Os workflows existentes permanecem intactos.

Para GTK/i686, `Cargo.toml` registra a feature e o binário, `src/lib.rs` expõe o módulo condicionado à feature e `src/zavix_linux.rs` desabilita capacidades que a interface reduzida não oferece. Esses são os únicos caminhos existentes modificados nesta etapa. A interface nova fica em `src/zavix_linux_gtk.rs`; os caminhos de Windows, macOS, Android e Linux64 permanecem iguais com `zavix-linux-gtk` desligada.

## Validação em ambiente limpo (14/10/2026)

O primeiro teste fora do runner encontrou duas dependências mascaradas pelo ambiente de desenvolvimento: o carregador não procurava `libyuv.so.0` ao lado de `librustdesk.so`, e o pacote não declarava `libegl1`. O empacotamento agora define RUNPATH `$ORIGIN` em `librustdesk.so` e `libyuv.so.0`, declara `libegl1`/`libgl1`, e o teste verifica que libyuv e libjpeg são resolvidas dentro do pacote instalado.

Com essas correções, o cliente abriu e ficou online em um contêiner Ubuntu 22.04/Xvfb isolado. A conexão de laboratório chegou ao cliente pelo relay, mas o diálogo de aceite não foi iniciado nesse ambiente sem loginctl/sessão gráfica registrada. O caminho existente de `is_prelogin()` não deve ser alterado apenas para contornar a ausência de uma sessão real no laboratório. Captura, teclado, mouse e aceite continuam pendentes em desktop Linux com usuário logado. Não há promoção para estável baseada nesse teste parcial.

## Disponibilização autorizada no portal

Em 14/10/2026, após receber o resultado da homologação parcial, o usuário solicitou disponibilizar esta build na central oficial. O pacote de 64 bits foi publicado em https://remote.zavix.app/download#linux-edition com identificação explícita de versão candidata para testes, Ubuntu 22.04/x86_64/X11 e limitações. O manifesto continua candidate e não houve promoção para estável. Código-fonte e SHA256 acompanham o instalador. Publicação do portal: commit 377a987. A variante de 32 bits só deve ganhar link após aprovação dos testes e conferência dos artefatos.
