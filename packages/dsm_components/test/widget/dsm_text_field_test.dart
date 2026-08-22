import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _wrap(Widget child) {
  return MaterialApp(
    theme: DsmTheme.light(),
    home: Scaffold(body: Center(child: child)),
  );
}

void main() {
  group('DsmTextField', () {
    testWidgets('renders label and placeholder', (WidgetTester tester) async {
      await tester.pumpWidget(
        _wrap(
            const DsmTextField(label: 'Email', placeholder: 'you@example.com')),
      );

      expect(find.text('Email'), findsOneWidget);
      expect(find.text('you@example.com'), findsOneWidget);
    });

    testWidgets('calls onChanged as the user types',
        (WidgetTester tester) async {
      String? lastValue;
      await tester.pumpWidget(
        _wrap(DsmTextField(
            label: 'Name', onChanged: (String v) => lastValue = v)),
      );

      await tester.enterText(find.byType(TextField), 'Ada Lovelace');

      expect(lastValue, 'Ada Lovelace');
    });

    testWidgets('shows helperText when no error is present',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        _wrap(const DsmTextField(
            label: 'Username', helperText: 'Must be unique')),
      );

      expect(find.text('Must be unique'), findsOneWidget);
    });

    testWidgets('shows errorText instead of helperText when both are provided',
        (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        _wrap(
          const DsmTextField(
            label: 'Username',
            helperText: 'Must be unique',
            errorText: 'Username is already taken',
          ),
        ),
      );

      expect(find.text('Username is already taken'), findsOneWidget);
      expect(find.text('Must be unique'), findsNothing);
    });

    testWidgets('respects enabled: false by disabling the underlying TextField',
        (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
          _wrap(const DsmTextField(label: 'Locked', enabled: false)));

      final TextField field = tester.widget<TextField>(find.byType(TextField));
      expect(field.enabled, isFalse);
    });

    testWidgets('populates controller text and reflects programmatic updates', (
      WidgetTester tester,
    ) async {
      final TextEditingController controller =
          TextEditingController(text: 'initial');
      await tester.pumpWidget(
          _wrap(DsmTextField(label: 'Bio', controller: controller)));

      expect(find.text('initial'), findsOneWidget);

      controller.text = 'updated';
      await tester.pump();

      expect(find.text('updated'), findsOneWidget);
      controller.dispose();
    });

    testWidgets('invokes onTrailingIconTap when the trailing icon is tapped', (
      WidgetTester tester,
    ) async {
      int tapCount = 0;
      await tester.pumpWidget(
        _wrap(
          DsmTextField(
            label: 'Password',
            obscureText: true,
            trailingIcon: Icons.visibility,
            onTrailingIconTap: () => tapCount++,
          ),
        ),
      );

      await tester.tap(find.byIcon(Icons.visibility));
      await tester.pump();

      expect(tapCount, 1);
    });
  });
}
