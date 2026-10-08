import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / 'docs/viva/SWIFT_VIVA_QUESTIONS_AND_ANSWERS.md'
content = path.read_text(encoding='utf-8')
counter = 0
def number(match):
    global counter
    counter += 1
    return f'### Q{counter:03d}. {match.group(1)}'
content = re.sub(r'^### Q\. (.+)$', number, content, flags=re.M)
if counter:
    sections = re.findall(r'^## (\d+)\. (.+)$', content, flags=re.M)
    toc = ['## Topic index', '', f'**{counter} questions and answers across {len(sections)} topics.**', '']
    for number_, title in sections:
        heading = number_ + '-'+ re.sub(r'[^a-z0-9 -]', '', title.lower()).replace(' ', '-')
        toc.append(f'- [{number_}. {title}](#{heading})')
    content = content.replace('## 1. Project explanation and contribution', '\n'.join(toc) + '\n\n## 1. Project explanation and contribution', 1)
    path.write_text(content, encoding='utf-8')

broken = []
for doc in (ROOT / 'docs/viva').glob('*.md'):
    text = doc.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith(('#', 'http:','https:')):
            continue
        dest = (doc.parent / target.split('#')[0]).resolve()
        if not dest.exists():
            broken.append((doc.name, target))
numbers = [int(n) for n in re.findall(r'^### Q(\d+)\.', content, re.M)]
print({'questions': len(numbers), 'sequential': numbers == list(range(1, len(numbers)+1)),
       'word_count': len(content.split()), 'broken_local_links': broken})
if broken or numbers != list(range(1, len(numbers)+1)):
    raise SystemExit(1)
