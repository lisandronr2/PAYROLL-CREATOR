/**
 * Service worker para poder consultar datos ya vistos (empresas,
 * trabajadores, contratos, convenios, nóminas y sus PDF) sin conexión.
 *
 * Solo cachea peticiones GET. Las peticiones de escritura (POST/PUT/PATCH/
 * DELETE) siempre van directas a la red y fallan igual que antes si no hay
 * conexión — esta app no soporta crear/editar datos estando offline.
 *
 * Estrategia: red primero, y si falla (sin conexión) se sirve la última
 * copia guardada. Cada respuesta correcta se guarda automáticamente, así
 * que "lo último que se vio estando online" queda disponible sin conexión.
 */
const CACHE_VERSION = "payroll-creator-v1";
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;
const SHELL_CACHE = `${CACHE_VERSION}-shell`;
const OFFLINE_URL = "/offline.html";

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll(["/", OFFLINE_URL]))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((key) => !key.startsWith(CACHE_VERSION)).map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

async function networkFirst(request, cacheName, fallbackUrl) {
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    if (cached) return cached;
    if (fallbackUrl) {
      const fallback = await cache.match(fallbackUrl);
      if (fallback) return fallback;
    }
    throw err;
  }
}

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Navegación entre páginas de la app: si no hay red, se sirve la copia
  // guardada de esa página o, si nunca se visitó estando online, la página
  // genérica de "sin conexión".
  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request, SHELL_CACHE, OFFLINE_URL));
    return;
  }

  // Solo cachear lecturas (GET). Las escrituras van siempre directas a la red.
  if (request.method !== "GET") return;

  event.respondWith(networkFirst(request, RUNTIME_CACHE));
});
