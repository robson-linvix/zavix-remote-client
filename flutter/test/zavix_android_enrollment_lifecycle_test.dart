import 'package:flutter_hbb/mobile/widgets/zavix_android_enrollment.dart';
import 'package:flutter_hbb/models/server_model.dart';
import 'package:flutter_test/flutter_test.dart';

class _UnusedServerModel implements ServerModel {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _CountingEnrollment extends ZavixAndroidEnrollment {
  int updates = 0;
  _CountingEnrollment() : super(_UnusedServerModel());

  @override
  Future<void> update() async { updates++; }
}

void main() {
  testWidgets('presence starts without a panel and continues after leaving it',
      (tester) async {
    final enrollment = _CountingEnrollment()..start();
    expect(enrollment.updates, 1);
    void panelListener() {}
    enrollment.addListener(panelListener);
    enrollment.removeListener(panelListener);
    await tester.pump(const Duration(seconds: 60));
    expect(enrollment.updates, 2);
    enrollment.dispose();
    await tester.pump(const Duration(seconds: 60));
    expect(enrollment.updates, 2);
  });

  testWidgets('repeated startup does not create duplicate presence timers',
      (tester) async {
    final enrollment = _CountingEnrollment()..start()..start();
    expect(enrollment.updates, 1);
    await tester.pump(const Duration(seconds: 60));
    expect(enrollment.updates, 2);
    enrollment.dispose();
  });
}
