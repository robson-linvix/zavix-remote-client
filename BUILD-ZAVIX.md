# Build Windows ZAVIX Remote

Base: RustDesk 1.5.0, commit fada664df7a294d1d1a9ca3e7cd3637069122f17.
Submódulo hbb_common: 229b904508364c8997aad0fb5af57effac859f60.

Clone com `git clone --recurse-submodules`. Execute `.github/workflows/windows.yml` por workflow_dispatch em Windows x64 e Ubuntu para geração da bridge. Os workflows upstream de referência permanecem em `.github/upstream-workflows` sem disparos automáticos.

O build usa Flutter 3.24.5, Rust 1.75, LLVM 15.0.6, o commit vcpkg registrado no workflow e a engine identificada pelo asset 210168939 e SHA256 ec8cabf36ee4ff24c8d98de25b00e70781eb03876265aee84d0fe554a110036e.

Saídas: EXE portátil, arquivo de fontes, manifesto, SHA256 e evidência de diagnóstico. Os pacotes são sem assinatura Authenticode. `scripts/test_windows.ps1` testa os binários antes de empacotar.

As alterações no runtime Windows ficam em src/zavix.rs e nos hooks mínimos de carregamento, configuração por nome e atualização. Não foi removida a validação de assinatura do formato comercial RustDesk.
