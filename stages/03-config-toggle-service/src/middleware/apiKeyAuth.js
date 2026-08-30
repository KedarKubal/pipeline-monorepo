'use strict';

const config = require('../config');
const AppError = require('../utils/AppError');

/**
 * Protects write routes with a simple API key check (`X-API-Key` header).
 * Reads remain public so dashboards/consumers can poll flag state freely.
 *
 * This is intentionally simple — swap for JWT/OAuth if the service grows
 * beyond an internal tool.
 */
function apiKeyAuth(req, res, next) {
  const key = req.headers['x-api-key'];

  if (!key || !config.apiKeys.includes(key)) {
    return next(AppError.unauthorized('Missing or invalid X-API-Key header.'));
  }

  next();
}

module.exports = apiKeyAuth;
