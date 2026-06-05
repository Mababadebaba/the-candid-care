import type { APIRoute } from "astro";
import { sanityClient } from "../lib/sanity";
import { HOMEPAGE_ARTICLES } from "../lib/queries";

const SITE_URL = "https://thecandidcare.com";

export const GET: APIRoute = async () => {
  let articles: {
    title: string;
    slug: string;
    excerpt?: string;
    category?: { slug: string };
    publishedAt: string;
  }[] = [];

  try {
    articles = await sanityClient.fetch(HOMEPAGE_ARTICLES);
  } catch {
    // Sanity not configured
  }

  const items = articles
    .map(
      (a) => `
    <item>
      <title><![CDATA[${a.title}]]></title>
      <link>${SITE_URL}/${a.category?.slug ?? "articles"}/${a.slug}</link>
      <description><![CDATA[${a.excerpt ?? ""}]]></description>
      <pubDate>${new Date(a.publishedAt).toUTCString()}</pubDate>
      <guid isPermaLink="true">${SITE_URL}/${a.category?.slug ?? "articles"}/${a.slug}</guid>
    </item>`
    )
    .join("");

  const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>The Candid Care</title>
    <description>Honest conversations about wellness, nutrition, and mindset.</description>
    <link>${SITE_URL}</link>
    <language>en</language>
    <atom:link href="${SITE_URL}/rss.xml" rel="self" type="application/rss+xml"/>
    ${items}
  </channel>
</rss>`;

  return new Response(rss, {
    headers: { "Content-Type": "application/xml; charset=utf-8" },
  });
};
