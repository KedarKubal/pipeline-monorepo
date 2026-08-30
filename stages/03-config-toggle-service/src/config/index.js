'use strict';

require('dotenv').config();
const path = require('path');

/**
 * Centralized application configuration.
 * All environment-variable access happens ONLY here — nowhere else in the
 * codebase should reference `process.env` directly. This keeps config
 * concerns in one place and makes the rest of the app trivially testable.
 */
const config = {
  env: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT, 10) || 3000,

  // Comma-separated list of API keys allowed to perform write operations
  // (create/update/delete flags). Read operations remain public.
  apiKeys: (process.env.API_KEYS || 'dev-local-key')
    .split(',')
    .map((k) => k.trim())
    .filter(Boolean),

  // Environments that a flag can be scoped to (e.g. rollout per environment).
  supportedEnvironments: ['development', 'staging', 'production'],

  // Where flag state is persisted. File-backed on purpose: this service is
  // intentionally small — no DB dependency required to run it.
  dataFilePath: process.env.DATA_FILE_PATH || path.join(__dirname, '..', 'data', 'flags.json'),

  corsOrigin: process.env.CORS_ORIGIN || '*',

  isProduction() {
    return this.env === 'production';
  },
};

module.exports = config;
