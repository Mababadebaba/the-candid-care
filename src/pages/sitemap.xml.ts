import type { APIRoute } from "astro";
import { sanityClient } from "../lib/sanity";
import { SITEMAP_ARTICLES, ALL_CATEGORY_SLUGS } from "../lib/queries";

const SITE_URL = "https://thecandidcare.com";

export const GET: APIRoute = async () => {
  const staticPages = [
    { url: "", priority: "1.0", changefreq: "daily" },
    { url: "about", priority: "0.7", changefreq: "monthly" },
  ];

  let articleEntries: { url: string; priority: string; changefreq: string }[] = [];
  let categoryEntries: { url: string; priority: string }[] = [];

  try {
    const [articles, categories] = await Promise.all([
      sanityClient.fetch<{ slug: string; category: string }[]>(SITEMAP_ARTICLES),
      sanityClient.fetch<{ slug: string }[]>(ALL_CATEGORY_SLUGS),
    ]);

    articleEntries = articles.map((a) => ({
      url: `${a.category}/${a.slug}`,
      priority: "0.8",
      changefreq: "weekly",
    }));

    categoryEntries = categories.map((c) => ({
      url: c.slug,
      priority: "0.7",
    }));
  } catch {
    // Sanity not configured — only static pages
  }

  const allEntries = [
    ...staticPages,
    ...categoryEntries.map((c) => ({ ...c, changefreq: "weekly" })),
    ...articleEntries,
  ];

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${allEntries
  .map(
    ({ url, priority, changefreq }) => `
  <url>
    <loc>${SITE_URL}/${url}</loc>
    <priority>${priority}</priority>
    <changefreq>${changefreq}</changefreq>
  </url>`
  )
  .join("")}
</urlset>`;

  return new Response(sitemap, {
    headers: { "Content-Type": "application/xml; charset=utf-8" },
  });
};
