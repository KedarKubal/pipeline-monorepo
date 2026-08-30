import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _wrap(Widget child) {
  return MaterialApp(
    theme: DsmTheme.light(),
    home: Scaffold(body: Center(child: child)),
  );
}

void main() {
  group('DsmCard', () {
    testWidgets('renders its child', (WidgetTester tester) async {
      await tester
          .pumpWidget(_wrap(const DsmCard(child: Text('Card content'))));
      expect(find.text('Card content'), findsOneWidget);
    });

    testWidgets('is not tappable when onTap is null',
        (WidgetTester tester) async {
      await tester.pumpWidget(_wrap(const DsmCard(child: Text('Static'))));
      expect(find.byType(InkWell), findsNothing);
    });

    testWidgets('invokes onTap when tapped', (WidgetTester tester) async {
      int tapCount = 0;
      await tester.pumpWidget(
        _wrap(DsmCard(onTap: () => tapCount++, child: const Text('Tappable'))),
      );

      await tester.tap(find.byType(DsmCard));
      await tester.pump();

      expect(tapCount, 1);
    });

    testWidgets('all variants render without throwing',
        (WidgetTester tester) async {
      for (final DsmCardVariant variant in DsmCardVariant.values) {
        await tester.pumpWidget(
          _wrap(DsmCard(variant: variant, child: Text(variant.name))),
        );
        expect(find.text(variant.name), findsOneWidget);
      }
    });
  });

  group('DsmBadge', () {
    testWidgets('renders label text', (WidgetTester tester) async {
      await tester.pumpWidget(_wrap(const DsmBadge(label: 'Active')));
      expect(find.text('Active'), findsOneWidget);
    });

    testWidgets('renders leading icon when provided',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        _wrap(
            const DsmBadge(label: 'Verified', leadingIcon: Icons.check_circle)),
      );
      expect(find.byIcon(Icons.check_circle), findsOneWidget);
    });

    testWidgets('all variants render without throwing',
        (WidgetTester tester) async {
      for (final DsmBadgeVariant variant in DsmBadgeVariant.values) {
        await tester
            .pumpWidget(_wrap(DsmBadge(label: variant.name, variant: variant)));
        expect(find.text(variant.name), findsOneWidget);
      }
    });

    testWidgets('all sizes render without throwing',
        (WidgetTester tester) async {
      for (final DsmBadgeSize size in DsmBadgeSize.values) {
        await tester.pumpWidget(_wrap(DsmBadge(label: size.name, size: size)));
        expect(find.text(size.name), findsOneWidget);
      }
    });
  });
}
