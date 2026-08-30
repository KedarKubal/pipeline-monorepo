'use strict';

const { Router } = require('express');
const controller = require('../controllers/flags.controller');
const apiKeyAuth = require('../middleware/apiKeyAuth');
const validateFlagPayload = require('../middleware/validateFlagPayload');

const router = Router();

// Reads — public, no auth required.
router.get('/', controller.list);
router.get('/audit', controller.getAudit);
router.get('/:key', controller.getOne);
router.get('/:key/history', controller.getHistory);


// Writes — require a valid X-API-Key header.
router.post('/', apiKeyAuth, validateFlagPayload({ requireKey: true }), controller.create);
router.patch('/:key', apiKeyAuth, validateFlagPayload(), controller.update);
router.post('/:key/toggle', apiKeyAuth, controller.toggle);
router.delete('/:key', apiKeyAuth, controller.remove);

module.exports = router;
