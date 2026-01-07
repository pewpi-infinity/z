// Jest setup file
// Mock Dexie for testing
global.Dexie = class MockDexie {
  constructor(dbName) {
    this.dbName = dbName;
    this.stores = {};
    this._isOpen = false;
  }

  version(num) {
    return {
      stores: (schema) => {
        this.stores = schema;
        return this;
      }
    };
  }

  async open() {
    this._isOpen = true;
    // Create mock tables
    for (const storeName of Object.keys(this.stores)) {
      this[storeName] = new MockTable(storeName);
    }
  }

  async close() {
    this._isOpen = false;
  }
};

class MockTable {
  constructor(name) {
    this.name = name;
    this.data = [];
    this.nextId = 1;
  }

  async add(item) {
    const id = this.nextId++;
    this.data.push({ ...item, id });
    return id;
  }

  async toArray() {
    return [...this.data];
  }

  async count() {
    return this.data.length;
  }

  async clear() {
    this.data = [];
  }

  where(field) {
    return {
      equals: (value) => ({
        first: async () => this.data.find(item => item[field] === value),
        toArray: async () => this.data.filter(item => item[field] === value),
        delete: async () => {
          const initialLength = this.data.length;
          this.data = this.data.filter(item => item[field] !== value);
          return initialLength - this.data.length;
        },
        modify: async (updates) => {
          let count = 0;
          this.data.forEach((item, index) => {
            if (item[field] === value) {
              this.data[index] = { ...item, ...updates };
              count++;
            }
          });
          return count;
        }
      })
    };
  }

  reverse() {
    return {
      limit: (n) => ({
        toArray: async () => [...this.data].reverse().slice(0, n)
      })
    };
  }

  async update(id, updates) {
    const index = this.data.findIndex(item => item.id === id);
    if (index >= 0) {
      this.data[index] = { ...this.data[index], ...updates };
      return 1;
    }
    return 0;
  }
}

// Mock localStorage
const localStorageMock = {
  store: {},
  getItem(key) {
    return this.store[key] || null;
  },
  setItem(key, value) {
    this.store[key] = value;
  },
  removeItem(key) {
    delete this.store[key];
  },
  clear() {
    this.store = {};
  }
};

global.localStorage = localStorageMock;

// Mock window.crypto for tests
global.crypto = {
  getRandomValues: (arr) => {
    for (let i = 0; i < arr.length; i++) {
      arr[i] = Math.floor(Math.random() * 256);
    }
    return arr;
  },
  subtle: {
    generateKey: jest.fn(),
    encrypt: jest.fn(),
    decrypt: jest.fn(),
    exportKey: jest.fn(),
    importKey: jest.fn(),
    deriveKey: jest.fn(),
    digest: jest.fn()
  }
};

// Clear mocks before each test
beforeEach(() => {
  localStorageMock.clear();
  jest.clearAllMocks();
});
