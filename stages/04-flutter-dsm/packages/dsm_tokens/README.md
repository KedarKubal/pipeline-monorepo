# dsm_tokens

Design tokens for the Flutter DSM: color, spacing, radius, border width,
motion durations, and typography. Pure Dart/Flutter `painting` types — no
widget dependencies — so it can be consumed by non-Flutter tooling (e.g. a
future design-token export script) without pulling in the full framework.

## Usage

```dart
import 'package:dsm_tokens/dsm_tokens.dart';

final colors = DsmColors.light();
final typography = DsmTypography();

Container(
  padding: const EdgeInsets.all(DsmSpacing.lg),
  decoration: BoxDecoration(
    color: colors.surface,
    borderRadius: BorderRadius.circular(DsmRadius.md),
  ),
  child: Text('Hello', style: typography.bodyLarge.copyWith(color: colors.onSurface)),
)
```

In practice, most consumers won't reach for these directly — use
`dsm_components`' `DsmTheme` and `context.dsmColors` / `context.dsmTypography`
instead, which wire these tokens into Flutter's `ThemeData`.
