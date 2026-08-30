import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import 'package:widgetbook/widgetbook.dart';
import 'use_cases/badge_use_cases.dart';
import 'use_cases/button_use_cases.dart';
import 'use_cases/card_use_cases.dart';
import 'use_cases/insights_use_cases.dart';
import 'use_cases/text_field_use_cases.dart';

void main() {
  runApp(const DsmWidgetbookApp());
}

/// Widgetbook catalog entrypoint. Run with:
/// ```
/// melos run widgetbook
/// ```
/// or directly:
/// ```
/// cd packages/dsm_widgetbook && flutter run -d chrome
/// ```
///
/// Use cases are defined manually under lib/use_cases/ rather than via
/// @widgetbook.UseCase codegen, so the catalog is buildable without first
/// running build_runner. Migrate to annotation-based generation later by
/// adding @widgetbook.UseCase annotations and running:
/// `dart run build_runner build -d`
class DsmWidgetbookApp extends StatelessWidget {
  const DsmWidgetbookApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Widgetbook.material(
      addons: <WidgetbookAddon<dynamic>>[
        ThemeAddon<ThemeData>(
          themes: <WidgetbookTheme<ThemeData>>[
            WidgetbookTheme(name: 'Light', data: DsmTheme.light()),
            WidgetbookTheme(name: 'Dark', data: DsmTheme.dark()),
          ],
          themeBuilder: (BuildContext context, ThemeData theme, Widget child) {
            return Theme(data: theme, child: child);
          },
        ),
        ViewportAddon(<ViewportData>[
          Viewports.none,
          IosViewports.iPhone13,
          AndroidViewports.samsungGalaxyNote20,
          MacosViewports.macbookPro,
        ]),
        TextScaleAddon(min: 0.8, max: 2.0),
        GridAddon(),
        InspectorAddon(),
      ],
      directories: <WidgetbookNode>[
        WidgetbookFolder(
          name: 'Components',
          children: <WidgetbookNode>[
            WidgetbookFolder(name: 'Button', children: buttonUseCases),
            WidgetbookFolder(name: 'TextField', children: textFieldUseCases),
            WidgetbookFolder(name: 'Card', children: cardUseCases),
            WidgetbookFolder(name: 'Badge', children: badgeUseCases),
          ],
        ),
        WidgetbookFolder(
          name: 'Pipeline Insights',
          children: insightsUseCases,
        ),
      ],
    );
  }
}
