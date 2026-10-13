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

`ZavixProvisionReceiver` é uma entrada administrativa separada. O manifesto exige `android.permission.DUMP`, concedida ao shell/sistema e não a aplicativos comuns. A ação `app.zavix.remote.MDM_PREPARE` só funciona no piloto gerenciado, Android 7–9, após verificar a acessibilidade específica do ZAVIX; a autorização de captura (`PROJECT_MEDIA=allow`) é conferida pelo script MDM e aplicada pelo próprio Android. Ela habilita o retorno após reinício e solicita captura pelo fluxo já existente do aplicativo. Não recebe, cria ou troca senha.

Não entregar APK com senha comum. Atualização assinada preserva a senha individual e os dados do aparelho. Android mais recente retorna `unsupported_android`; requer homologação do fabricante/MDM e não recebe essas concessões automaticamente.

## Cadastro automático SUNMI

O receiver protegido recebe apenas um ticket efêmero por serial, nunca uma senha fixa. O APK lê série/modelo e se registra quando aberto; o servidor confere o ticket e vincula o cadastro ao ID remoto. Equipamentos existentes preservam suas credenciais. Equipamentos novos recebem senha individual, com confirmação antes de liberar a conexão. Uma chave individual no armazenamento interno sem backup atualiza presença/estados e permite os próprios diagnósticos; não administra outros dispositivos.

Em Android 7, o serial é lido de `Build.SERIAL`. Em versões restritas, usa o serial conferido no MDM, recusando conflitos com o valor de hardware quando disponível. `MainActivity` possui dois hooks de canal para ler configuração e confirmar a chave; o novo módulo Flutter cuida do registro/heartbeat e sincronismo de senha. O painel só inclui estado/serial e inicia/encerra esse módulo. O diagnóstico acrescenta apenas o campo serial. Sem alteração no núcleo Rust ou nas APIs FFI existentes; APK 1.2.0/código 1005 reutiliza bibliotecas apenas após a verificação da mesma árvore Rust.

Superfície adicional: `AndroidManifest.xml` registra apenas esse receiver com permissão administrativa; o restante do fluxo manual e de boot permanece intacto. Workflow Android passa a gerar versão 1.1.1, código 1004, e pode reaproveitar bibliotecas de um APK assinado somente após conferir árvore Rust idêntica e certificado. O arquivo de fontes correspondente acompanha o APK.

### Distribuição SUNMI 1.2.2

O nome visível do piloto é **Zavix Remote Sunmi**. O pacote, assinatura e nome interno de armazenamento permanecem iguais para preservar ID, senha e configurações nas atualizações. O futuro aplicativo Android geral terá o nome **Zavix Remote** e não faz parte desta homologação.

No Android 7, a operação `PROJECT_MEDIA` não possui mapeamento de string na API AppOps usada inicialmente. O receiver não consulta essa API incompatível: o script administrativo confirma a permissão e o sistema Android valida MediaProjection. O helper de preparação reaproveita o fluxo de retorno do serviço e pode registrar `boot_received` sem um reinício físico; nenhum teste de reinício é implícito nesse registro.
