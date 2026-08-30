import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:golden_toolkit/golden_toolkit.dart';

void main() {
  group('DsmTextField golden', () {
    testGoldens('renders resting, helper, error, and disabled states', (
      WidgetTester tester,
    ) async {
      final GoldenBuilder builder = GoldenBuilder.column(
        wrap: (Widget child) =>
            Padding(padding: const EdgeInsets.all(8), child: child),
      );

      builder
        ..addScenario(
          'resting with placeholder',
          const DsmTextField(label: 'Email', placeholder: 'you@example.com'),
        )
        ..addScenario(
          'with helper text',
          const DsmTextField(label: 'Username', helperText: 'Must be unique'),
        )
        ..addScenario(
          'with error',
          const DsmTextField(
            label: 'Username',
            errorText: 'Username is already taken',
          ),
        )
        ..addScenario(
          'disabled',
          const DsmTextField(
              label: 'Locked field',
              enabled: false,
              placeholder: 'Cannot edit'),
        )
        ..addScenario(
          'with leading and trailing icons',
          const DsmTextField(
            label: 'Search',
            placeholder: 'Search components...',
            leadingIcon: Icons.search,
            trailingIcon: Icons.clear,
          ),
        );

      await tester.pumpWidgetBuilder(
        builder.build(),
        wrapper: materialAppWrapper(theme: DsmTheme.light()),
        surfaceSize: const Size(400, 1100),
      );

      await screenMatchesGolden(tester, 'dsm_text_field_states');
    });
  });
}
