"""Verify the single, version-free latest reader using only Python stdlib."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from urllib.parse import urlparse, unquote
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def check_latest(root=ROOT):
    root = Path(root).resolve()
    book = root / 'e-book'
    manifest = json.loads((book / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['policy'] == 'single_latest_local_history', 'Unexpected storage policy'
    declared = manifest['sha256']
    assert declared and len(declared) == manifest['file_count']
    assert 'manifest.json' not in declared, 'Manifest cannot hash itself'
    checked_links = 0
    for name, expected in declared.items():
        rel = PurePosixPath(name)
        assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in name, name
        assert not re.search(r'(?:^|[/_])v\d', name, flags=re.I), name
        path = (book / name).resolve()
        assert path.is_relative_to(book.resolve()), name
        assert path.is_file() and sha256(path.read_bytes()).hexdigest() == expected, name
        if path.suffix.lower() not in ['.md', '.html', '.svg']:
            continue
        text = path.read_text(encoding='utf-8-sig')
        refs = re.findall(r'(?:src|href)=["\']([^"\']+)', text)
        refs += re.findall(r'url\(["\']?([^\)"\']+)', text)
        if path.suffix == '.md':
            refs += re.findall(r'!?\[[^\]]*\]\(([^)\s]+)\)', text)
        for ref in refs:
            ref = ref.strip()
            parsed = urlparse(ref)
            if not ref or ref.startswith('#') or parsed.scheme or parsed.netloc:
                continue
            if not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            assert target.is_relative_to(root) and target.exists(), (name, ref)
            checked_links += 1
    assert (book / 'ebook.pdf').read_bytes().startswith(b'%PDF-')
    return {
        'status': 'passed',
        'checked_at_seoul': datetime.now(timezone(timedelta(hours=9))).isoformat(),
        'scope': 'Latest declared bytes and local links only; no statistical or reader retest',
        'files_checked': len(declared),
        'local_links_checked': checked_links,
        'pdf_pages_recorded': manifest['pdf_pages'],
        'decision_page_recorded': manifest['decision_page'],
        'pdf_sha256': declared['ebook.pdf'],
        'human_or_field_test_performed': False,
    }


if __name__ == '__main__':
    print(json.dumps(check_latest(), ensure_ascii=False, indent=2))
