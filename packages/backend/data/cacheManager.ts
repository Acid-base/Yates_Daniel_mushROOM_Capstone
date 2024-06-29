import NodeCache from 'node-cache';

const cache = new NodeCache({ stdTTL: 3600 });

const cacheManager = {
  get: (key: string) => cache.get(key),
  set: (key: string, value: any) => cache.set(key, value),
};

export default cacheManager;
