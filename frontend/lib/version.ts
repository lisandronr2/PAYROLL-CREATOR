// Incrementar BUILD (y VERSION si el cambio es significativo) en cada
// actualización que se despliegue a producción. Mantener sincronizado con
// backend/app/version.py y el archivo VERSION en la raíz del proyecto.
export const VERSION = "1.0.0";
export const BUILD = "2741";
export const FULL_VERSION = `${VERSION}+${BUILD}`;
