import 'package:flutter/painting.dart';

/// Typography scale for the design system.
///
/// Mirrors [TextTheme] naming loosely (display/headline/title/body/label)
/// so it maps cleanly onto Flutter's ThemeData.textTheme when consumed via
/// dsm_components' DsmTheme. Font family defaults to the platform default;
/// override [fontFamily] at construction time to apply a brand typeface.
class DsmTypography {
  const DsmTypography({this.fontFamily});

  final String? fontFamily;

  TextStyle get displayLarge =>
      _style(fontSize: 40, weight: FontWeight.w700, height: 1.15);
  TextStyle get displayMedium =>
      _style(fontSize: 32, weight: FontWeight.w700, height: 1.2);

  TextStyle get headlineLarge =>
      _style(fontSize: 28, weight: FontWeight.w600, height: 1.25);
  TextStyle get headlineMedium =>
      _style(fontSize: 24, weight: FontWeight.w600, height: 1.3);
  TextStyle get headlineSmall =>
      _style(fontSize: 20, weight: FontWeight.w600, height: 1.3);

  TextStyle get titleLarge =>
      _style(fontSize: 18, weight: FontWeight.w600, height: 1.35);
  TextStyle get titleMedium =>
      _style(fontSize: 16, weight: FontWeight.w600, height: 1.4);
  TextStyle get titleSmall =>
      _style(fontSize: 14, weight: FontWeight.w600, height: 1.4);

  TextStyle get bodyLarge =>
      _style(fontSize: 16, weight: FontWeight.w400, height: 1.5);
  TextStyle get bodyMedium =>
      _style(fontSize: 14, weight: FontWeight.w400, height: 1.5);
  TextStyle get bodySmall =>
      _style(fontSize: 12, weight: FontWeight.w400, height: 1.5);

  TextStyle get labelLarge =>
      _style(fontSize: 14, weight: FontWeight.w500, height: 1.2);
  TextStyle get labelMedium =>
      _style(fontSize: 12, weight: FontWeight.w500, height: 1.2);
  TextStyle get labelSmall => _style(
      fontSize: 11, weight: FontWeight.w500, height: 1.2, letterSpacing: 0.4);

  TextStyle _style({
    required double fontSize,
    required FontWeight weight,
    required double height,
    double letterSpacing = 0,
  }) {
    return TextStyle(
      fontFamily: fontFamily,
      fontSize: fontSize,
      fontWeight: weight,
      height: height,
      letterSpacing: letterSpacing,
    );
  }
}
