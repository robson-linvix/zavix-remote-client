# ZAVIX Remote Android — piloto e acesso corporativo

## Candidato 1.1.0-piloto — T2 Mini S (13/10/2026)

O proprietário aprovou acesso não supervisionado como padrão Android e envio de diagnóstico direto pelo servidor para `robson@linvix.com.br`. Alvo: `t2mini_s`, SUNMI OS 3.0.3 / 237; a família usa Android 7.1, a confirmar no aparelho. O candidato ARMv7 usa package separado `app.zavix.remote.pilot.t2mini` e não atualiza nem remove o piloto 1.0.0, cuja chave de debug era efêmera. Nome no launcher: **ZAVIX Remote T2 Mini (teste)**.

O padrão é aprovação por senha permanente individual. Não há senha embutida, aceite indiscriminado ou credencial SMTP no APK. A política de aprovação é um default local, podendo ser alterada explicitamente para assistido. A senha deve ser configurada no equipamento e cadastrada pelo administrador no dispositivo do portal, com autorização não supervisionada. A inicialização JNI aplica o mesmo perfil antes de ligar o servidor, inclusive no retorno do boot.

Permissões de captura e controle exigem configuração inicial. O painel mostra as permissões separadas do registro online. Quando uma conexão autorizada não consegue iniciar a captura, ela é encerrada e um diagnóstico de captura indisponível é emitido. O Android pode encerrar a captura de outro aplicativo; não testar o ZAVIX e o visualizador SUNMI simultaneamente.

Retorno após reinício é habilitado explicitamente no painel somente depois da senha e permissões. No Android 7–9, usa uma nova solicitação normal de MediaProjection; a autorização lembrada pelo sistema pode permitir retorno automático, dependendo do firmware. Em Android 10 ou superior, registra que a abertura/provisionamento OEM é necessário; não contorna restrições de segundo plano nem recicla token de captura. Homologar reinício e eventual primeiro desbloqueio no T2 Mini S.

Diagnóstico limitado aos últimos 200 eventos do próprio app, no armazenamento privado sem backup Android. Eventos: permissões, início/fim/falha de captura, solicitação/autorização, boot e falha Java. Sem conteúdo da tela, clipboard, texto digitado, senhas, tokens ou logcat de outros apps. **Enviar logs** pede a senha cadastrada no portal para autenticar o equipamento por HTTPS; o servidor usa o provedor SMTP existente, destino fixo Robson, auditoria e limite de um envio por equipamento a cada cinco minutos. Cadastro autorizado no portal é requisito do envio; o totem não precisa de aplicativo de e-mail.

Assinatura de teste estável PKCS12, com chave privada criptografada fora do Git, disponível somente nos secrets de Actions. A identidade pública do certificado fica em `branding/android-test-certificate.sha256`. Não usar esse candidato como homologação da frota nem publicação Play. Windows 1.5.0.6 permanece preservado.

### Ordem do teste

1. Instalar o novo aplicativo e abrir **ZAVIX Remote T2 Mini (teste)**. Encerrar o APK anterior para evitar disputa de captura.
2. Definir senha exclusiva (mínimo 12 caracteres), copiar o ID exibido no painel e habilitar Controle de Entrada nas configurações do Android. Esses passos podem usar o visualizador SUNMI.
3. No portal, cadastrar esse ID e configurar o dispositivo como não supervisionado, com a mesma senha e autorização. Associar à integração CRM quando aplicável.
4. Preparar a captura; lembrar a autorização se o firmware apresentar essa opção. A assistência SUNMI pode congelar ao entregar a captura ao ZAVIX. Continuar pelo dispositivo cadastrado no CRM/portal, no modo não supervisionado.
5. Testar tela, toque, teclado, reconexão e encerramento. Pelo ZAVIX, habilitar retorno após reinício e testar sem reabrir a captura SUNMI.
6. Usar **Enviar logs** para encaminhar o diagnóstico a Robson. Não enviar a senha pelo chat. O envio indica aceite do SMTP, não confirmação de leitura do destinatário.

### Superfície da alteração

Android: perfil, initializer Rust específico, manifesto/Gradle/boot, hooks mínimos Kotlin de estado/diagnóstico e widget próprio Flutter. `src/flutter_ffi.rs` recebe somente os hooks dentro do módulo JNI Android. Mobile server page adiciona painel e tratamento de captura indisponível; settings oculta o boot genérico em favor da configuração gerenciada. Workflow, signer e validação são exclusivos do Android. Submodule permanece no commit original. Nenhuma pipeline, versão, credencial, serviço ou protocolo Windows foi alterado. Backend de diagnóstico e distribuição é um serviço separado na VPS, com reload gracioso do Nginx e sem reiniciar portal/gateways.

## Histórico do piloto 1.0.0 (assistido)

## Estado em 12/10/2026

Preparação de código em `codex/android-pilot-20261012`, inicialmente baseada
em `6363cae` e atualizada com a main `19b1c49`, preservando integralmente o
MSI e a aprovação assistida da outra frente. Não publicado no Google Play,
não homologado em aparelho real.
O proprietário autorizou iniciar a versão Android e informou SUNMI D2 Mini
com Play Store como primeiro equipamento. Confirmar versão do Android,
arquitetura, firmware e possibilidade de habilitar acessibilidade nesse aparelho.
Depois esclareceu que o objetivo é acesso **não supervisionado**, pois os
terminais normalmente não têm operador presente. Aceita uma configuração
inicial autorizada, preferencialmente remota, e informou possuir acesso SUNMI
para distribuição pela loja aos equipamentos. A versão exata Android/SUNMI OS
ainda não foi fornecida. A base assistida abaixo não atende sozinha ao objetivo.

Nenhum workflow, certificado, chave, perfil ou arquivo de marca do Windows
foi alterado. Não substituir o instalador Windows ou os downloads de produção.

## Identidade e compilação

Primeiro APK ARMv7 gerado pela execução `38332085902`, fonte `6462401`:
`ZAVIXRemote-1.0.0-piloto-armeabi-v7a.apk`, 60.438.658 bytes,
SHA256 `e864449ea2d3ea0ae0b34c22eedfcf5b0ef0227f48fbada421f4792b94dbbb42`.
Download local e hashes do APK/fontes conferidos. Relatório aapt do CI confirma
`app.zavix.remote.pilot`, versão `1.0.0-piloto`/code1001, min24, target36,
label ZAVIX Remote e ABI armeabi-v7a. apksigner no CI confirma assinatura v2,
certificado Android Debug; certificado SHA256
`79da3bf2a1b7caac45710b3c698ffb17ca73dd1f543758fe7b6bc49c2267ef3b`.
Bibliotecas baixadas inspecionadas como ELF32 ARM; perfil e inicializador das
fontes correspondentes iguais aos da revisão compilada. Fonte AGPL acompanha.
JRE/SDK locais indisponíveis: conferência criptográfica foi a do CI, com hashes
locais iguais, não uma segunda execução local do apksigner.
Pacote **assistido para teste**, não homologado no SUNMI nem solução não supervisionada.
Não instalar na frota ou considerar pronto para loja/provisionamento permanente.
Após ARMv7 concluir, a reexecução somente do job ARM64 foi aceita (attempt2,
databaseId115091633426); download NDK passou e codecs estavam em compilação.
Primeira de no máximo duas reexecuções adicionais por falha de download nessa fonte.
Main Windows avançou separadamente a `36ff952`/1.5.0.4; a branch Android conserva
baseline `19b1c49` sem modificá-lo. Não promover essa branch sobre main sem integrar
os avanços Windows e validar novamente; nenhum build Windows foi tocado.

ARM64 concluído na mesma execução/source (attempt2), sem recompilar ARMv7:
`ZAVIXRemote-1.0.0-piloto-arm64-v8a.apk`, 72.213.118 bytes,
SHA256 `1e946eb6d21bf113834f6476a1d3af6664d44e2bb045e7f4865a33006a081d45`.
Fontes SHA256 `cbcc2fb638a7faa8705f8dbc9a0457931fac9d092b5f8072b0f79706253e2be0`.
Hashes locais passaram; aapt do CI confirma code2001, versão1.0.0-piloto, min24,
target36, package/label iguais e ABIarm64-v8a. apksigner no CI verificou v2,
certificado Android Debug SHA256
`58b33005b107090e7006d4167091dd2f72bd76a552606a77a248e7f545cb38dc`.
As quatro libs são ELF64 AArch64; perfil/inicializador no pacote de fontes iguais
ao commit compilado. Ambos APKs/fontes preservados em diretórios de saída separados.
Os certificados de desenvolvimento ARMv7/ARM64 diferem: não são um par de atualização
compatível nem chave de produção. Não substituir uma variante pela outra como atualização.

Conferência binária ARM64: todas as libs têm PT_LOAD com alinhamento >=16KB e dados
ZIP sem compressão com offset múltiplo de16KB. libapp/libflutter usam64KB;
libc++_shared/librustdesk usam16KB. Entretanto o fim de GNU_RELRO de libc++_shared
fica com resto8192 em módulo16384; as demais passam ou não possuem RELRO.
Isso impede declarar compatibilidade completa16KB: analisar/reconstruir essa dependência
e validar em ambiente16KB antes de loja/aparelhos recentes. Não editar binário nem
desativar proteção para mascarar a divergência. Não impede por si só o piloto4KB
Android antigo, mas nenhuma compatibilidade de aparelho real foi comprovada.
Critério da conferência: [Android — alinhamento e RELRO](https://developer.android.com/guide/practices/page-sizes).
Compilações encerradas; próximos passos exigem teste do terminal/firmware, assinatura
estável e provisionamento explicitamente autorizado para acesso não supervisionado.

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

## Caminho não supervisionado — pendente de firmware e homologação

Distribuir o APK pelo SUNMI DMP não comprova autorização para captura ou
controle por um aplicativo terceiro. A SUNMI documenta distribuição em grupos,
controle remoto próprio e APIs de integração; ainda confirmar na conta/firmware
quais capacidades estão disponíveis ao ZAVIX. Não confundir o controle remoto
nativo do DMP com integração já implementada no nosso protocolo.

No AOSP Android 7.1 e 8.1, o diálogo de captura possui uma opção para lembrar
a autorização concedida pelo usuário. Quando essa autorização existe, o próprio
sistema pode emitir uma nova projeção sem repetir o diálogo. É um caminho
legítimo a testar no firmware SUNMI, não uma garantia para todo Android 7+.
Não conceder AppOps por ADB/root nem reaproveitar um token de captura inválido.
Android recente tem regras diferentes, incluindo consentimento por sessão.

O perfil futuro deverá ser opcional, provisionado explicitamente, com credencial
individual protegida, revogação e registro de acesso. Preservar o perfil assistido.
Validar reinício, encerramento do processo, reconexão e revogação antes de
anunciar operação sem operador. A inicialização JNI direta também deverá aplicar
o perfil Android antes de iniciar o servidor, não depender apenas do Flutter.
O certificado de desenvolvimento efêmero do piloto não serve para distribuição
em lote: reinstalar pode perder permissões. Definir assinatura estável protegida
antes do provisionamento permanente. Não distribuir na frota nesta etapa.

Fontes: [SUNMI DMP](https://www.sunmi.com/en/partner/),
[diálogo AOSP 7.1](https://android.googlesource.com/platform/frameworks/base/+/android-7.1.2_r39/packages/SystemUI/src/com/android/systemui/media/MediaProjectionPermissionActivity.java),
[diálogo AOSP 8.1](https://android.googlesource.com/platform/frameworks/base/+/android-8.1.0_r81/packages/SystemUI/src/com/android/systemui/media/MediaProjectionPermissionActivity.java),
[MediaProjection atual](https://developer.android.com/media/grow/media-projection).

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
Nessa execução, o cliente Rust ARM64 compilou; a avaliação Gradle falhou ao
resolver `productFlavors.store.signingConfig`. A configuração de assinatura foi
movida para o bloco do flavor `store`, sem mudar a chave nem o perfil de piloto.
Nova compilação necessária para confirmar a correção. O proprietário informou
dificuldade de login SUNMI; consultar o portal mais tarde, sem insistir no acesso.
Na execução seguinte `38330127619` (fonte `643d18d`), a avaliação Gradle
passou e ARM64 avançou até R8/lint, mas falhou com `Java heap space`.
O workflow exclusivo Android agora reserva heap de 4 GB e limita a dois workers
nesse passo, sem mudar `gradle.properties`, desativar lint/R8 ou afetar o build
Windows. A próxima execução ainda precisa comprovar o APK final.
Na execução `38332085902` (fonte `6462401`), ARM64 falhou no download do NDK
r28c (`aborted`, após as tentativas da action), antes de compilar. ARMv7 passou
pelo download e estava compilando o cliente nativo. Uma tentativa de reexecutar
somente o job ARM64 foi recusada pelo GitHub enquanto a execução seguia ativa;
aguardar o resultado ARMv7 e repetir somente o job necessário, sem mudar NDK,
desabilitar verificações ou iniciar execução duplicada.

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
