import ast
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs' / 'viva'
OUT.mkdir(parents=True, exist_ok=True)
roots = ['backend/app', 'backend/tests', 'backend/scripts', 'backend/alembic',
         'backend/evaluation', 'frontend/src', 'ml/swiftbench', 'ml/scripts',
         'ml/OCR', 'ml/kaggle', 'datasets/translation', 'datasets/localization',
         'notebooks', 'paper/experiments', 'scripts', 'synthetic_ticket_dataset']
files = sorted({p for root in roots for p in (ROOT / root).rglob('*')
                if p.suffix in {'.py', '.ts', '.tsx', '.ipynb'}
                and not any(x in p.parts for x in ['node_modules', '__pycache__', '.venv'])})
lines = ['# Swift source map', '', 'Generated from the working tree on 7 October 2026. '
         'This is a navigation index, not a claim that every file has been executed. '
         'Generated assets, dependency code, credentials and environment files are excluded.', '']
group = None
errors = []
for p in files:
    rel = p.relative_to(ROOT).as_posix()
    section = '/'.join(rel.split('/')[:2])
    if section != group:
        lines += ['## ' + section, '']
        group = section
    content = p.read_text(encoding='utf-8-sig')
    if p.suffix == '.ipynb':
        nb = json.loads(content)
        headings = []
        for cell in nb.get('cells', []):
            if cell.get('cell_type') == 'markdown':
                headings += [x.strip('# ').strip() for x in ''.join(cell.get('source', [])).splitlines() if x.startswith('#')]
        detail = '; '.join(headings[:5]) or 'Experiment notebook; inspect cells and saved outputs.'
    elif p.suffix == '.py':
        try:
            tree = ast.parse(content)
            doc = ast.get_docstring(tree) or ''
            names = [f'{n.name} (line {n.lineno})' for n in tree.body
                     if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
            detail = (doc.splitlines()[0] + ' ' if doc else '') + '; '.join(names)
            detail = detail or 'Module constants, imports or package initializer.'
        except SyntaxError as exc:
            errors.append(f'{rel}: {exc}')
            detail = 'Could not parse; inspect manually.'
    else:
        names = re.findall(r'^(?:export\s+)?(?:async\s+)?(?:function|class|interface|type)\s+(\w+)|^export\s+const\s+(\w+)', content, re.M)
        detail = '; '.join(a or b for a, b in names) or 'React/TypeScript module; inspect exports and handlers.'
    detail = detail.replace('|', '\\|').replace('\n', ' ')
    lines += [f'- [{rel}](../../{rel}): {detail}', '']
(OUT / 'SWIFT_SOURCE_MAP.md').write_text('\n'.join(lines), encoding='utf-8')
tracks = ['english', 'sinhala', 'singlish', 'tamil', 'tamilish']
datasets = {}
records = {}
for track in tracks:
    for split in ['train', 'test']:
        path = ROOT / 'datasets' / track / (split + '_labeled.csv')
        with path.open(encoding='utf-8-sig', newline='') as handle:
            rows = list(csv.DictReader(handle))
        records[track, split] = rows
        datasets[f'{track}/{split}'] = {
            'rows': len(rows), 'unique_ids': len({r['id'] for r in rows}),
            'category_counts': dict(Counter(r['category'] for r in rows)),
            'sentiment_counts': dict(Counter(r['sentiment'] for r in rows)),
            'priority_counts': dict(Counter(r['priority'] for r in rows))}
alignment = {}
for split in ['train', 'test']:
    base = {r['id']: r for r in records['english', split]}
    for track in tracks[1:]:
        other = {r['id']: r for r in records[track, split]}
        alignment[f'{track}/{split}'] = {
            'ids_match': set(base) == set(other),
            'label_mismatches': sum(any(base[k][c] != other[k][c] for c in ['category', 'priority', 'sentiment']) for k in set(base) & set(other)),
            'source_text_mismatches': sum(base[k]['text_en'] != other[k]['text_en'] for k in set(base) & set(other))}
manifest = json.loads((ROOT / 'ml/splits/split_manifest.json').read_text())
summary = {'audit_date': '2026-10-07', 'source_files_indexed': len(files),
           'python_parse_errors': errors, 'datasets': datasets, 'alignment': alignment,
           'split_sha': manifest['sha'], 'split_counts': manifest['counts']}
def score(rows, truth_key, task):
    labels = sorted({r[truth_key] for r in rows} | {r['y_pred'] for r in rows})
    f1s = []
    for label in (['Negative'] if task == 'sentiment' else labels):
        tp = sum(r[truth_key] == label and r['y_pred'] == label for r in rows)
        fp = sum(r[truth_key] != label and r['y_pred'] == label for r in rows)
        fn = sum(r[truth_key] == label and r['y_pred'] != label for r in rows)
        f1s.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0)
    return {'headline': sum(f1s) / len(f1s),
            'accuracy': sum(r[truth_key] == r['y_pred'] for r in rows) / len(rows)}
metrics = {}
for task, model, arm in [('intent', 'labse', 'class-weight'), ('sentiment', 'labse', 'class-weight'), ('priority', 'tfidf-svm', 'class-weight')]:
    path = ROOT / 'ml/predictions/runs' / f'{task}__{model}__tr-english-sinhala-singlish-tamil-tamilish__ev-all__arm-{arm}__test.csv'
    if not path.exists():
        continue
    with path.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    col = 'category' if task == 'intent' else task
    keyed = {(lang, r['id']): r[col] for lang in tracks for r in records[lang, 'test']}
    for r in rows:
        r['current_truth'] = keyed[r['language'], r['id']]
    metrics[task] = {'prediction_path': str(path.relative_to(ROOT)), 'n': len(rows),
                     'embedded_truth': score(rows, 'y_true', task),
                     'current_csv_truth': score(rows, 'current_truth', task),
                     'changed_truth_rows': sum(r['y_true'] != r['current_truth'] for r in rows),
                     'embedded_truth_counts': dict(Counter(r['y_true'] for r in rows)),
                     'current_truth_counts': dict(Counter(r['current_truth'] for r in rows))}
summary['saved_prediction_checks'] = metrics
print(json.dumps({'prediction_checks': metrics}, indent=2))
(OUT / 'SOURCE_AUDIT.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps({'indexed': len(files), 'parse_errors': errors,
                  'english_counts': {s: {k: v for k, v in datasets['english/' + s].items() if k != 'category_counts'} for s in ['train', 'test']},
                  'alignment': alignment, 'split': manifest['counts']}, indent=2))
