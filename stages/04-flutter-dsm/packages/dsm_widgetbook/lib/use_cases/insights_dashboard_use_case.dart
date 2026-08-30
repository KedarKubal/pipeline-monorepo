import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';
import '../services/flag_service.dart';
import '../services/metrics_service.dart';

/// Base URLs for the two pipeline services this dashboard reads from.
/// Override at build/run time, e.g.:
/// flutter run --dart-define=TOGGLE_SERVICE_URL=http://localhost:3000 \
///             --dart-define=METRICS_API_URL=http://localhost:8001
const _toggleServiceUrl = String.fromEnvironment(
  'TOGGLE_SERVICE_URL',
  defaultValue: 'http://localhost:3000',
);
const _metricsApiUrl = String.fromEnvironment(
  'METRICS_API_URL',
  defaultValue: 'http://localhost:8001',
);
const _alertFlagKey = 'high-cart-abandonment-alert';
const _metricName = 'cart_abandonment_rate';

/// Stage 4 of the pipeline: the "insight" a hiring manager sees at the end
/// of the chain. Combines the live alert flag (Stage 3's decision) with the
/// raw metric value (Stage 2's computation) into one view — the same data,
/// shown two ways, sourced from two different pipeline stages.
class InsightsDashboardUseCase extends StatefulWidget {
  const InsightsDashboardUseCase({super.key});

  @override
  State<InsightsDashboardUseCase> createState() => _InsightsDashboardUseCaseState();
}

class _InsightsDashboardUseCaseState extends State<InsightsDashboardUseCase> {
  late final FlagService _flagService;
  late final MetricsService _metricsService;

  @override
  void initState() {
    super.initState();
    _flagService = FlagService(baseUrl: _toggleServiceUrl, flagKey: _alertFlagKey)..start();
    _metricsService = MetricsService(baseUrl: _metricsApiUrl, metricName: _metricName)..start();
  }

  @override
  void dispose() {
    _flagService.dispose();
    _metricsService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: StreamBuilder<bool>(
        stream: _flagService.onChange,
        initialData: _flagService.lastKnownValue,
        builder: (context, flagSnapshot) {
          final alertActive = flagSnapshot.data ?? false;
          return StreamBuilder<MetricSnapshot?>(
            stream: _metricsService.onChange,
            initialData: _metricsService.lastKnownValue,
            builder: (context, metricSnapshot) {
              final metric = metricSnapshot.data;
              return DsmCard(
                variant: DsmCardVariant.elevated,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text('Cart Abandonment', style: Theme.of(context).textTheme.titleMedium),
                          const Spacer(),
                          DsmBadge(
                            label: alertActive ? 'Alert' : 'Normal',
                            variant: alertActive ? DsmBadgeVariant.danger : DsmBadgeVariant.success,
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (metric == null)
                        Text('No metric computed yet.', style: Theme.of(context).textTheme.bodyMedium)
                      else ...[
                        Text(
                          '${(metric.metricValue * 100).toStringAsFixed(1)}%',
                          style: Theme.of(context).textTheme.headlineMedium,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'based on ${metric.sampleSize} carts · computed ${metric.computedAt}',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                      const SizedBox(height: 8),
                      Text(
                        'Sourced from adobe-analytics-demo -> migration-platform ETL -> config-toggle-service flag',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(fontStyle: FontStyle.italic),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
