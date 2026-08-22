# dsm_components

Reusable Flutter components implementing the design system: `DsmButton`,
`DsmTextField`, `DsmCard`, `DsmBadge`, and `DsmTheme` for wiring
[`dsm_tokens`](../dsm_tokens) into `ThemeData`.

See the [root README](../../README.md) for full usage examples, the
component gallery, and architecture notes.

## Quick reference

| Component | Variants | Sizes |
|---|---|---|
| `DsmButton` | `primary`, `secondary`, `ghost`, `danger` | `small`, `medium`, `large` |
| `DsmTextField` | — (state-driven: resting/focused/error/disabled) | — |
| `DsmCard` | `outlined`, `elevated`, `filled` | — |
| `DsmBadge` | `neutral`, `primary`, `success`, `warning`, `danger` | `small`, `medium` |

## Testing

```bash
flutter test                          # widget + golden tests
flutter test --update-goldens         # regenerate golden images
```

Or from the repo root via Melos: `melos run test`, `melos run test:golden`.
