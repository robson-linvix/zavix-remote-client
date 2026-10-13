# ZAVIX Remote Android — piloto assistido

## Estado em 12/10/2026

Preparação de código em `codex/android-pilot-20261012`, inicialmente baseada
em `6363cae` e atualizada com a main `19b1c49`, preservando integralmente o
MSI e a aprovação assistida da outra frente. Não publicado no Google Play,
não homologado em aparelho real.
O proprietário autorizou iniciar a versão Android e informou SUNMI D2 Mini
com Play Store como primeiro equipamento. Confirmar versão do Android,
arquitetura, firmware e possibilidade de habilitar acessibilidade nesse aparelho.

Nenhum workflow, certificado, chave, perfil ou arquivo de marca do Windows
foi alterado. Não substituir o instalador Windows ou os downloads de produção.

## Identidade e compilação

- Package de produção proposto: `app.zavix.remote` (não registrado na loja).
- Piloto: `app.zavix.remote.pilot`, coexistente com o RustDesk original e com a
  futura versão de produção. Nome visível ZAVIX Remote; versionName de piloto.
- Android mínimo API 24 (7.0), compile/target 36; essas configurações não são
  prova de compatibilidade dos plugins e bibliotecas nativas.
- Flavors `pilot` e `store`. O piloto usa certificado de desenvolvimento do
  runner; não constitui a chave definitiva e pode exigir reinstalação entre
  builds. O flavor store mantém assinatura de release, sem fallback de debug.
- Workflow separado `.github/workflows/android-pilot.yml`, acionável manualmente
  ou por push apenas da branch do piloto. ARMv7/ARM64, sem upload para loja,
  sem GitHub Release e sem publicação em servidor.
- Reutiliza somente o gerador de bridge existente, sem modificar o gerador ou
  os builds Windows. NDK r28c; linker nativo com alinhamento de 16 KB.
  Ainda validar **todas** as bibliotecas finais, incluindo a engine Flutter,
  antes de declarar compatibilidade 16 KB ou aptidão para o Google Play.
- Artefatos: APK por ABI, identidade, assinatura, fontes correspondentes,
  revision e hashes. APK é candidato, não homologação automática.

## Perfil assistido

Configuração Android própria em `branding/zavix-android.json`; servidor, relay
e chave **pública** são os mesmos do Windows. Nenhuma senha permanente ou
token do CRM é embutido. Inicialização Rust restrita por cfg ao Android; a
configuração comercial externa não é carregada nesse caminho.

Recebimento de suporte, aprovação por clique, sem updater upstream, boot
desabilitado, gravação automática desligada. Sobreposição flutuante desabilitada
no perfil inicial; áudio desligado. Os recursos upstream opcionais e suas
permissões ainda exigem revisão antes da loja — não anunciar esse piloto como
versão com permissões mínimas já homologadas.

Aviso separado antes do consentimento MediaProjection e antes de abrir as
configurações de acessibilidade. Cancelamento do aviso de tela devolve o mesmo
resultado de recusa da captura Android. Não marcar `isAccessibilityTool=true`:
assistência remota não se apresenta como ferramenta voltada a deficiência.

**Limite preservado:** a autorização exclusiva por atendimento do CRM no
protocolo nativo ainda não está homologada. Não prometer que todo acesso
nativo externo é tecnicamente impedido. O aceite local continua obrigatório.
O esquema `zavixremote` é reservado no manifesto; integração de links de
atendimento não está implementada nesse piloto.

## Homologação requerida

1. Instalação do APK compatível com a ABI real do SUNMI; abertura, marca,
   idioma, ID e registro somente no servidor ZAVIX.
2. Recusar e aceitar captura; recusar e habilitar controle; nenhuma captura
   ou entrada antes de consentimento; atendimento só após aceite.
3. Tela e interação do PDV, teclado, orientação e eventual segunda tela.
   Não usar dados reais de pagamento ou clientes nos testes.
4. Encerramento pelo cliente e pelo atendente; revogação de acessibilidade;
   perda de rede; retorno do Wi-Fi; minimização; bloqueio; reinício.
5. Compatibilidade com visualizador Remote, convite/identificação pelo CRM e
   eventos de duração conectada. Teste Windows de regressão, sem mudar seu build.
6. Android recente, captura por sessão, foreground service e ambiente 16 KB.

## Publicação no Google Play

Conta empresarial da Linvix Softwares: cadastro iniciado na sessão do
proprietário, pendente de D-U-N-S. Dados empresariais não são guardados neste
repositório público. Solicitação gratuita do D-U-N-S autorizada pelo proprietário.
Depois, autorizou consultar o preço de emissão acelerada no canal oficial,
sem contratar. Nenhum serviço pago ou inscrição Google Play foi contratado.
O chat oficial da CIAL confirmou recebimento dos dados para retorno de consultor
em até 3 horas úteis sobre a opção expressa. Isso é um **contato comercial**,
não comprovação de emissão do D-U-N-S, contratação ou aprovação da conta Google.
Emissão gratuita não foi confirmada como protocolada nesse fluxo. O proprietário
optou por aguardar o retorno. A conta Google continua pendente de D-U-N-S.

Validação inicial: três testes do perfil passaram e YAML do workflow foi
validado. Compilação completa em andamento na execução
`38328301290`; nenhuma conclusão de compatibilidade ou APK pronto pode ser
inferida desses testes estáticos. A primeira execução `38328227765` foi cancelada
por esta frente para incorporar a main Windows atual antes de continuar.

Antes da loja: chave definitiva protegida e backup, Play App Signing, package
confirmado, AAB de release validado, privacidade pública e dentro do app,
Data Safety coerente com transmissão de tela e metadados, declarações de
acessibilidade/foreground services, vídeo e acesso de revisão, ficha e imagens.
Preservar AGPL, avisos e fontes correspondentes. Validar atualização e plano
de instalação APK/Play sem incompatibilidade de assinaturas.

Não aceitar contratos, pagar inscrição, enviar documentos de identidade,
publicar app ou contratar serviço de terceiros sem a autorização necessária
para a respectiva etapa. O proprietário acompanha o cadastro.

## Superfície de regressão

- Gradle/manifesto/strings/Kotlin Android: identidade, assinatura de piloto,
  consentimento e boot somente no Android; mantida implementação JNI/namespace.
- `src/lib.rs` e `src/flutter_ffi.rs`: módulo e hook com cfg Android; caminho
  Windows permanece original.
- `flutter/lib/mobile/pages/settings_page.dart`: oculta boot somente quando
  a opção compilada `zavix-android-assisted` é Y; outros perfis não mudam.
- Novos perfil, módulo, validação, empacotamento e workflow isolados.

Referências: [Google Play](https://support.google.com/googleplay/android-developer/answer/9859152),
[MediaProjection](https://developer.android.com/media/grow/media-projection),
[acessibilidade](https://support.google.com/googleplay/android-developer/answer/10964491),
[API alvo](https://developer.android.com/google/play/requirements/target-sdk),
[16 KB](https://developer.android.com/guide/practices/page-sizes),
[D-U-N-S](https://www.dnb.com/en-us/smb/duns/google-developers.html).
