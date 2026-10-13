# Controles do gateway ZAVIX

Compilação Linux com `--dart-define=ZAVIX_GATEWAY=true`. Windows e APK Android usam o caminho anterior quando esse define não está presente.

A barra nativa oferece Power somente para Android com controle de entrada autorizado. O comando existente `onMobilePower` abre o menu de energia pelo serviço de acessibilidade; não reinicia, desliga nem remove o quiosque automaticamente. As restrições do fabricante continuam valendo.

O controle alterna Automático → Desempenho → Resolução. Automático pede a qualidade nativa mais alta, com a adaptação existente de FPS/bitrate do RustDesk. Desempenho pede o perfil econômico. O menu de resolução escolhe o tamanho da transmissão do gateway; não muda a resolução física do Android ou Windows. O menu de tela original continua disponível para resoluções suportadas pelo cliente.

Somente modo e resolução são publicados em `/config/.zavix-view-controls.json`. O portal lê esses valores pelo runner, com isolamento pelo identificador da sessão. O controle HTML anterior é ocultado depois que a barra nativa anuncia sua presença.

O pacote inclui libyuv e seu aviso de licença. Validar dependências no container de produção antes de criar o marcador `VERIFIED`. Os gateways existentes mantêm seu processo e seu pacote; uma nova versão só é montada em novas sessões.

## Superfície de regressão

- `remote_toolbar.dart`: um import e uma inclusão condicionada do novo widget na barra; necessários para exibir os controles dentro da sessão. Com o define desligado, a barra original permanece.
- Workflow Linux: novo pacote Flutter/Rust e dependência libyuv; sem mudança no núcleo Rust, protocolo, submódulos ou assinatura das funções existentes.
- Limites: a barra horizontal é o formato validado; o Power depende do serviço de acessibilidade e do menu OEM. A qualidade depende das duas etapas cliente→gateway e gateway→navegador.

## Provisionamento Android 1.1.1

`ZavixProvisionReceiver` é uma entrada administrativa separada. O manifesto exige `android.permission.DUMP`, concedida ao shell/sistema e não a aplicativos comuns. A ação `app.zavix.remote.MDM_PREPARE` só funciona no piloto gerenciado, Android 7–9, após verificar captura (`PROJECT_MEDIA=allow`) e a acessibilidade específica do ZAVIX. Ela habilita o retorno após reinício e solicita captura pelo fluxo já existente do aplicativo. Não recebe, cria ou troca senha.

Não entregar APK com senha comum. Atualização assinada preserva a senha individual e os dados do aparelho. Android mais recente retorna `unsupported_android`; requer homologação do fabricante/MDM e não recebe essas concessões automaticamente.

Superfície adicional: `AndroidManifest.xml` registra apenas esse receiver com permissão administrativa; o restante do fluxo manual e de boot permanece intacto. Workflow Android passa a gerar versão 1.1.1, código 1004, e pode reaproveitar bibliotecas de um APK assinado somente após conferir árvore Rust idêntica e certificado. O arquivo de fontes correspondente acompanha o APK.
