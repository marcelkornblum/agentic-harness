---
trigger: model_decision
description: When building or editing public-facing HTML page shells, head metadata, social cards, or structured data
---

# Public-Page SEO & Structured Data

- **Document Metadata**: Set `<html lang="...">`, concise per-page `<title>` and `<meta name="description">` tags, and `<link rel="canonical">` to prevent duplicate indexing.
- **Social Cards**: Include Open Graph (`og:title`, `og:description`, `og:image`, `og:url`, `og:type`) and `twitter:*` metadata with high-resolution preview imagery on shareable pages.
- **Structured Data**: Emit Schema.org JSON-LD (`<script type="application/ld+json">`) matching visible page content (`Article`, `Product`, `FAQPage`, `BreadcrumbList`) where rich search metadata applies.
