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
| 🎲 scrandled | https://scrandled.vercel.app/ |
| 🧱 CrispStrobe | https://crispstrobe.github.io/extensions/ |

Данные лежат в [`extensions.json`](extensions.json) — 923 расширения из 12 источников, 482 уникальных после объединения дублей по id расширения (а не по имени).

Сайт: https://123asxcqasdc.github.io/turbowarp-extensions/

## Сборка

Всё воспроизводимо из исходных галерей:

```bash
python3 update.py    # collect.py -> fetch_ids.py -> build_data.py
```

| Скрипт | Что делает | Выход |
|---|---|---|
| `collect.py` | тянет каталоги со всех 12 галерей (новый источник добавляется, только если приносит хотя бы одно новое расширение) | `turbowarp_extensions.json` |
| `fetch_ids.py` | скачивает каждый `.js` и достаёт зарегистрированный `id` расширения (понимает UTF-16) | `extension_ids.json` |
| `build_data.py` | объединяет дубли по `id` (fallback — по имени) и назначает категории | `extensions.json` |

Запустить по отдельности тоже можно: каждый скрипт читает пути из `TW_RAW` / `TW_IDS` / `TW_CACHE` (по умолчанию — рядом со скриптом). Кэш скачанных `.js` — `.ext_cache/` (в `.gitignore`).

⚠️ `fetch_ids.py` скачивает сотни расширений; для полноценной работы `collect.py` (dashblocks) нужен `node` в `PATH`.

## Проверка обновлений через GitHub Actions

Workflow «Проверка обновлений каталога» запускается каждый понедельник в 04:17 UTC и вручную через **Actions → Проверка обновлений каталога → Run workflow**. Плановые запуски GitHub выполняет только на ветке по умолчанию; для ручного запуска выберите ветку с этим workflow.

Workflow собирает свежие данные во временный каталог, сравнивает записи галерей с сохранённой базой и публикует отчёт в Summary и три JSON-файла вместе с отчётом в артефакте `catalog-update` (хранится 30 дней). **Он не меняет и не публикует базу в репозитории.** Сравнение по источнику и URL: изменения URL выглядят как удаление и добавление, обновления исходного кода JS при неизменных метаданных не отслеживаются. Правило пропуска источников без новых названий сохраняется, поэтому отчёт отражает результаты текущего сборщика, а не обязательно все записи каждой галереи.

Если источник недоступен или возвращает пустой каталог, либо не удалось загрузить JS для извлечения id, сборка завершается ошибкой без публикации неполного результата. Формат галерей может измениться: проверяйте отчёт и логи перед ручным применением данных. Для работы workflow необходим доступ GitHub Actions к сайтам источников; в настройках репозитория должны быть разрешены Actions. При сборке DashBlocks выполняется JavaScript из внешнего источника, поэтому workflow имеет только разрешение на чтение репозитория и не использует секреты.
