#!/usr/bin/env python3
"""
Cloud publisher for GitHub Actions.
Reads publish-queue.json, finds the next unpublished article,
converts its frontmatter, and writes it to the Astro content collection.
"""

import re
import os
import json
import sys
from datetime import date, datetime
from pathlib import Path


TAG_MAP = {
    "فندق": "الفنادق والسياحة",
    "فنادق": "الفنادق والسياحة",
    "منتجع": "الفنادق والسياحة",
    "مصنع": "المصانع والمنشآت",
    "مصانع": "المصانع والمنشآت",
    "صناع": "المصانع والمنشآت",
    "مضخ": "الري والمزارع",
    "الري": "الري والمزارع",
    "بئر": "الري والمزارع",
    "آبار": "الري والمزارع",
    "مزرع": "الري والمزارع",
    "بطاري": "البطاريات والتخزين",
    "ليثيوم": "البطاريات والتخزين",
    "تخزين": "البطاريات والتخزين",
    "هجين": "الأنظمة الهجينة",
    "هايبرد": "الأنظمة الهجينة",
    "أوف جريد": "الأنظمة الهجينة",
    "صافي القياس": "اللوائح والربط بالشبكة",
    "هيئة الطاقة": "اللوائح والربط بالشبكة",
    "الكتاب الدوري": "اللوائح والربط بالشبكة",
    "معتمدة": "اللوائح والربط بالشبكة",
    "شروط": "اللوائح والربط بالشبكة",
    "الشبكة": "اللوائح والربط بالشبكة",
    "تقسيط": "التمويل والتقسيط",
    "قرض": "التمويل والتقسيط",
    "تمويل": "التمويل والتقسيط",
    "سعر": "الأسعار والتكاليف",
    "أسعار": "الأسعار والتكاليف",
    "اسعار": "الأسعار والتكاليف",
    "تكلفة": "الأسعار والتكاليف",
    "استرداد": "الأسعار والتكاليف",
    "شرائح": "الأسعار والتكاليف",
    "إنفرتر": "المعدات والمكونات",
    "انفرتر": "المعدات والمكونات",
    "ألواح": "المعدات والمكونات",
    "الواح": "المعدات والمكونات",
    "لوح": "المعدات والمكونات",
    "منزل": "المنازل والفيلات",
    "فيلا": "المنازل والفيلات",
    "عمارة": "المنازل والفيلات",
    "سطح": "المنازل والفيلات",
    "صيانة": "الصيانة والتشغيل",
    "تنظيف": "الصيانة والتشغيل",
    "أعطال": "الصيانة والتشغيل",
}


def guess_tag(title, keyword):
    text = f"{title} {keyword}".lower()
    for fragment, tag in TAG_MAP.items():
        if fragment in text:
            return tag
    return "الطاقة الشمسية"


def make_nav_title(title):
    nav = re.sub(r'\s*\|.*$', '', title)
    nav = re.sub(r'\s*[-–—]\s*شمس الوادي للطاقة الشمسية.*$', '', nav)
    nav = re.sub(r'\s*\(20\d{2}.*?\)', '', nav)
    nav = re.sub(r"\s*القاهرة:?\s*", ' ', nav).strip()
    if len(nav) <= 30:
        return nav
    words = nav.split()
    result = ''
    for w in words:
        test = f"{result} {w}".strip()
        if len(test) > 30:
            break
        result = test
    return result or nav[:30]


def extract_subtitle(body):
    text = re.sub(r'^#+\s+.*$', '', body, flags=re.MULTILINE)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'[*_`]', '', text)
    text = re.sub(r'\n+', ' ', text).strip()
    if not text:
        return ''
    if len(text) <= 200:
        return text
    cutoff = text[:200].rfind('.')
    if cutoff > 100:
        return text[:cutoff + 1]
    return text[:200].rsplit(' ', 1)[0] + '...'


def escape_yaml(s):
    if not s:
        return '""'
    s = s.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{s}"'


def normalize_key(key):
    return key.lower().replace(' ', '_').strip()


def get_field(fm, *keys):
    for k in keys:
        if k in fm and fm[k]:
            val = fm[k]
            if isinstance(val, list):
                return ', '.join(str(v) for v in val)
            return str(val).strip().strip('"').strip("'")
    return ''


def parse_frontmatter(content):
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None, content
    fm_text = match.group(1)
    body = content[match.end():]
    try:
        import yaml
        fm = yaml.safe_load(fm_text)
    except Exception:
        fm = {}
        for line in fm_text.split('\n'):
            if ':' in line and not line.startswith(' ') and not line.startswith('-'):
                key, _, val = line.partition(':')
                fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm or {}, body


def extract_faq(body):
    """Pull FAQ Q&A pairs from a '## FAQ'-style section for schema."""
    pairs = []
    faq_match = re.search(r'^##\s+.*(?:FAQ|Frequently Asked|الأسئلة الشائعة|أسئلة شائعة|الأسئلة المتكررة).*$', body, re.MULTILINE | re.IGNORECASE)
    if not faq_match:
        return pairs
    section = body[faq_match.end():]
    next_h2 = re.search(r'^##\s+', section, re.MULTILINE)
    if next_h2:
        section = section[:next_h2.start()]
    blocks = re.split(r'^###\s+', section, flags=re.MULTILINE)
    for block in blocks[1:]:
        lines = block.strip().split('\n', 1)
        if len(lines) == 2:
            question = lines[0].strip()
            answer = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', lines[1])
            answer = re.sub(r'[*_`]', '', answer)
            answer = re.sub(r'\n+', ' ', answer).strip()
            if question and answer:
                pairs.append({'question': question, 'answer': answer})
    # Fallback: bold-question format
    if not pairs:
        for m in re.finditer(r'^\*\*(.+?)\*\*\s*\n+([^\n#*][^\n]*(?:\n(?![#*\n])[^\n]*)*)', section, re.MULTILINE):
            q = m.group(1).strip()
            a = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', m.group(2))
            a = re.sub(r'[*_`]', '', a).strip()
            if q.endswith('?') and a:
                pairs.append({'question': q, 'answer': a})
    return pairs


def clean_body_links(body):
    body = re.sub(r'https?://shamselwadi\.com/', '/', body)
    body = re.sub(r'(\(/[^)]*?)\.html\)', r'\1/)', body)
    return body


def convert_and_write(draft_path, output_path, publish_date, slug):
    with open(draft_path, 'r', encoding='utf-8') as f:
        content = f.read()

    fm, body = parse_frontmatter(content)
    if fm is None:
        print(f"ERROR: No frontmatter in {draft_path}")
        return False

    normalized = {normalize_key(k): v for k, v in fm.items()}

    meta_title = get_field(normalized, 'meta_title', 'metatitle', 'title')
    meta_description = get_field(normalized, 'meta_description', 'metadescription', 'description')
    primary_keyword = get_field(normalized, 'primary_keyword', 'primarykeyword', 'keyword')
    secondary_keywords = get_field(normalized, 'secondary_keywords', 'secondarykeywords')

    h1_match = re.match(r'^#\s+(.+)$', body.strip(), re.MULTILINE)
    title = h1_match.group(1).strip() if h1_match else meta_title
    if h1_match:
        body = body[:h1_match.start()] + body[h1_match.end():]
        body = body.lstrip('\n')

    nav_title = make_nav_title(title)
    tag = guess_tag(title, primary_keyword)
    subtitle = extract_subtitle(body)
    body = clean_body_links(body)
    faq = extract_faq(body)
    canonical = f'https://shamselwadi.com/blog/{slug}/'

    lines = ['---']
    lines.append(f'title: {escape_yaml(title)}')
    lines.append(f'navTitle: {escape_yaml(nav_title)}')
    lines.append(f'metaTitle: {escape_yaml(meta_title)}')
    lines.append(f'metaDescription: {escape_yaml(meta_description)}')
    lines.append(f'primaryKeyword: {escape_yaml(primary_keyword)}')
    if secondary_keywords:
        lines.append(f'secondaryKeywords: {escape_yaml(secondary_keywords)}')
    lines.append(f'publishedDate: "{publish_date}"')
    lines.append(f'tag: {escape_yaml(tag)}')
    lines.append(f'subtitle: {escape_yaml(subtitle)}')
    lines.append(f'canonical: {escape_yaml(canonical)}')
    if faq:
        lines.append('faq:')
        for item in faq:
            lines.append(f'  - question: {escape_yaml(item["question"])}')
            lines.append(f'    answer: {escape_yaml(item["answer"])}')
    lines.append('---')
    lines.append('')

    output = '\n'.join(lines) + body

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)
    return True


def main():
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent

    queue_path = repo_root / 'publish-queue.json'
    if not queue_path.exists():
        print("ERROR: publish-queue.json not found")
        sys.exit(1)

    with open(queue_path, 'r', encoding='utf-8') as f:
        queue = json.load(f)

    next_item = None
    next_idx = None
    for i, item in enumerate(queue):
        if not item.get('published'):
            next_item = item
            next_idx = i
            break

    if next_item is None:
        print("All articles have been published!")
        commit_msg_path = script_dir / 'commit-msg.txt'
        with open(commit_msg_path, 'w') as f:
            f.write('No new articles to publish')
        sys.exit(0)

    draft_rel = next_item['draft']
    draft_path = repo_root / draft_rel
    slug = re.sub(r'-\d{4}-\d{2}-\d{2}\.md$', '', Path(draft_rel).name)
    slug = re.sub(r'\.md$', '', slug)
    output_path = repo_root / 'src' / 'content' / 'blog' / f'{slug}.md'
    publish_date = date.today().isoformat()

    print(f"Publishing: {slug}")

    if not draft_path.exists():
        print(f"ERROR: Draft file not found: {draft_path}")
        sys.exit(1)

    success = convert_and_write(str(draft_path), str(output_path), publish_date, slug)
    if not success:
        print("ERROR: Conversion failed")
        sys.exit(1)

    queue[next_idx]['published'] = True
    queue[next_idx]['publishedAt'] = datetime.utcnow().isoformat() + 'Z'

    with open(queue_path, 'w', encoding='utf-8') as f:
        json.dump(queue, f, indent=2)

    commit_msg_path = script_dir / 'commit-msg.txt'
    with open(commit_msg_path, 'w') as f:
        f.write(f'Publish blog post: {slug}')

    print(f"Successfully published: {slug}")


if __name__ == '__main__':
    main()
