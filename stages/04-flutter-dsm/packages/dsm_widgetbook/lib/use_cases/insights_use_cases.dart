import 'package:flutter/material.dart';
import 'package:widgetbook/widgetbook.dart';
import 'insights_dashboard_use_case.dart';

/// Use case tree for the pipeline insights dashboard, registered under
/// "Pipeline Insights" (top-level, not nested under Components — this
/// isn't a design-system component, it's the Stage 4 consumer of the
/// adobe-analytics-demo -> migration-platform -> config-toggle-service
/// pipeline).
final List<WidgetbookNode> insightsUseCases = <WidgetbookNode>[
  WidgetbookUseCase(
    name: 'Cart Abandonment Dashboard',
    builder: (BuildContext context) => const InsightsDashboardUseCase(),
  ),
];
