import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

/// A single funnel metric snapshot from migration-platform's metrics API.
class MetricSnapshot {
  const MetricSnapshot({
    required this.metricName,
    required this.metricValue,
    required this.sampleSize,
    required this.computedAt,
  });

  final String metricName;
  final double metricValue;
  final int sampleSize;
  final String computedAt;

  factory MetricSnapshot.fromJson(Map<String, dynamic> json) {
    return MetricSnapshot(
      metricName: json['metric_name'] as String,
      metricValue: (json['metric_value'] as num).toDouble(),
      sampleSize: json['sample_size'] as int? ?? 0,
      computedAt: json['computed_at'] as String,
    );
  }
}

/// Polls migration-platform's read-only metrics API and exposes the latest
/// value as a stream. Fails open: on any error or non-200 response it keeps
/// emitting the last known good value rather than showing a broken UI.
class MetricsService {
  MetricsService({
    required this.baseUrl,
    required this.metricName,
    this.pollInterval = const Duration(seconds: 5),
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final String metricName;
  final Duration pollInterval;
  final http.Client _client;

  final _controller = StreamController<MetricSnapshot?>.broadcast();
  Timer? _timer;
  MetricSnapshot? _lastKnown;

  Stream<MetricSnapshot?> get onChange => _controller.stream;
  MetricSnapshot? get lastKnownValue => _lastKnown;

  void start() {
    _poll();
    _timer = Timer.periodic(pollInterval, (_) => _poll());
  }

  Future<void> _poll() async {
    try {
      final uri = Uri.parse('$baseUrl/api/metrics/latest?metric_name=$metricName');
      final response = await _client.get(uri).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        _lastKnown = MetricSnapshot.fromJson(body);
      }
      // non-200 (incl. 404 "no metric computed yet") -> fail open, keep _lastKnown
    } catch (_) {
      // network error/timeout -> fail open, keep _lastKnown
    }
    if (!_controller.isClosed) _controller.add(_lastKnown);
  }

  void dispose() {
    _timer?.cancel();
    _controller.close();
    _client.close();
  }
}
