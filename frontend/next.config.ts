import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        // El navegador nunca debe cachear el propio archivo del service
        // worker, para que los usuarios reciban siempre la última versión
        // de la lógica offline en cuanto se despliega un cambio.
        source: "/sw.js",
        headers: [
          { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
        ],
      },
    ];
  },
};

export default nextConfig;
