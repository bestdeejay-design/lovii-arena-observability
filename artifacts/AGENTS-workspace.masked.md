# Lovii — корневой инструкционный файл воркспейса

Commerce-платформа lovii.ru: мульти-мерчант каталог, корзина, заказы, лояльность.
Ты — агент, работающий в этом воркспейсе. Не жди объяснений от владельца: контекст
ниже, дальше действуй сам (см. «Протокол задачи»). Общение с владельцем — по-русски.

## Карта компонентов (соседние репо, org lovii-tech)

| Репо | Что это |
|---|---|
| `lovii-core` | backend API (Laravel 13, PHP 8.5): единственный владелец commerce-таблиц, миграций, инфраструктуры (PostgreSQL+PostGIS, Redis, Meilisearch, Horizon) |
| `lovii-app` | мобильный web-клиент покупателя (Vue 3 + TS + Vite + Pinia), ходит только в core API |
| `lovii-b2b` | кабинет партнёров/точек (Laravel + Filament v5), схема БД `lovii_b2b` |
| `lovii-admin` | супер-админка (Laravel + Filament v5, Shield RBAC), схема `lovii_admin` |
| `lovii-design` | дизайн-система «Лови» — источник истины токенов (ветка main) |
| `lovii-demo` | демо-витрина дизайн-системы |

В каждом репо: `CLAUDE.md` (= симлинк AGENTS.md) — правила репо; `docs/sessions/` —
история работ (читай последние перед задачей, дописывай после).

## Стенды и ветки

| Компонент | Production | Staging (ветка `staging`) |
|---|---|---|
| app | app.lovii.ru | app-staging.lovii.ru |
| core (API) | api.lovii.ru | api-staging.lovii.ru |
| b2b | b2b.lovii.ru | b2b-staging.lovii.ru |
| admin | admin.lovii.ru | admin-staging.lovii.ru |

- Поток: фича-ветка → `staging` (проверка на стенде) → `master` (прод **только вручную**:
  `gh workflow run ci.yml --repo lovii-tech/<repo> --ref master`).
- Авто-деплой на staging из ветки `staging` **сейчас не срабатывает**: GitHub Actions
  не запускается — лимит биллинга исчерпан (п. 4 «Протокола задачи»). Пуш и merge
  работают, но checks не стартуют, поэтому приёмка — только локальным гейтом.
- Изменения только доков (*.md, docs/) CI не триггерят.
- Staging — копия прод-данных до 2026-09-05; прод — чистая БД со справочниками.

## Локальный стенд (OrbStack) — читать до запуска тестов

Полный регламент: **`ПРОТОКОЛ-ЛОКАЛЬНОГО-СТЕНДА.md`** — порты, гейт, контрольные
числа живой БД и что делать, если гейт красный.

- Подъём: сначала `docker compose up -d` в `lovii-core`, потом b2b и admin;
  app — `VITE_PORT=5174 docker compose up -d`. **Не** `yarn dev`: на :5173 уже
  висит чужой host-Vite, его не трогаем.
- Порты стенда: core API — `http://localhost` (:80), admin — :8001, b2b — :8002,
  app — :5174.
- **Тесты — только через безопасный runner:** `bash ~/LOVII/tools/core-tests.sh`
  (аналоги `admin-tests.sh`, `b2b-tests.sh`). Прямой
  `docker exec lovii-<repo>-app-1 composer test` / `php artisan test` /
  `vendor/bin/pest` **сносит живую базу**: при закэшированном
  `bootstrap/cache/config.php` Laravel игнорирует `<env>` из `phpunit.xml`, и
  `RefreshDatabase` выполняет `migrate:fresh` по **живой** БД. Инцидент
  2026-09-26: стёрто 3 юзера, 121 заказ, 240 позиций заказа, 1183 ledger-записи
  и 97 транзакций кошелька; восстановлено из CSV-снапшота.
- Гейт: `GATE=unit` (только тесты) / `GATE=lint` (Pint+Rector+PHPStan) /
  `GATE=type` (type coverage); по умолчанию `GATE=full`. Runner снимает кэш
  конфига **в той же оболочке**, что и Pest, и обратно его **не кэширует** —
  иначе ловушка перевзводится.
- `lovii-app`: полный `yarn test` **мутирует** рабочее дерево
  (`prettier --write`, `eslint --fix`) и может затереть чужие незакоммиченные
  правки. На грязном дереве — только
  `yarn test:unit && yarn type-check && yarn build-only`.

## Глубокая справка — читать по теме задачи, не всё сразу

**`lovii_docs/canon/PRODUCT_QUALITY_BAR.md` — продуктовый стандарт, ОБЯЗАТЕЛЕН
для любого агента в любой задаче с видимым пользователю результатом**: канон
дизайна (lovii-demo/lovii-design), скрин-тест «премиальный банк», три состояния
экрана, адаптив mobile+web, честные цифры, a11y. Ресёрчи практик — в
`lovii_docs/artifacts/` (реестр `REGISTRY.md`); ссылка на них в task-файле —
до кода.

`lovii-docs/` (создаётся отдельным агентом): `README.md` — карта файлов; `testing.md` —
все тесты платформы и когда их запускать; `deploy.md`; `design-system.md`; `status.md` —
«что сейчас в работе» (читать в начале задачи, обновлять в конце). Если нужного файла
ещё нет — читай `CLAUDE.md` соответствующего репо + последние `docs/sessions/` в нём.

## Ловушка для агентов: трение документации (ОБЯЗАТЕЛЬНО)

Если во время задачи документация вас подвела — битая/устаревшая ссылка, два
конкурирующих «источника истины», лишняя глубина чтения — **сразу** добавьте
одну строку-факт в `~/LOVII/DOC-FRICTION.md` (формат и шаблон — в файле).
Фиксируем факт, НЕ чиним указатели сами: правку карты делает куратор доков
по накопленной статистике — правится только то, что реально экономит время
и делает систему устойчивее; решение владельца — там, где меняется канон.
Бэклог доков — только открытое; закрытые пункты —
`lovii_docs/canon/BACKLOG_ARCHIVE.md`; жизненный цикл пункта —
`lovii_docs/canon/BACKLOG.md` §0.2.

## Протокол задачи (выполняй сам, без подсказок владельца)

0. **Синхронизация с GitHub перед любыми правками.** Перед началом работы
   в любом репо выполни `git fetch` + `git pull --rebase origin main` (или
   актуальную ветку). Это гарантирует, что ты работаешь с последней версией
   кода и не затираешь чужие/уже опубликованные изменения. Если pull
   выдаёт конфликты — разберись до начала правок, не оставляй конфликты
   на потом.
1. `git fetch` + `git pull` нужных репо; рабочие деревья держим чистыми.
2. Прочитать контекст по теме (см. раздел выше); неуверенность в выборе репо/подхода
   снимай чтением кода, переспрашивай только принципиальные развилки.
3. Фича-ветка от `staging` → работа → гейт (полный разбор — в
   `ПРОТОКОЛ-ЛОКАЛЬНОГО-СТЕНДА.md`):
   - core/b2b/admin: `bash ~/LOVII/tools/<repo>-tests.sh`.
     **КАТЕГОРИЧЕСКИ НЕЛЬЗЯ** `docker exec lovii-<repo>-app-1 composer test`:
     при закэшированном `bootstrap/cache/config.php` Laravel игнорирует env из
     `phpunit.xml` и `RefreshDatabase` делает `migrate:fresh` по ЖИВОЙ базе.
     Инцидент 2026-09-26: стёрто 3 юзера, 121 заказ, 1183 строки ledger,
     97 транзакций кошелька. Безопасный runner снимает кэш в той же оболочке
     и проверяет через `config:show`, что тесты идут в `testing`.
   - app: `yarn test:unit && yarn type-check && yarn build-only` (read-only).
     Полный `yarn test` МУТИРУЕТ дерево (`prettier --write`, `eslint --fix`) —
     запускать только когда в дереве нет чужих правок. e2e по теме:
     `yarn test:e2e` (local) или `E2E_TARGET=staging yarn test:e2e:scenarios`.
4. **CI/CD живёт на self-hosted раннерах** (с 27.09; GitHub-hosted Actions стоит
   — лимит биллинга исчерпан, ждём сброса). Пуш в `staging` → checks на
   `gostiny-ci-*` (раннеры на прод-сервере, минуты не тратятся) → автодеплой
   стенда. После пуша смотреть прогон: `gh run watch <id> --exit-status`
   (id — свежий из `gh run list --branch staging --limit 1`). Прод — только
   вручную (`gh workflow run ci.yml --ref master`), тоже на нашем раннере.
   Полный канон — `lovii_docs/canon/CI_RUNNERS_SELFHOSTED.md` (работа, откат,
   возврат на GitHub-hosted, обслуживание, грабли pecl/алиасов). С 28.09 —
   оптимизированный режим: тесты гоняются ПОЛНОСТЬЮ, но в один проход
   (type-coverage внутри), install скипается при кэш-хите, core-деплой
   пересобирает образ только при изменении docker//locks; правила и экономика
   минут GitHub — в разделе «Оптимизированный режим CI» этого канона.
   Локальный гейт из п.3 остаётся обязателен ДО пуша; если раннер offline —
   приёмка по-старинке: гейт + ручной деплой по SSH.
   **С 05.10 — волна 1 аудита CI/CD во всех 4 репо** (канон — раздел
   «Волна 1 аудита CI/CD» в CI_RUNNERS_SELFHOSTED.md): деплой-ключ стирается
   с раннера после деплоя, `permissions: contents: read`, деплой-джобы не
   отменяются, деплоится проверенный `DEPLOY_SHA`, known_hosts из переменной
   `DEPLOY_HOST_KEY`, actions только с SHA-пинами, PR-прогоны — на
   ubuntu-latest (не на прод-раннерах). Менять ci.yml/compose — только через
   репо, никогда руками на сервере.
   Мержим **по одному**: перед пушем `git pull` (см. «Параллельные сессии»).
5. Зафиксировать работу: `docs/sessions/NNN-<тема>.md` в репо + обновить
   `lovii-docs/status.md`; коммиты — conventional (feat/fix/docs/chore), как в истории.
6. Отчёт владельцу: что сделано, где посмотреть (стенд/файл), что дальше.

## Страж производительности (SZ-060, с 2026-09-19)

Базлайн staging: ~235 rps чтения (авторизованные эндпоинты, p50 ~70 мс до 10 VU),
деградация очередью без отказов до 200 VU; запись ~3,5–9 цепочек
«заказ+оплата»/с. Следующий узкий узел — Postgres. Полные замеры и методика:
`lovii-app/scripts/stress/README.md`.

- Страж НЕ гоняется «после каждого чиха» (решение владельца 19.09). Прогоны —
  **по факту крупных обновлений** (фичи в горячих путях — каталог/корзина/
  чекаут/кошелёк/поиск/лояльность/пул, инфраструктура, зависимости, миграции
  тяжёлых таблиц). Приоритетно — **на локальном стенде**:
  `STRESS_BASE=http://localhost python3 scripts/stress/stress.py read 10 25 50 100`
  (в lovii-app; сравнение — относительно, локальный стенд быстрее сети staging).
  Прогон против staging — по решению владельца (пороги в `baseline.json`,
  smoke.sh остаётся быстрым инструментом, но не обязанность на каждый мерж).
  Красные цифры = искать N+1, отсутствующий индекс, синхронный HTTP в request
  path; разбирать в session-доке и перемерять.
- В request path запрещено: N+1 запросы в цикле, синхронные вызовы внешних
  API (только через очередь), запросы без LIMIT на больших таблицах.
- Деградацию БД пишет в laravel.log страж `db.slow_requests` (суммарно >500 мс
  SQL на запрос) — всплеск таких записей после мержа = регресс, разбирать.

## Параллельные сессии

- Одна задача = одна фича-ветка в одном репо. Задача, затрагивающая несколько репо,
  ведёт **один** агент вертикально.
- В `staging` в один момент пушит только один агент (после `git pull`).
- Агенты друг друга не видят: общий канал — коммиты, `docs/sessions/`, `lovii-docs/status.md`.

## Известные факты (экономят время)

- **Прод-сервер и мониторинг метрик** — `~/LOVII/PROD-SERVER-AND-MONITORING.md`
  (читать ПЕРЕД любыми действиями с сервером или стеком метрик): SSH прод =
  `root@<PROD-IP>` (ключ мака, без пароля; .31 = второй IP той же машины),
  **prod+staging = ОДИН сервер** (стенды различаются суффиксом `-staging` в именах
  контейнеров); Prometheus-хаб на CHUWI (:9090/:3002 Grafana, :9093 Alertmanager),
  экспортеры на проде слушают только localhost, канал — SSH-туннель `mon-tunnel`
  с CHUWI (ключ `mon_prod`, таргеты через 172.17.0.1); алерты описаны, канал
  уведомлений ещё НЕ подключён; Kuma :3001 не заменена (внешние проверки).
- **Домашняя сборочная станция CHUWI** (`~/LOVII/CHUWI-BUILD-STATION.md` — читать перед работой с ней):
  мини-ПК N100/12ГБ/512ГБ, чистая Ubuntu Server 24.04.5 (hostname `gostiny-bild`), Docker активен,
  SSH `lovii@<CHUWI-IP>` (кабель) / `.239` (Wi-Fi Sveta) — с мака владельца вход по ключу,
  sudo-пароль в доке. Раннер v2.337.0 ЗАРЕГИСТРИРОВАН и работает (служба systemd, `gostiny-build`, лейбл
  `gostiny-ci-build` — только сборки; деплой НЕ переносить, остаётся на прод-раннерах `gostiny-ci-*`).
- GitHub: доступ ВОССТАНОВЛЕН 2026-09-18 — `bestdeejay-design` разблокирован,
  `gh auth status` ✓ (repo+workflow), пуш в `lovii-tech` открыт. **Карта всей
  незапушенной работы и порядок: `~/LOVII/ПУШ-ПЛАН.md` — прочитать первым перед
  любым пушем.** Доки: хаб `lovii-ru/lovii-docs` (mirror) синхронизирован до
  fe63f87+; профиль `lovii-ru` — выделенный и изолированный, правила анти-абьюза
  (`canon/WORK_PROTOCOL.md` §9 в хабе) обязательны для всех агентов. Аккаунт
  `axiiom-ru` жив (SSH `id_ed25519`), его `axiiom-ru/lovii` — Pages-лендинг.
  Секреты (ключи Т-Банка, доступы, OTP-токены) в git не класть. Детали: `canon/FINDINGS.md` → F-051.
- Тестовый покупатель e2e: номер задаётся `E2E_TEST_PHONE` (по умолчанию `+79990000001`,
  заглушка; номер `+79967271894` из тестов выведен). OTP-код тесты читают из
  `GET /api/v1/dev/otp/last-code` (работает при `OTP_DEV_BYPASS=true`, dev/staging;
  на прод роута нет). Бипас-код `1234` по-прежнему принимается на dev/staging.
  Канал доставки в e2e — `sms` (на dev/staging лог-транспорт).
- **Картотека тестовых профилей (актёров)** — `lovii_docs/canon/TEST_PROFILES.md`:
  постоянные профили по ролям и статусам заявки МСП (покупатель, msp-new/pending/
  approved, представитель с личным кодом AAT3ST, амбассадор, негатив), правила
  данных (одноразовые сценарии + чистка, влад. данные не трогать) и раннер
  `~/LOVII/tools/stage-actor.py` (create/login/state). Читать ДО создания любого
  нового тестового профиля — не изобретать свою авторизацию.
- MAX OTP-доставка на staging РАБОТАЕТ (бот «Лови» @id7842223709_bot, `OTP_MAX_TRANSPORT=bot_api`):
  личный диалог в MAX Bot API адресуется `POST /messages?user_id={user_id}` (НЕ chat_id в теле —
  даёт 400 «Unknown recipient»); вебхук bot_started/message_created зарегистрирован, `LOG_LEVEL=info`.
  ⚠️ В «Боты Макс.txt» подписи токенов перепутаны: «Лови» = второй токен. Прод: env+вебхук+`OTP_DEV_BYPASS=false`.
  Детали: `lovii-core/docs/sessions/004,009–011-…`, `lovii-app/docs/sessions/009-…`.
- Оплата в платформе **не подключена** (нет ни UI, ни API): путь покупателя заканчивается
  созданием заказа.
- Ключи на staging добавлены (2026-09-06): `VITE_YANDEX_MAP_API_KEY` запечён в стенд-сборку app
  (карта работает), в `/opt/lovii-core-staging/.env` есть `YANDEX_GEOCODER_API_KEY` +
  `YANDEX_GEOCODER_REFERER` — `/geo/{resolve,reverse,suggest}` отвечают 200. Локально Yandex
  JS API не инициализируется (Referer-ограничение ключа): дровер-спеки адреса в e2e —
  staging-only с замоканными `/geo/*`. Перед продом не забыть ключ и в `/opt/lovii-core/.env`.
  Детали: `lovii-app/docs/sessions/010-…`, `lovii-core/docs/sessions/005-…`.
- Kuper/автоимпорт в core выключены (`INTEGRATIONS_ENABLED=false`).
- e2e app против staging гонять как есть — сетевые подвохи машины уже учтены
  (`e2e/helpers/network.ts`, детали в `lovii-app/e2e/README.md`).
- `START.md` в корне — первоначальная справка владельца (историческая), заменяется этим файлом.


<!-- autoclaw:skill-path-guidance -->
## Installing Skills

When creating or installing a new skill, always place it in:

`/Users/best/.openclaw-autoclaw/skills/<skill-name>/SKILL.md`

This is the managed skills directory. The agent will automatically discover
any skill placed here — no extra configuration needed. Do NOT install skills
into `~/.agents/skills/` (that directory is shared with other tools).

<!-- autoclaw:browser-agent-guidance -->
## Browser Automation

For any task that requires a browser, **prefer `autoglm-browser-agent`**. Use it as the first choice. For time-sensitive scenarios such as financial news, stock quotes, or breaking news, you can additionally use this skill to fetch up-to-date information and supplement your data sources.

- ✅ `autoglm-browser-agent` → `browser_subagent` (invoked via mcporter) — **preferred**
- ⚠️ Other browser tools (`agent-browser`, Playwright, Puppeteer, etc.) — fallback only when `autoglm-browser-agent` is unavailable or fails

Always try `autoglm-browser-agent` first. Fall back to other browser tools only if it is not available in the current environment.

**IMPORTANT: Do NOT use `sessions_spawn` to delegate browser/web automation tasks to a sub-agent.** Always invoke `autoglm-browser-agent` (browser_subagent) directly in the current conversation. Browser tasks must be handled by yourself, not by a spawned child agent.
<!-- /autoclaw:browser-agent-guidance -->

<!-- autoclaw:image-recognition-guidance -->
## Image Recognition

For image tasks, prefer the model's native visual capability when the image is available to the selected model through its native image-input channel and the model supports image input.

- ✅ Native image input + an image-capable model — read and judge the image directly; do not invoke `autoglm-image-recognition`
- ✅ Existing `[图片参考描述]` — reuse the description; do not invoke the recognition skill again
- ⚠️ `autoglm-image-recognition` — fallback only for text-only models, images offloaded or unavailable through the native input channel, or unavailable native vision capability

<!-- /autoclaw:image-recognition-guidance -->

<!-- autoclaw:feishu-lark-skill-guidance -->
## Feishu / Lark Requests

When the user asks about Feishu/Lark/飞书 matters, route through Feishu/Lark skills first. This includes messaging, contacts, calendars, approvals, tasks, docs, sheets, Base, Drive, Wiki, mail, meetings, minutes, attendance, OKRs, or any other Feishu/Lark workspace operation.

1. If a relevant Feishu/Lark skill is already available, use that skill directly.
2. If no relevant skill is available, search the skill catalog/store or available skill list for a matching Feishu/Lark skill.
3. If you find a matching skill that is not installed or enabled, ask the user whether to install/enable and use it before proceeding.
4. If no matching skill exists, say so briefly and continue with the safest available fallback.
<!-- /autoclaw:feishu-lark-skill-guidance -->
<!-- autoclaw:mcp-tools-guidance -->
## MCP Tools

When the user asks for configured MCP services or external data providers, use the workspace MCP catalog before web search.
Match the user request against the available MCP tool names and descriptions below.

Call tools with: `mcporter --config /Users/best/LOVII/config/mcporter.json call <server>.<tool> key="value"`

Available MCP tools:
- No MCP tools are currently healthy.
<!-- /autoclaw:mcp-tools-guidance -->
