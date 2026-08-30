'use strict';

const fsSync = require('fs');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const request = require('supertest');

// Config is read at require-time, so env vars must be set BEFORE any
// module that transitively requires ../src/config is loaded below.
const tmpDir = fsSync.mkdtempSync(path.join(os.tmpdir(), 'flags-route-test-'));
const tmpFile = path.join(tmpDir, 'flags.json');
process.env.DATA_FILE_PATH = tmpFile;
process.env.API_KEYS = 'test-key-123';

const createApp = require('../src/app');
const app = createApp();

afterAll(async () => {
  await fs.rm(path.dirname(tmpFile), { recursive: true, force: true });
});

beforeEach(async () => {
  await fs.writeFile(tmpFile, '{}', 'utf-8');
});

describe('GET /api/health', () => {
  test('returns 200 ok', async () => {
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
  });
});

describe('GET /api/flags', () => {
  test('returns empty list initially', async () => {
    const res = await request(app).get('/api/flags');
    expect(res.status).toBe(200);
    expect(res.body.flags).toEqual([]);
  });
});

describe('POST /api/flags', () => {
  test('rejects request without API key', async () => {
    const res = await request(app).post('/api/flags').send({ key: 'no-auth' });
    expect(res.status).toBe(401);
  });

  test('creates a flag with a valid API key', async () => {
    const res = await request(app)
      .post('/api/flags')
      .set('X-API-Key', 'test-key-123')
      .send({ key: 'new-flag', description: 'desc', enabled: true });
    expect(res.status).toBe(201);
    expect(res.body.key).toBe('new-flag');
    expect(res.body.enabled).toBe(true);
  });

  test('rejects malformed payload', async () => {
    const res = await request(app)
      .post('/api/flags')
      .set('X-API-Key', 'test-key-123')
      .send({ key: 'bad', enabled: 'yes' }); // enabled must be boolean
    expect(res.status).toBe(400);
  });
});

describe('POST /api/flags/:key/toggle', () => {
  test('toggles an existing flag', async () => {
    await request(app).post('/api/flags').set('X-API-Key', 'test-key-123').send({ key: 'togglable' });

    const res = await request(app).post('/api/flags/togglable/toggle').set('X-API-Key', 'test-key-123');
    expect(res.status).toBe(200);
    expect(res.body.enabled).toBe(true);
  });

  test('returns 404 for unknown flag', async () => {
    const res = await request(app).post('/api/flags/nope/toggle').set('X-API-Key', 'test-key-123');
    expect(res.status).toBe(404);
  });
});

describe('DELETE /api/flags/:key', () => {
  test('deletes a flag', async () => {
    await request(app).post('/api/flags').set('X-API-Key', 'test-key-123').send({ key: 'to-delete' });
    const res = await request(app).delete('/api/flags/to-delete').set('X-API-Key', 'test-key-123');
    expect(res.status).toBe(204);

    const getRes = await request(app).get('/api/flags/to-delete');
    expect(getRes.status).toBe(404);
  });
});
