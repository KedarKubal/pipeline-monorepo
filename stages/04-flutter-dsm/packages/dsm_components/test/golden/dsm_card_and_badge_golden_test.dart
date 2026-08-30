import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:golden_toolkit/golden_toolkit.dart';

void main() {
  group('DsmCard golden', () {
    testGoldens('renders every variant', (WidgetTester tester) async {
      final GoldenBuilder builder = GoldenBuilder.column(
        wrap: (Widget child) =>
            Padding(padding: const EdgeInsets.all(8), child: child),
      );

      for (final DsmCardVariant variant in DsmCardVariant.values) {
        builder.addScenario(
          variant.name,
          DsmCard(
            variant: variant,
            child: Text(
                '${variant.name[0].toUpperCase()}${variant.name.substring(1)} card'),
          ),
        );
      }

      await tester.pumpWidgetBuilder(
        builder.build(),
        wrapper: materialAppWrapper(theme: DsmTheme.light()),
        surfaceSize: const Size(400, 500),
      );

      await screenMatchesGolden(tester, 'dsm_card_variants');
    });
  });

  group('DsmBadge golden', () {
    testGoldens('renders every variant x size combination',
        (WidgetTester tester) async {
      final GoldenBuilder builder = GoldenBuilder.grid(
        columns: DsmBadgeSize.values.length,
        widthToHeightRatio: 3,
      );

      for (final DsmBadgeVariant variant in DsmBadgeVariant.values) {
        for (final DsmBadgeSize size in DsmBadgeSize.values) {
          builder.addScenario(
            '${variant.name} / ${size.name}',
            DsmBadge(label: variant.name, variant: variant, size: size),
          );
        }
      }

      await tester.pumpWidgetBuilder(
        builder.build(),
        wrapper: materialAppWrapper(theme: DsmTheme.light()),
        surfaceSize: const Size(700, 700),
      );

      await screenMatchesGolden(tester, 'dsm_badge_variants_sizes');
    });
  });
}
