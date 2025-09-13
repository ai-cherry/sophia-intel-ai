// Voice Service Worker for Offline Support
const CACHE_NAME = 'sophia-voice-v1';
const urlsToCache = [
    '/',
    '/voice',
    '/static/js/voice.js',
    '/static/wasm/whisper-tiny.wasm'  // For offline STT
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});
