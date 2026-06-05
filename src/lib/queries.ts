// ── Shared fragments ──

const ARTICLE_CARD = /* groq */ `
  _id,
  title,
  "slug": slug.current,
  excerpt,
  "heroImage": heroImage.asset->url,
  "heroImageAlt": heroImage.alt,
  "category": category->{ title, "slug": slug.current },
  "author": author->{ name, "slug": slug.current, "image": image.asset->url },
  publishedAt,
  "tags": tags
`;

// ── Homepage ──

/** 首页文章列表（latest 6），含分类/作者/meta */
export const HOMEPAGE_ARTICLES = /* groq */ `
  *[_type == "article"] | order(publishedAt desc) [0...6] {
    ${ARTICLE_CARD}
  }
`;

// ── Category page ──

/** 分类页文章列表 */
export const CATEGORY_ARTICLES = /* groq */ `
  *[_type == "article" && category->slug.current == $category] | order(publishedAt desc) [0...12] {
    ${ARTICLE_CARD}
  }
`;

/** 分类 meta 信息 */
export const CATEGORY_META = /* groq */ `
  *[_type == "category" && slug.current == $category][0] {
    title,
    description
  }
`;

// ── Article detail ──

/** 单篇文章完整内容（含 body Portable Text、FAQs、Key Takeaways） */
export const ARTICLE_BY_SLUG = /* groq */ `
  *[_type == "article" && slug.current == $slug][0] {
    ${ARTICLE_CARD},
    body,
    "keyTakeaways": keyTakeaways,
    "faqs": faqs[] { question, answer },
    seoTitle,
    seoDescription
  }
`;

/** 所有文章 slug（用于 SSG 预渲染） */
export const ALL_ARTICLE_SLUGS = /* groq */ `
  *[_type == "article" && defined(slug.current)] {
    "slug": slug.current,
    "category": category->slug.current
  }
`;

// ── Sitemap / RSS ──

/** Sitemap 用：轻量文章列表 */
export const SITEMAP_ARTICLES = /* groq */ `
  *[_type == "article" && defined(slug.current)] | order(publishedAt desc) {
    "slug": slug.current,
    "category": category->slug.current,
    publishedAt
  }
`;

/** 全部分类 slug */
export const ALL_CATEGORY_SLUGS = /* groq */ `
  *[_type == "category" && defined(slug.current)] {
    "slug": slug.current
  }
`;
