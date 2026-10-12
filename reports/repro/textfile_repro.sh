#!/usr/bin/env bash
# A-2 P1-1: stand_shas_textfile.sh молча не обновляет .prom при «тихом» логе деплоев.
# Usage: bash textfile_repro.sh /path/to/lovii-observability/exporters/stand_shas_textfile.sh
# Работает в /tmp, пути /opt и /home/deploy подменяются; ничего в системе не меняет.
set -u
SRC="${1:?путь к stand_shas_textfile.sh}"
W=$(mktemp -d /tmp/textfile_repro.XXXX); mkdir -p "$W/opt/lovii-core" "$W/out"
git -C "$W/opt/lovii-core" init -q && git -C "$W/opt/lovii-core" -c user.email=a@a -c user.name=a commit -q --allow-empty -m init
sed -e "s#/opt/#$W/opt/#g" -e "s#/home/deploy/lovii-deploy.log#$W/deploy.log#" "$SRC" > "$W/run.sh"
echo "A) лог без START/OK:";  printf '2026-10-10T10:00:00Z heartbeat\n' > "$W/deploy.log"
bash "$W/run.sh" "$W/out/a.prom"; echo "  exit=$?  .prom создан: $([ -f $W/out/a.prom ] && echo да || echo НЕТ)  остаток: $(ls $W/out)"
echo "B) лога нет:";          rm -f "$W/deploy.log"
bash "$W/run.sh" "$W/out/b.prom"; echo "  exit=$?  .prom создан: $([ -f $W/out/b.prom ] && echo да || echo НЕТ)"
echo "C) лог с START/OK (контроль):"
printf '2026-10-12T10:00:00Z START stack=core sha=abcdef1234 pb=x\n' > "$W/deploy.log"
bash "$W/run.sh" "$W/out/c.prom"; echo "  exit=$?  .prom создан: $([ -f $W/out/c.prom ] && echo да || echo НЕТ)"
rm -rf "$W"
