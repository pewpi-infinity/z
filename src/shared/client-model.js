/**
 * ClientModel - Mongoose-style model emulator for frontend use
 * Allows front-end code to operate without a backend using IndexedDB/localStorage
 */

class ClientModel {
  constructor(name, schema, storage) {
    this.name = name;
    this.schema = schema;
    this.storage = storage; // TokenService instance or compatible storage
    this.collection = name.toLowerCase() + 's';
  }

  /**
   * Create a new document
   */
  async create(data) {
    this.validateSchema(data);
    
    const doc = {
      _id: this.generateId(),
      ...data,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    await this.storage.createToken({
      hash: doc._id,
      type: this.collection,
      metadata: doc,
      ...doc
    });

    return doc;
  }

  /**
   * Find documents by query
   */
  async find(query = {}) {
    const allDocs = await this.storage.getAll({ type: this.collection });
    return allDocs
      .filter(doc => this.matchesQuery(doc.metadata, query))
      .map(doc => doc.metadata);
  }

  /**
   * Find one document by query
   */
  async findOne(query = {}) {
    const results = await this.find(query);
    return results.length > 0 ? results[0] : null;
  }

  /**
   * Find document by ID
   */
  async findById(id) {
    const doc = await this.storage.getByHash(id);
    return doc && doc.type === this.collection ? doc.metadata : null;
  }

  /**
   * Update document by ID
   */
  async findByIdAndUpdate(id, updates, options = {}) {
    const doc = await this.findById(id);
    if (!doc) {
      if (options.upsert) {
        return await this.create({ _id: id, ...updates });
      }
      throw new Error('Document not found');
    }

    const updatedDoc = {
      ...doc,
      ...updates,
      updatedAt: new Date()
    };

    await this.storage.updateToken(id, {
      metadata: updatedDoc,
      updated_at: updatedDoc.updatedAt.toISOString()
    });

    return options.new ? updatedDoc : doc;
  }

  /**
   * Update many documents
   */
  async updateMany(query, updates) {
    const docs = await this.find(query);
    let count = 0;

    for (const doc of docs) {
      await this.findByIdAndUpdate(doc._id, updates);
      count++;
    }

    return { modifiedCount: count };
  }

  /**
   * Delete document by ID
   */
  async findByIdAndDelete(id) {
    const doc = await this.findById(id);
    if (!doc) return null;

    await this.storage.deleteToken(id);
    return doc;
  }

  /**
   * Delete many documents
   */
  async deleteMany(query) {
    const docs = await this.find(query);
    let count = 0;

    for (const doc of docs) {
      await this.storage.deleteToken(doc._id);
      count++;
    }

    return { deletedCount: count };
  }

  /**
   * Count documents
   */
  async countDocuments(query = {}) {
    const docs = await this.find(query);
    return docs.length;
  }

  /**
   * Check if document exists
   */
  async exists(query) {
    const doc = await this.findOne(query);
    return doc !== null;
  }

  /**
   * Validate data against schema
   */
  validateSchema(data) {
    for (const [key, rules] of Object.entries(this.schema)) {
      // Required check
      if (rules.required && !(key in data)) {
        throw new Error(`Field '${key}' is required`);
      }

      // Type check
      if (key in data && rules.type) {
        const actualType = typeof data[key];
        const expectedType = rules.type.name.toLowerCase();
        
        if (actualType !== expectedType) {
          throw new Error(`Field '${key}' must be of type ${expectedType}`);
        }
      }

      // Enum check
      if (key in data && rules.enum) {
        if (!rules.enum.includes(data[key])) {
          throw new Error(`Field '${key}' must be one of: ${rules.enum.join(', ')}`);
        }
      }

      // Min/Max checks for numbers
      if (key in data && typeof data[key] === 'number') {
        if (rules.min !== undefined && data[key] < rules.min) {
          throw new Error(`Field '${key}' must be >= ${rules.min}`);
        }
        if (rules.max !== undefined && data[key] > rules.max) {
          throw new Error(`Field '${key}' must be <= ${rules.max}`);
        }
      }

      // Custom validator
      if (key in data && rules.validate) {
        if (!rules.validate(data[key])) {
          throw new Error(`Field '${key}' failed validation`);
        }
      }
    }
  }

  /**
   * Check if document matches query
   */
  matchesQuery(doc, query) {
    for (const [key, value] of Object.entries(query)) {
      // Handle operators
      if (typeof value === 'object' && value !== null) {
        if ('$eq' in value && doc[key] !== value.$eq) return false;
        if ('$ne' in value && doc[key] === value.$ne) return false;
        if ('$gt' in value && doc[key] <= value.$gt) return false;
        if ('$gte' in value && doc[key] < value.$gte) return false;
        if ('$lt' in value && doc[key] >= value.$lt) return false;
        if ('$lte' in value && doc[key] > value.$lte) return false;
        if ('$in' in value && !value.$in.includes(doc[key])) return false;
        if ('$nin' in value && value.$nin.includes(doc[key])) return false;
      } else {
        // Simple equality
        if (doc[key] !== value) return false;
      }
    }
    return true;
  }

  /**
   * Generate unique ID
   */
  generateId() {
    return `${this.collection}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Create index (no-op for client-side, but keeps API compatible)
   */
  async createIndex(fields) {
    console.log(`[ClientModel] Index created for ${this.name}:`, fields);
  }

  /**
   * Static method to create a model
   */
  static model(name, schema, storage) {
    return new ClientModel(name, schema, storage);
  }
}

// Pre-defined schema types for convenience
ClientModel.SchemaTypes = {
  String: String,
  Number: Number,
  Boolean: Boolean,
  Date: Date,
  Array: Array,
  Object: Object
};

// Export for use in different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ClientModel;
}
if (typeof window !== 'undefined') {
  window.ClientModel = ClientModel;
}
