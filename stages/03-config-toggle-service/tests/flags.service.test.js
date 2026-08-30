'use strict';

const fsSync = require('fs');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');

// Point the service at an isolated temp file BEFORE requiring it, since
// config reads the env var at module-load time.
const tmpDir = fsSync.mkdtempSync(path.join(os.tmpdir(), 'flags-test-'));
const tmpFile = path.join(tmpDir, 'flags.json');
process.env.DATA_FILE_PATH = tmpFile;

// Require after env var is set so config picks it up.
const flagsService = require('../src/services/flags.service');

afterAll(async () => {
  await fs.rm(path.dirname(tmpFile), { recursive: true, force: true });
});

beforeEach(async () => {
  // Reset store to empty before each test for isolation.
  await fs.writeFile(tmpFile, '{}', 'utf-8');
});

describe('flags.service', () => {
  test('createFlag creates a new flag with defaults', async () => {
    const flag = await flagsService.createFlag({ key: 'test-flag', description: 'A test flag' });
    expect(flag.key).toBe('test-flag');
    expect(flag.enabled).toBe(false);
    expect(flag.environments).toEqual(['development', 'staging', 'production']);
  });

  test('createFlag rejects invalid keys', async () => {
    await expect(flagsService.createFlag({ key: 'Bad Key!' })).rejects.toThrow(/must be lowercase/);
  });

  test('createFlag rejects duplicate keys', async () => {
    await flagsService.createFlag({ key: 'dup-flag' });
    await expect(flagsService.createFlag({ key: 'dup-flag' })).rejects.toThrow(/already exists/);
  });

  test('getFlag throws 404-style error for missing flag', async () => {
    await expect(flagsService.getFlag('missing')).rejects.toThrow(/not found/);
  });

  test('toggleFlag flips the enabled state', async () => {
    await flagsService.createFlag({ key: 'toggle-me', enabled: false });
    const toggled = await flagsService.toggleFlag('toggle-me');
    expect(toggled.enabled).toBe(true);
    const toggledAgain = await flagsService.toggleFlag('toggle-me');
    expect(toggledAgain.enabled).toBe(false);
  });

  test('updateFlag only changes provided fields', async () => {
    await flagsService.createFlag({ key: 'update-me', description: 'original', enabled: false });
    const updated = await flagsService.updateFlag('update-me', { enabled: true });
    expect(updated.enabled).toBe(true);
    expect(updated.description).toBe('original');
  });

  test('deleteFlag removes the flag', async () => {
    await flagsService.createFlag({ key: 'delete-me' });
    await flagsService.deleteFlag('delete-me');
    await expect(flagsService.getFlag('delete-me')).rejects.toThrow(/not found/);
  });

  test('listFlags filters by environment', async () => {
    await flagsService.createFlag({ key: 'dev-only', environments: ['development'] });
    await flagsService.createFlag({ key: 'prod-only', environments: ['production'] });
    const devFlags = await flagsService.listFlags({ environment: 'development' });
    expect(devFlags.map((f) => f.key)).toEqual(['dev-only']);
  });

  test('concurrent creates do not corrupt the store', async () => {
    const creations = Array.from({ length: 10 }, (_, i) =>
      flagsService.createFlag({ key: `concurrent-${i}` })
    );
    await Promise.all(creations);
    const all = await flagsService.listFlags();
    expect(all).toHaveLength(10);
  });
});
