'use strict';

const AppError = require('../utils/AppError');

/**
 * Validates the request body shape before it reaches the controller/service.
 * `requireKey` is true only for creation, since PATCH/toggle identify the
 * flag via the URL param instead.
 */
function validateFlagPayload({ requireKey = false } = {}) {
  return (req, res, next) => {
    const body = req.body || {};

    if (requireKey && (!body.key || typeof body.key !== 'string')) {
      return next(AppError.badRequest('"key" is required and must be a string.'));
    }

    if ('enabled' in body && typeof body.enabled !== 'boolean') {
      return next(AppError.badRequest('"enabled" must be a boolean.'));
    }

    if ('description' in body && typeof body.description !== 'string') {
      return next(AppError.badRequest('"description" must be a string.'));
    }

    if ('environments' in body && !Array.isArray(body.environments)) {
      return next(AppError.badRequest('"environments" must be an array of strings.'));
    }

    next();
  };
}

module.exports = validateFlagPayload;
