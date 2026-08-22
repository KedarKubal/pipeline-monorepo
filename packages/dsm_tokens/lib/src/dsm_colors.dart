import 'dart:ui' show Brightness;

import 'package:flutter/painting.dart';

/// Primitive color scale. Do not reference these directly in components —
/// use [DsmColors] semantic tokens instead so theming stays swappable.
///
/// Each scale runs 50 (lightest) -> 900 (darkest), following the common
/// Material/Tailwind convention so designers and engineers share a vocabulary.
abstract final class DsmPalette {
  // Brand blue
  static const Map<int, Color> blue = <int, Color>{
    50: Color(0xFFEFF6FF),
    100: Color(0xFFDBEAFE),
    200: Color(0xFFBFDBFE),
    300: Color(0xFF93C5FD),
    400: Color(0xFF60A5FA),
    500: Color(0xFF3B82F6),
    600: Color(0xFF2563EB),
    700: Color(0xFF1D4ED8),
    800: Color(0xFF1E40AF),
    900: Color(0xFF1E3A8A),
  };

  // Neutral gray
  static const Map<int, Color> gray = <int, Color>{
    50: Color(0xFFF9FAFB),
    100: Color(0xFFF3F4F6),
    200: Color(0xFFE5E7EB),
    300: Color(0xFFD1D5DB),
    400: Color(0xFF9CA3AF),
    500: Color(0xFF6B7280),
    600: Color(0xFF4B5563),
    700: Color(0xFF374151),
    800: Color(0xFF1F2937),
    900: Color(0xFF111827),
  };

  // Error/danger red
  static const Map<int, Color> red = <int, Color>{
    50: Color(0xFFFEF2F2),
    100: Color(0xFFFEE2E2),
    300: Color(0xFFFCA5A5),
    500: Color(0xFFEF4444),
    600: Color(0xFFDC2626),
    700: Color(0xFFB91C1C),
  };

  // Success green
  static const Map<int, Color> green = <int, Color>{
    50: Color(0xFFF0FDF4),
    100: Color(0xFFDCFCE7),
    300: Color(0xFF86EFAC),
    500: Color(0xFF22C55E),
    600: Color(0xFF16A34A),
    700: Color(0xFF15803D),
  };

  // Warning amber
  static const Map<int, Color> amber = <int, Color>{
    50: Color(0xFFFFFBEB),
    100: Color(0xFFFEF3C7),
    300: Color(0xFFFCD34D),
    500: Color(0xFFF59E0B),
    600: Color(0xFFD97706),
    700: Color(0xFFB45309),
  };

  static const Color white = Color(0xFFFFFFFF);
  static const Color black = Color(0xFF000000);
}

/// Semantic color tokens. Components should only ever reference these.
///
/// Provides both a [light] and [dark] instance; consumers typically resolve
/// the active set via [DsmColors.of] against a [Brightness], or by pulling
/// it from `DsmTheme` (see dsm_theme.dart) once wired into a [ThemeExtension].
class DsmColors {
  const DsmColors({
    required this.brightness,
    required this.background,
    required this.surface,
    required this.surfaceVariant,
    required this.onSurface,
    required this.onSurfaceMuted,
    required this.border,
    required this.primary,
    required this.onPrimary,
    required this.primaryHover,
    required this.primaryPressed,
    required this.danger,
    required this.onDanger,
    required this.success,
    required this.warning,
    required this.disabled,
    required this.onDisabled,
    required this.focusRing,
  });

  /// Light theme semantic palette.
  factory DsmColors.light() => DsmColors(
        brightness: Brightness.light,
        background: DsmPalette.white,
        surface: DsmPalette.gray[50]!,
        surfaceVariant: DsmPalette.gray[100]!,
        onSurface: DsmPalette.gray[900]!,
        onSurfaceMuted: DsmPalette.gray[500]!,
        border: DsmPalette.gray[300]!,
        primary: DsmPalette.blue[600]!,
        onPrimary: DsmPalette.white,
        primaryHover: DsmPalette.blue[700]!,
        primaryPressed: DsmPalette.blue[800]!,
        danger: DsmPalette.red[600]!,
        onDanger: DsmPalette.white,
        success: DsmPalette.green[600]!,
        warning: DsmPalette.amber[600]!,
        disabled: DsmPalette.gray[200]!,
        onDisabled: DsmPalette.gray[400]!,
        focusRing: DsmPalette.blue[300]!,
      );

  /// Dark theme semantic palette.
  factory DsmColors.dark() => DsmColors(
        brightness: Brightness.dark,
        background: DsmPalette.gray[900]!,
        surface: DsmPalette.gray[800]!,
        surfaceVariant: DsmPalette.gray[700]!,
        onSurface: DsmPalette.gray[50]!,
        onSurfaceMuted: DsmPalette.gray[400]!,
        border: DsmPalette.gray[600]!,
        primary: DsmPalette.blue[400]!,
        onPrimary: DsmPalette.gray[900]!,
        primaryHover: DsmPalette.blue[300]!,
        primaryPressed: DsmPalette.blue[200]!,
        danger: DsmPalette.red[500]!,
        onDanger: DsmPalette.gray[900]!,
        success: DsmPalette.green[500]!,
        warning: DsmPalette.amber[500]!,
        disabled: DsmPalette.gray[700]!,
        onDisabled: DsmPalette.gray[500]!,
        focusRing: DsmPalette.blue[400]!,
      );

  final Brightness brightness;
  final Color background;
  final Color surface;
  final Color surfaceVariant;
  final Color onSurface;
  final Color onSurfaceMuted;
  final Color border;
  final Color primary;
  final Color onPrimary;
  final Color primaryHover;
  final Color primaryPressed;
  final Color danger;
  final Color onDanger;
  final Color success;
  final Color warning;
  final Color disabled;
  final Color onDisabled;
  final Color focusRing;

  /// Resolves the semantic palette for a given [Brightness].
  static DsmColors of(Brightness brightness) =>
      brightness == Brightness.dark ? DsmColors.dark() : DsmColors.light();
}
