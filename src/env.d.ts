/// <reference types="astro/client" />

interface ImportMetaEnv {
  // Sanity CMS (public — 客户端可见)
  readonly PUBLIC_SANITY_PROJECT_ID: string;
  readonly PUBLIC_SANITY_DATASET: string;
  // Sanity CMS (private — 仅服务端)
  readonly SANITY_API_TOKEN: string;
  // Cloudinary
  readonly PUBLIC_CLOUDINARY_CLOUD_NAME: string;
  // Webhook / Deploy
  readonly SANITY_WEBHOOK_SECRET: string;
  readonly VERCEL_DEPLOY_HOOK_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
