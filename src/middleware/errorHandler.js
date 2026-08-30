'use strict';

const logger = require('../utils/logger');
const config = require('../config');

/**
 * Single place where every error in the app is turned into an HTTP
 * response. Keeps routes/controllers free of repetitive try/catch
 * boilerplate around status codes.
 */
// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
  const statusCode = err.statusCode || 500;
  const code = err.code || 'INTERNAL_ERROR';
  const isOperational = err.isOperational === true;

  if (!isOperational) {
    // Unexpected/programmer error — log full stack for debugging.
    logger.error('unhandled error', { message: err.message, stack: err.stack });
  } else {
    logger.warn('operational error', { message: err.message, code, statusCode });
  }

  res.status(statusCode).json({
    error: {
      message: isOperational ? err.message : 'Something went wrong.',
      code,
      // Only leak stack traces outside production.
      ...(config.isProduction() ? {} : { stack: err.stack }),
    },
  });
}

function notFoundHandler(req, res) {
  res.status(404).json({
    error: { message: `Route ${req.method} ${req.originalUrl} not found.`, code: 'ROUTE_NOT_FOUND' },
  });
}

module.exports = { errorHandler, notFoundHandler };
