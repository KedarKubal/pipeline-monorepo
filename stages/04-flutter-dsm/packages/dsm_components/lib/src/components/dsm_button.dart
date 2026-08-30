import 'package:dsm_tokens/dsm_tokens.dart';
import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';

import '../dsm_theme.dart';

/// Visual treatment of a [DsmButton].
enum DsmButtonVariant {
  /// Solid fill, highest emphasis. Use for the primary action on a screen.
  primary,

  /// Outlined, medium emphasis. Use for secondary actions.
  secondary,

  /// No fill or border, lowest emphasis. Use for tertiary/inline actions.
  ghost,

  /// Solid fill using the danger color. Use for destructive actions.
  danger,
}

/// Size of a [DsmButton], controlling height, padding, and text style.
enum DsmButtonSize { small, medium, large }

/// A pressable button following DSM tokens, with built-in hover/press/focus
/// states, a loading spinner state, and optional leading/trailing icons.
///
/// ```dart
/// DsmButton(
///   label: 'Save changes',
///   onPressed: () => save(),
///   variant: DsmButtonVariant.primary,
///   leadingIcon: Icons.save,
/// )
/// ```
class DsmButton extends HookWidget {
  const DsmButton({
    required this.label,
    required this.onPressed,
    super.key,
    this.variant = DsmButtonVariant.primary,
    this.size = DsmButtonSize.medium,
    this.leadingIcon,
    this.trailingIcon,
    this.isLoading = false,
    this.isExpanded = false,
    this.semanticsLabel,
  });

  final String label;

  /// Called when the button is tapped. If `null`, the button renders in a
  /// disabled state and does not respond to input.
  final VoidCallback? onPressed;
  final DsmButtonVariant variant;
  final DsmButtonSize size;
  final IconData? leadingIcon;
  final IconData? trailingIcon;

  /// Shows a spinner in place of the label and suppresses taps, without
  /// changing the button's layout size (avoids content jump).
  final bool isLoading;

  /// If true, the button fills the width of its parent.
  final bool isExpanded;

  /// Overrides the label as the accessibility announcement, e.g. to add
  /// context a sighted user gets from surrounding UI.
  final String? semanticsLabel;

  bool get _isDisabled => onPressed == null || isLoading;

  @override
  Widget build(BuildContext context) {
    final DsmColors colors = context.dsmColors;
    final ValueNotifier<bool> hovered = useState(false);
    final ValueNotifier<bool> pressed = useState(false);

    final _ButtonPalette palette =
        _resolvePalette(variant, colors, _isDisabled);
    final _ButtonMetrics metrics = _resolveMetrics(size);

    final Color background = pressed.value
        ? palette.pressed
        : hovered.value
            ? palette.hover
            : palette.background;

    Widget content = _ButtonContent(
      label: label,
      textStyle: metrics.textStyle(context).copyWith(color: palette.foreground),
      leadingIcon: leadingIcon,
      trailingIcon: trailingIcon,
      iconColor: palette.foreground,
      iconSize: metrics.iconSize,
      isLoading: isLoading,
      spinnerColor: palette.foreground,
    );

    Widget button = AnimatedContainer(
      duration: DsmMotion.fast,
      height: metrics.height,
      width: isExpanded ? double.infinity : null,
      padding: metrics.padding,
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(DsmRadius.md),
        border: palette.border != null
            ? Border.all(color: palette.border!, width: DsmBorderWidth.thin)
            : null,
      ),
      alignment: Alignment.center,
      child: content,
    );

    return MouseRegion(
      cursor:
          _isDisabled ? SystemMouseCursors.forbidden : SystemMouseCursors.click,
      onEnter: (_) => hovered.value = true,
      onExit: (_) => hovered.value = false,
      child: GestureDetector(
        onTapDown: _isDisabled ? null : (_) => pressed.value = true,
        onTapUp: _isDisabled ? null : (_) => pressed.value = false,
        onTapCancel: _isDisabled ? null : () => pressed.value = false,
        onTap: _isDisabled ? null : onPressed,
        child: Semantics(
          button: true,
          container: true, // <-- add this line
          excludeSemantics: true,
          enabled: !_isDisabled,
          label: semanticsLabel ?? label,
          focusable: !_isDisabled,
          onTap: _isDisabled ? null : onPressed,
          child: Focus(
            child: Builder(
              builder: (BuildContext context) {
                final bool hasFocus = Focus.of(context).hasFocus;
                return AnimatedContainer(
                  duration: DsmMotion.fast,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(DsmRadius.md + 2),
                    border: hasFocus
                        ? Border.all(
                            color: colors.focusRing,
                            width: DsmBorderWidth.thick)
                        : null,
                  ),
                  padding: hasFocus ? const EdgeInsets.all(2) : EdgeInsets.zero,
                  child: button,
                );
              },
            ),
          ),
        ),
      ),
    );
  }

  _ButtonPalette _resolvePalette(
      DsmButtonVariant variant, DsmColors colors, bool disabled) {
    if (disabled) {
      return _ButtonPalette(
        background: colors.disabled,
        hover: colors.disabled,
        pressed: colors.disabled,
        foreground: colors.onDisabled,
        border: variant == DsmButtonVariant.secondary ? colors.border : null,
      );
    }

    switch (variant) {
      case DsmButtonVariant.primary:
        return _ButtonPalette(
          background: colors.primary,
          hover: colors.primaryHover,
          pressed: colors.primaryPressed,
          foreground: colors.onPrimary,
          border: null,
        );
      case DsmButtonVariant.secondary:
        return _ButtonPalette(
          background: colors.surface,
          hover: colors.surfaceVariant,
          pressed: colors.surfaceVariant,
          foreground: colors.onSurface,
          border: colors.border,
        );
      case DsmButtonVariant.ghost:
        return _ButtonPalette(
          background: Colors.transparent,
          hover: colors.surfaceVariant,
          pressed: colors.surfaceVariant,
          foreground: colors.onSurface,
          border: null,
        );
      case DsmButtonVariant.danger:
        return _ButtonPalette(
          background: colors.danger,
          hover: colors.danger.withValues(alpha: 0.9),
          pressed: colors.danger.withValues(alpha: 0.8),
          foreground: colors.onDanger,
          border: null,
        );
    }
  }

  _ButtonMetrics _resolveMetrics(DsmButtonSize size) {
    switch (size) {
      case DsmButtonSize.small:
        return _ButtonMetrics(
          height: 32,
          padding: const EdgeInsets.symmetric(horizontal: DsmSpacing.md),
          iconSize: 16,
          textStyle: (BuildContext c) => c.dsmTypography.labelMedium,
        );
      case DsmButtonSize.medium:
        return _ButtonMetrics(
          height: 40,
          padding: const EdgeInsets.symmetric(horizontal: DsmSpacing.lg),
          iconSize: 18,
          textStyle: (BuildContext c) => c.dsmTypography.labelLarge,
        );
      case DsmButtonSize.large:
        return _ButtonMetrics(
          height: 48,
          padding: const EdgeInsets.symmetric(horizontal: DsmSpacing.xl),
          iconSize: 20,
          textStyle: (BuildContext c) => c.dsmTypography.titleSmall,
        );
    }
  }
}

class _ButtonPalette {
  const _ButtonPalette({
    required this.background,
    required this.hover,
    required this.pressed,
    required this.foreground,
    required this.border,
  });

  final Color background;
  final Color hover;
  final Color pressed;
  final Color foreground;
  final Color? border;
}

class _ButtonMetrics {
  const _ButtonMetrics({
    required this.height,
    required this.padding,
    required this.iconSize,
    required this.textStyle,
  });

  final double height;
  final EdgeInsets padding;
  final double iconSize;
  final TextStyle Function(BuildContext) textStyle;
}

class _ButtonContent extends StatelessWidget {
  const _ButtonContent({
    required this.label,
    required this.textStyle,
    required this.iconColor,
    required this.iconSize,
    required this.isLoading,
    required this.spinnerColor,
    this.leadingIcon,
    this.trailingIcon,
  });

  final String label;
  final TextStyle textStyle;
  final IconData? leadingIcon;
  final IconData? trailingIcon;
  final Color iconColor;
  final double iconSize;
  final bool isLoading;
  final Color spinnerColor;

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return SizedBox(
        height: iconSize,
        width: iconSize,
        child: CircularProgressIndicator(strokeWidth: 2, color: spinnerColor),
      );
    }

    final List<Widget> children = <Widget>[
      if (leadingIcon != null) ...<Widget>[
        Icon(leadingIcon, size: iconSize, color: iconColor),
        const SizedBox(width: DsmSpacing.sm),
      ],
      Flexible(
        child: Text(
          label,
          style: textStyle,
          overflow: TextOverflow.ellipsis,
          maxLines: 1,
        ),
      ),
      if (trailingIcon != null) ...<Widget>[
        const SizedBox(width: DsmSpacing.sm),
        Icon(trailingIcon, size: iconSize, color: iconColor),
      ],
    ];

    return Row(mainAxisSize: MainAxisSize.min, children: children);
  }
}
