import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import vercel from "@astrojs/vercel";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://thecandidcare.com",
  // Astro 5: static 模式默认支持服务端 API 端点
  integrations: [sitemap()],
  adapter: vercel(),
  vite: {
    plugins: [tailwindcss()],
  },
});
