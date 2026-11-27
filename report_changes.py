#!/usr/bin/env python3
"""Compare raw gallery records by source and URL, ignoring generation dates."""
import json
import sys
from collections import defaultdict


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compare(old, new):
    def records(data):
        result = defaultdict(list)
        for record in data['extensions']:
            result[(record['source'], record['url'])].append(record)
        return result

    before, after = records(old), records(new)
    changes = defaultdict(lambda: defaultdict(list))
    for key in sorted(before.keys() | after.keys()):
        # Cancel identical duplicate records first, then pair remaining records.
        left, right = list(before[key]), list(after[key])
        for record in left[:]:
            if record in right:
                left.remove(record)
                right.remove(record)
        paired = min(len(left), len(right))
        changes[key[0]]['Изменены метаданные'].extend(right[:paired])
        changes[key[0]]['Удалены'].extend(left[paired:])
        changes[key[0]]['Добавлены'].extend(right[paired:])
    changes = {source: {kind: entries for kind, entries in groups.items() if entries}
               for source, groups in changes.items()}
    changes = {source: groups for source, groups in changes.items() if groups}
    return changes


def main():
    old, new = map(load, sys.argv[1:3])
    changes = compare(old, new)
    print('# Изменения галерей\n')
    print(f"Сравнение базы от {old.get('generated_at', '?')} с данными от {new.get('generated_at', '?')}.\n")
    print('Сравнение по источнику и URL: смена URL считается удалением и добавлением. Изменения кода JS без изменения метаданных не учитываются.\n')
    if not changes:
        print('Изменений записей не обнаружено.')
    for source, groups in sorted(changes.items()):
        print(f'## {source}\n')
        for kind, entries in groups.items():
            print(f'**{kind}: {len(entries)}**\n')
            for entry in entries:
                name = str(entry.get('name', '')).replace('\n', ' ').replace('[', '\\[').replace(']', '\\]')
                print(f"- {name} — {entry['url']}")
            print()

    if len(sys.argv) > 3:
        failures = load(sys.argv[3])
        print(f'## Недоступные файлы JS: {len(failures)}\n')
        if failures:
            print('Использован прежний ID, если он был известен, иначе null. Объединение расширений может быть неточным.\n')
            for failure in failures:
                print(f"- {failure['url']} — {failure['error']} (прежний ID: {failure['previous_id']})")


if __name__ == '__main__':
    main()
