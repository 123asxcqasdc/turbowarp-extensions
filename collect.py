#!/usr/bin/env python3
"""Collect TurboWarp extension catalogs from 10 galleries into a raw catalog.

Usage:
    python3 collect.py [--out /path/to/turbowarp_extensions.json]

Sources (galleries, not single repos):
  official     https://extensions.turbowarp.org/
  sharkpool    https://sharkpool-sp.github.io/SharkPools-Extensions/
  penguinmod   https://extensions.penguinmod.com/
  dimka-10     https://dimka-10.github.io/Scratch-Extensions-Gallery.github.io/
  turbowarp-cn https://github.com/turbowarp-cn/cn-extensions
  bluedome77   https://github.com/BlueDome77/Turbowarp-Extension-List
  mistwarp     https://extensions.mistium.com/
  dinosaurmod  https://dinosaurmod.github.io/extensions/
  snail-ide    https://snail-ide.js.org/community-extensions/
  dashblocks   https://dashblocks.org/extensions/

A source is skipped if it introduces no extension name that is not already
present (per project rule). Output schema:
    {generated_at, sources[], extensions[{name, description, url, open,
     image, author, author_link, documentation, samples, tags, deprecated, source}]}
"""
import argparse, json, os, re, subprocess, sys, tempfile, urllib.request
from urllib.parse import quote

UA = {"User-Agent": "Mozilla/5.0 (turbowarp-extensions-catalog)"}


def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", errors="replace")


def norm(name):
    return re.sub(r'[^a-z0-9а-яё]+', '', (name or '').lower())


def strip_html(t):
    t = re.sub(r'<[^>]+>', '', t)
    for a, b in (('&#39;', "'"), ('&amp;', '&'), ('&quot;', '"'), ('&lt;', '<'), ('&gt;', '>')):
        t = t.replace(a, b)
    return re.sub(r'\s+', ' ', t).strip()


# --------------------------------------------------------------------- official
def fetch_official():
    html = get("https://extensions.turbowarp.org/")
    recs = []
    for m in re.finditer(r'data-copy="https://extensions\.turbowarp\.org/([^"]+)"', html):
        path = m.group(1)
        start = html.rfind('<div class="extension">', 0, m.start())
        end = html.find('<div class="extension">', m.end())
        card = html[start:end if end != -1 else len(html)]
        h2 = re.search(r'<h2[^>]*>(.*?)</h2>', card, re.S)
        p = re.search(r'<p[^>]*>(.*?)</p>', card, re.S)
        img = re.search(r'<img[^>]+src="([^"]+)"', card)
        recs.append({
            "name": strip_html(h2.group(1)) if h2 else path,
            "description": strip_html(p.group(1)) if p else None,
            "url": "https://extensions.turbowarp.org/" + path,
            "image": ("https://extensions.turbowarp.org/" + img.group(1)) if img else None,
            "source": "official",
        })
    return recs


# -------------------------------------------------------------------- sharkpool
def fetch_sharkpool():
    base = "https://sharkpool-sp.github.io/SharkPools-Extensions/"
    data = json.loads(get(base + "Gallery%20Files/Extension-Keys.json"))
    recs = []
    for name, info in (data.get("extensions") or {}).items():
        url = info.get("url")
        if not url:
            continue
        recs.append({
            "name": name,
            "description": info.get("desc"),
            "url": base + "extension-code/" + url,
            "image": base + "extension-thumbs/" + info["banner"] if info.get("banner") else None,
            "author": info.get("creator"),
            "tags": info.get("tags"),
            "source": "sharkpool",
        })
    return recs


# ------------------------------------------------------------------- penguinmod
def fetch_penguinmod():
    base = "https://extensions.penguinmod.com/"
    data = json.loads(get(base + "extensions.json"))
    recs = []
    for e in data:
        code = e.get("code")
        if not code:
            continue
        creator = e.get("creator")
        if isinstance(creator, list):
            creator = ", ".join(c.get("name", "") if isinstance(c, dict) else str(c) for c in creator)
        recs.append({
            "name": e.get("name"),
            "description": e.get("description"),
            "url": base + "extensions/" + code,
            "image": base + "images/" + e["banner"] if e.get("banner") else None,
            "author": creator,
            "source": "penguinmod",
        })
    return recs


# --------------------------------------------------------------------- dimka-10
def fetch_dimka10():
    base = "https://dimka-10.github.io/Scratch-Extensions-Gallery.github.io/"
    src = get(base + "extension.js")
    m = re.search(r'window\.addons\s*=\s*(\[.*?\]);?\s*$', src, re.S)
    raw = m.group(1) if m else "[]"
    # Keys are unquoted JS identifiers -> quote them to make valid JSON.
    raw = re.sub(r'([{,]\s*)([A-Za-z_$][\w$]*)(\s*:)', r'\1"\2"\3', raw)
    raw = re.sub(r",(\s*[}\]])", r"\1", raw)
    addons = json.loads(raw) if m else []
    recs = []
    for a in addons:
        recs.append({
            "name": a.get("name"),
            "description": a.get("description"),
            "url": base + a["file"] if a.get("file") else None,
            "image": base + a["image"] if a.get("image") else None,
            "author": a.get("author"),
            "author_link": a.get("authorLink"),
            "source": "dimka-10",
        })
    return [r for r in recs if r["url"]]


def github_js_files(repo, folder, ref="main"):
    """List *.js files under `folder` in a GitHub repo via codeload tarball
    (no API rate limit). Returns (relpath_from_folder, basename) pairs."""
    import io, tarfile
    url = f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{ref}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        blob = r.read()
    out = []
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            parts = member.name.split("/", 1)
            path = parts[1] if len(parts) == 2 else parts[0]
            if path.startswith(folder + "/") and path.endswith(".js"):
                out.append((path[len(folder) + 1:], os.path.basename(path)[:-3]))
    return out


# ------------------------------------------------------------------ turbowarp-cn
def fetch_cn():
    base = "https://raw.githubusercontent.com/turbowarp-cn/cn-extensions/main/extensions/"
    recs = []
    for rel, name in github_js_files("turbowarp-cn/cn-extensions", "extensions"):
        recs.append({
            "name": name,
            "description": None,
            "url": base + quote(rel),
            "image": None,
            "source": "turbowarp-cn",
        })
    return recs


# ------------------------------------------------------------------- bluedome77
def fetch_bluedome():
    base = "https://raw.githubusercontent.com/BlueDome77/Turbowarp-Extension-List/main/Extensions/"
    recs = []
    for rel, name in github_js_files("BlueDome77/Turbowarp-Extension-List", "Extensions"):
        recs.append({
            "name": name,
            "description": None,
            "url": base + quote(rel),
            "image": None,
            "source": "bluedome77",
        })
    return recs


# ---------------------------------------------------------------------- mistwarp
def fetch_mistwarp():
    meta = json.loads(get("https://extensions.mistium.com/generated-metadata/extensions-v0.json"))
    raw_base = "https://raw.githubusercontent.com/Mistium/extensions.mistium/main/"
    gallery = "https://extensions.mistium.com/"
    recs = []
    for ext in meta["extensions"]:
        folder = "featured" if ext.get("featured") else "files"
        by = ext.get("by") or []
        recs.append({
            "name": ext["name"],
            "description": ext.get("description"),
            "url": raw_base + folder + "/" + quote(ext["filename"]),
            "image": gallery + quote(ext["image"]) if ext.get("image") else None,
            "author": ", ".join(b["name"] for b in by if b.get("name")) or None,
            "author_link": by[0].get("link") if by else None,
            "source": "mistwarp",
        })
    return recs


# ------------------------------------------------------------------- dinosaurmod
def fetch_dinosaurmod():
    src = re.sub(r'/\*.*?\*/', '', get(
        "https://raw.githubusercontent.com/Dinosaurmod/extensions/main/src/extensions.jsx"), flags=re.S)
    base = "https://raw.githubusercontent.com/Dinosaurmod/extensions/main/"
    icon_map = {"dmPythonIcon": "src/icons/python.png", "dmLuaIcon": "src/icons/lua.png",
                "dmKeysPlusIcon": "src/icons/keysPlus.png", "defaultExtensionIcon": "src/icons/placeholder.png"}
    legacy = "https://gabsthecuriouskid.github.io/DinosaurModExtensions/"
    recs = []
    for arr in re.findall(r'const \w+\s*=\s*\[(.*?)\n\];', src, flags=re.S):
        for body in re.findall(r'\{(.*?)\n    \}', arr, flags=re.S):
            def field(key):
                m = re.search(key + r":\s*'((?:[^'\\]|\\.)*)'", body)
                return m.group(1).replace("\\'", "'") if m else None
            if re.search(r'disabled:\s*true', body):
                continue
            name = field("name")
            ext_url = re.search(r"extensionUrl \+ '([^']+)'", body)
            if not name or not ext_url:
                continue
            icon = field("iconURL")
            if "legacyExtensionUrl +" in body:
                m = re.search(r"iconURL:\s*legacyExtensionUrl \+ '([^']+)'", body)
                image = legacy + m.group(1) if m else None
            elif icon and icon.startswith("http"):
                image = icon
            elif icon in icon_map:
                image = base + icon_map[icon]
            else:
                image = None
            author = field("extDeveloper")
            m2 = re.search(r"extDevHREF:\s*\{\s*name:\s*\"((?:[^\"\\]|\\.)*)\"", body)
            if m2:
                author = m2.group(1)
            dev_href = re.search(r"href:\s*'(https?://[^']+)'", body)
            recs.append({
                "name": name,
                "description": field("description"),
                "url": base + "src/extensions/" + ext_url.group(1),
                "image": image,
                "author": author,
                "author_link": dev_href.group(1) if dev_href else None,
                "source": "dinosaurmod",
            })
    return recs


# --------------------------------------------------------------------- snail-ide
def fetch_snail():
    html = get("https://snail-ide.js.org/community-extensions/")
    raw_base = "https://raw.githubusercontent.com/Snail-IDE/community-extensions/master/"
    recs = []
    for m in re.finditer(r'data-copy="https://extensions\.turbowarp\.org/([^"]+)"', html):
        path = m.group(1)
        start = html.rfind('<div class="extension">', 0, m.start())
        end = html.find('<div class="extension">', m.end())
        card = html[start:end if end != -1 else len(html)]
        h2 = re.search(r'<h2>(.*?)</h2>', card, re.S)
        p = re.search(r'<p>(.*?)</p>', card, re.S)
        img = re.search(r'<img[^>]+src="([^"]+)"', card)
        folder = path.split('/')[0] if '/' in path else None
        recs.append({
            "name": strip_html(h2.group(1)) if h2 else path,
            "description": strip_html(p.group(1)) if p else None,
            "url": raw_base + "extensions/" + path,
            "image": raw_base + "images/" + img.group(1)[len("images/"):] if img else None,
            "author": folder if folder and folder != "lab" else None,
            "source": "snail-ide",
        })
    return recs


# -------------------------------------------------------------------- dashblocks
def fetch_dashblocks():
    src = get("https://raw.githubusercontent.com/DashBlocks/extensions/develop/src/lib/extensions.js")
    with tempfile.TemporaryDirectory() as td:
        mjs = os.path.join(td, "dash.mjs")
        open(mjs, "w").write(src)
        out = subprocess.check_output(["node", "-e",
            "(async()=>{const m=await import('file://" + mjs + "');"
            "console.log(JSON.stringify({main:m.extensions,other:m.otherExtensions||[]}))})()"], text=True)
    data = json.loads(out)
    js_base = "https://dashblocks.org/extensions/static/extensions/"
    img_base = "https://dashblocks.org/extensions/static/images/"
    recs = []
    for entry in data["main"] + data["other"]:
        code = entry.get("code")
        if not code or not entry.get("name"):
            continue
        creator = entry.get("creator")
        creators = creator if isinstance(creator, list) else [creator]
        creators = [c for c in creators if (isinstance(c, dict) and c.get("name")) or isinstance(c, str)]
        creators = [{"name": c, "link": None} if isinstance(c, str) else c for c in creators]
        link = next((c.get("link") for c in creators if str(c.get("link", "")).startswith("http")), None)
        if link is None:
            link = next(("https://github.com/" + c["name"] for c in creators if c.get("link") == "_github_"), None)
        banner = entry.get("banner")
        if banner and not banner.startswith("http"):
            banner = img_base + banner
        recs.append({
            "name": entry["name"],
            "description": entry.get("description") or None,
            "url": code if code.startswith("http") else js_base + code,
            "image": banner,
            "author": ", ".join(c["name"] for c in creators) or None,
            "author_link": link,
            "source": "dashblocks",
        })
    return recs


SOURCES = [
    ("official", "TurboWarp Extension Gallery (official)", "https://extensions.turbowarp.org/", fetch_official, True),
    ("sharkpool", "SharkPool's Extension Collection", "https://sharkpool-sp.github.io/SharkPools-Extensions/", fetch_sharkpool, False),
    ("penguinmod", "PenguinMod Extension Gallery", "https://extensions.penguinmod.com/", fetch_penguinmod, False),
    ("dimka-10", "Dimka10 Scratch-Extensions-Gallery", "https://dimka-10.github.io/Scratch-Extensions-Gallery.github.io/", fetch_dimka10, False),
    ("turbowarp-cn", "turbowarp-cn/cn-extensions", "https://github.com/turbowarp-cn/cn-extensions", fetch_cn, False),
    ("bluedome77", "BlueDome77 Turbowarp-Extension-List", "https://github.com/BlueDome77/Turbowarp-Extension-List", fetch_bluedome, False),
    ("mistwarp", "MistWarp", "https://extensions.mistium.com/", fetch_mistwarp, False),
    ("dinosaurmod", "DinosaurMod", "https://dinosaurmod.github.io/extensions/", fetch_dinosaurmod, False),
    ("snail-ide", "Snail IDE", "https://snail-ide.js.org/community-extensions/", fetch_snail, False),
    ("dashblocks", "DashBlocks", "https://dashblocks.org/extensions/", fetch_dashblocks, False),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "turbowarp_extensions.json"))
    args = ap.parse_args()

    extensions = []
    known = set()
    source_meta = []
    for sid, sname, surl, fetch, always in SOURCES:
        try:
            records = fetch()
        except Exception as ex:
            print(f"  ! {sid}: ошибка загрузки: {ex}", file=sys.stderr)
            continue
        new_names = [r["name"] for r in records if norm(r["name"]) not in known]
        if not always and not new_names:
            print(f"  - {sid}: {len(records)} расширений, новых нет -> пропуск")
            continue
        for r in records:
            r.pop("open", None)
        extensions.extend(records)
        known.update(norm(r["name"]) for r in records)
        source_meta.append({"id": sid, "name": sname, "url": surl, "count": len(records)})
        extra = "" if always else f" (новых: {len(new_names)})"
        print(f"  + {sid}: {len(records)} расширений{extra}")

    out = {
        "generated_at": __import__("datetime").date.today().isoformat(),
        "sources": source_meta,
        "extensions": extensions,
    }
    json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=1)
    print(f"итого: {len(extensions)} расширений из {len(source_meta)} источников -> {args.out}")


if __name__ == "__main__":
    main()
