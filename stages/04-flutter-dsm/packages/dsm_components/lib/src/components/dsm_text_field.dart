import 'package:dsm_tokens/dsm_tokens.dart';
import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';

import '../dsm_theme.dart';

/// Visual/interaction state of a [DsmTextField], derived automatically from
/// focus and [DsmTextField.errorText] unless the field is [disabled].
enum _DsmTextFieldState { resting, focused, error, disabled }

/// A labeled text input with helper/error text, optional leading/trailing
/// icons, and focus-driven border styling — the DSM equivalent of Material's
/// [TextField] wrapped with opinionated tokens.
///
/// ```dart
/// DsmTextField(
///   label: 'Email',
///   controller: emailController,
///   errorText: emailError,
///   keyboardType: TextInputType.emailAddress,
/// )
/// ```
class DsmTextField extends HookWidget {
  const DsmTextField({
    required this.label,
    super.key,
    this.controller,
    this.placeholder,
    this.helperText,
    this.errorText,
    this.leadingIcon,
    this.trailingIcon,
    this.onTrailingIconTap,
    this.obscureText = false,
    this.enabled = true,
    this.keyboardType,
    this.textInputAction,
    this.onChanged,
    this.onSubmitted,
    this.maxLines = 1,
    this.autofocus = false,
  });

  final String label;
  final TextEditingController? controller;
  final String? placeholder;

  /// Shown below the field when there is no [errorText].
  final String? helperText;

  /// Shown below the field in the danger color, replacing [helperText],
  /// and switches the field's border to the danger palette.
  final String? errorText;
  final IconData? leadingIcon;
  final IconData? trailingIcon;

  /// Called when [trailingIcon] is tapped — commonly used for a
  /// show/hide-password toggle or a clear button.
  final VoidCallback? onTrailingIconTap;
  final bool obscureText;
  final bool enabled;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final int maxLines;
  final bool autofocus;

  @override
  Widget build(BuildContext context) {
    final DsmColors colors = context.dsmColors;
    final FocusNode focusNode = useFocusNode();
    final bool hasFocus = useListenable(focusNode).hasFocus;

    final bool hasError = errorText != null && errorText!.isNotEmpty;
    final _DsmTextFieldState state = !enabled
        ? _DsmTextFieldState.disabled
        : hasError
            ? _DsmTextFieldState.error
            : hasFocus
                ? _DsmTextFieldState.focused
                : _DsmTextFieldState.resting;

    final Color borderColor = switch (state) {
      _DsmTextFieldState.resting => colors.border,
      _DsmTextFieldState.focused => colors.primary,
      _DsmTextFieldState.error => colors.danger,
      _DsmTextFieldState.disabled => colors.border,
    };

    final double borderWidth =
        state == _DsmTextFieldState.focused || state == _DsmTextFieldState.error
            ? DsmBorderWidth.thick
            : DsmBorderWidth.thin;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Text(
          label,
          style: context.dsmTypography.labelLarge.copyWith(
            color: enabled ? colors.onSurface : colors.onDisabled,
          ),
        ),
        const SizedBox(height: DsmSpacing.xs),
        AnimatedContainer(
          duration: DsmMotion.fast,
          decoration: BoxDecoration(
            color: enabled ? colors.background : colors.disabled,
            borderRadius: BorderRadius.circular(DsmRadius.md),
            border: Border.all(color: borderColor, width: borderWidth),
          ),
          child: Row(
            children: <Widget>[
              if (leadingIcon != null)
                Padding(
                  padding: const EdgeInsets.only(left: DsmSpacing.md),
                  child:
                      Icon(leadingIcon, size: 20, color: colors.onSurfaceMuted),
                ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: DsmSpacing.md,
                    vertical: DsmSpacing.sm,
                  ),
                  child: TextField(
                    controller: controller,
                    focusNode: focusNode,
                    enabled: enabled,
                    obscureText: obscureText,
                    keyboardType: keyboardType,
                    textInputAction: textInputAction,
                    onChanged: onChanged,
                    onSubmitted: onSubmitted,
                    maxLines: maxLines,
                    autofocus: autofocus,
                    style: context.dsmTypography.bodyLarge
                        .copyWith(color: colors.onSurface),
                    decoration: InputDecoration(
                      isDense: true,
                      border: InputBorder.none,
                      hintText: placeholder,
                      hintStyle: context.dsmTypography.bodyLarge.copyWith(
                        color: colors.onSurfaceMuted,
                      ),
                    ),
                  ),
                ),
              ),
              if (trailingIcon != null)
                Padding(
                  padding: const EdgeInsets.only(right: DsmSpacing.md),
                  child: GestureDetector(
                    onTap: onTrailingIconTap,
                    child: Icon(trailingIcon,
                        size: 20, color: colors.onSurfaceMuted),
                  ),
                ),
            ],
          ),
        ),
        if (hasError ||
            (helperText != null && helperText!.isNotEmpty)) ...<Widget>[
          const SizedBox(height: DsmSpacing.xs),
          Text(
            hasError ? errorText! : helperText!,
            style: context.dsmTypography.bodySmall.copyWith(
              color: hasError ? colors.danger : colors.onSurfaceMuted,
            ),
          ),
        ],
      ],
    );
  }
}
