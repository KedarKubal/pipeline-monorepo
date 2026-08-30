import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:golden_toolkit/golden_toolkit.dart';

void main() {
  group('DsmButton golden', () {
    testGoldens('renders every variant x size combination',
        (WidgetTester tester) async {
      final GoldenBuilder builder = GoldenBuilder.grid(
        columns: DsmButtonSize.values.length,
        widthToHeightRatio: 3,
      );

      for (final DsmButtonVariant variant in DsmButtonVariant.values) {
        for (final DsmButtonSize size in DsmButtonSize.values) {
          builder.addScenario(
            '${variant.name} / ${size.name}',
            DsmButton(
              label: 'Continue',
              onPressed: () {},
              variant: variant,
              size: size,
            ),
          );
        }
      }

      await tester.pumpWidgetBuilder(
        builder.build(),
        wrapper: materialAppWrapper(theme: DsmTheme.light()),
        surfaceSize: const Size(900, 700),
      );

      await screenMatchesGolden(tester, 'dsm_button_variants_sizes');
    });

    testGoldens('renders disabled and loading states',
        (WidgetTester tester) async {
      final GoldenBuilder builder = GoldenBuilder.column(
        wrap: (Widget child) =>
            Padding(padding: const EdgeInsets.all(8), child: child),
      );

      builder
        ..addScenario(
            'disabled', const DsmButton(label: 'Disabled', onPressed: null))
        ..addScenario(
          'loading',
          DsmButton(label: 'Loading', onPressed: () {}, isLoading: true),
        )
        ..addScenario(
          'expanded',
          DsmButton(label: 'Full width', onPressed: () {}, isExpanded: true),
        )
        ..addScenario(
          'with icons',
          DsmButton(
            label: 'Download',
            onPressed: () {},
            leadingIcon: Icons.download,
            trailingIcon: Icons.chevron_right,
          ),
        );

      await tester.pumpWidgetBuilder(
        builder.build(),
        wrapper: materialAppWrapper(theme: DsmTheme.light()),
        surfaceSize: const Size(400, 500),
      );

      await screenMatchesGolden(
        tester,
        'dsm_button_states',
        customPump: (WidgetTester tester) =>
            tester.pump(const Duration(milliseconds: 100)),
      );
    });

    testGoldens('renders correctly in dark theme', (WidgetTester tester) async {
      final GoldenBuilder builder = GoldenBuilder.column();

      for (final DsmButtonVariant variant in DsmButtonVariant.values) {
        builder.addScenario(variant.name,
            DsmButton(label: variant.name, onPressed: () {}, variant: variant));
      }

      await tester.pumpWidgetBuilder(
        builder.build(),
        wrapper: materialAppWrapper(theme: DsmTheme.dark()),
        surfaceSize: const Size(400, 500),
      );

      await screenMatchesGolden(tester, 'dsm_button_dark_theme');
    });
  });
}
