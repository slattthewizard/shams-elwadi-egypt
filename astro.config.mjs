import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import fs from 'node:fs';

// Sitemap <lastmod> for blog posts, read from frontmatter (updatedDate, else publishedDate).
// Other pages get no lastmod: a missing date is better than a guessed one.
const BLOG_DIR = new URL('./src/content/blog/', import.meta.url);
const postDates = {};
for (const file of fs.readdirSync(BLOG_DIR)) {
  if (!file.endsWith('.md')) continue;
  const frontmatter = fs.readFileSync(new URL(file, BLOG_DIR), 'utf8').split(/^---\s*$/m)[1] ?? '';
  const pick = (key) => frontmatter.match(new RegExp(`^${key}:\\s*"?(\\d{4}-\\d{2}-\\d{2})"?`, 'm'))?.[1];
  const date = pick('updatedDate') ?? pick('publishedDate');
  if (date) postDates[`https://shamselwadi.com/blog/${file.replace(/\.md$/, '')}/`] = date;
}
const latestPostDate = Object.values(postDates).sort().at(-1);

export default defineConfig({
  site: 'https://shamselwadi.com',
  trailingSlash: 'always',
  integrations: [
    sitemap({
      serialize(item) {
        if (postDates[item.url]) item.lastmod = postDates[item.url];
        else if (item.url === 'https://shamselwadi.com/blog/' && latestPostDate) item.lastmod = latestPostDate;
        return item;
      },
    }),
  ],
});
