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
