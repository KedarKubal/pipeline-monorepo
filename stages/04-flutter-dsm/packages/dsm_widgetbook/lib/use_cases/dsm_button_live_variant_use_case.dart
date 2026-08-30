import 'package:dsm_components/dsm_components.dart';
import 'package:flutter/material.dart';

import '../services/flag_service.dart';

/// Toggle service base URL. Override at build/run time with:
/// flutter run --dart-define=TOGGLE_SERVICE_URL=http://localhost:3000
const _toggleServiceUrl = String.fromEnvironment(
  'TOGGLE_SERVICE_URL',
  defaultValue: 'http://localhost:3000',
);

const _flagKey = 'component-preview-variant';

class DsmButtonLiveVariantUseCase extends StatefulWidget {
  const DsmButtonLiveVariantUseCase({super.key});

  @override
  State<DsmButtonLiveVariantUseCase> createState() =>
      _DsmButtonLiveVariantUseCaseState();
}

class _DsmButtonLiveVariantUseCaseState
    extends State<DsmButtonLiveVariantUseCase> {
  late final FlagService _flagService;

  @override
  void initState() {
    super.initState();
    _flagService = FlagService(
      baseUrl: _toggleServiceUrl,
      flagKey: _flagKey,
    )..start();
  }

  @override
  void dispose() {
    _flagService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<bool>(
      stream: _flagService.onChange,
      initialData: _flagService.lastKnownValue,
      builder: (context, snapshot) {
        final danger = snapshot.data ?? false;
        return Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DsmButton(
                label: 'Live-flagged button',
                variant:
                    danger ? DsmButtonVariant.danger : DsmButtonVariant.primary,
                onPressed: () {},
              ),
              const SizedBox(height: 8),
              Text(
                '$_flagKey: ${danger ? "danger" : "primary"}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              TextButton(
                onPressed: () => setState(() {}), // manual refresh nudge
                child: const Text('Refresh'),
              ),
            ],
          ),
        );
      },
    );
  }
}
