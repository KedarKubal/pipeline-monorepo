import 'package:dsm_tokens/dsm_tokens.dart';
import 'package:flutter/material.dart';

import '../dsm_theme.dart';

/// Elevation/border treatment for a [DsmCard].
enum DsmCardVariant {
  /// Flat surface with a hairline border, no shadow. Default — works well
  /// on any background.
  outlined,

  /// Flat surface with a drop shadow, no border.
  elevated,

  /// Tinted background using the surfaceVariant token, no border or shadow.
  filled,
}

/// A container surface with consistent padding, corner radius, and optional
/// tap interaction (for card-as-button use cases like list items).
///
/// ```dart
/// DsmCard(
///   variant: DsmCardVariant.elevated,
///   onTap: () => openDetails(),
///   child: Text('Card content'),
/// )
/// ```
class DsmCard extends StatelessWidget {
  const DsmCard({
    required this.child,
    super.key,
    this.variant = DsmCardVariant.outlined,
    this.padding = const EdgeInsets.all(DsmSpacing.lg),
    this.onTap,
    this.semanticsLabel,
  });

  final Widget child;
  final DsmCardVariant variant;
  final EdgeInsetsGeometry padding;

  /// If provided, the card becomes tappable with a ripple/hover affordance.
  final VoidCallback? onTap;
  final String? semanticsLabel;

  @override
  Widget build(BuildContext context) {
    final DsmColors colors = context.dsmColors;

    final BoxDecoration decoration = switch (variant) {
      DsmCardVariant.outlined => BoxDecoration(
          color: colors.background,
          borderRadius: BorderRadius.circular(DsmRadius.lg),
          border: Border.all(color: colors.border, width: DsmBorderWidth.thin),
        ),
      DsmCardVariant.elevated => BoxDecoration(
          color: colors.background,
          borderRadius: BorderRadius.circular(DsmRadius.lg),
          boxShadow: <BoxShadow>[
            BoxShadow(
              color: colors.onSurface.withValues(alpha: 0.08),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
      DsmCardVariant.filled => BoxDecoration(
          color: colors.surfaceVariant,
          borderRadius: BorderRadius.circular(DsmRadius.lg),
        ),
    };

    final Widget content = Container(
      padding: padding,
      decoration: decoration,
      child: child,
    );

    if (onTap == null) return content;

    return Semantics(
      button: true,
      label: semanticsLabel,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(DsmRadius.lg),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(DsmRadius.lg),
          child: content,
        ),
      ),
    );
  }
}
