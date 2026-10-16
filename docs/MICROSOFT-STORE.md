# Microsoft Store — ZAVIX Remote e Linvix Remote

Estas edições são separadas dos EXE/MSI distribuídos no site. A compilação
`windows-msix.yml` não cria releases nem publica arquivos no portal.

## Comportamento

- Windows 10 versão 2004 (build 19041) ou posterior e Windows 11, x64.
- Atendimento assistido: abrir o aplicativo, informar o ID e aceitar a solicitação.
- Fechar a janela principal encerra o aplicativo e o acesso dessa edição.
- Sem serviço, inicialização automática, elevação, controle da tela UAC ou drivers.
- Nomes e logos públicos preservados; perfis internos `ZAVIXRemoteStore` e
  `LinvixRemoteStore` evitam compartilhar o serviço/configuração dos instaladores.
- O cliente só recebe conexões; servidor e chave continuam embutidos.

## Associação com a Store

Os candidatos usam identidade provisória e não estão prontos para submissão.
Depois da aprovação da conta da LINVIX, reservar os dois produtos no Partner
Center e copiar **Package/Identity/Name**, **Package/Identity/Publisher** e o ID
do produto. Não inventar esses valores nem reutilizar a identidade de outra marca.

Exemplo de arquivo para `scripts/build_msix.py --identity identidade.json`:

```json
{
  "name": "COPIAR_DO_PARTNER_CENTER",
  "publisher": "CN=COPIAR_DO_PARTNER_CENTER",
  "publisher_display_name": "LINVIX SOFTWARES LTDA",
  "partner_center_product_id": "COPIAR_DO_PARTNER_CENTER",
  "confirmed": true
}
```

A versão nativa 1.5.0.6 corresponde ao pacote 1.5.6.0 (último componente zero,
conforme a regra da Store). O pacote de submissão permanece sem assinatura;
a Microsoft assina na distribuição. O teste CI assina somente uma cópia com
certificado temporário, que é removido ao terminar e não é distribuído.

## Textos iniciais da página da Store (pt-BR)

Usar o nome **ZAVIX Remote** ou **Linvix Remote** conforme o produto.

**Descrição curta:** Suporte remoto assistido com autorização do cliente.

**Descrição:** Receba atendimento remoto da sua equipe de suporte. Abra o
aplicativo, informe o ID ao atendente e aceite a solicitação no seu computador.
Mantenha o aplicativo aberto durante o atendimento. Ao fechar a janela principal,
o aplicativo e o acesso são encerrados. Permita conexões somente quando você
tiver solicitado suporte. Esta edição utiliza a infraestrutura ZAVIX Remote.

**Recursos:** compartilhamento de tela; controle de teclado e mouse após aceite;
identificação visual da marca; conexão com a infraestrutura de suporte configurada.

**Limitações:** esta edição não instala serviço e não permite acesso sem o
aplicativo aberto. Não controla janelas elevadas ou a tela de confirmação UAC.

**Privacidade e licença:** https://remote.zavix.app/privacidade

**Suporte:** suporte@linvix.com.br — https://linvix.com.br

**Justificativa de runFullTrust:** aplicativo desktop Win32 de suporte remoto;
necessita captura de tela e entrada de teclado/mouse no contexto do usuário
para uma conexão recebida e aprovada por ele. Não instala serviço nem solicita
elevação. A capacidade está sujeita à análise da Microsoft.

## Validação antes de publicar

O fluxo compila cada marca, valida a configuração no executável real, bloqueio
dos comandos administrativos, manifesto MakeAppx, instalação MSIX, ativação,
encerramento pela janela e desinstalação em um runner descartável Windows.
O artefato inclui fontes correspondentes, hashes e evidências.

Ainda são necessários: identidade oficial, sessão real em Windows 10/11,
Windows App Certification Kit e capturas finais para a ficha da Store.
Antes da publicação, disponibilizar as fontes específicas destas edições na
página Privacidade e licença, preservando os instaladores atuais no site.
Uma compilação bem-sucedida não equivale à certificação ou aprovação da Store.

## Superfície de regressão

- `Cargo.toml` e `src/lib.rs`: registram a feature opt-in `zavix-msix` e seu
  módulo. A lista padrão de features continua inalterada no repositório.
- `src/core_main.rs`: chama o bloqueio de comandos e diagnóstico somente quando
  a feature Windows Store está compilada.
- `src/platform/windows.rs`: impede `run_uac` e `run_as_system` nessa feature.
- `src/platform/windows/installer_shell.rs`: impede a elevação do instalador
  embutido, que utiliza um caminho diferente de `run_uac`.
- `src/server/portable_service.rs`: impede o helper de serviço nessa feature.
- `src/ui_cm_interface.rs`: remove a oferta e a ação de elevação nessa feature.
- `flutter/lib/desktop/widgets/tabbar_widget.dart`: fechar encerra o processo
  apenas com a opção embutida `store-assisted=Y`; os builds existentes continuam
  ocultando a janela como antes.

Os pontos compartilhados são guardas curtas necessárias para garantir ausência
de serviço/elevação e acesso somente com o app aberto. Os workflows atuais dos
EXE/MSI, a configuração padrão e o site de downloads não são alterados.
