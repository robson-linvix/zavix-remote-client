# Avisos de componentes de terceiros

O cliente ZAVIX Remote deriva do RustDesk OSS, sob AGPL-3.0. A licença completa está em LICENCE e os avisos das modificações em NOTICE-ZAVIX.md.

O pacote inclui os textos originais encontrados nas dependências Cargo em legal/cargo e os avisos dos ports vcpkg efetivamente instalados em legal/vcpkg. O inventário cargo-inventory.json mantém nome, versão e licença declarada, sem inferir licença para registros sem metadados. Esses registros exigem esclarecimento dos titulares; o hbb_common é uma pendência já registrada no projeto.

O Flutter gera avisos das dependências Dart no arquivo NOTICES.Z dos assets. A engine modificada é obtida da referência e hash documentados em BUILD-ZAVIX.md; a base Flutter está sob BSD-3-Clause. A DLL WindowInjection usa a licença MIT de fufesou; o texto integral acompanha o pacote em legal/WindowInjection-LICENSE.txt e a fonte é fixada pelo workflow no commit ecd8d6a139eee76845ea66423fb739af450fda90 de rustdesk-org/RustDeskTempTopMostWindow.

Não são incluídos os pacotes opcionais de driver de monitor virtual usbmmidd nem de impressora. A existência de inventário e fontes não substitui o esclarecimento das dependências sem indicação de licença nem a revisão de conformidade por versão.

## Variante Windows x86 legada

A variante de 32 bits usa o caminho Sciter mantido pela base RustDesk; ela não é uma compilação Flutter x86. O engine `sciter.dll` é um componente binário de Terra Informatica, com EULA própria, e não é apresentado como código AGPL de autoria ZAVIX. A referência e o SHA256 estão em `branding/sciter-x86.json`; o texto original da licença acompanha a fonte em `branding/Sciter-LICENSE.htm` e o pacote em `legal/Sciter-LICENSE.htm`. O diálogo Sobre mantém a atribuição e o link exigidos pelo titular. A assinatura desse arquivo de terceiro não é alterada.

A inclusão dessa dependência não demonstra elegibilidade para patrocínio SignPath. A candidatura segue pendente; o novo perfil e as dependências precisam integrar a análise do projeto antes de qualquer assinatura patrocinada.
