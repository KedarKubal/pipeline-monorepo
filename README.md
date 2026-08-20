# Flutter DSM — Design System Component Library

A reusable Flutter design system: tokens, components, golden-tested visual
regression coverage, and a Widgetbook catalog for visual QA — structured as
a Melos monorepo so tokens, components, and the catalog can version and
publish independently.

## Packages

| Package | Purpose |
|---|---|
| [`dsm_tokens`](packages/dsm_tokens) | Design tokens: color, spacing, radius, border width, motion, typography. No Flutter widget dependencies beyond `dart:ui`/`painting`. |
| [`dsm_components`](packages/dsm_components) | Component library: `DsmButton`, `DsmTextField`, `DsmCard`, `DsmBadge`, plus `DsmTheme` for wiring tokens into `ThemeData`. |
| [`dsm_widgetbook`](packages/dsm_widgetbook) | Standalone Widgetbook app cataloguing every component/variant for visual QA and design review. |

## Getting started

```bash
# Install Melos (one-time)
dart pub global activate melos

# Bootstrap the workspace — links local packages, runs pub get everywhere
melos bootstrap
```

### Common tasks

```bash
melos run analyze              # dart analyze across all packages
melos run format               # dart format --set-exit-if-changed
melos run test                 # flutter test across all packages
melos run test:golden          # regenerate golden images after intentional visual changes
melos run test:golden:verify   # verify goldens match (CI-safe, no writes)
melos run widgetbook           # launch the Widgetbook catalog in Chrome
```

## Using the components in an app

Add a path or git dependency on `dsm_components` (which re-exports
`dsm_tokens`, so you only need one import):

```yaml
dependencies:
  dsm_components:
    path: ../flutter_dsm/packages/dsm_components
    # or, once published to a private registry / git:
    # git:
    #   url: https://github.com/your-org/flutter_dsm.git
    #   path: packages/dsm_components
```

Wire the theme once at the app root:

```dart
import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      theme: DsmTheme.light(),
      darkTheme: DsmTheme.dark(),
      themeMode: ThemeMode.system,
      home: const HomeScreen(),
    );
  }
}
```

Then use components anywhere in the tree:

```dart
DsmButton(
  label: 'Save changes',
  variant: DsmButtonVariant.primary,
  size: DsmButtonSize.medium,
  onPressed: () => save(),
),

DsmTextField(
  label: 'Email',
  placeholder: 'you@example.com',
  errorText: emailError,
  onChanged: (value) => setState(() => email = value),
),

DsmCard(
  variant: DsmCardVariant.elevated,
  onTap: () => openDetails(),
  child: const Text('Tap to view details'),
),

DsmBadge(label: 'Active', variant: DsmBadgeVariant.success),
```

Components read tokens via `context.dsmColors` / `context.dsmTypography`
(exposed by a `ThemeExtension`), so anything wrapped in `DsmTheme.light()`
or `.dark()` automatically gets consistent theming — no per-widget token
plumbing required.

## Component gallery

> Screenshots below are placeholders — replace with actual PNGs exported
> from the Widgetbook run (`melos run widgetbook`, then use its built-in
> screenshot/export tooling, or capture goldens from `test/golden/*.png`
> after running `melos run test:golden`).

### Button
`![Button variants](docs/screenshots/button-variants.png)`

Variants: `primary`, `secondary`, `ghost`, `danger`
Sizes: `small`, `medium`, `large`
States: default, hover, pressed, focused, disabled, loading

### TextField
`![TextField states](docs/screenshots/text-field-states.png)`

States: resting, focused, error, disabled — with optional helper text,
leading/trailing icons, and obscure-text mode for passwords.

### Card
`![Card variants](docs/screenshots/card-variants.png)`

Variants: `outlined`, `elevated`, `filled` — optionally tappable.

### Badge
`![Badge variants](docs/screenshots/badge-variants.png)`

Variants: `neutral`, `primary`, `success`, `warning`, `danger`
Sizes: `small`, `medium`

## Architecture notes

- **Tokens are the only source of visual truth.** Components never
  hardcode a `Color` or spacing value — everything routes through
  `DsmColors` / `DsmSpacing` / `DsmTypography` / `DsmRadius`, so a full
  rebrand is a token-file change, not a component-by-component sweep.
- **Theming via `ThemeExtension`.** `DsmThemeExtension` bundles the
  semantic color set + typography scale onto Flutter's `ThemeData`, so
  components read `context.dsmColors` the same way you'd read
  `Theme.of(context).colorScheme`. Light/dark are separate `DsmColors`
  instances resolved once at theme-construction time.
- **`flutter_hooks` for local interaction state.** Hover/press/focus
  tracking in `DsmButton` and focus tracking in `DsmTextField` use
  `useState`/`useFocusNode`/`useListenable` instead of converting every
  component into a `StatefulWidget` — keeps the widget declarative and the
  state colocated with where it's used.
- **Golden tests via `golden_toolkit`.** Each component has a golden test
  covering its full variant × size matrix plus edge states (disabled,
  loading, error). `flutter_test_config.dart` loads real fonts so goldens
  reflect actual typography rather than the `Ahem` fallback font.
- **Widgetbook use cases are hand-written, not codegen'd**, so the catalog
  builds without running `build_runner` first. Each component has a
  `Playground` use case with live knobs (variant/size/text/boolean toggles)
  plus one or more static "gallery" use cases. Migrate to
  `@widgetbook.UseCase` annotations + `build_runner` later if you want
  auto-discovery as the catalog grows.

## Testing strategy

- **Widget tests** (`test/widget/`) assert behavior: taps invoke
  callbacks, disabled/loading states suppress interaction, text/icons
  render, semantics are correct.
- **Golden tests** (`test/golden/`) assert appearance: pixel-diffed
  snapshots per variant/size/state combination, plus a dark-theme pass for
  `DsmButton` to catch tokens that don't adapt correctly.
- Run `melos run test:golden` after any intentional visual change and
  commit the updated PNGs alongside the code change. CI runs
  `test:golden:verify` (no image writes) to catch unintentional drift.

## Adding a new component

1. Add tokens it needs to `dsm_tokens` first (don't introduce new
   one-off colors/spacing inside the component).
2. Create `packages/dsm_components/lib/src/components/dsm_<name>.dart`
   with variant/size enums as needed, following the existing components'
   pattern (semantic-only token access via `context.dsmColors`).
3. Export it from `packages/dsm_components/lib/dsm_components.dart`.
4. Add widget tests under `test/widget/` and a golden test under
   `test/golden/`.
5. Add a Widgetbook use case under
   `packages/dsm_widgetbook/lib/use_cases/` and register it in
   `main.dart`.
6. Run `melos run test:golden` to generate the initial golden images,
   `melos run analyze`, and `melos run test` before opening a PR.
