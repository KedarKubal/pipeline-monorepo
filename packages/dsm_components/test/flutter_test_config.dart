import 'dart:async';

import 'package:golden_toolkit/golden_toolkit.dart';

/// Global test config picked up automatically by `flutter test`.
///
/// Wraps every test in [testExecutable] so golden tests load real fonts
/// (via golden_toolkit's `loadAppFonts`) instead of the default Ahem
/// fallback, which would make text-heavy component goldens meaningless.
Future<void> testExecutable(FutureOr<void> Function() testMain) async {
  await loadAppFonts();
  return testMain();
}
