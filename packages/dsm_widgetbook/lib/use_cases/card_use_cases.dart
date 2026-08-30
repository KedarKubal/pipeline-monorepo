import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import 'package:widgetbook/widgetbook.dart';

/// Use case tree for [DsmCard], registered under Components > Card.
final List<WidgetbookNode> cardUseCases = <WidgetbookNode>[
  WidgetbookUseCase(
    name: 'Playground',
    builder: (BuildContext context) {
      final DsmCardVariant variant =
          context.knobs.object.dropdown<DsmCardVariant>(
        label: 'Variant',
        options: DsmCardVariant.values,
        labelBuilder: (DsmCardVariant v) => v.name,
      );
      final bool tappable =
          context.knobs.boolean(label: 'Tappable', initialValue: false);

      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: SizedBox(
            width: 280,
            child: DsmCard(
              variant: variant,
              onTap: tappable ? () {} : null,
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  Text('Card title',
                      style:
                          TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                  SizedBox(height: 8),
                  Text(
                      'Supporting copy that describes the card content in more detail.'),
                ],
              ),
            ),
          ),
        ),
      );
    },
  ),
  WidgetbookUseCase(
    name: 'All variants',
    builder: (BuildContext context) => Center(
      child: Wrap(
        spacing: 16,
        runSpacing: 16,
        children: DsmCardVariant.values
            .map(
              (DsmCardVariant v) => SizedBox(
                width: 220,
                child: DsmCard(variant: v, child: Text(v.name)),
              ),
            )
            .toList(),
      ),
    ),
  ),
];
