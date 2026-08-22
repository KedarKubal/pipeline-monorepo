import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import 'package:widgetbook/widgetbook.dart';

/// Use case tree for [DsmButton], registered under Components > Button.
final List<WidgetbookNode> buttonUseCases = <WidgetbookNode>[
  WidgetbookUseCase(
    name: 'Playground',
    builder: (BuildContext context) {
      final DsmButtonVariant variant =
          context.knobs.object.dropdown<DsmButtonVariant>(
        label: 'Variant',
        options: DsmButtonVariant.values,
        labelBuilder: (DsmButtonVariant v) => v.name,
      );
      final DsmButtonSize size = context.knobs.object.dropdown<DsmButtonSize>(
        label: 'Size',
        options: DsmButtonSize.values,
        labelBuilder: (DsmButtonSize s) => s.name,
      );
      final String label =
          context.knobs.string(label: 'Label', initialValue: 'Continue');
      final bool isLoading =
          context.knobs.boolean(label: 'Loading', initialValue: false);
      final bool isDisabled =
          context.knobs.boolean(label: 'Disabled', initialValue: false);
      final bool isExpanded =
          context.knobs.boolean(label: 'Expanded', initialValue: false);
      final bool showLeadingIcon =
          context.knobs.boolean(label: 'Leading icon', initialValue: false);
      final bool showTrailingIcon =
          context.knobs.boolean(label: 'Trailing icon', initialValue: false);

      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: DsmButton(
            label: label,
            variant: variant,
            size: size,
            isLoading: isLoading,
            isExpanded: isExpanded,
            leadingIcon: showLeadingIcon ? Icons.download : null,
            trailingIcon: showTrailingIcon ? Icons.chevron_right : null,
            onPressed: isDisabled ? null : () {},
          ),
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
        children: DsmButtonVariant.values
            .map(
              (DsmButtonVariant v) =>
                  DsmButton(label: v.name, variant: v, onPressed: () {}),
            )
            .toList(),
      ),
    ),
  ),
  WidgetbookUseCase(
    name: 'All sizes',
    builder: (BuildContext context) => Center(
      child: Wrap(
        spacing: 12,
        runSpacing: 12,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: DsmButtonSize.values
            .map((DsmButtonSize s) =>
                DsmButton(label: s.name, size: s, onPressed: () {}))
            .toList(),
      ),
    ),
  ),
];
