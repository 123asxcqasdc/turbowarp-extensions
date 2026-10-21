#!/usr/bin/env python3
"""Fetch every extension .js and extract its registered extension id.

Writes /home/ulitos/extension_ids.json mapping url -> id (or null).
Uses a local cache (/home/ulitos/.ext_cache) to avoid re-downloading.
"""
import json, os, re, hashlib, urllib.request, concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.environ.get("TW_RAW", os.path.join(HERE, "turbowarp_extensions.json"))
OUT = os.environ.get("TW_IDS", os.path.join(HERE, "extension_ids.json"))
CACHE = os.environ.get("TW_CACHE", os.path.join(HERE, ".ext_cache"))
os.makedirs(CACHE, exist_ok=True)

data = json.load(open(RAW))
urls = sorted({e["url"] for e in data["extensions"]})
print("unique urls:", len(urls))


def fetch(url):
    key = hashlib.sha1(url.encode()).hexdigest()
    path = os.path.join(CACHE, key)
    if os.path.exists(path):
        return open(path, encoding="utf-8", errors="replace").read()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
    except Exception as ex:
        raw = b""
    text = decode_js(raw)
    open(path, "w", encoding="utf-8").write(text)
    return text


def decode_js(raw):
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    # UTF-16 without BOM shows up as many NUL bytes
    if raw.count(b"\x00") > len(raw) // 4:
        if raw[:1] == b"\x00":
            return raw.decode("utf-16-be", errors="replace")
        return raw.decode("utf-16-le", errors="replace")
    return raw.decode("utf-8", errors="replace")


ID_PATTERNS = [
    re.compile(r'id\s*:\s*["\']([^"\']+)["\']'),
    re.compile(r'\bstatic\s+id\s*=\s*["\']([^"\']+)["\']'),
    re.compile(r'\bextId\s*=\s*["\']([^"\']+)["\']'),
    re.compile(r'\bextension\s*\(\s*["\']([^"\']+)["\']'),
    re.compile(r'getInfo\s*\(\s*\)\s*\{[^}]*?\bid\s*:\s*["\']([^"\']+)["\']', re.S),
    re.compile(r'\.register\w*\(\s*["\']([^"\']+)["\']'),
    re.compile(r'register\w*\(\s*["\']([^"\']+)["\']'),
]


def extract_id(text):
    if not text:
        return None
    # Prefer an id declared close to a register call.
    reg = re.search(r'(?:extensions|Scratch\.extensions)\.register', text)
    if reg:
        window = text[max(0, reg.start() - 6000): reg.end() + 500]
        m = re.search(r'id\s*:\s*["\']([^"\']+)["\']', window)
        if m:
            return m.group(1)
    for rx in ID_PATTERNS:
        m = rx.search(text)
        if m:
            return m.group(1)
    return None


results = {}
def work(url):
    text = fetch(url)
    return url, extract_id(text)

with cf.ThreadPoolExecutor(max_workers=24) as ex:
    for url, eid in ex.map(work, urls):
        results[url] = eid

json.dump(results, open(OUT, "w"), ensure_ascii=False, indent=1)
found = sum(1 for v in results.values() if v)
print(f"ids found: {found}/{len(urls)}")
print("sample:", list(results.items())[:5])
