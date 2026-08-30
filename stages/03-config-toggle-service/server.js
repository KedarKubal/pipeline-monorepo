'use strict';

const createApp = require('./src/app');
const config = require('./src/config');
const logger = require('./src/utils/logger');

const app = createApp();

const server = app.listen(config.port, () => {
  logger.info(`config-toggle-service listening on port ${config.port}`, { env: config.env });
});

// Graceful shutdown for containerized environments (SIGTERM from Docker/K8s).
function shutdown(signal) {
  logger.info(`${signal} received, shutting down gracefully`);
  server.close(() => {
    logger.info('server closed');
    process.exit(0);
  });
  // Force-exit if connections don't close in time.
  setTimeout(() => process.exit(1), 10_000).unref();
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

module.exports = server;
