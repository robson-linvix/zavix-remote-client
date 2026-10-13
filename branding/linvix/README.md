# Linvix Remote para Windows

A edição Linvix Remote usa os mesmos padrões assistidos, servidor e chave pública do ZAVIX Remote. O aplicativo tem nome interno `LinvixRemote`, nome visível `Linvix Remote`, serviço próprio, pasta de configuração própria e UpgradeCodes separados do ZAVIX. Não inclui senha permanente ou credencial administrativa.

A seleção da marca acontece antes da compilação através de `python scripts/prepare_brand.py linvix`, em checkout limpo. O padrão `zavix` não transforma fontes. Os workflows Windows x64, x86 e universal têm o input `brand`.

A transformação é limitada a nomes de produto, guards das funções específicas já presentes, ícones, avisos da edição e identidade dos pacotes. Endpoints, chave pública e política de aceite permanecem iguais. Os arquivos transformados são incluídos nos arquivos de fontes de cada arquitetura, junto aos inputs gerados realmente compilados. Para recompilar um arquivo de fontes já transformado, não aplique o perfil novamente; para recompilar o Git, aplique a seleção antes do build.

O EXE único contém ambos os MSIs. Windows 7 SP1/8/8.1 usam o aplicativo Sciter de 32 bits, inclusive nos sistemas de 64 bits. Windows 10 de 32 bits usa a mesma variante; Windows 10/11 de 64 bits usam Flutter x64. Windows 7/8 e Windows 32 bits aguardam validação em máquina real pelo time, autorizada pelo responsável para ocorrer em produção. O CI x86 executa o aplicativo e MSI sob WOW64, o que não equivale a essa homologação.

Os símbolos do ícone derivam do SVG corporativo Linvix disponibilizado no workspace. `logo.svg` preserva o logotipo original, e `icon.svg` usa sua letra L e cor em formato quadrado para o Windows. A rasterização e o invólucro ICO são recursos de build; não mudam a marca do componente Sciter, seus avisos ou assinatura original.

Nenhum pacote possui assinatura Authenticode no momento. A candidatura SignPath está pendente. Direitos, licença AGPL e avisos upstream continuam incluídos; a marca Linvix não substitui o crédito ao RustDesk.
