import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    // Os ~120 SVGs dos Meteocons cabem no limite de inline do Vite e iriam
    // todos como base64 dentro do JS (dobrando o bundle), embora so um seja
    // exibido por vez. Emiti-los como arquivos deixa o browser buscar apenas
    // o icone da condicao atual. Restrito a SVG: os demais formatos mantem o
    // inline, que para eles continua sendo a escolha certa.
    assetsInlineLimit: (arquivo: string) =>
      arquivo.endsWith(".svg") ? false : undefined,
  },
  server: {
    proxy: {
      // Encaminha /api ao backend: o browser so ve a origem do Vite,
      // o que dispensa CORS em desenvolvimento.
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
