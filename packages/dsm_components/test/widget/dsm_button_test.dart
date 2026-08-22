import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Wraps [child] in a minimal MaterialApp using the DSM light theme, which
/// every widget test needs since components read tokens via [BuildContext].
Widget _wrap(Widget child) {
  return MaterialApp(
    theme: DsmTheme.light(),
    home: Scaffold(body: Center(child: child)),
  );
}

void main() {
  group('DsmButton', () {
    testWidgets('renders label text', (WidgetTester tester) async {
      await tester
          .pumpWidget(_wrap(DsmButton(label: 'Save', onPressed: () {})));
      expect(find.text('Save'), findsOneWidget);
    });

    testWidgets('invokes onPressed when tapped', (WidgetTester tester) async {
      int tapCount = 0;
      await tester.pumpWidget(
        _wrap(DsmButton(label: 'Tap me', onPressed: () => tapCount++)),
      );

      await tester.tap(find.byType(DsmButton));
      await tester.pump();

      expect(tapCount, 1);
    });

    testWidgets('does not invoke onPressed when onPressed is null (disabled)', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
          _wrap(const DsmButton(label: 'Disabled', onPressed: null)));

      await tester.tap(find.byType(DsmButton));
      await tester.pump();

      // No exception thrown, no callback to invoke — button should simply
      // be inert. We assert via absence of a GestureDetector.onTap handler
      // indirectly by checking the label still renders (didn't crash).
      expect(find.text('Disabled'), findsOneWidget);
    });

    testWidgets('does not invoke onPressed while isLoading',
        (WidgetTester tester) async {
      int tapCount = 0;
      await tester.pumpWidget(
        _wrap(
          DsmButton(
            label: 'Submitting',
            onPressed: () => tapCount++,
            isLoading: true,
          ),
        ),
      );

      await tester.tap(find.byType(DsmButton));
      await tester.pump();

      expect(tapCount, 0);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      // Label is replaced by the spinner while loading.
      expect(find.text('Submitting'), findsNothing);
    });

    testWidgets('renders leading and trailing icons when provided', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        _wrap(
          DsmButton(
            label: 'Download',
            onPressed: () {},
            leadingIcon: Icons.download,
            trailingIcon: Icons.arrow_forward,
          ),
        ),
      );

      expect(find.byIcon(Icons.download), findsOneWidget);
      expect(find.byIcon(Icons.arrow_forward), findsOneWidget);
    });

    testWidgets('exposes correct semantics label', (WidgetTester tester) async {
      final SemanticsHandle handle = tester.ensureSemantics();

      await tester.pumpWidget(
        _wrap(
          DsmButton(
            label: 'Delete',
            onPressed: () {},
            semanticsLabel: 'Delete this item permanently',
          ),
        ),
      );

      expect(
        tester.getSemantics(
            find.bySemanticsLabel('Delete this item permanently')),
        matchesSemantics(
          label: 'Delete this item permanently',
          isButton: true,
          isEnabled: true,
          hasEnabledState: true,
          hasTapAction: true,
          isFocusable: true,
        ),
      );

      handle.dispose();
    });

    testWidgets('all variants render without throwing',
        (WidgetTester tester) async {
      for (final DsmButtonVariant variant in DsmButtonVariant.values) {
        await tester.pumpWidget(
          _wrap(DsmButton(
              label: variant.name, onPressed: () {}, variant: variant)),
        );
        expect(find.text(variant.name), findsOneWidget);
      }
    });

    testWidgets('all sizes render without throwing',
        (WidgetTester tester) async {
      for (final DsmButtonSize size in DsmButtonSize.values) {
        await tester.pumpWidget(
          _wrap(DsmButton(label: size.name, onPressed: () {}, size: size)),
        );
        expect(find.text(size.name), findsOneWidget);
      }
    });
  });
}
