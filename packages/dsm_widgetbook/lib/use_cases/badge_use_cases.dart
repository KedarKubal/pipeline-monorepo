import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import 'package:widgetbook/widgetbook.dart';

/// Use case tree for [DsmBadge], registered under Components > Badge.
final List<WidgetbookNode> badgeUseCases = <WidgetbookNode>[
  WidgetbookUseCase(
    name: 'Playground',
    builder: (BuildContext context) {
      final DsmBadgeVariant variant =
          context.knobs.object.dropdown<DsmBadgeVariant>(
        label: 'Variant',
        options: DsmBadgeVariant.values,
        labelBuilder: (DsmBadgeVariant v) => v.name,
      );
      final DsmBadgeSize size = context.knobs.object.dropdown<DsmBadgeSize>(
        label: 'Size',
        options: DsmBadgeSize.values,
        labelBuilder: (DsmBadgeSize s) => s.name,
      );
      final String label =
          context.knobs.string(label: 'Label', initialValue: 'Active');
      final bool showIcon =
          context.knobs.boolean(label: 'Leading icon', initialValue: false);

      return Center(
        child: DsmBadge(
          label: label,
          variant: variant,
          size: size,
          leadingIcon: showIcon ? Icons.check_circle : null,
        ),
      );
    },
  ),
  WidgetbookUseCase(
    name: 'All variants',
    builder: (BuildContext context) => Center(
      child: Wrap(
        spacing: 12,
        runSpacing: 12,
        children: DsmBadgeVariant.values
            .map((DsmBadgeVariant v) => DsmBadge(label: v.name, variant: v))
            .toList(),
      ),
    ),
  ),
];
