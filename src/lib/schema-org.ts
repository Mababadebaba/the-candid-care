// ── JSON-LD Structured Data Generators ──

interface ArticleSEO {
  title: string;
  slug: string;
  excerpt: string;
  heroImage: string;
  heroImageAlt?: string;
  author: { name: string };
  category: { title: string };
  publishedAt: string;
  tags?: string[];
  seoTitle?: string;
  seoDescription?: string;
}

interface FAQ {
  question: string;
  answer: string;
}

const SITE_URL = "https://thecandidcare.com";

// ── Article Schema ──
export function generateArticleSchema(article: ArticleSEO) {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.seoTitle || article.title,
    description: article.seoDescription || article.excerpt,
    image: article.heroImage,
    datePublished: article.publishedAt,
    author: {
      "@type": "Person",
      name: article.author.name,
    },
    publisher: {
      "@type": "Organization",
      name: "The Candid Care",
    },
    url: `${SITE_URL}/${article.category.title.toLowerCase()}/${article.slug}`,
  };
}

// ── FAQ Schema (GEO) ──
export function generateFAQSchema(faqs: FAQ[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: faq.answer,
      },
    })),
  };
}

// ── Breadcrumb Schema ──
export function generateBreadcrumbSchema(items: { name: string; url: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: `${SITE_URL}${item.url}`,
    })),
  };
}

// ── Organization Schema (EEAT) ──
export function generateOrganizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "The Candid Care",
    url: SITE_URL,
    description: "Honest, science-backed wellness content — no fluff, no trends.",
    sameAs: [
      "https://twitter.com/thecandidcare",
      "https://instagram.com/thecandidcare",
    ],
  };
}

// ── WebSite Schema ──
export function generateWebSiteSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "The Candid Care",
    url: SITE_URL,
    potentialAction: {
      "@type": "SearchAction",
      target: `${SITE_URL}/search?q={search_term_string}`,
      "query-input": "required name=search_term_string",
    },
  };
}

// ── CollectionPage Schema (Category pages) ──
export function generateCollectionPageSchema(category: { title: string; slug: string }, articleUrls: string[]) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: `${category.title} — The Candid Care`,
    description: `Articles about ${category.title.toLowerCase()} — honest, research-backed wellness content.`,
    url: `${SITE_URL}/${category.slug}`,
    mainEntity: {
      "@type": "ItemList",
      itemListElement: articleUrls.map((url, i) => ({
        "@type": "ListItem",
        position: i + 1,
        url,
      })),
    },
  };
}
