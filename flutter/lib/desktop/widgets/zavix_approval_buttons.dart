import 'package:flutter/material.dart';

class ZavixApprovalButtons extends StatelessWidget {
  const ZavixApprovalButtons({
    super.key,
    required this.showAccept,
    required this.canElevate,
    required this.acceptLabel,
    required this.cancelLabel,
    required this.elevationHint,
    required this.onAccept,
    required this.onElevate,
    required this.onAccepted,
    required this.onCancel,
  });

  final bool showAccept;
  final bool canElevate;
  final String acceptLabel;
  final String cancelLabel;
  final String elevationHint;
  final VoidCallback onAccept;
  final VoidCallback onElevate;
  final VoidCallback onAccepted;
  final VoidCallback onCancel;

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      if (showAccept)
        Expanded(
          child: Padding(
            padding: const EdgeInsets.all(4),
            child: Tooltip(
              message: canElevate ? elevationHint : acceptLabel,
              child: ElevatedButton(
                onPressed: () {
                  onAccept();
                  if (canElevate) onElevate();
                  onAccepted();
                },
                child: Text(acceptLabel),
              ),
            ),
          ),
        ),
      Expanded(
        child: Padding(
          padding: const EdgeInsets.all(4),
          child: OutlinedButton(onPressed: onCancel, child: Text(cancelLabel)),
        ),
      ),
    ]);
  }
}
