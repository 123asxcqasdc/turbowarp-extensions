# 🐌 Расширения TurboWarp

Каталог расширений для [TurboWarp](https://turbowarp.org/) в стиле «Ули»: официальная галерея + галереи сообщества.

> ⚠️ **Предупреждение:** расширения TurboWarp выполняются без песочницы и **могут содержать вредоносный код**.
> Официальная галерея проверяется вручную, остальные источники — нет.
> Используйте на свой страх и риск и читайте код перед запуском.

## Источники

| Источник | Описание |
|---|---|
| ✅ Официальная галерея | https://extensions.turbowarp.org/ |
| 🦈 SharkPool | https://sharkpool-sp.github.io/SharkPools-Extensions/ |
| 🐧 PenguinMod | https://extensions.penguinmod.com/ |
| 🔟 Dimka-10 | https://dimka-10.github.io/Scratch-Extensions-Gallery.github.io/ |
| 🀄 turbowarp-cn | https://github.com/turbowarp-cn/cn-extensions |
| 🩵 BlueDome77 | https://github.com/BlueDome77/Turbowarp-Extension-List (архив) |
| 🌫️ MistWarp | https://extensions.mistium.com/ |
| 🦕 DinosaurMod | https://dinosaurmod.github.io/extensions/ |
| 🔥 DashBlocks | https://dashblocks.org/extensions/ |
| 🐌 Snail IDE | https://snail-ide.js.org/community-extensions/ |

Данные лежат в [`extensions.json`](extensions.json) — 655 расширений из 10 источников, 402 уникальных после объединения дублей по id расширения (а не по имени).

Сайт: https://123asxcqasdc.github.io/turbowarp-extensions/

## Сборка

Всё воспроизводимо из исходных галерей:

```bash
python3 update.py    # collect.py -> fetch_ids.py -> build_data.py
```

| Скрипт | Что делает | Выход |
|---|---|---|
| `collect.py` | тянет каталоги со всех 10 галерей (новый источник добавляется, только если приносит хотя бы одно новое расширение) | `turbowarp_extensions.json` |
| `fetch_ids.py` | скачивает каждый `.js` и достаёт зарегистрированный `id` расширения (понимает UTF-16) | `extension_ids.json` |
| `build_data.py` | объединяет дубли по `id` (fallback — по имени) и назначает категории | `extensions.json` |

Запустить по отдельности тоже можно: каждый скрипт читает пути из `TW_RAW` / `TW_IDS` / `TW_CACHE` (по умолчанию — рядом со скриптом). Кэш скачанных `.js` — `.ext_cache/` (в `.gitignore`).

⚠️ `fetch_ids.py` скачивает сотни расширений; для полноценной работы `collect.py` (dashblocks) нужен `node` в `PATH`.
