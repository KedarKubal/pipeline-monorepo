/// Spacing scale, in logical pixels, on a 4px base grid.
///
/// Use these instead of magic numbers so layout rhythm stays consistent
/// across every component. Named for their multiplier (e.g. [xs] = 1x base).
abstract final class DsmSpacing {
  static const double none = 0;
  static const double xxs = 2;
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 24;
  static const double xxl = 32;
  static const double xxxl = 48;
  static const double xxxxl = 64;
}

/// Corner radius scale, in logical pixels.
abstract final class DsmRadius {
  static const double none = 0;
  static const double sm = 4;
  static const double md = 8;
  static const double lg = 12;
  static const double xl = 16;

  /// Fully rounded — pass a large value so [BorderRadius.circular] clips
  /// to a pill/circle regardless of the widget's height.
  static const double full = 9999;
}

/// Border width scale, in logical pixels.
abstract final class DsmBorderWidth {
  static const double thin = 1;
  static const double medium = 1.5;
  static const double thick = 2;
}

/// Standard motion durations, in milliseconds equivalents via [Duration].
abstract final class DsmMotion {
  static const Duration fast = Duration(milliseconds: 120);
  static const Duration standard = Duration(milliseconds: 200);
  static const Duration slow = Duration(milliseconds: 320);
}
