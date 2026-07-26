// 本地存储封装：带命名空间 + 容错

const NS = 'hudongzhimou:';

export const storage = {
  get(key, fallback = null) {
    try {
      const raw = localStorage.getItem(NS + key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch {
      return fallback;
    }
  },

  set(key, value) {
    try {
      localStorage.setItem(NS + key, JSON.stringify(value));
      return true;
    } catch {
      return false;
    }
  },

  remove(key) {
    try {
      localStorage.removeItem(NS + key);
    } catch { /* noop */ }
  },

  clear() {
    try {
      Object.keys(localStorage)
        .filter((k) => k.startsWith(NS))
        .forEach((k) => localStorage.removeItem(k));
    } catch { /* noop */ }
  },
};

/** 离线 FMS 记录队列：无后端时暂存本地，联网后同步 */
export const offlineQueue = {
  add(record) {
    const q = storage.get('fms_offline_queue', []);
    q.push(record);
    storage.set('fms_offline_queue', q);
  },
  all() {
    return storage.get('fms_offline_queue', []);
  },
  clear() {
    storage.set('fms_offline_queue', []);
  },
  size() {
    return storage.get('fms_offline_queue', []).length;
  },
};
