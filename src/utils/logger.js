'use strict';

/**
 * Minimal structured logger. Kept dependency-free on purpose — this is a
 * small service and pulling in winston/pino would be overkill. Swap this
 * module out later if log aggregation needs grow.
 */
function timestamp() {
  return new Date().toISOString();
}

const logger = {
  info: (message, meta = {}) => {
    console.log(JSON.stringify({ level: 'info', timestamp: timestamp(), message, ...meta }));
  },
  warn: (message, meta = {}) => {
    console.warn(JSON.stringify({ level: 'warn', timestamp: timestamp(), message, ...meta }));
  },
  error: (message, meta = {}) => {
    console.error(JSON.stringify({ level: 'error', timestamp: timestamp(), message, ...meta }));
  },
};

module.exports = logger;
