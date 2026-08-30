'use strict';

const fsSync = require('fs');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');

// Point the service at an isolated temp file BEFORE requiring it, since
// config reads the env var at module-load time. AUDIT_FILE_PATH is derived
// from path.dirname(DATA_FILE_PATH), so this isolates flag_audit.json too.
const tmpDir = fsSync.mkdtempSync(path.join(os.tmpdir(), 'flags-audit-test-'));
const tmpFile = path.join(tmpDir, 'flags.json');
process.env.DATA_FILE_PATH = tmpFile;

const flagsService = require('../src/services/flags.service');

afterAll(async () => {
  await fs.rm(path.dirname(tmpFile), { recursive: true, force: true });
});

beforeEach(async () => {
  // Reset both stores before each test for isolation.
  await fs.writeFile(tmpFile, '{}', 'utf-8');
  const auditFile = path.join(path.dirname(tmpFile), 'flag_audit.json');
  await fs.rm(auditFile, { force: true });
});

describe('flag audit log', () => {
  test('createFlag appends a create entry with previousState null', async () => {
    await flagsService.createFlag({ key: 'audit-me', description: 'x' });

    const history = await flagsService.getFlagHistory('audit-me');

    expect(history).toHaveLength(1);
    expect(history[0]).toMatchObject({
      key: 'audit-me',
      action: 'create',
      previousState: null,
    });
    expect(history[0].newState).toMatchObject({ key: 'audit-me' });
    expect(history[0].timestamp).toBeDefined();
  });

  test('updateFlag appends an update entry with both previous and new state', async () => {
    await flagsService.createFlag({ key: 'audit-me', description: 'x' });
    await flagsService.updateFlag('audit-me', { enabled: true });

    const history = await flagsService.getFlagHistory('audit-me');

    expect(history).toHaveLength(2);
    const updateEntry = history[1];
    expect(updateEntry.action).toBe('update');
    expect(updateEntry.previousState.enabled).toBe(false);
    expect(updateEntry.newState.enabled).toBe(true);
  });

  test('toggleFlag appends a toggle entry reflecting the flip', async () => {
    await flagsService.createFlag({ key: 'audit-me', enabled: false });
    await flagsService.toggleFlag('audit-me');

    const history = await flagsService.getFlagHistory('audit-me');
    const toggleEntry = history[history.length - 1];

    expect(toggleEntry.action).toBe('toggle');
    expect(toggleEntry.previousState.enabled).toBe(false);
    expect(toggleEntry.newState.enabled).toBe(true);
  });

  test('deleteFlag appends a delete entry with newState null', async () => {
    await flagsService.createFlag({ key: 'audit-me' });
    await flagsService.deleteFlag('audit-me');

    const history = await flagsService.getFlagHistory('audit-me');
    const deleteEntry = history[history.length - 1];

    expect(deleteEntry.action).toBe('delete');
    expect(deleteEntry.newState).toBeNull();
    expect(deleteEntry.previousState).toMatchObject({ key: 'audit-me' });
  });

  test('getFlagHistory only returns entries for the requested key', async () => {
    await flagsService.createFlag({ key: 'flag-a' });
    await flagsService.createFlag({ key: 'flag-b' });
    await flagsService.toggleFlag('flag-a');

    const historyA = await flagsService.getFlagHistory('flag-a');
    const historyB = await flagsService.getFlagHistory('flag-b');

    expect(historyA).toHaveLength(2);
    expect(historyB).toHaveLength(1);
    expect(historyA.every((e) => e.key === 'flag-a')).toBe(true);
  });

  test('getFlagHistory returns an empty array for a flag with no audit entries', async () => {
    // Simulates a pre-seeded flag that was never written through the
    // audited create/update/toggle/delete path — documented behavior,
    // not a bug.
    const history = await flagsService.getFlagHistory('never-audited');
    expect(history).toEqual([]);
  });

  test('getAuditSince with no argument returns every entry across all flags', async () => {
    await flagsService.createFlag({ key: 'flag-a' });
    await flagsService.createFlag({ key: 'flag-b' });

    const all = await flagsService.getAuditSince();

    expect(all).toHaveLength(2);
  });

  test('getAuditSince filters entries strictly before the given timestamp', async () => {
    await flagsService.createFlag({ key: 'old-flag' });

    // Timestamp comfortably after the entry just created above.
    const cutoff = new Date(Date.now() + 60_000).toISOString();
    await flagsService.createFlag({ key: 'new-flag' });

    const recent = await flagsService.getAuditSince(cutoff);

    expect(recent).toEqual([]);
  });

  test('getAuditSince rejects an unparseable timestamp', async () => {
    await expect(flagsService.getAuditSince('not-a-date')).rejects.toThrow(/Invalid "since" timestamp/);
  });

  test('appendAuditEntry does not deadlock when called from within an already-serialized mutation', async () => {
    // Regression test for the double-serialize deadlock: createFlag calls
    // appendAuditEntry from inside its own serialize() block. If
    // appendAuditEntry ever gets wrapped in its own serialize() call, this
    // will hang instead of resolving.
    await expect(flagsService.createFlag({ key: 'no-deadlock' })).resolves.toBeDefined();
  }, 2000);
});

describe('flag audit routing', () => {
  const request = require('supertest');
  const createApp = require('../src/app');
  const app = createApp();

  test('GET /api/flags/audit is not swallowed by the /:key route', async () => {
    // Regression test for route registration order: "audit" must not be
    // matched as a flag key by GET /api/flags/:key.
    const res = await request(app).get('/api/flags/audit');

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('entries');
    expect(res.body).not.toHaveProperty('key', 'audit');
  });

  test('GET /api/flags/audit?since= filters via the HTTP layer', async () => {
    await flagsService.createFlag({ key: 'via-http' });
    const cutoff = new Date(Date.now() + 60_000).toISOString();

    const res = await request(app).get('/api/flags/audit').query({ since: cutoff });

    expect(res.status).toBe(200);
    expect(res.body.entries).toEqual([]);
  });

  test('GET /api/flags/audit?since=garbage returns 400', async () => {
    const res = await request(app).get('/api/flags/audit').query({ since: 'garbage' });

    expect(res.status).toBe(400);
    expect(res.body.error.code).toBe('BAD_REQUEST');
  });

  test('GET /api/flags/:key/history returns count and history for a real key', async () => {
    await flagsService.createFlag({ key: 'http-history' });
    await flagsService.toggleFlag('http-history');

    const res = await request(app).get('/api/flags/http-history/history');

    expect(res.status).toBe(200);
    expect(res.body.key).toBe('http-history');
    expect(res.body.count).toBe(2);
    expect(res.body.history).toHaveLength(2);
  });
});
