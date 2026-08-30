'use strict';

const path = require('path');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');

const config = require('./config');
const flagsRoutes = require('./routes/flags.routes');
const healthRoutes = require('./routes/health.routes');
const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');

function createApp() {
  const app = express();

  // Security & parsing middleware
  app.use(helmet());
  app.use(cors({ origin: config.corsOrigin }));
  app.use(express.json({ limit: '100kb' }));
  app.use(morgan(config.isProduction() ? 'combined' : 'dev'));

  // Static toggle dashboard
  app.use('/dashboard', express.static(path.join(__dirname, '..', 'public')));

  // API routes
  app.use('/api/health', healthRoutes);
  app.use('/api/flags', flagsRoutes);

  app.get('/', (req, res) => {
    res.json({
      service: 'config-toggle-service',
      docs: 'See README.md for full API reference.',
      endpoints: {
        health: 'GET /api/health',
        listFlags: 'GET /api/flags',
        getFlag: 'GET /api/flags/:key',
        createFlag: 'POST /api/flags (requires X-API-Key)',
        updateFlag: 'PATCH /api/flags/:key (requires X-API-Key)',
        toggleFlag: 'POST /api/flags/:key/toggle (requires X-API-Key)',
        deleteFlag: 'DELETE /api/flags/:key (requires X-API-Key)',
        dashboard: 'GET /dashboard',
      },
    });
  });

  // 404 + centralized error handling (must be registered last)
  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}

module.exports = createApp;
