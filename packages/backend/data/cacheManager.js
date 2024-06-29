// cache/cacheManager.js

const NodeCache = require('node-cache'); // Use require for CommonJS import
const cache = new NodeCache({ stdTTL: 3600 }); // Cache entries expire after 1 hour

const cacheManager = {
  get: (key) => cache.get(key),
  set: (key, value) => cache.set(key, value),
};

module.exports = cacheManager; // Export using CommonJS
