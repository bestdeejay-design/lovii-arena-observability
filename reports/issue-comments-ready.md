# Готовые комментарии к issue #1–#5 (не опубликованы: токен арены получил 403 на создание комментариев)

## issue #1 (А-2)

ВЕРДИКТ: **NO-GO** на приёмку Ф-1 (нет grafana/deploy; textfile молча залипает; кэш копит дубли). Ветка `arena/b456e49e-lovii-arena-observability`, отчёт `reports/A-2-dashboard.md`.
@bestdeejay-design: нужна выгрузка `grafana/*.json`, `deploy/*` и обезличенные 50 строк `lovii-deploy.log`.

## issue #2 (А-3)

ВЕРДИКТ: **ТРЕБУЕТ ФИКСОВ** (P0 по коду не найдено; P1: широкий read-токен на `lovii-tech/*`, публичный репо, общие Grafana-креды, дизайн аннотаций). Ветка `arena/b456e49e-lovii-arena-observability`, отчёт `reports/A-3-redteam.md`.
@bestdeejay-design: проверьте видимость `lovii-observability` (сейчас public). Нужна выгрузка: права ключа `mon-tunnel` на проде и роли пользователей Grafana.

## issue #3 (А-4)

ВЕРДИКТ: **NO-GO** для прод-мониторинга (heartbeat подделывается: дата из будущего даёт вечный active, воспроизведено). Ветка `arena/b456e49e-lovii-arena-observability`, отчёт `reports/A-4-heartbeat.md`.
@bestdeejay-design: нужен AGENTS.md воркспейсов (протокол обновления heartbeat).

## issue #4 (А-5)

ВЕРДИКТ: **NO-GO** на юридически значимый след (ручной SSH/.env/SQL/cron не покрыты; деплой-пользователь общий; коммиты не подписаны). Ветка `arena/b456e49e-lovii-arena-observability`, отчёт `reports/A-5-audit-trail.md`.
@bestdeejay-design: нужна выгрузка `authorized_keys` пользователя deploy, код `lovii-deploy`, настройки веток `lovii-tech/*` и схема хранения платёжных настроек.

## issue #5 (А-6)

ВЕРДИКТ: **NO-GO** (файлов правил в репо нет; правило 🔴 «прод-деплой вне workflow_dispatch» на текущих метриках не сработает; сторожа нет). Ветка `arena/b456e49e-lovii-arena-observability`, отчёт `reports/A-6-alerts.md`.
@bestdeejay-design: нужны `deploy/alerts*.yml` (или актуальный текст правил Ф-3) и конфиг `scrape_configs`/`rule_files` Prometheus на CHUWI.

