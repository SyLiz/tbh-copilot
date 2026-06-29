// TBH Co-pilot service worker.
// Network-first for the app shell (html/js — a deploy always wins; cache only serves
// offline), cache-first for game art under assets/ (immutable pixel sprites).
// The HTML document is fetched with cache:'no-store' so a deploy is visible instantly
// instead of waiting out GitHub Pages' ~10-min HTTP cache on the unversioned dashboard.html.
const CACHE = 'tbh-shell-2';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  const isArt = u.pathname.includes('/assets/') || /icon-\d+\.png$/.test(u.pathname);
  if (isArt) {
    e.respondWith(caches.open(CACHE).then(async c => {
      const hit = await c.match(e.request);
      if (hit) return hit;
      const r = await fetch(e.request);
      if (r.ok) c.put(e.request, r.clone());
      return r;
    }));
    return;
  }
  // The HTML doc is unversioned (no ?v=), so bypass the HTTP cache to always get the
  // freshest deploy; the ?v-stamped JS bundles can use the normal network-first path.
  const isDoc = e.request.mode === 'navigate' || u.pathname.endsWith('.html') || u.pathname.endsWith('/');
  e.respondWith(
    fetch(isDoc ? new Request(e.request.url, { cache: 'no-store' }) : e.request).then(r => {
      if (r.ok) caches.open(CACHE).then(c => c.put(e.request, r.clone()));
      return r;
    }).catch(() => caches.match(e.request).then(hit => hit || Response.error()))
  );
});
