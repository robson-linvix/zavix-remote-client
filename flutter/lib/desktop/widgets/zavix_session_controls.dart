import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import '../../common.dart';
import '../../models/model.dart';
import '../../consts.dart';

const zavixGatewayControls = bool.fromEnvironment('ZAVIX_GATEWAY');

class ZavixSessionControls extends StatefulWidget {
  final FFI ffi;
  const ZavixSessionControls({super.key, required this.ffi});

  @override
  State<ZavixSessionControls> createState() => _ZavixSessionControlsState();
}

class _ZavixSessionControlsState extends State<ZavixSessionControls> {
  final _menu = MenuController();
  int _tab = 0;
  String _mode = 'auto';
  String _resolution = 'auto';
  bool _powerBusy = false;

  @override
  void initState() {
    super.initState();
    _applyMode();
  }

  Future<void> _publish() async {
    try {
      final file = File('/config/.zavix-view-controls.json');
      final temporary = File('${file.path}.tmp');
      await temporary.writeAsString(jsonEncode({
        'schema': 1,
        'native_toolbar': true,
        'mode': _mode,
        'resolution': _resolution,
      }), flush: true);
      await temporary.rename(file.path);
    } catch (_) {
      if (mounted) showToast('Não foi possível atualizar a transmissão.');
    }
  }

  Future<void> _applyMode() async {
    await bind.sessionSetImageQuality(sessionId: widget.ffi.sessionId,
        value: _mode == 'auto' ? kRemoteImageQualityBest : kRemoteImageQualityLow);
    await _publish();
  }

  void _cycle() {
    _menu.close();
    setState(() { _tab = (_tab + 1) % 3; });
    if (_tab == 2) {
      _menu.open();
    } else {
      _mode = _tab == 0 ? 'auto' : 'economy';
      _applyMode();
    }
  }

  Future<void> _power() async {
    if (_powerBusy || !widget.ffi.ffiModel.isPeerAndroid ||
        widget.ffi.ffiModel.viewOnly || !widget.ffi.ffiModel.keyboard) return;
    setState(() { _powerBusy = true; });
    try {
      await widget.ffi.inputModel.onMobilePower();
    } finally {
      if (mounted) setState(() { _powerBusy = false; });
    }
  }

  void _setResolution(String value) {
    setState(() { _resolution = value; });
    _publish();
    _menu.close();
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: widget.ffi.ffiModel,
    builder: (context, _) {
      final android = widget.ffi.ffiModel.isPeerAndroid;
      final canPower = android && !widget.ffi.ffiModel.viewOnly &&
          widget.ffi.ffiModel.keyboard && !_powerBusy;
      final labels = ['Automático', 'Desempenho', 'Resolução'];
      return Row(mainAxisSize: MainAxisSize.min, children: [
        if (android) Tooltip(
          message: canPower ? 'Power — abrir menu de energia' : 'Power — controle indisponível',
          child: IconButton(onPressed: canPower ? _power : null,
            icon: const Icon(Icons.power_settings_new),
            style: IconButton.styleFrom(backgroundColor: const Color(0xff2e91f4),
              foregroundColor: Colors.white, disabledBackgroundColor: Colors.grey,
              minimumSize: const Size(38, 38), shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8))),
          ),
        ),
        MenuAnchor(controller: _menu, menuChildren: [
          const Padding(padding: EdgeInsets.all(12),
            child: Text('Resolução da transmissão')),
          for (final entry in const {
            'auto': 'Automática — priorizar nitidez',
            '1280x720': '1280 × 720',
            '1600x900': '1600 × 900',
            '1920x1080': '1920 × 1080',
            '2560x1440': '2560 × 1440',
          }.entries)
            MenuItemButton(onPressed: () => _setResolution(entry.key),
              leadingIcon: Icon(_resolution == entry.key ? Icons.check : Icons.monitor),
              child: Text(entry.value)),
        ], builder: (context, controller, child) => Tooltip(
          message: 'Alternar Automático, Desempenho e Resolução',
          child: TextButton.icon(onPressed: _cycle,
            icon: Icon(_tab == 2 ? Icons.aspect_ratio : Icons.tune, size: 20),
            label: Text(labels[_tab]),
            style: TextButton.styleFrom(backgroundColor: const Color(0xff2e91f4),
              foregroundColor: Colors.white, minimumSize: const Size(38, 38),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
          ),
        )),
      ]);
    },
  );
}
