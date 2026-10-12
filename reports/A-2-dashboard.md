# A-2 — аудит дашборда «Пайплайны и стенды» (Ф-1)

- Issue: #1. Объект: `bestdeejay-design/lovii-observability` @ `a1adced` (main), файлы `exporters/*`, `README.md`.
- Ветка: `arena/b456e49e-lovii-arena-observability` (сессия закреплена за ней; см. комментарий в issue).
- Воспроизведение: `reports/repro/audit_repro.py`, `reports/repro/textfile_repro.sh` (без сети, подменённые вызовы).

## ВЕРДИКТ: NO-GO на приёмку Ф-1

Основания:
1. Ф-1 не поставлен в репо: нет `grafana/*.json` (дашборда), нет `deploy/` (systemd-юниты, scrape-конфиг), нет панели dev-стенда. README:25 сам отмечает `grafana/` как «пусто, Ф-1».
2. В экспортёре и textfile-скрипте есть дефекты, которые делают данные на дашборде **молча ложными** (P1-1, P1-2). Это хуже, чем отсутствие данных.
3. Чек-лист п.1 (дельта SHA считается экспортёром) и п.2 (тайминги шагов) не выполнены (P1-3, P1-5).
4. Регрессия A-1: пункт «TTL-кэш» закрыт в A-1 как P1, но в текущем коде сам кэш вносит дефект F-2. Вывод A-1 «GO на Ф-1» нужно пересмотреть.

## Проверки чек-листа issue

| # | Пункт | Результат |
|---|---|---|
| 1 | SHA стенда vs источника; дельта экспортёром | **НЕ ВЫПОЛНЕНО**: дельта только для app; core/b2b/admin не сравниваются; dev нет (P1-5, P1-6) |
| 2 | Тайминги честные, in_progress не завершение | **ЧАСТИЧНО**: `in_progress` не даёт duration (ок), но длительность — по `updated_at` run-level, шагов нет (P1-3) |
| 3 | TTL-кэш, ≤1 пересбор в TTL | **ВЫПОЛНЕНО** по коду: ≈20 вызовов GitHub на сбор → ≈1200/ч при TTL 60 с (лимит 5000/ч). Но см. F-2 и P2-1 |
| 4 | Аннотации деплоев — отдельный SA | **НЕ РЕАЛИЗОВАНО** (кода нет). Требование к следующей итерации (см. A-3 п.4) |
| 5 | Нет сырых логов/секретов в панелях; лейблы экранированы | Экранирование **ок**: `pipeline_exporter.py:35`, `agents_exporter.py:27`. Панелей нет → требуется выгрузка |
| 6 | systemd: непривилегированный, EnvironmentFile 600, bind 127.0.0.1 | bind **ок**: `pipeline_exporter.py:116`, `agents_exporter.py:66`. Юнитов нет → требуется выгрузка |

## Замечания

**P1-1 (F-1). textfile-скрипт молча перестаёт обновлять данные стендов.**
`exporters/stand_shas_textfile.sh:11` — `set -euo pipefail`; `:37` — `tail -n 200 "$LOG" | grep -E "START|OK" | tail -n 40 | while …`. Если в последних 200 строках лога нет `START`/`OK` (или лога нет), `grep` даёт код 1, pipefail пропагирует его, скрипт падает на `:45` до `mv`.
Воспроизведено (`textfile_repro.sh`): сценарии «лог без START/OK» и «лога нет» → exit=1, `.prom` не создан/не обновлён, остаётся `*.prom.tmp`. Ошибки в метриках нет.
Итог: SHA на дашборде «залипает» на старом значении и выглядит свежим.
**Фикс:** на фильтре `|| true`; писать `lovii_stands_textfile_timestamp_seconds <epoch>` и `lovii_stands_textfile_ok`; `trap 'rm -f "$OUT.tmp"' EXIT`; алерт на старость (см. A-6 строка 7).

**P1-2 (F-2). Ошибка сбора накапливает дубли и отдаёт устаревшие данные как текущие.**
`exporters/pipeline_exporter.py:99-103`: при исключении тело = прежнее тело + `lovii_exporter_collect_failed 1`, `ts` обновляется.
(а) Воспроизведено (`audit_repro.py`, F-2): 3 сбоя подряд → 3 одинаковые строки в одном ответе. Формат exposition не допускает двух строк одной серии в одном ответе; что именно делает Prometheus (отбрасывает дубль или весь scrape) — на конкретной версии не проверено.
(б) Последние успешные `lovii_ci_run_*` отдаются бесконечно как текущие: красный прогон, случившийся после последнего успеха, не виден.
(в) Нет метрики времени последнего успеха.
**Фикс:** хранить `last_good_body` отдельно и отдавать `last_good_body + failure_line` (не конкатенировать на каждом цикле); добавить `lovii_exporter_last_success_timestamp_seconds`; `collect_failed` — gauge 0/1, а не строка.

**P1-3. Тайминги шагов не реализованы; длительность приблизительна.**
`pipeline_exporter.py:70-71`: `ended = iso_ts(run["updated_at"])` — поле run-level, не момент завершения. Вызовов jobs API в коде нет (`grep -i jobs` пуст), хотя `README.md:35` обещает «actions/runs + jobs API».
Шаг, на котором застрял прогон (DoD п.1 `PLAN.md`), не выгружается.
**Фикс:** для последнего прогона `GET /repos/{o}/{r}/actions/runs/{id}/jobs`; `duration = max(job.completed_at) − min(job.started_at)`; метрика текущего шага `lovii_ci_run_step{…,step}`.

**P1-4. «Последний прогон ветки» не фильтруется по workflow и event.**
`pipeline_exporter.py:57` — `actions/runs?branch={branch}&per_page=1`: берётся последний run любого workflow с этим `head_branch`. Зелёный побочный прогон гасит красный деплой. Лейбл `event`/`triggering_actor` не экспортируется.
Отдельно: `pipeline_exporter.py:72-73` — `lovii_ci_run_in_progress` эмитится для любого `status != completed`, включая `queued`/`waiting`. Название врёт.
**Фикс:** `…/actions/workflows/<deploy>.yml/runs?branch=…&event=push&per_page=5`; экспорт `event`, `triggering_actor`; переименовать или фильтровать метрику по `status == "in_progress"`.

**P1-5. Дельта SHA не считается экспортёром для core/b2b/admin; dev-стенда нет.**
App: `pipeline_exporter.py:82-85` (`lovii_app_stand_sha_behind`, только `lovii-app`, см. `:84`). Core/b2b/admin: только `lovii_stack_sha` из textfile (`stand_shas_textfile.sh:17-24`, только prod/staging); SHA источника для них — лишь как лейбл `lovii_branch_sha_age_seconds` (`pipeline_exporter.py:56`).
Дельта «staging vs задеплоенный» для трёх репо придётся делать join по лейблу на клиенте Grafana — прямо против чек-листа п.1. Dev (CHUWI) в экспортёре отсутствует, хотя `PLAN.md` Ф-1 требует «второй target».
Лейблы расходятся: `stand="prod"` у app (`pipeline_exporter.py:82`) и `stand="prod-core"` у core (`stand_shas_textfile.sh:18`).
**Фикс:** экспортёр сам считает `lovii_stack_behind{repo,stand,branch}` (compare, `behind_by`) для 4 репо; единая схема лейблов `stand` × `repo`; добавить dev-target.

**P1-6. «Задеплоенный SHA» = git HEAD checkout, а не то, что запущено.**
`stand_shas_textfile.sh:29` — `git -C "$dir" rev-parse HEAD`; `README.md:32-33` подтверждает модель `git reset --hard $sha`. Если reset выполнен, а `docker compose up` не выполнен или упал, дашборд покажет новый SHA как задеплоенный.
**Фикс:** брать SHA из запущенных контейнеров (label `org.opencontainers.image.revision` или env `GIT_SHA` в образе) и выводить расхождение HEAD vs контейнер как метрику. Это же ответ на вопрос A-5 Q2: git HEAD сам по себе не является фактом «что задеплоено».

**P2-1.** `pipeline_exporter.py:30` — `COLLECT_TTL_SEC` без нижней границы. При `0` кэш отключён (`:95`), каждый scrape = ≈20 вызовов GitHub. **Фикс:** `max(TTL, 30)`.

**P2-2.** Частичный сбой compare даёт два противоречивых ряда для одного стенда. `pipeline_exporter.py:82` (`sha=X 1`) и `:87` (`sha="fetch_error" 0`) — воспроизведено (`audit_repro.py`, P2-2). Ошибка compare для master помечает весь стенд как `fetch_error`. **Фикс:** разнести метрики version.json и compare.

**P2-3.** `pipeline_exporter.py:85` — `len(cmp["commits"])`. Compare без пагинации отдаёт до 250 коммитов ([GitHub changelog, 2021-03-22](https://github.blog/changelog/2021-03-22-compare-rest-api-now-supports-pagination/)), поэтому счётчик занижается при большом отставании. **Фикс:** `cmp["behind_by"]`.

**P2-4.** `pipeline_exporter.py:62` — `run_id`, `status`, `conclusion` в лейблах `lovii_ci_run_*`. Каждый прогон и каждая смена статуса создают новую серию (churn). **Фикс:** фиксированный набор лейблов; `run_id` — в annotation, не в серии.

**P2-5.** Сбор идёт внутри scrape-обработчика на однопоточном `HTTPServer` (`pipeline_exporter.py:116`). При 20 вызовах × timeout 10 с сбор может длиться минуты и срывать scrape-timeout Prometheus (10 с по умолчанию). **Фикс:** фоновый таймер; scrape отдаёт готовый кэш.

**P2-6.** `stand_shas_textfile.sh:43` — `ts` как лейбл: серия на каждый деплой. **Фикс:** значение = epoch; лейблы `stack`, `event`, `sha`.

**P2-7.** `pipeline_exporter.py:64-68` — ветка `else` недостижима при `per_page=1`. Не баг, но путает ревью.

## Не проверено (нужна выгрузка)

- `grafana/*.json`, `deploy/*` (systemd, scrape-конфиг), правила алертов.
- Обезличенный фрагмент `lovii-deploy.log` (≈50 строк). Парсинг в `stand_shas_textfile.sh:38-41` построен на предположении о формате `key=value` и токенах `START`/`OK`; на реальном логе не проверен.
- Права `EnvironmentFile` (600) и пользователь сервисов.

## За пределами рамок (не влияет на вердикт)

- Репо `lovii-observability` сейчас **public** (коммит `a1adced`, «репо открыт (public) для доступа арены»). Секретов в нём не найдено (grep по всей истории, 4 коммита), но в публичном виде раскрыта схема деплоя. Подробно — A-3, пункт 2.
- Публичный `version.json` стендов app уже раскрывает SHA прода (существующая поверхность, A-3 п.7).
