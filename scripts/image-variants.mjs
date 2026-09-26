// Generate responsive image variants in public/images. Safe to re-run: existing variants are skipped.
//
//   node scripts/image-variants.mjs
//
// For each source image (not already a variant):
//   <name>-1200.webp    width 1200, for srcset between the existing -800 and the full-size file
//   <name>-mobile.webp  full-height centre crop at 1.2:1, only for full-bleed "cover" heroes
//                       (home panorama, blog post heroes). On a phone those heroes show only the
//                       centre of a wide image, so a crop keeps the same pixels at half the bytes.
//
// Run it after adding a new blog hero image (public/images/blog/<slug>.webp).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const ROOT = fileURLToPath(new URL('../public/images/', import.meta.url));
const VARIANT = /-(800|1200|mobile)\.webp$/;
const QUALITY = 80;
const MOBILE_RATIO = 1.2;

const sources = [
  ...['about', 'hero-panorama', 'city-1', 'city-2', 'city-3', 'city-4', 'city-5', 'city-6',
      'service-1', 'service-2', 'service-3', 'service-4', 'tile-1', 'tile-2', 'tile-3', 'tile-4']
    .map((name) => ({ file: `${name}.webp`, cover: name === 'hero-panorama' })),
  ...fs.readdirSync(path.join(ROOT, 'blog'))
    .filter((f) => f.endsWith('.webp') && !VARIANT.test(f))
    .map((f) => ({ file: `blog/${f}`, cover: true })),
];

for (const { file, cover } of sources) {
  const src = path.join(ROOT, file);
  if (!fs.existsSync(src)) { console.warn(`skip (missing): ${file}`); continue; }
  const { width, height } = await sharp(src).metadata();
  const base = src.replace(/\.webp$/, '');

  if (width > 1200 && !fs.existsSync(`${base}-1200.webp`)) {
    await sharp(src).resize({ width: 1200 }).webp({ quality: QUALITY }).toFile(`${base}-1200.webp`);
    console.log(`made ${file.replace(/\.webp$/, '-1200.webp')}`);
  }

  if (cover && !fs.existsSync(`${base}-mobile.webp`)) {
    const cropWidth = Math.min(width, Math.round(height * MOBILE_RATIO));
    await sharp(src)
      .extract({ left: Math.round((width - cropWidth) / 2), top: 0, width: cropWidth, height })
      .webp({ quality: QUALITY })
      .toFile(`${base}-mobile.webp`);
    console.log(`made ${file.replace(/\.webp$/, '-mobile.webp')} (${cropWidth}x${height})`);
  }
}
