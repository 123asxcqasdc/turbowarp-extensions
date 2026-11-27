#!/usr/bin/env python3
"""Validate generated files before publishing and detect meaningful changes."""
import json
import sys
from pathlib import Path

FILES = ('turbowarp_extensions.json', 'extension_ids.json', 'extensions.json')


def read(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def validate(old_dir, new_dir):
    old = {name: read(old_dir / name) for name in FILES}
    new = {name: read(new_dir / name) for name in FILES}
    raw, ids, merged = (new[name] for name in FILES)
    if not isinstance(ids, dict) or not isinstance(raw.get('extensions'), list):
        raise ValueError('Неверный формат каталога или ID')
    sources = {s['id']: s['count'] for s in raw['sources']}
    previous_sources = {s['id']: s['count'] for s in old[FILES[0]]['sources']}
    for sid, count in previous_sources.items():
        if sid not in sources or sources[sid] < count * 0.5:
            raise ValueError(f'Источник {sid} исчез или сократился более чем наполовину')
    if len(raw['extensions']) < len(old[FILES[0]]['extensions']) * 0.7:
        raise ValueError('Каталог сократился более чем на 30%')
    urls = {e['url'] for e in raw['extensions']}
    if urls != set(ids) or merged['total_raw'] != len(raw['extensions']) or merged['total_merged'] != len(merged['extensions']):
        raise ValueError('Сгенерированные файлы не согласованы')
    for name in (FILES[0], FILES[2]):
        old[name].pop('generated_at', None)
        new[name].pop('generated_at', None)
    return old != new


if __name__ == '__main__':
    try:
        print('true' if validate(Path(sys.argv[1]), Path(sys.argv[2])) else 'false')
    except (ValueError, KeyError, TypeError, OSError) as e:
        sys.exit(f'Публикация отменена: {e}')
