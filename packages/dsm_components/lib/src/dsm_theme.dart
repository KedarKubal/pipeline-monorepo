import 'package:dsm_tokens/dsm_tokens.dart';
import 'package:flutter/material.dart';

/// Bundles [DsmColors] and [DsmTypography] as a [ThemeExtension] so
/// components can read `Theme.of(context).extension<DsmThemeExtension>()`
/// instead of threading tokens through constructors.
class DsmThemeExtension extends ThemeExtension<DsmThemeExtension> {
  const DsmThemeExtension({required this.colors, required this.typography});

  final DsmColors colors;
  final DsmTypography typography;

  @override
  DsmThemeExtension copyWith({DsmColors? colors, DsmTypography? typography}) {
    return DsmThemeExtension(
      colors: colors ?? this.colors,
      typography: typography ?? this.typography,
    );
  }

  @override
  DsmThemeExtension lerp(ThemeExtension<DsmThemeExtension>? other, double t) {
    // Tokens are discrete design decisions, not continuously interpolable
    // values, so we snap rather than blend. This avoids nonsensical
    // in-between colors mid-theme-transition.
    if (other is! DsmThemeExtension) return this;
    return t < 0.5 ? this : other;
  }
}

/// Builds a complete [ThemeData] wired with DSM tokens.
///
/// This is the single entrypoint consuming apps should use:
/// ```dart
/// MaterialApp(theme: DsmTheme.light(), darkTheme: DsmTheme.dark());
/// ```
abstract final class DsmTheme {
  static ThemeData light({String? fontFamily}) => _build(
        colors: DsmColors.light(),
        typography: DsmTypography(fontFamily: fontFamily),
      );

  static ThemeData dark({String? fontFamily}) => _build(
        colors: DsmColors.dark(),
        typography: DsmTypography(fontFamily: fontFamily),
      );

  static ThemeData _build(
      {required DsmColors colors, required DsmTypography typography}) {
    return ThemeData(
      brightness: colors.brightness,
      scaffoldBackgroundColor: colors.background,
      colorScheme: ColorScheme.fromSeed(
        seedColor: colors.primary,
        brightness: colors.brightness,
        primary: colors.primary,
        onPrimary: colors.onPrimary,
        surface: colors.surface,
        onSurface: colors.onSurface,
        error: colors.danger,
        onError: colors.onDanger,
      ),
      fontFamily: typography.fontFamily,
      extensions: <ThemeExtension<dynamic>>[
        DsmThemeExtension(colors: colors, typography: typography),
      ],
    );
  }
}

/// Convenience accessor: `context.dsmColors` / `context.dsmTypography`.
extension DsmThemeContext on BuildContext {
  DsmThemeExtension get _ext {
    final DsmThemeExtension? ext =
        Theme.of(this).extension<DsmThemeExtension>();
    assert(
      ext != null,
      'DsmThemeExtension not found. Wrap your app with ThemeData from '
      'DsmTheme.light()/DsmTheme.dark(), or add DsmThemeExtension to your '
      'existing ThemeData.extensions.',
    );
    // Fall back to light tokens in release/profile builds so a missing
    // theme extension degrades gracefully instead of crashing the UI.
    return ext ??
        DsmThemeExtension(
            colors: DsmColors.light(), typography: const DsmTypography());
  }

  DsmColors get dsmColors => _ext.colors;

  DsmTypography get dsmTypography => _ext.typography;
}
