#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assemble Arabic governorate service-area pages from site-copy/<slug>.json.

Emits src/pages/<slug>/index.astro matching the existing hand-built pages
(solar-minya, solar-giza, ...) exactly: same sections, classes, inline styles
and JSON-LD shape. Run from the repo root:

    python build_governorate_pages.py            # build all NEW governorates
    python build_governorate_pages.py solar-aswan solar-qena   # build a subset

Never overwrites a page unless its slug is in NEW_GOVERNORATES.
"""
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent
COPY = REPO / "site-copy"
PAGES = REPO / "src" / "pages"

SITE = "https://shamselwadi.com"
BRAND = "شمس الوادي للطاقة الشمسية"
PHONE_DISPLAY = "+20 128 335 5408"
PHONE_TEL = "+201283355408"
EMAIL = "info@shamselwadi.com"
HUB = "القاهرة"
REGION = "مصر"
NICHE_SHORT = "الطاقة الشمسية"

# Existing pages, not rebuilt here — listed only so areaServed is complete.
EXISTING = ["الجيزة", "الإسكندرية", "الدقهلية", "الشرقية", "المنيا", "البحر الأحمر"]

# slug -> (arabic name, city image 1..6)
NEW_GOVERNORATES = {
    "solar-assiut":        ("أسيوط", 5),
    "solar-sohag":         ("سوهاج", 3),
    "solar-qena":          ("قنا", 5),
    "solar-luxor":         ("الأقصر", 6),
    "solar-aswan":         ("أسوان", 5),
    "solar-beni-suef":     ("بني سويف", 3),
    "solar-fayoum":        ("الفيوم", 3),
    "solar-new-valley":    ("الوادي الجديد", 5),
    "solar-gharbia":       ("الغربية", 4),
    "solar-menoufia":      ("المنوفية", 3),
    "solar-qalyubia":      ("القليوبية", 1),
    "solar-kafr-el-sheikh":("كفر الشيخ", 3),
    "solar-beheira":       ("البحيرة", 3),
    "solar-damietta":      ("دمياط", 2),
    "solar-port-said":     ("بورسعيد", 2),
    "solar-ismailia":      ("الإسماعيلية", 4),
    "solar-suez":          ("السويس", 4),
    "solar-south-sinai":   ("جنوب سيناء", 6),
    "solar-north-sinai":   ("شمال سيناء", 6),
    "solar-matrouh":       ("مطروح", 6),
}

ALL_AREAS = [HUB] + EXISTING + [v[0] for v in NEW_GOVERNORATES.values()]

FONT = "'IBM Plex Sans Arabic', 'Noto Kufi Arabic', system-ui, sans-serif"


def j(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(", ", ": "))


def org_node():
    return {
        "@type": ["ProfessionalService", "LocalBusiness"],
        "@id": f"{SITE}/#organization",
        "name": BRAND,
        "url": SITE,
        "logo": {"@type": "ImageObject", "url": f"{SITE}/images/og-image.webp"},
        "priceRange": "$$",
        "telephone": PHONE_DISPLAY,
        "email": EMAIL,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": HUB,
            "addressRegion": REGION,
            "addressCountry": "EG",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": 30.0444, "longitude": 31.2357},
        "areaServed": [
            {"@type": "City", "name": a, "addressRegion": REGION} for a in ALL_AREAS
        ],
    }


def build(slug, city, img, d):
    url = f"{SITE}/{slug}/"

    service_ld = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": f"{NICHE_SHORT} Service in {city}, {REGION}",
        "description": d["metaDescription"],
        "url": url,
        "provider": org_node(),
    }
    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "الرئيسية", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": d["h1"], "item": url},
        ],
    }
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f["q"],
                "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
            }
            for f in d["faq"]
        ],
    }

    svc_cards = "\n".join(
        f'''      <div style="background:#fff;border:1px solid #e3ded4;border-radius:10px;padding:26px;box-shadow:0 2px 8px rgba(14,77,110,0.05);">
        <h3 style="font-family:{FONT};font-size:18px;font-weight:800;color:#0A3D5C;margin:0 0 8px;">{s["title"]}</h3>
        <p style="font-size:14.5px;line-height:1.7;color:#555;margin:0;">{s["desc"]}</p>
      </div>'''
        for s in d["services"]
    )

    body_sections = "\n".join(
        f'''<section style="padding:0 24px;">
  <div style="max-width:860px;margin:0 auto 56px;">
    <h2 class="section-heading" style="font-size:clamp(22px,3vw,32px);margin:0 0 18px;">{sec["heading"]}</h2>
    <div class="rich">{sec["html"]}</div>
  </div>
</section>'''
        for sec in d["sections"]
    )

    faq_items = "\n".join(
        f'''      <div style="background:#fff;border:1px solid #e3ded4;border-radius:8px;padding:24px 28px;">
        <h3 style="font-family:{FONT};font-size:18px;font-weight:800;color:#0A3D5C;margin:0 0 10px;">{f["q"]}</h3>
        <p style="font-size:15px;line-height:1.75;color:#555;margin:0;">{f["a"]}</p>
      </div>'''
        for f in d["faq"]
    )

    return f'''---
import Layout from '../../layouts/Layout.astro';
---

<Layout
  title="{d["metaTitle"]}"
  description="{d["metaDescription"]}"
  canonical="{url}"
>
<Fragment slot="head">
<script type="application/ld+json">{j(service_ld)}</script>
<script type="application/ld+json">{j(breadcrumb_ld)}</script>
<script type="application/ld+json">{j(faq_ld)}</script>
<style is:global>
  .rich p {{ font-size: 16px; line-height: 1.8; color: #555; margin: 0 0 16px; }}
  .rich ul {{ padding-inline-start: 20px; margin: 0 0 16px; }}
  .rich li {{ font-size: 16px; line-height: 1.8; color: #555; margin-bottom: 8px; }}
  .rich strong {{ color: #2B3A44; }}
  .rich a {{ color: #1273A8; font-weight: 600; text-decoration: none; }}
  .rich a:hover {{ text-decoration: underline; }}
</style>
</Fragment>

<nav aria-label="مسار التنقل" style="max-width:1180px;margin:0 auto;padding:16px 24px;">
  <ol style="list-style:none;padding:0;margin:0;display:flex;gap:8px;font-size:13px;color:#888;">
    <li><a href="/" style="color:#1273A8;text-decoration:none;">الرئيسية</a></li>
    <li>/</li>
    <li style="color:#2B3A44;">{city}</li>
  </ol>
</nav>
<section style="background:linear-gradient(135deg, #08344B 0%, #0E4D6E 65%, #08344B 100%);padding:72px 24px;">
  <div class="hero-grid" style="max-width:1180px;margin:0 auto;display:grid;grid-template-columns:1.1fr 0.9fr;gap:56px;align-items:center;">
    <div>
      <span style="display:inline-block;margin-bottom:12px;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;background:rgba(143,208,234,0.18);color:#8FD0EA;border:1px solid rgba(143,208,234,0.3);">نطاق الخدمة</span>
      <h1 style="font-family:{FONT};font-weight:800;color:#fff;line-height:1.08;letter-spacing:-0.01em;font-size:clamp(30px,4.4vw,52px);margin:0 0 18px;">{d["h1"]}</h1>
      <p style="font-size:18px;line-height:1.7;color:rgba(255,255,255,0.85);max-width:540px;margin:0 0 28px;">{d["heroSub"]}</p>
      <div style="display:flex;flex-wrap:wrap;gap:16px;">
        <a href="tel:{PHONE_TEL}" class="btn-cream">اتصل الآن — <bdi>{PHONE_DISPLAY}</bdi></a>
        <a href="/#contact" class="btn-outline-white">اطلب عرض سعر</a>
      </div>
    </div>
    <div class="hero-img" style="border-radius:12px;overflow:hidden;box-shadow:0 24px 48px rgba(0,0,0,0.3);">
      <img src="/images/city-{img}.webp" alt="{d["h1"]}" width="800" height="533" style="width:100%;height:100%;object-fit:cover;display:block;" loading="eager" fetchpriority="high">
    </div>
  </div>
</section>
<style>
  @media (max-width: 860px) {{ .hero-grid {{ grid-template-columns: 1fr !important; }} .hero-img {{ max-height: 320px; }} }}
</style>
<section style="padding:72px 24px 40px;"><div style="max-width:860px;margin:0 auto;"><div class="rich">{d["introHtml"]}</div></div></section>
<section style="padding:0 24px 64px;"><div style="max-width:1100px;margin:0 auto;">
    <span class="kicker">ما ننفذه في {city}</span>
    <h2 class="section-heading" style="font-size:clamp(22px,3vw,32px);margin:0 0 28px;">خدماتنا في {city}</h2>
    <div class="feat-grid" style="display:grid;grid-template-columns:repeat(2,1fr);gap:20px;">
{svc_cards}
</div>
<style>
  @media (max-width: 860px) {{ .feat-grid {{ grid-template-columns: 1fr !important; }} }}
</style>
  </div></section>
{body_sections}
<section style="padding:72px 24px;background:#EAF5FB;">
  <div style="max-width:860px;margin:0 auto;">
    <span class="kicker">الأسئلة الشائعة</span>
    <h2 class="section-heading" style="font-size:clamp(24px,3.5vw,36px);margin:0 0 32px;">الأسئلة الشائعة</h2>
    <div style="display:flex;flex-direction:column;gap:16px;">
{faq_items}
    </div>
  </div>
</section>
<section style="background:linear-gradient(135deg, #0E4D6E 0%, #16648C 50%, #0E4D6E 100%);padding:64px 24px;text-align:center;">
  <h2 style="font-family:{FONT};font-size:clamp(26px,4vw,40px);font-weight:800;color:#fff;margin-bottom:16px;">لديك مشروع في {city}؟ تواصل معنا.</h2>
  <p style="font-size:16px;color:rgba(255,255,255,0.8);margin-bottom:28px;max-width:520px;margin-inline-start:auto;margin-inline-end:auto;">معاينة مجانية وعرض سعر مكتوب. دعم فني عند الأعطال.</p>
  <div style="display:flex;justify-content:center;gap:16px;flex-wrap:wrap;">
    <a href="tel:{PHONE_TEL}" class="btn-cream">اتصل الآن — <bdi>{PHONE_DISPLAY}</bdi></a>
    <a href="/#contact" class="btn-outline-white">اطلب عرض سعر</a>
  </div>
</section>

</Layout>
'''


REQUIRED = ["slug", "city", "metaTitle", "metaDescription", "h1", "heroSub",
            "introHtml", "services", "sections", "faq"]


def main():
    wanted = sys.argv[1:] or list(NEW_GOVERNORATES)
    built, missing, bad = [], [], []
    for slug in wanted:
        if slug not in NEW_GOVERNORATES:
            print(f"  SKIP {slug}: not in NEW_GOVERNORATES (refusing to touch it)")
            continue
        city, img = NEW_GOVERNORATES[slug]
        src = COPY / f"{slug}.json"
        if not src.exists():
            missing.append(slug)
            continue
        try:
            d = json.loads(src.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            bad.append(f"{slug}: invalid JSON ({e})")
            continue
        gaps = [k for k in REQUIRED if k not in d]
        if gaps:
            bad.append(f"{slug}: missing keys {gaps}")
            continue
        counts = (len(d["services"]), len(d["sections"]), len(d["faq"]))
        if counts != (4, 3, 4):
            bad.append(f"{slug}: expected 4/3/4 services/sections/faq, got {counts}")
            continue
        if '"' in d["metaTitle"] or '"' in d["metaDescription"]:
            bad.append(f"{slug}: double quote in metaTitle/metaDescription would break the Astro attribute")
            continue
        out = PAGES / slug / "index.astro"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build(slug, city, img, d), encoding="utf-8")
        built.append(slug)

    print(f"built {len(built)}: {', '.join(built) if built else '-'}")
    if missing:
        print(f"NO JSON YET ({len(missing)}): {', '.join(missing)}")
    if bad:
        print("REJECTED:")
        for b in bad:
            print("  " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
