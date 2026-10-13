import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_hbb/desktop/widgets/zavix_approval_buttons.dart';

void main() {
  Future<void> show(WidgetTester tester, List<String> actions,
      {required bool canElevate}) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: ZavixApprovalButtons(
      showAccept: true,
      canElevate: canElevate,
      acceptLabel: 'Aceitar',
      cancelLabel: 'Cancelar',
      elevationHint: 'Solicitar elevação com consentimento do Windows',
      onAccept: () => actions.add('accept'),
      onElevate: () => actions.add('elevate'),
      onAccepted: () => actions.add('minimize'),
      onCancel: () => actions.add('cancel'),
    ))));
  }

  testWidgets('one Accept requests elevation after accepting when available', (tester) async {
    final actions = <String>[];
    await show(tester, actions, canElevate: true);
    expect(find.text('Aceitar'), findsOneWidget);
    expect(find.text('Aceitar e Elevar'), findsNothing);
    await tester.tap(find.text('Aceitar'));
    expect(actions, ['accept', 'elevate', 'minimize']);
  });

  testWidgets('already elevated acceptance does not request elevation again', (tester) async {
    final actions = <String>[];
    await show(tester, actions, canElevate: false);
    await tester.tap(find.text('Aceitar'));
    expect(actions, ['accept', 'minimize']);
  });

  testWidgets('Cancel grants neither connection nor elevation', (tester) async {
    final actions = <String>[];
    await show(tester, actions, canElevate: true);
    await tester.tap(find.text('Cancelar'));
    expect(actions, ['cancel']);
  });
}
