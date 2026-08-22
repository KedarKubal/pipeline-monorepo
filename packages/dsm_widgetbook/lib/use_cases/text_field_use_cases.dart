import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import 'package:widgetbook/widgetbook.dart';

/// Use case tree for [DsmTextField], registered under Components > TextField.
final List<WidgetbookNode> textFieldUseCases = <WidgetbookNode>[
  WidgetbookUseCase(
    name: 'Playground',
    builder: (BuildContext context) {
      final String label =
          context.knobs.string(label: 'Label', initialValue: 'Email');
      final String placeholder = context.knobs.string(
        label: 'Placeholder',
        initialValue: 'you@example.com',
      );
      final String helperText =
          context.knobs.string(label: 'Helper text', initialValue: '');
      final String errorText =
          context.knobs.string(label: 'Error text', initialValue: '');
      final bool enabled =
          context.knobs.boolean(label: 'Enabled', initialValue: true);
      final bool obscureText =
          context.knobs.boolean(label: 'Obscure text', initialValue: false);
      final bool showLeadingIcon =
          context.knobs.boolean(label: 'Leading icon', initialValue: false);

      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: SizedBox(
            width: 320,
            child: DsmTextField(
              label: label,
              placeholder: placeholder,
              helperText: helperText.isEmpty ? null : helperText,
              errorText: errorText.isEmpty ? null : errorText,
              enabled: enabled,
              obscureText: obscureText,
              leadingIcon: showLeadingIcon ? Icons.search : null,
            ),
          ),
        ),
      );
    },
  ),
  WidgetbookUseCase(
    name: 'States',
    builder: (BuildContext context) => Center(
      child: SizedBox(
        width: 320,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: const <Widget>[
            DsmTextField(label: 'Resting', placeholder: 'Type here...'),
            SizedBox(height: 24),
            DsmTextField(
                label: 'With helper', helperText: 'We will never share this'),
            SizedBox(height: 24),
            DsmTextField(
                label: 'With error', errorText: 'This field is required'),
            SizedBox(height: 24),
            DsmTextField(
                label: 'Disabled', enabled: false, placeholder: 'Cannot edit'),
          ],
        ),
      ),
    ),
  ),
];
