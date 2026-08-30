import 'package:dsm_tokens/dsm_tokens.dart';
import 'package:flutter/material.dart';

import '../dsm_theme.dart';

/// Semantic color treatment for a [DsmBadge].
enum DsmBadgeVariant { neutral, primary, success, warning, danger }

/// Size of a [DsmBadge].
enum DsmBadgeSize { small, medium }

/// A small pill-shaped label used to display status, counts, or categories.
///
/// ```dart
/// DsmBadge(label: 'Active', variant: DsmBadgeVariant.success)
/// ```
class DsmBadge extends StatelessWidget {
  const DsmBadge({
    required this.label,
    super.key,
    this.variant = DsmBadgeVariant.neutral,
    this.size = DsmBadgeSize.medium,
    this.leadingIcon,
  });

  final String label;
  final DsmBadgeVariant variant;
  final DsmBadgeSize size;
  final IconData? leadingIcon;

  @override
  Widget build(BuildContext context) {
    final DsmColors colors = context.dsmColors;
    final (Color background, Color foreground) = switch (variant) {
      DsmBadgeVariant.neutral => (colors.surfaceVariant, colors.onSurface),
      DsmBadgeVariant.primary => (
          colors.primary.withValues(alpha: 0.12),
          colors.primary
        ),
      DsmBadgeVariant.success => (
          colors.success.withValues(alpha: 0.12),
          colors.success
        ),
      DsmBadgeVariant.warning => (
          colors.warning.withValues(alpha: 0.12),
          colors.warning
        ),
      DsmBadgeVariant.danger => (
          colors.danger.withValues(alpha: 0.12),
          colors.danger
        ),
    };

    final bool isSmall = size == DsmBadgeSize.small;
    final TextStyle textStyle = (isSmall
            ? context.dsmTypography.labelSmall
            : context.dsmTypography.labelMedium)
        .copyWith(color: foreground);

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isSmall ? DsmSpacing.sm : DsmSpacing.md,
        vertical: isSmall ? DsmSpacing.xxs : DsmSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(DsmRadius.full),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          if (leadingIcon != null) ...<Widget>[
            Icon(leadingIcon, size: isSmall ? 12 : 14, color: foreground),
            const SizedBox(width: DsmSpacing.xxs),
          ],
          Text(label, style: textStyle),
        ],
      ),
    );
  }
}
