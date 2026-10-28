import re
from pathlib import Path

STOP = {
    'the', 'and', 'for', 'are', 'you', 'your', 'what', 'who', 'how', 'can',
    'about', 'with', 'this', 'that', 'have', 'does', 'tell', 'me', 'my',
}


def load_chunks(path='knowledge.txt'):
    p = Path(path)
    if not p.exists():
        return []
    text = p.read_text(encoding='utf-8')
    return [c.strip() for c in re.split(r'\n\s*\n', text) if c.strip()]


def _words(text):
    return {w for w in re.findall(r"[a-z0-9']+", text.lower())
            if w not in STOP and len(w) > 2}


def retrieve(query, chunks, k=2):
    q = _words(query)
    scored = []
    for chunk in chunks:
        overlap = len(q & _words(chunk))
        if overlap:
            scored.append((overlap, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:k]]
