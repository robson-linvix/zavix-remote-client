# Publicação Windows 1.5.0.3 — ZAVIX Remote e Linvix Remote

As duas edições foram publicadas em https://remote.zavix.app/download. O EXE único contém os MSIs de 32 e 64 bits; escolhe Sciter x86 para Windows 7 SP1/8/8.1 e Windows 10 x86, ou Flutter x64 para Windows 10/11 x64. Os MSIs separados e fontes correspondentes também estão disponíveis.

- Empacotamento: e19137812f363379af2b9c60d4d31227f7edb957, ramo codex/windows-universal-v3.
- ZAVIX x86: build38332814926 / eb9a865; x64: build38331622778 / 711c3c3; EXE: build38335498550.
- Linvix x86: build38332818230 / eb9a865; x64: build38333488074 / a5d980e; EXE: build38335500679.
- Fontes incluem os inputs reais por arquitetura, perfil selecionado, lockfiles/arquivos gerados e proveniência individual. O manifesto universal registra compiled_revisions; a revisão de empacotamento é separada da compilação.
- Os quatro ciclos MSI e os dois ciclos EXE passaram no Windows2022. O x86 também abriu a GUI sob WOW64. EXE: seleção automática x64, substituição de MSI x86, serviço, reparo e remoção. As revisões x64 passaram os três testes Flutter do aceite único e a verificação de runtime/proteção contra renomeação. Os downloads públicos foram conferidos integralmente contra SHA256.

Os pacotes permanecem sem Authenticode. SignPath ainda aguarda avaliação. Windows 7/8 e sistemas de 32 bits não foram homologados em máquina real; o proprietário autorizou esse teste em produção com seu time. UAC interativo, sessão real dos novos instaladores e migração de instalação EXE antiga completa dependem dos testes do time. A fixture de versão MSI anterior usa o payload atual com número anterior, não o binário antigo.

A orientação de segurança do cliente 1.5.0.4 foi preservada no main para a próxima compilação; não foi incorporada sem recompilar aos binários 1.5.0.3.

## Histórico anterior ao build MSI/universal

# Build Windows ZAVIX Remote

Base: RustDesk 1.5.0, commit fada664df7a294d1d1a9ca3e7cd3637069122f17.
Submódulo hbb_common: 229b904508364c8997aad0fb5af57effac859f60.

Clone com `git clone --recurse-submodules`. Execute `.github/workflows/windows.yml` por workflow_dispatch em Windows x64 e Ubuntu para geração da bridge. Os workflows upstream de referência permanecem em `.github/upstream-workflows` sem disparos automáticos.

O build usa Flutter 3.24.5, Rust 1.75, LLVM 15.0.6, o commit vcpkg registrado no workflow e a engine identificada pelo asset 210168939 e SHA256 ec8cabf36ee4ff24c8d98de25b00e70781eb03876265aee84d0fe554a110036e.

Saídas: EXE portátil, arquivo de fontes, manifesto, SHA256 e evidência de diagnóstico. Os pacotes são sem assinatura Authenticode. `scripts/test_windows.ps1` testa os binários antes de empacotar.

As alterações no runtime Windows ficam em src/zavix.rs e nos hooks mínimos de carregamento, configuração por nome e atualização. Não foi removida a validação de assinatura do formato comercial RustDesk.

## Próxima compilação — decisões do proprietário em 12/10/2026

- Gerar MSI Windows x64 em lugar do EXE portátil como pacote de distribuição. Manter a decisão de não usar certificado Authenticode. A versão 1.5.0.1 já publicada continua sendo EXE; estas decisões ainda não estão implementadas no build.
- Exibir uma única opção de aprovação, `Aceitar`, com a mesma ação de `Aceitar e Elevar` quando a elevação estiver disponível. Preservar a confirmação UAC do Windows; não garantir privilégios de administrador quando o usuário recusar ou não tiver credenciais. Quando o serviço instalado já atender às permissões necessárias, aceitar normalmente.
- Explicar claramente que o perfil é assistido e exige aprovação no computador, substituindo a apresentação confusa de senha `—` por uma indicação desse modo. Não adicionar senha permanente.
- Rever a redação do aviso rosa do modo portátil: o proprietário confirmou que esse aviso sobre UAC foi interpretado como erro; não houve confirmação de falha da instalação.
- Validar o MSI no mesmo Windows: instalação, serviço, atalhos, marca, conexão assistida, UAC, desinstalação e atualização. Conferir coexistência com RustDesk antigo sem alterar sua configuração. Só substituir o download após o novo pacote e suas fontes passarem na validação.

No teste real do EXE portátil, o proprietário confirmou o aceite e o funcionamento normal da digitação. Relatou desconforto com deslocamento automático da tela; esse ajuste pertence ao visualizador do portal, não ao instalador Windows.
