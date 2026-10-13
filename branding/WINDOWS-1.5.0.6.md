# Windows 1.5.0.6 — título aprovado

Publicado em 13/10/2026 para ZAVIX Remote e Linvix Remote. O título exibido no aplicativo é **Assistência Remota**. Preserva os logos por marca, a orientação dos canais oficiais e as correções de instalação da 1.5.0.5.

Revisão compilada e de empacotamento: `a53572be440dc02d864994c0e9f01fd1606fd45f`.

| Edição | x86 | x64 | Universal |
| --- | --- | --- | --- |
| ZAVIX | 38344616577 | 38344614544 | 38346701354 |
| Linvix | 38344620867 | 38344618740 | 38346606484 |

Os seis workflows concluíram com sucesso. Foram verificadas configuração nativa, abertura x86 sob WOW64, instalação, atualização, bloqueio de downgrade, reparo, desinstalação, serviço automático e atalhos. Os dois EXEs passaram em atualização sobre o MSI público 1.5.0.5, seleção/migração de arquitetura e execução da interface do instalador, incluindo **Concluir e abrir**, dono do processo, servidor ativo antes da GUI e janela única. Capturas reais x86/x64 confirmam o título e os logos. Os oito downloads públicos tiveram tamanho e SHA-256 conferidos após a publicação.

Os testes executam em Windows Server 2022 x64; não substituem homologação em Windows 7/8 nem em sistema realmente de 32 bits. Pacotes ainda sem Authenticode. Fontes correspondentes, avisos e licenças seguem incluídos.

## Superfície da alteração

- `flutter/lib/desktop/pages/desktop_home_page.dart`: string do título da edição Windows x64.
- `src/ui/index.tis`: mesma string na interface Windows x86.
- `branding/zavix.json`, `branding/linvix.json`, `.github/workflows/windows.yml`, `.github/workflows/windows-x86.yml`: versão e nomes dos pacotes atualizados para distinguir o novo build.

Nenhuma mudança de lógica em protocolo, autorização, serviço Windows, armazenamento de credenciais ou controle de sessão. Logos e instalação seguem a implementação da 1.5.0.5. A VPS recebeu somente arquivos de distribuição e promoção dos ponteiros `current`; nenhum serviço foi reiniciado nem aplicativo de cliente já aberto foi atualizado.

[Download oficial](https://remote.zavix.app/download) · [Release ZAVIX](https://github.com/robson-linvix/zavix-remote-client/releases/tag/v1.5.0.6) · [Release Linvix](https://github.com/robson-linvix/zavix-remote-client/releases/tag/linvix-v1.5.0.6)
