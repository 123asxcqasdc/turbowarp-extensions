#!/usr/bin/env python3
"""Merge duplicate extensions and assign categories for the site."""
import json, re, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.environ.get("TW_RAW", os.path.join(HERE, 'turbowarp_extensions.json'))))

SOURCE_LABELS = {
    "official": "Официальная галерея",
    "sharkpool": "SharkPool",
    "dimka-10": "Dimka-10",
    "turbowarp-cn": "turbowarp-cn",
    "bluedome77": "BlueDome77",
    "penguinmod": "PenguinMod",
    "mistwarp": "MistWarp",
    "dinosaurmod": "DinosaurMod",
    "snail-ide": "Snail IDE",
    "dashblocks": "DashBlocks",
}
SOURCE_EMOJI = {
    "official": "✅", "sharkpool": "🦈", "dimka-10": "🔟",
    "turbowarp-cn": "🀄", "bluedome77": "🩵", "penguinmod": "🐧",
    "mistwarp": "🌫️", "dinosaurmod": "🦕", "snail-ide": "🐌",
    "dashblocks": "🔥",
}

# ordered: first matches win priority (we collect up to 3)
RULES = [
    ("Костюмы и скины", r"\bskin|costume|looks|сскин|скин|костюм|внешност|appearance|render as"),
    ("3D и физика", r"\b3d\b|box2d|physics|физик|augmented reality|\bar\b|пространств|threejs|three js|movement tracking|движение"),
    ("Графика и эффекты", r"\bpen\b|graphic|draw|blend|clip|canvas|shader|colour|color|effect|visual|stamp|render|график|перо|цвет|цветн|эффект|рисован|отрисовк|канвас|шейдер|смешиван|обрез"),
    ("Звук и видео", r"\bsound|audio|music|video|tune|microphone|звук|аудио|музык|видео|микрофон|воспроизведен|песн"),
    ("Сеть и онлайн", r"http|fetch|network|websocket|cloud|api|online|request|discord|steam|itch\.io|gamejolt|newgrounds|webhook|dictionary|search|nfc|geolocation|offline|сеть|интернет|онлайн|запрос|облачн|данны.*(сайт|сайт)|сайт|словар|геолокац|позицион"),
    ("Устройство и датчики", r"camera|face|gamepad|battery|vibrat|keyboard|mouse|cursor|pointer|screen resolution|wake ?lock|hardware|webcam|камер|лиц|геймпад|батар|вибрац|клавиатур|мыш|курсор|экран|датчик|устройств|сенсор|тач|touch|мобиль"),
    ("Файлы и хранилище", r"\bfile|storage|zip|\bfs\b|filesystem|file system|folder|download files|файл|хранилищ|папк|архив|zip|диск"),
    ("Окно и интерфейс", r"window|fullscreen|full screen|menu|control|notification|prompt|monitor|style|browser|окн|полноэкран|меню|уведомлен|подсказк|интерфейс|стиль|вкладк|закрыт|кнопк.*(показ|скрыт)|показ.*кнопк|stage size|разрешен"),
    ("Время и таймеры", r"\btime\b|date|timer|timezone|delta|время|дат[аы]|таймер|часы|часов|пояс"),
    ("Текст и шрифты", r"\btext\b|string|char|font|case|regexp|regular expression|json|xml|base ?64|encod|декод|текст|строк|символ|шрифт|регистр|регулярн|кодиров"),
    ("Математика и логика", r"math|number|numeric|base\b|bitwise|bigint|random|compar|geometry|mean|median|variance|probab|round|tri|sin|cos|мат|числ|баз[аы] |счислен|случайн|сравнен|геометр|среднее|дисперс|вероят|тригономет"),
    ("Скрипты и данные", r"clone|event|script|variable|\blist\b|message|broadcast|thread|temp|timer|block|comment|cast|dictionar|asset|menu|клона|событи|скрипт|переменн|списк|сообщен|вещан|поток|блок|коммент|словар|конвертац|asset"),
    ("Утилиты", r"utilit|helper|misc|shovel|rixxy|toolbox|lily|утилит|помощ|разнообраз|прочее|набор блок"),
]
COMPILED = [(c, re.compile(p, re.I)) for c, p in RULES]

SHARK_TAG_MAP = {
    "Graphics": "Графика и эффекты",
    "Sound": "Звук и видео",
    "Online": "Сеть и онлайн",
    "Math": "Математика и логика",
    "Data Management": "Скрипты и данные",
    "Hardware": "Устройство и датчики",
    "Time": "Время и таймеры",
    "Utility": "Утилиты",
    "Category Expansion": "Скрипты и данные",
    "Runtime": "Утилиты",
    "Editor Tool": "Окно и интерфейс",
    "Configuration": "Окно и интерфейс",
}

def norm_key(name):
    k = re.sub(r'[^a-z0-9а-яё]+', '', (name or '').lower())
    return k

IDS = {}
_ids_path = os.environ.get("TW_IDS", os.path.join(HERE, 'extension_ids.json'))
if os.path.exists(_ids_path):
    IDS = json.load(open(_ids_path))

_id_cache = {}
def ext_id(e):
    """Registered extension id parsed from the .js code, or None."""
    url = e.get('url')
    if url not in _id_cache:
        raw = IDS.get(url)
        _id_cache[url] = re.sub(r'[^a-z0-9]+', '', raw.lower()) if raw else None
    return _id_cache[url]

def categorize(ext, variants):
    text = ' '.join(filter(None, [ext.get('name'), ext.get('description')] + [v.get('description') or '' for v in variants]))
    cats = []
    for cat, rx in COMPILED:
        if rx.search(text) and cat not in cats:
            cats.append(cat)
        if len(cats) >= 3:
            break
    for v in variants:
        for t in (v.get('tags') or []):
            mapped = SHARK_TAG_MAP.get(t)
            if mapped and mapped not in cats:
                cats.append(mapped)
    if not cats:
        cats = ['Прочее']
    return cats[:3]

merged = {}
order = []
by_id = {}
for e in DATA['extensions']:
    key = norm_key(e['name'])
    if not key:
        continue
    eid = ext_id(e)
    variant = {
        "source": e['source'],
        "source_label": SOURCE_LABELS.get(e['source'], e['source']),
        "source_emoji": SOURCE_EMOJI.get(e['source'], '🐌'),
        "url": e['url'],
        "open": e.get('open') or ("https://turbowarp.org/editor?extension=" + e['url']),
        "image": e.get('image'),
        "description": e.get('description'),
        "author": e.get('author') or None,
        "author_link": e.get('author_link'),
        "documentation": e.get('documentation'),
        "deprecated": bool(e.get('deprecated')),
        "tags": e.get('tags'),
        "ext_id": eid,
    }
    # merge by registered id first, else fall back to normalized name
    existing = by_id.get(eid) if eid else None
    if existing is None:
        existing = merged.get(key)
    if existing is None:
        merged[key] = {"name": e['name'], "variants": [variant]}
        order.append(key)
        if eid:
            by_id[eid] = merged[key]
    else:
        existing["variants"].append(variant)
        if eid:
            by_id[eid] = existing
        cur = existing
        if not cur.get('description') and e.get('description'):
            cur['description'] = e['description']
        # prefer non-deprecated, richer name
        if any(not v['deprecated'] for v in cur['variants']) and cur['variants'][0]['deprecated']:
            cur['variants'].sort(key=lambda v: v['deprecated'])

result = []
for key in order:
    m = merged[key]
    vs = m['variants']
    # best description / image / author
    desc = next((v['description'] for v in vs if v['description']), None)
    image = next((v['image'] for v in vs if v['image']), None)
    author = next((v['author'] for v in vs if v['author']), None)
    entry = {
        "name": m['name'],
        "description": desc,
        "author": author,
        "image": image,
        "categories": categorize({"name": m['name'], "description": desc}, vs),
        "sources_count": len(vs),
        "all_deprecated": all(v['deprecated'] for v in vs),
        "variants": vs,
    }
    result.append(entry)

cats = sorted({c for e in result for c in e['categories']})
out = {
    "generated_at": "2026-10-18",
    "total_raw": len(DATA['extensions']),
    "total_merged": len(result),
    "categories": cats,
    "extensions": result,
}
json.dump(out, open(os.path.join(HERE, 'extensions.json'), 'w'), ensure_ascii=False, indent=1)

print('raw:', len(DATA['extensions']), '-> merged:', len(result))
print('categories:', cats)
cc = Counter(c for e in result for c in e['categories'])
for c, n in cc.most_common():
    print(f'  {c}: {n}')
dups = [e['name'] for e in result if e['sources_count'] > 1]
print('merged dups:', len(dups), dups[:15])
