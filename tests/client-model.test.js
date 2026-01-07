/**
 * Unit tests for ClientModel
 */

const ClientModel = require('../src/shared/client-model');
const TokenService = require('../src/shared/token-service');

describe('ClientModel', () => {
  let tokenService;
  let UserModel;

  const userSchema = {
    username: { type: String, required: true },
    email: { type: String, required: true },
    age: { type: Number, min: 0, max: 150 },
    role: { type: String, enum: ['admin', 'user', 'guest'] }
  };

  beforeEach(async () => {
    tokenService = new TokenService({ dbName: 'test-models' });
    await tokenService.init();
    UserModel = new ClientModel('User', userSchema, tokenService);
  });

  afterEach(async () => {
    await tokenService.clearAll();
    await tokenService.close();
  });

  describe('Initialization', () => {
    test('should create a model', () => {
      expect(UserModel.name).toBe('User');
      expect(UserModel.collection).toBe('users');
      expect(UserModel.schema).toEqual(userSchema);
    });

    test('should create model with static method', () => {
      const TestModel = ClientModel.model('Test', userSchema, tokenService);
      expect(TestModel.name).toBe('Test');
    });
  });

  describe('CRUD Operations', () => {
    test('should create a document', async () => {
      const user = await UserModel.create({
        username: 'testuser',
        email: 'test@example.com',
        age: 25,
        role: 'user'
      });

      expect(user).toHaveProperty('_id');
      expect(user.username).toBe('testuser');
      expect(user.email).toBe('test@example.com');
      expect(user).toHaveProperty('createdAt');
      expect(user).toHaveProperty('updatedAt');
    });

    test('should throw error for missing required field', async () => {
      await expect(UserModel.create({
        username: 'testuser'
        // email is required but missing
      })).rejects.toThrow('required');
    });

    test('should find all documents', async () => {
      await UserModel.create({ username: 'user1', email: 'user1@test.com' });
      await UserModel.create({ username: 'user2', email: 'user2@test.com' });

      const users = await UserModel.find();

      expect(users.length).toBe(2);
      expect(users[0].username).toBe('user1');
      expect(users[1].username).toBe('user2');
    });

    test('should find documents with query', async () => {
      await UserModel.create({ username: 'admin', email: 'admin@test.com', role: 'admin' });
      await UserModel.create({ username: 'user', email: 'user@test.com', role: 'user' });

      const admins = await UserModel.find({ role: 'admin' });

      expect(admins.length).toBe(1);
      expect(admins[0].username).toBe('admin');
    });

    test('should find one document', async () => {
      await UserModel.create({ username: 'user1', email: 'user1@test.com' });
      await UserModel.create({ username: 'user2', email: 'user2@test.com' });

      const user = await UserModel.findOne({ username: 'user1' });

      expect(user).toBeDefined();
      expect(user.username).toBe('user1');
    });

    test('should return null if document not found', async () => {
      const user = await UserModel.findOne({ username: 'nonexistent' });
      expect(user).toBeNull();
    });

    test('should find document by ID', async () => {
      const created = await UserModel.create({ username: 'testuser', email: 'test@test.com' });
      const found = await UserModel.findById(created._id);

      expect(found).toBeDefined();
      expect(found._id).toBe(created._id);
      expect(found.username).toBe('testuser');
    });

    test('should update document by ID', async () => {
      const user = await UserModel.create({ username: 'oldname', email: 'test@test.com' });
      
      const updated = await UserModel.findByIdAndUpdate(user._id, { username: 'newname' }, { new: true });

      expect(updated.username).toBe('newname');
      expect(updated.email).toBe('test@test.com');
    });

    test('should return old document when new option is false', async () => {
      const user = await UserModel.create({ username: 'oldname', email: 'test@test.com' });
      
      const result = await UserModel.findByIdAndUpdate(user._id, { username: 'newname' }, { new: false });

      expect(result.username).toBe('oldname');
    });

    test('should upsert when document not found', async () => {
      const newId = 'nonexistent_id';
      const result = await UserModel.findByIdAndUpdate(
        newId,
        { username: 'upserted', email: 'upsert@test.com' },
        { upsert: true, new: true }
      );

      expect(result.username).toBe('upserted');
    });

    test('should update many documents', async () => {
      await UserModel.create({ username: 'user1', email: 'user1@test.com', role: 'user' });
      await UserModel.create({ username: 'user2', email: 'user2@test.com', role: 'user' });

      const result = await UserModel.updateMany({ role: 'user' }, { role: 'member' });

      expect(result.modifiedCount).toBe(2);

      const users = await UserModel.find({ role: 'member' });
      expect(users.length).toBe(2);
    });

    test('should delete document by ID', async () => {
      const user = await UserModel.create({ username: 'testuser', email: 'test@test.com' });
      
      const deleted = await UserModel.findByIdAndDelete(user._id);

      expect(deleted).toBeDefined();
      expect(deleted.username).toBe('testuser');

      const found = await UserModel.findById(user._id);
      expect(found).toBeNull();
    });

    test('should delete many documents', async () => {
      await UserModel.create({ username: 'user1', email: 'user1@test.com', role: 'guest' });
      await UserModel.create({ username: 'user2', email: 'user2@test.com', role: 'guest' });
      await UserModel.create({ username: 'user3', email: 'user3@test.com', role: 'user' });

      const result = await UserModel.deleteMany({ role: 'guest' });

      expect(result.deletedCount).toBe(2);

      const remaining = await UserModel.find();
      expect(remaining.length).toBe(1);
    });
  });

  describe('Query Operators', () => {
    beforeEach(async () => {
      await UserModel.create({ username: 'user1', email: 'a@test.com', age: 20 });
      await UserModel.create({ username: 'user2', email: 'b@test.com', age: 30 });
      await UserModel.create({ username: 'user3', email: 'c@test.com', age: 40 });
    });

    test('should support $eq operator', async () => {
      const users = await UserModel.find({ age: { $eq: 30 } });
      expect(users.length).toBe(1);
      expect(users[0].age).toBe(30);
    });

    test('should support $ne operator', async () => {
      const users = await UserModel.find({ age: { $ne: 30 } });
      expect(users.length).toBe(2);
    });

    test('should support $gt operator', async () => {
      const users = await UserModel.find({ age: { $gt: 25 } });
      expect(users.length).toBe(2);
    });

    test('should support $gte operator', async () => {
      const users = await UserModel.find({ age: { $gte: 30 } });
      expect(users.length).toBe(2);
    });

    test('should support $lt operator', async () => {
      const users = await UserModel.find({ age: { $lt: 35 } });
      expect(users.length).toBe(2);
    });

    test('should support $lte operator', async () => {
      const users = await UserModel.find({ age: { $lte: 30 } });
      expect(users.length).toBe(2);
    });

    test('should support $in operator', async () => {
      const users = await UserModel.find({ age: { $in: [20, 40] } });
      expect(users.length).toBe(2);
    });

    test('should support $nin operator', async () => {
      const users = await UserModel.find({ age: { $nin: [20, 40] } });
      expect(users.length).toBe(1);
      expect(users[0].age).toBe(30);
    });
  });

  describe('Schema Validation', () => {
    test('should validate type', async () => {
      await expect(UserModel.create({
        username: 'test',
        email: 'test@test.com',
        age: 'not a number' // should be number
      })).rejects.toThrow('type');
    });

    test('should validate enum', async () => {
      await expect(UserModel.create({
        username: 'test',
        email: 'test@test.com',
        role: 'invalid_role'
      })).rejects.toThrow('enum');
    });

    test('should validate min value', async () => {
      await expect(UserModel.create({
        username: 'test',
        email: 'test@test.com',
        age: -5
      })).rejects.toThrow('>=');
    });

    test('should validate max value', async () => {
      await expect(UserModel.create({
        username: 'test',
        email: 'test@test.com',
        age: 200
      })).rejects.toThrow('<=');
    });

    test('should validate with custom validator', async () => {
      const EmailModel = new ClientModel('Email', {
        address: {
          type: String,
          required: true,
          validate: (val) => val.includes('@')
        }
      }, tokenService);

      await expect(EmailModel.create({
        address: 'invalid-email'
      })).rejects.toThrow('validation');
    });
  });

  describe('Utility Methods', () => {
    test('should count documents', async () => {
      await UserModel.create({ username: 'user1', email: 'user1@test.com' });
      await UserModel.create({ username: 'user2', email: 'user2@test.com' });

      const count = await UserModel.countDocuments();
      expect(count).toBe(2);
    });

    test('should count with query', async () => {
      await UserModel.create({ username: 'user1', email: 'user1@test.com', role: 'admin' });
      await UserModel.create({ username: 'user2', email: 'user2@test.com', role: 'user' });

      const count = await UserModel.countDocuments({ role: 'admin' });
      expect(count).toBe(1);
    });

    test('should check if document exists', async () => {
      await UserModel.create({ username: 'testuser', email: 'test@test.com' });

      const exists = await UserModel.exists({ username: 'testuser' });
      const notExists = await UserModel.exists({ username: 'nonexistent' });

      expect(exists).toBe(true);
      expect(notExists).toBe(false);
    });

    test('should generate unique IDs', () => {
      const id1 = UserModel.generateId();
      const id2 = UserModel.generateId();

      expect(id1).not.toBe(id2);
      expect(id1).toContain('users_');
      expect(id2).toContain('users_');
    });

    test('should create index (no-op)', async () => {
      // Should not throw
      await UserModel.createIndex({ username: 1 });
    });
  });

  describe('SchemaTypes', () => {
    test('should expose schema types', () => {
      expect(ClientModel.SchemaTypes).toHaveProperty('String');
      expect(ClientModel.SchemaTypes).toHaveProperty('Number');
      expect(ClientModel.SchemaTypes).toHaveProperty('Boolean');
      expect(ClientModel.SchemaTypes).toHaveProperty('Date');
      expect(ClientModel.SchemaTypes).toHaveProperty('Array');
      expect(ClientModel.SchemaTypes).toHaveProperty('Object');
    });
  });
});
