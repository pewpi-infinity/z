/**
 * Crypto Helpers - AES-GCM encryption and ECDH key exchange for P2P sync
 * Production-ready encryption with browser SubtleCrypto API
 */

class CryptoHelpers {
  constructor() {
    this.crypto = window.crypto || window.msCrypto;
    this.subtle = this.crypto.subtle;
  }

  /**
   * Generate AES-GCM key
   */
  async generateAESKey() {
    return await this.subtle.generateKey(
      {
        name: 'AES-GCM',
        length: 256
      },
      true,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Export AES key to raw format
   */
  async exportAESKey(key) {
    const raw = await this.subtle.exportKey('raw', key);
    return this.arrayBufferToBase64(raw);
  }

  /**
   * Import AES key from raw format
   */
  async importAESKey(base64Key) {
    const raw = this.base64ToArrayBuffer(base64Key);
    return await this.subtle.importKey(
      'raw',
      raw,
      { name: 'AES-GCM', length: 256 },
      true,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Encrypt data with AES-GCM
   */
  async encryptAES(data, key) {
    const iv = this.crypto.getRandomValues(new Uint8Array(12));
    const encoded = new TextEncoder().encode(JSON.stringify(data));

    const encrypted = await this.subtle.encrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      key,
      encoded
    );

    return {
      ciphertext: this.arrayBufferToBase64(encrypted),
      iv: this.arrayBufferToBase64(iv)
    };
  }

  /**
   * Decrypt data with AES-GCM
   */
  async decryptAES(encryptedData, key) {
    const ciphertext = this.base64ToArrayBuffer(encryptedData.ciphertext);
    const iv = this.base64ToArrayBuffer(encryptedData.iv);

    const decrypted = await this.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      key,
      ciphertext
    );

    const decoded = new TextDecoder().decode(decrypted);
    return JSON.parse(decoded);
  }

  /**
   * Generate ECDH key pair
   */
  async generateECDHKeyPair() {
    const keyPair = await this.subtle.generateKey(
      {
        name: 'ECDH',
        namedCurve: 'P-256'
      },
      true,
      ['deriveKey', 'deriveBits']
    );

    return keyPair;
  }

  /**
   * Export ECDH public key
   */
  async exportECDHPublicKey(publicKey) {
    const exported = await this.subtle.exportKey('spki', publicKey);
    return this.arrayBufferToBase64(exported);
  }

  /**
   * Import ECDH public key
   */
  async importECDHPublicKey(base64Key) {
    const spki = this.base64ToArrayBuffer(base64Key);
    return await this.subtle.importKey(
      'spki',
      spki,
      {
        name: 'ECDH',
        namedCurve: 'P-256'
      },
      true,
      []
    );
  }

  /**
   * Derive shared AES key from ECDH key exchange
   */
  async deriveSharedKey(privateKey, publicKey) {
    return await this.subtle.deriveKey(
      {
        name: 'ECDH',
        public: publicKey
      },
      privateKey,
      {
        name: 'AES-GCM',
        length: 256
      },
      true,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Perform complete ECDH key exchange
   * Returns: { myPublicKey, sharedKey }
   */
  async performKeyExchange(theirPublicKeyBase64) {
    // Generate our key pair
    const myKeyPair = await this.generateECDHKeyPair();
    
    // Export our public key
    const myPublicKey = await this.exportECDHPublicKey(myKeyPair.publicKey);
    
    // Import their public key
    const theirPublicKey = await this.importECDHPublicKey(theirPublicKeyBase64);
    
    // Derive shared key
    const sharedKey = await this.deriveSharedKey(myKeyPair.privateKey, theirPublicKey);
    
    return {
      myPublicKey,
      sharedKey
    };
  }

  /**
   * Hash data with SHA-256
   */
  async hash(data) {
    const encoded = new TextEncoder().encode(data);
    const hashBuffer = await this.subtle.digest('SHA-256', encoded);
    return this.arrayBufferToHex(hashBuffer);
  }

  /**
   * Generate random bytes
   */
  randomBytes(length) {
    return this.crypto.getRandomValues(new Uint8Array(length));
  }

  /**
   * Convert ArrayBuffer to Base64
   */
  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  /**
   * Convert Base64 to ArrayBuffer
   */
  base64ToArrayBuffer(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  /**
   * Convert ArrayBuffer to Hex string
   */
  arrayBufferToHex(buffer) {
    const bytes = new Uint8Array(buffer);
    return Array.from(bytes)
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  /**
   * Generate secure token
   */
  generateSecureToken(length = 32) {
    const bytes = this.randomBytes(length);
    return this.arrayBufferToHex(bytes);
  }
}

/**
 * P2P Sync Manager - WebRTC DataChannel with configurable signaling
 * Stub implementation for future P2P synchronization
 */
class P2PSyncManager {
  constructor(options = {}) {
    this.signalingUrl = options.signalingUrl || 'wss://signal.pewpi.io';
    this.turnServers = options.turnServers || [
      {
        urls: 'stun:stun.l.google.com:19302'
      }
    ];
    this.crypto = new CryptoHelpers();
    this.connections = new Map();
    this.enabled = false;
  }

  /**
   * Initialize P2P sync (stub)
   */
  async init() {
    console.log('[P2PSyncManager] Initializing P2P sync...');
    console.log('[P2PSyncManager] Signaling URL:', this.signalingUrl);
    console.log('[P2PSyncManager] TURN servers:', this.turnServers);
    
    // This is a stub - full WebRTC implementation would go here
    this.enabled = true;
    
    return {
      success: true,
      message: 'P2P sync initialized (stub mode)'
    };
  }

  /**
   * Connect to peer (stub)
   */
  async connectToPeer(peerId) {
    console.log('[P2PSyncManager] Connecting to peer:', peerId);
    
    // Generate ECDH key pair for this connection
    const keyPair = await this.crypto.generateECDHKeyPair();
    const publicKey = await this.crypto.exportECDHPublicKey(keyPair.publicKey);
    
    // Store connection stub
    this.connections.set(peerId, {
      peerId,
      status: 'connecting',
      publicKey,
      keyPair,
      connected: false
    });
    
    return {
      success: true,
      peerId,
      publicKey
    };
  }

  /**
   * Send data to peer (stub)
   */
  async sendToPeer(peerId, data) {
    const connection = this.connections.get(peerId);
    if (!connection) {
      throw new Error('Not connected to peer');
    }
    
    console.log('[P2PSyncManager] Sending data to peer:', peerId, data);
    
    return {
      success: true,
      message: 'Data sent (stub mode)'
    };
  }

  /**
   * Disconnect from peer (stub)
   */
  async disconnectFromPeer(peerId) {
    this.connections.delete(peerId);
    console.log('[P2PSyncManager] Disconnected from peer:', peerId);
    
    return {
      success: true,
      peerId
    };
  }

  /**
   * Get connection status
   */
  getConnectionStatus(peerId) {
    const connection = this.connections.get(peerId);
    return connection ? connection.status : 'disconnected';
  }

  /**
   * List all connections
   */
  listConnections() {
    return Array.from(this.connections.entries()).map(([peerId, conn]) => ({
      peerId,
      status: conn.status,
      connected: conn.connected
    }));
  }

  /**
   * Configure signaling server
   */
  setSignalingUrl(url) {
    this.signalingUrl = url;
    console.log('[P2PSyncManager] Signaling URL updated:', url);
  }

  /**
   * Configure TURN servers
   */
  setTurnServers(servers) {
    this.turnServers = servers;
    console.log('[P2PSyncManager] TURN servers updated:', servers);
  }
}

// Export for use in different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { CryptoHelpers, P2PSyncManager };
}
if (typeof window !== 'undefined') {
  window.CryptoHelpers = CryptoHelpers;
  window.P2PSyncManager = P2PSyncManager;
}
