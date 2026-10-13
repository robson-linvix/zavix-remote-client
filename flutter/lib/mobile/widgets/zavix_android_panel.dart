import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../../common.dart';
import '../../models/platform_model.dart';
import '../../models/server_model.dart';
import 'zavix_android_enrollment.dart';

bool get isZavixManagedAndroid => isAndroid &&
    bind.mainGetBuildinOption(key: 'zavix-android-managed') == 'Y';

class ZavixAndroidPanel extends StatefulWidget {
  final ServerModel model;
  const ZavixAndroidPanel({super.key, required this.model});
  @override
  State<ZavixAndroidPanel> createState() => _ZavixAndroidPanelState();
}

class _ZavixAndroidPanelState extends State<ZavixAndroidPanel> {
  bool _sending = false;
  String _message = '';
  String _serial = '', _enrollmentMessage = '';
  late final ZavixAndroidEnrollment _enrollment;

  @override
  void initState() {
    super.initState();
    _enrollment = ZavixAndroidEnrollment(widget.model, (serial, status) {
      if (mounted) setState(() {
        if (serial.isNotEmpty) _serial = serial;
        _enrollmentMessage = status;
      });
    });
    _enrollment.start();
  }

  @override
  void dispose() { _enrollment.dispose(); super.dispose(); }

  Future<void> _setPassword() async {
    final password = TextEditingController();
    final confirmation = TextEditingController();
    final accepted = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      title: const Text('Senha individual do equipamento'),
      content: Column(mainAxisSize: MainAxisSize.min, children: [
        const Text('Use pelo menos 12 caracteres. Cadastre a mesma senha no dispositivo do portal para permitir acesso não supervisionado.'),
        TextField(controller: password, obscureText: true, enableSuggestions: false, autocorrect: false,
          decoration: const InputDecoration(labelText: 'Senha')),
        TextField(controller: confirmation, obscureText: true, enableSuggestions: false, autocorrect: false,
          decoration: const InputDecoration(labelText: 'Confirmar senha')),
      ]),
      actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
        FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Salvar'))],
    ));
    if (accepted == true) {
      if (password.text.length < 12 || password.text != confirmation.text) {
        if (mounted) setState(() { _message = 'Use pelo menos 12 caracteres e confirme a mesma senha.'; });
      } else {
        final ok = await bind.mainSetPermanentPasswordWithResult(password: password.text);
        final synced = ok && await _enrollment.syncPassword(password.text);
        widget.model.updatePasswordModel();
        if (mounted) setState(() { _message = ok ? (synced ? 'Senha salva e sincronizada com o painel.' : 'Senha salva neste equipamento. Atualize também o portal.') : 'Não foi possível salvar a senha.'; });
      }
    }
    password.clear();confirmation.clear();password.dispose();confirmation.dispose();
  }

  Future<void> _viewDiagnostics() async {
    final snapshot = await gFFI.invokeMethodWithResult<String>('zavix_diagnostics');
    if (!mounted || snapshot == null) return;
    await showDialog<void>(context: context, builder: (context) => AlertDialog(
      title: const Text('Diagnóstico local'),
      content: SizedBox(width: 600, height: 400, child: SingleChildScrollView(
        child: SelectableText(const JsonEncoder.withIndent('  ').convert(jsonDecode(snapshot))))),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Fechar'))],
    ));
  }

  Future<void> _sendDiagnostics() async {
    final password = TextEditingController();
    final cfgRaw = await gFFI.invokeMethodWithResult<String>('zavix_enrollment_config');
    final agentToken = cfgRaw == null ? '' : (jsonDecode(cfgRaw)['token'] as String? ?? '');
    if (!mounted) { password.dispose(); return; }
    final accepted = agentToken.isNotEmpty || (await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      title: const Text('Enviar diagnóstico'),
      content: Column(mainAxisSize: MainAxisSize.min, children: [
        const Text('Informe a senha de acesso cadastrada para este equipamento no portal. Os logs serão enviados a robson@linvix.com.br.'),
        TextField(controller: password, obscureText: true, enableSuggestions: false,
          autocorrect: false, decoration: const InputDecoration(labelText: 'Senha do equipamento')),
      ]),
      actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
        FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Enviar'))],
    ))) == true;
    if (!accepted || (agentToken.isEmpty && password.text.isEmpty)) { password.clear(); password.dispose(); return; }
    if (!mounted) { password.clear(); password.dispose(); return; }
    setState(() { _sending = true; _message = ''; });
    final client = http.Client();
    try {
      await widget.model.fetchID();
      final snapshot = await gFFI.invokeMethodWithResult<String>('zavix_diagnostics');
      final request = http.Request('POST', Uri.parse('https://remote.zavix.app/api/android/diagnostics'));
      request.followRedirects = false;
      request.headers['Content-Type'] = 'application/json';
      request.headers['Authorization'] = agentToken.isNotEmpty ? 'Bearer $agentToken' : 'Basic ${base64Encode(utf8.encode('${widget.model.serverId.text.replaceAll(' ', '')}:${password.text}'))}';
      if (snapshot == null) throw StateError("Diagnostic unavailable");
      request.body = snapshot;
      final response = await client.send(request).timeout(const Duration(seconds: 25));
      await response.stream.drain<void>();
      final ok = response.statusCode == 200;
      await gFFI.invokeMethod('zavix_diagnostic_event', ok ? 'diagnostics_sent' : 'diagnostics_failed');
      if (mounted) setState(() { _message = ok ? 'Logs encaminhados para robson@linvix.com.br.' :
        response.statusCode == 401 ? 'Cadastre o ID e a mesma senha no portal com acesso não supervisionado autorizado.' :
        response.statusCode == 429 ? 'Aguarde alguns minutos antes de reenviar.' : 'Envio indisponível. Os logs permanecem no aparelho.'; });
    } catch (_) {
      await gFFI.invokeMethod('zavix_diagnostic_event', 'diagnostics_failed');
      if (mounted) setState(() { _message = 'Não foi possível enviar. Os logs permanecem no aparelho.'; });
    } finally {
      client.close(); password.clear(); password.dispose();
      if (mounted) setState(() { _sending = false; });
    }
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<String>(
    future: bind.mainGetCommon(key: 'permanent-password-set'),
    builder: (context, snapshot) {
      final passwordSet = snapshot.data == 'true';
      return Padding(padding: const EdgeInsets.all(12), child: Card(child: Padding(
        padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(widget.model.approveMode == 'password' ? 'Acesso não supervisionado' : 'Acesso assistido',
            style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text('ID do equipamento: ${widget.model.serverId.text}'),
          if (_serial.isNotEmpty) Text('Número de série: $_serial'),
          if (_enrollmentMessage.isNotEmpty) Text(_enrollmentMessage),
          Text(passwordSet ? 'Senha individual configurada.' : 'Defina uma senha exclusiva para este equipamento antes do primeiro acesso.'),
          Text('Captura: ${widget.model.mediaOk ? "disponível" : "permissão pendente"}'),
          Text('Controle: ${widget.model.inputOk ? "habilitado" : "permissão pendente"}'),
          const SizedBox(height: 12),
          Wrap(spacing: 8, runSpacing: 8, children: [
            OutlinedButton(onPressed: _setPassword, child: Text(passwordSet ? 'Alterar senha' : 'Definir senha')),
            OutlinedButton(onPressed: passwordSet && widget.model.mediaOk && widget.model.inputOk ? () async {
              final ok = await gFFI.invokeMethod('zavix_enable_boot');
              if (mounted) setState(() { _message = ok == true ?
                'Retorno após reinício habilitado. Teste a autorização lembrada neste SUNMI.' : 'Configure as permissões antes de habilitar o retorno.'; });
            } : null, child: const Text('Habilitar retorno após reinício')),
            OutlinedButton(onPressed: _viewDiagnostics, child: const Text('Ver logs')),
            FilledButton(onPressed: _sending ? null : _sendDiagnostics,
              child: Text(_sending ? 'Enviando…' : 'Enviar logs')),
          ]),
          if (_message.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_message)),
        ]),
      )));
    },
  );
}
