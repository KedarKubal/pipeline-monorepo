'use strict';

const fs = require('fs/promises');
const path = require('path');
const config = require('../config');
const AppError = require('../utils/AppError');
const logger = require('../utils/logger');

const KEY_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/; // e.g. "new-checkout-flow"

const AUDIT_FILE_PATH = path.join(path.dirname(config.dataFilePath), 'flag_audit.json');

/**
 * Serializes writes to the data file so concurrent requests can't interleave
 * and corrupt it. A real DB gives you this for free; a flat JSON file does
 * not, so we chain writes through a single promise queue.
 */
let writeQueue = Promise.resolve();
function serialize(fn) {
  const result = writeQueue.then(fn, fn);
  // Swallow errors here so one failed write doesn't permanently poison the
  // queue for subsequent, unrelated requests.
  writeQueue = result.catch(() => {});
  return result;
}

async function readStore() {
  try {
    const raw = await fs.readFile(config.dataFilePath, 'utf-8');
    return JSON.parse(raw);
  } catch (err) {
    if (err.code === 'ENOENT') return {};
    throw new AppError(`Failed to read flag store: ${err.message}`, 500);
  }
}

async function writeStore(store) {
  const tmpPath = `${config.dataFilePath}.tmp`;
  // Write to a temp file then rename — avoids leaving a truncated/corrupt
  // file behind if the process dies mid-write.
  await fs.writeFile(tmpPath, JSON.stringify(store, null, 2), 'utf-8');
  await fs.rename(tmpPath, config.dataFilePath);
}

async function readAuditStore() {
  try {
    const raw = await fs.readFile(AUDIT_FILE_PATH, 'utf-8');
    return JSON.parse(raw);
  } catch (err) {
    if (err.code === 'ENOENT') return [];
    throw new AppError(`Failed to read audit log: ${err.message}`, 500);
  }
}

async function writeAuditStore(entries) {
  const tmpPath = `${AUDIT_FILE_PATH}.tmp`;
  await fs.writeFile(tmpPath, JSON.stringify(entries, null, 2), 'utf-8');
  await fs.rename(tmpPath, AUDIT_FILE_PATH);
}

/**
 * Appends one audit entry. NOT wrapped in serialize() itself — every caller
 * is already running inside a serialize()'d mutation (createFlag, updateFlag,
 * toggleFlag, deleteFlag), so a nested serialize() call here would deadlock
 * against the outer queue slot.
 */
async function appendAuditEntry({ key, action, previousState, newState, actor = 'unknown' }) {
  const entries = await readAuditStore();
  entries.push({
    key,
    action, // 'create' | 'update' | 'toggle' | 'delete'
    previousState: previousState || null,
    newState: newState || null,
    actor,
    timestamp: new Date().toISOString(),
  });
  await writeAuditStore(entries);
}

async function getFlagHistory(key) {
  const entries = await readAuditStore();
  return entries.filter((e) => e.key === key);
}

async function getAuditSince(since) {
  const entries = await readAuditStore();
  if (!since) return entries;

  const sinceDate = new Date(since);
  if (Number.isNaN(sinceDate.getTime())) {
    throw AppError.badRequest(`Invalid "since" timestamp: "${since}". Expected ISO 8601.`);
  }

  return entries.filter((e) => new Date(e.timestamp) >= sinceDate);
}

function validateKey(key) {
  if (typeof key !== 'string' || !KEY_PATTERN.test(key)) {
    throw AppError.badRequest(
      'Flag key must be lowercase, alphanumeric, and hyphen-separated (e.g. "new-checkout-flow").'
    );
  }
}

function validateEnvironments(environments) {
  if (environments === undefined) return;
  if (!Array.isArray(environments) || environments.length === 0) {
    throw AppError.badRequest('environments must be a non-empty array.');
  }
  const invalid = environments.filter((e) => !config.supportedEnvironments.includes(e));
  if (invalid.length > 0) {
    throw AppError.badRequest(
      `Unsupported environment(s): ${invalid.join(', ')}. Allowed: ${config.supportedEnvironments.join(', ')}.`
    );
  }
}

async function listFlags({ environment } = {}) {
  const store = await readStore();
  const flags = Object.values(store);
  if (!environment) return flags;
  validateEnvironments([environment]);
  return flags.filter((flag) => flag.environments.includes(environment));
}

async function getFlag(key) {
  const store = await readStore();
  const flag = store[key];
  if (!flag) throw AppError.notFound(`Flag "${key}" not found.`);
  return flag;
}

async function createFlag({ key, description, enabled = false, environments, actor = 'unknown' }) {
  validateKey(key);
  validateEnvironments(environments);

  return serialize(async () => {
    const store = await readStore();
    if (store[key]) throw AppError.conflict(`Flag "${key}" already exists.`);

    const flag = {
      key,
      description: description || '',
      enabled: Boolean(enabled),
      environments: environments || [...config.supportedEnvironments],
      updatedBy: actor,
      updatedAt: new Date().toISOString(),
    };

    store[key] = flag;
    await writeStore(store);
    await appendAuditEntry({ key, action: 'create', previousState: null, newState: flag, actor });
    logger.info('flag created', { key, actor });
    return flag;
  });
}

async function updateFlag(key, updates, actor = 'unknown') {
  if ('environments' in updates) validateEnvironments(updates.environments);

  return serialize(async () => {
    const store = await readStore();
    const existing = store[key];
    if (!existing) throw AppError.notFound(`Flag "${key}" not found.`);

    const updated = {
      ...existing,
      ...(typeof updates.enabled === 'boolean' ? { enabled: updates.enabled } : {}),
      ...(typeof updates.description === 'string' ? { description: updates.description } : {}),
      ...(updates.environments ? { environments: updates.environments } : {}),
      updatedBy: actor,
      updatedAt: new Date().toISOString(),
    };

    store[key] = updated;
    await writeStore(store);
    await appendAuditEntry({ key, action: 'update', previousState: existing, newState: updated, actor });
    logger.info('flag updated', { key, actor, changes: Object.keys(updates) });
    return updated;
  });
}

async function toggleFlag(key, actor = 'unknown') {
  return serialize(async () => {
    const store = await readStore();
    const existing = store[key];
    if (!existing) throw AppError.notFound(`Flag "${key}" not found.`);

    const updated = {
      ...existing,
      enabled: !existing.enabled,
      updatedBy: actor,
      updatedAt: new Date().toISOString(),
    };

    store[key] = updated;
    await writeStore(store);
    await appendAuditEntry({ key, action: 'toggle', previousState: existing, newState: updated, actor });
    logger.info('flag toggled', { key, actor, enabled: updated.enabled });
    return updated;
  });
}

async function deleteFlag(key, actor = 'unknown') {
  return serialize(async () => {
    const store = await readStore();
    const existing = store[key];
    if (!existing) throw AppError.notFound(`Flag "${key}" not found.`);
    delete store[key];
    await writeStore(store);
    await appendAuditEntry({ key, action: 'delete', previousState: existing, newState: null, actor });
    logger.info('flag deleted', { key, actor });
  });
}

module.exports = {
  listFlags,
  getFlag,
  createFlag,
  updateFlag,
  toggleFlag,
  deleteFlag,
  validateKey,
  validateEnvironments,
  appendAuditEntry,
  getFlagHistory,
  getAuditSince,
};
