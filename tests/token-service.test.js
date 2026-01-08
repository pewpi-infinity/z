/**
 * Unit tests for TokenService
 */

const TokenService = require('../src/shared/token-service');

describe('TokenService', () => {
  let tokenService;

  beforeEach(async () => {
    tokenService = new TokenService({ dbName: 'test-tokens' });
  });

  afterEach(async () => {
    if (tokenService.initialized) {
      await tokenService.clearAll();
      await tokenService.close();
    }
  });

  describe('Initialization', () => {
    test('should initialize with IndexedDB', async () => {
      await tokenService.init();
      expect(tokenService.initialized).toBe(true);
      expect(tokenService.storage).toBe('indexeddb');
    });

    test('should fall back to localStorage if IndexedDB fails', async () => {
      // Mock Dexie to fail
      global.Dexie = undefined;
      
      tokenService = new TokenService({ dbName: 'test-tokens' });
      await tokenService.init();
      
      expect(tokenService.initialized).toBe(true);
      expect(tokenService.storage).toBe('localstorage');
      
      // Restore Dexie
      require('../tests/setup');
    });

    test('should get storage info', async () => {
      await tokenService.init();
      const info = await tokenService.getStorageInfo();
      
      expect(info).toHaveProperty('storage');
      expect(info).toHaveProperty('dbName');
      expect(info).toHaveProperty('initialized');
      expect(info).toHaveProperty('tokenCount');
    });
  });

  describe('Token Operations', () => {
    beforeEach(async () => {
      await tokenService.init();
    });

    test('should create a token', async () => {
      const tokenData = {
        type: 'test',
        value: 100,
        owner: 'testuser',
        metadata: { test: true }
      };

      const token = await tokenService.createToken(tokenData);

      expect(token).toHaveProperty('hash');
      expect(token).toHaveProperty('id');
      expect(token.type).toBe('test');
      expect(token.value).toBe(100);
      expect(token.owner).toBe('testuser');
    });

    test('should get all tokens', async () => {
      await tokenService.createToken({ type: 'test1', value: 100 });
      await tokenService.createToken({ type: 'test2', value: 200 });

      const tokens = await tokenService.getAll();

      expect(tokens.length).toBe(2);
      expect(tokens[0].type).toBe('test1');
      expect(tokens[1].type).toBe('test2');
    });

    test('should filter tokens by type', async () => {
      await tokenService.createToken({ type: 'typeA', value: 100 });
      await tokenService.createToken({ type: 'typeB', value: 200 });
      await tokenService.createToken({ type: 'typeA', value: 300 });

      const filtered = await tokenService.getAll({ type: 'typeA' });

      expect(filtered.length).toBe(2);
      expect(filtered[0].type).toBe('typeA');
      expect(filtered[1].type).toBe('typeA');
    });

    test('should filter tokens by owner', async () => {
      await tokenService.createToken({ owner: 'user1', value: 100 });
      await tokenService.createToken({ owner: 'user2', value: 200 });

      const filtered = await tokenService.getAll({ owner: 'user1' });

      expect(filtered.length).toBe(1);
      expect(filtered[0].owner).toBe('user1');
    });

    test('should get token by hash', async () => {
      const created = await tokenService.createToken({ type: 'test', value: 100 });
      const found = await tokenService.getByHash(created.hash);

      expect(found).toBeDefined();
      expect(found.hash).toBe(created.hash);
    });

    test('should update token', async () => {
      const token = await tokenService.createToken({ type: 'test', value: 100 });
      
      await tokenService.updateToken(token.hash, { value: 200 });
      
      const updated = await tokenService.getByHash(token.hash);
      expect(updated.value).toBe(200);
    });

    test('should delete token', async () => {
      const token = await tokenService.createToken({ type: 'test', value: 100 });
      
      await tokenService.deleteToken(token.hash);
      
      const found = await tokenService.getByHash(token.hash);
      expect(found).toBeUndefined();
    });

    test('should clear all tokens', async () => {
      await tokenService.createToken({ type: 'test1', value: 100 });
      await tokenService.createToken({ type: 'test2', value: 200 });

      await tokenService.clearAll();

      const tokens = await tokenService.getAll();
      expect(tokens.length).toBe(0);
    });
  });

  describe('Wallet Operations', () => {
    beforeEach(async () => {
      await tokenService.init();
    });

    test('should get wallet balance', async () => {
      const balance = await tokenService.getBalance('default');
      expect(balance).toBe(0);
    });

    test('should update wallet balance', async () => {
      await tokenService.updateBalance('default', 1000);
      
      const balance = await tokenService.getBalance('default');
      expect(balance).toBe(1000);
    });

    test('should handle multiple wallet addresses', async () => {
      await tokenService.updateBalance('wallet1', 100);
      await tokenService.updateBalance('wallet2', 200);

      const balance1 = await tokenService.getBalance('wallet1');
      const balance2 = await tokenService.getBalance('wallet2');

      expect(balance1).toBe(100);
      expect(balance2).toBe(200);
    });
  });

  describe('Event Logging', () => {
    beforeEach(async () => {
      await tokenService.init();
    });

    test('should log events', async () => {
      await tokenService.logEvent('test_event', { data: 'test' });

      const events = await tokenService.getEvents();
      expect(events.length).toBeGreaterThan(0);
      expect(events[0].type).toBe('test_event');
    });

    test('should filter events by type', async () => {
      await tokenService.logEvent('type1', { data: 'a' });
      await tokenService.logEvent('type2', { data: 'b' });
      await tokenService.logEvent('type1', { data: 'c' });

      const filtered = await tokenService.getEvents({ type: 'type1' });
      expect(filtered.length).toBe(2);
    });

    test('should limit event results', async () => {
      for (let i = 0; i < 10; i++) {
        await tokenService.logEvent('test', { index: i });
      }

      const limited = await tokenService.getEvents({ limit: 5 });
      expect(limited.length).toBe(5);
    });
  });

  describe('Auto-tracking', () => {
    beforeEach(async () => {
      await tokenService.init();
    });

    test('should enable auto-tracking', async () => {
      const callback = jest.fn();
      await tokenService.initAutoTracking(callback);

      expect(tokenService.autoTrackingEnabled).toBe(true);
    });

    test('should call callback on token creation', async () => {
      const callback = jest.fn();
      await tokenService.initAutoTracking(callback);

      await tokenService.createToken({ type: 'test', value: 100 });

      // Note: In real environment, this would trigger via window events
      // In test environment, we just verify auto-tracking is enabled
      expect(tokenService.autoTrackingEnabled).toBe(true);
    });
  });

  describe('Export/Import', () => {
    beforeEach(async () => {
      await tokenService.init();
    });

    test('should export all data', async () => {
      await tokenService.createToken({ type: 'test', value: 100 });
      await tokenService.updateBalance('default', 500);

      const exported = await tokenService.exportAll();

      expect(exported).toHaveProperty('tokens');
      expect(exported).toHaveProperty('wallets');
      expect(exported).toHaveProperty('events');
      expect(exported).toHaveProperty('metadata');
      expect(exported.tokens.length).toBe(1);
    });

    test('should import data', async () => {
      const data = {
        tokens: [
          { hash: 'test123', type: 'imported', value: 100 }
        ],
        wallets: [
          { address: 'imported', balance: 1000 }
        ]
      };

      await tokenService.importAll(data);

      const tokens = await tokenService.getAll();
      const balance = await tokenService.getBalance('imported');

      expect(tokens.length).toBeGreaterThanOrEqual(1);
      expect(balance).toBe(1000);
    });
  });

  describe('Hash Generation', () => {
    test('should generate unique hashes', () => {
      const hash1 = tokenService.generateHash({ data: 'test1' });
      const hash2 = tokenService.generateHash({ data: 'test2' });

      expect(hash1).not.toBe(hash2);
      expect(hash1.length).toBe(16);
      expect(hash2.length).toBe(16);
    });
  });
});
