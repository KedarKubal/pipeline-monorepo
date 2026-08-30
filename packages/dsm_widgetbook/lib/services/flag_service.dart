import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Polls the Config Toggle Service for a single boolean flag and
/// exposes it as a stream. Fails open: on any error or non-200
/// response it keeps emitting the last known good value rather than
/// flipping to a surprising default.
class FlagService {
  FlagService({
    required this.baseUrl,
    required this.flagKey,
    this.pollInterval = const Duration(seconds: 5),
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final String flagKey;
  final Duration pollInterval;
  final http.Client _client;

  final _controller = StreamController<bool>.broadcast();
  Timer? _timer;
  bool _lastKnown = false;

  Stream<bool> get onChange => _controller.stream;
  bool get lastKnownValue => _lastKnown;

  void start() {
    _poll();
    _timer = Timer.periodic(pollInterval, (_) => _poll());
  }

  Future<void> _poll() async {
    try {
      final uri = Uri.parse('$baseUrl/api/flags/$flagKey');
      final response =
          await _client.get(uri).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        _lastKnown = body['enabled'] as bool? ?? _lastKnown;
      }
      // non-200 -> fail open, keep _lastKnown
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
