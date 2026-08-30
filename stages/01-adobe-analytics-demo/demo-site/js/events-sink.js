/**
 * Lightweight event sink for the analytics pipeline.
 * Posts each tracked event to a local collector endpoint (server.js),
 * which appends it to data/events.jsonl for migration-platform to extract.
 */
const EVENTS_ENDPOINT = '/api/events';

async function recordEvent(eventName, payload) {
  const event = {
    event: eventName,
    timestamp: new Date().toISOString(),
    ...payload,
  };
  try {
    await fetch(EVENTS_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event),
    });
  } catch (err) {
    // Telemetry must never break the shopping flow
    console.warn('[events-sink] failed to record event', err);
  }
}

window.recordEvent = recordEvent;
