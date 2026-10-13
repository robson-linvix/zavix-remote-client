import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../common.dart';
import '../../models/platform_model.dart';
import '../../models/server_model.dart';

class ZavixAndroidEnrollment {
  final ServerModel model;
  final void Function(String serial, String status) changed;
  Timer? _timer;
  bool _busy = false;
  ZavixAndroidEnrollment(this.model, this.changed);

  void start() {
    update();
    _timer = Timer.periodic(const Duration(seconds: 60), (_) => update());
  }
  void dispose() => _timer?.cancel();

  Future<Map<String, dynamic>> _request(String endpoint, String token, Map<String, dynamic> body) async {
    final client = http.Client();
    try {
      final request = http.Request('POST', Uri.parse('https://remote.zavix.app/api/android/$endpoint'));
      request.followRedirects = false;
      request.headers.addAll({'Authorization': 'Bearer $token', 'Content-Type': 'application/json'});
      request.body = jsonEncode(body);
      final response = await http.Response.fromStream(await client.send(request)).timeout(const Duration(seconds: 20));
      if (response.statusCode != 200 || response.bodyBytes.length > 4096) throw StateError('Enrollment unavailable');
      return jsonDecode(response.body) as Map<String, dynamic>;
    } finally { client.close(); }
  }

  Future<Map<String, dynamic>> _configuration() async {
    final raw = await gFFI.invokeMethodWithResult<String>('zavix_enrollment_config');
    return raw == null ? {} : jsonDecode(raw) as Map<String, dynamic>;
  }

  Future<void> update() async {
    if (_busy) return;
    _busy = true;
    try {
      final cfg = await _configuration();
      final serial = cfg['serial'] as String? ?? '';
      changed(serial, '');
      await model.fetchID();
      final packet = {'serial': serial, 'rustdesk_id': model.serverId.text.replaceAll(' ', ''),
        'model': cfg['model'], 'app_version': cfg['app_version']};
      var token = cfg['token'] as String? ?? '';
      final ticket = cfg['ticket'] as String? ?? '';
      if (token.isEmpty && ticket.isEmpty) return;
      if (token.isEmpty) {
        final enrolled = await _request('enrollment/claim', ticket, packet);
        final password = enrolled['password'] as String?;
        if (password != null && !await bind.mainSetPermanentPasswordWithResult(password: password)) {
          throw StateError('Password not saved');
        }
        model.updatePasswordModel();
        token = enrolled['token'] as String;
        await gFFI.invokeMethod('zavix_enrollment_saved', token);
      }
      await _request('enrollment/activate', token, {...packet, 'password_saved': true});
      await _request('heartbeat', token, {...packet, 'capture_ready': model.mediaOk, 'control_ready': model.inputOk});
      changed(serial, 'Vinculado ao painel ZAVIX Remote.');
    } catch (_) {
      changed('', 'Não foi possível atualizar o vínculo. Nova tentativa automática em um minuto.');
    } finally { _busy = false; }
  }

  Future<bool> syncPassword(String password) async {
    final cfg = await _configuration();
    final token = cfg['token'] as String? ?? '';
    if (token.isEmpty) return false;
    try {
      await _request('credentials', token, {'serial':cfg['serial'],
        'rustdesk_id':model.serverId.text.replaceAll(' ', ''), 'password':password});
      return true;
    } catch (_) { return false; }
  }
}
