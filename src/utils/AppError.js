'use strict';

/**
 * Typed application error. Thrown from services/controllers with an explicit
 * HTTP status so the central error handler can respond consistently without
 * every route re-implementing status-code logic.
 */
class AppError extends Error {
  /**
   * @param {string} message - human-readable error message
   * @param {number} statusCode - HTTP status code to respond with
   * @param {string} [code] - machine-readable error code for API consumers
   */
  constructor(message, statusCode = 500, code = 'INTERNAL_ERROR') {
    super(message);
    this.name = 'AppError';
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = true; // distinguishes expected errors from bugs
    Error.captureStackTrace(this, this.constructor);
  }

  static notFound(message = 'Resource not found') {
    return new AppError(message, 404, 'NOT_FOUND');
  }

  static badRequest(message = 'Invalid request') {
    return new AppError(message, 400, 'BAD_REQUEST');
  }

  static conflict(message = 'Resource already exists') {
    return new AppError(message, 409, 'CONFLICT');
  }

  static unauthorized(message = 'Unauthorized') {
    return new AppError(message, 401, 'UNAUTHORIZED');
  }
}

module.exports = AppError;
