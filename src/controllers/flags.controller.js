'use strict';

const flagsService = require('../services/flags.service');

/**
 * Controllers stay thin: parse/validate the HTTP request, call the service,
 * shape the response. No business logic lives here.
 */

async function list(req, res, next) {
  try {
    const { environment } = req.query;
    const flags = await flagsService.listFlags({ environment });
    res.json({ count: flags.length, flags });
  } catch (err) {
    next(err);
  }
}

async function getOne(req, res, next) {
  try {
    const flag = await flagsService.getFlag(req.params.key);
    res.json(flag);
  } catch (err) {
    next(err);
  }
}

async function create(req, res, next) {
  try {
    const { key, description, enabled, environments } = req.body;
    const actor = req.headers['x-actor'] || 'api';
    const flag = await flagsService.createFlag({ key, description, enabled, environments, actor });
    res.status(201).json(flag);
  } catch (err) {
    next(err);
  }
}

async function update(req, res, next) {
  try {
    const actor = req.headers['x-actor'] || 'api';
    const flag = await flagsService.updateFlag(req.params.key, req.body, actor);
    res.json(flag);
  } catch (err) {
    next(err);
  }
}

async function toggle(req, res, next) {
  try {
    const actor = req.headers['x-actor'] || 'api';
    const flag = await flagsService.toggleFlag(req.params.key, actor);
    res.json(flag);
  } catch (err) {
    next(err);
  }
}

async function remove(req, res, next) {
  try {
    const actor = req.headers['x-actor'] || 'api';
    await flagsService.deleteFlag(req.params.key, actor);
    res.status(204).send();
  } catch (err) {
    next(err);
  }
}

module.exports = { list, getOne, create, update, toggle, remove };
