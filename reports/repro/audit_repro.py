#!/usr/bin/env python3
"""Воспроизведение дефектов из отчётов A-2/A-4 (арена, 2026-10-12).

Запуск:  python3 reports/repro/audit_repro.py /path/to/lovii-observability/exporters
Не ходит в сеть: вызовы GitHub и version.json подменяются заглушками.
Не меняет репо аудита: модули импортируются, файлы регистра создаются во временном каталоге.
"""
import io, json, os, sys, tempfile, urllib.request

EXP = sys.argv[1] if len(sys.argv) > 1 else "exporters"
sys.path.insert(0, EXP)

def section(t): print(f"\n=== {t} ===")

# ---- A-2 F-2: накопление дублей в кэше сбора при повторных сбоях ----
import pipeline_exporter as pe
pe.TTL = 0
def boom(): raise RuntimeError("simulated GitHub failure")
pe.collect = boom
for _ in range(3):
    body = pe.collect_cached().decode()
section("A-2 F-2: 3 сбоя подряд")
print("строк lovii_exporter_collect_failed:", body.count("lovii_exporter_collect_failed"))

# ---- A-2 P2-2: частичный сбой compare даёт два ряда на один стенд ----
class _Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
def fake_gh(path):
    if "/compare/" in path: raise RuntimeError("simulated compare 404")
    if "/branches/" in path:
        return {"commit": {"sha": "a" * 40, "commit": {"committer": {"date": "2026-10-12T07:00:00Z"}}}}
    return {"workflow_runs": []}
import importlib
pe = importlib.reload(pe)  # настоящий collect() после подмены в тесте F-2
pe.gh = fake_gh
urllib.request.urlopen = lambda url, timeout=0: _Resp(json.dumps({"version": "production·abcdef1·2026-10-12"}).encode())
section("A-2 P2-2: compare упал, version.json ок")
print("\n".join(l for l in pe.collect().splitlines() if "app_stand_sha" in l))

# ---- A-4 P0-1: дата из будущего делает агента вечно активным ----
import agents_exporter as ae
reg = tempfile.mkdtemp(prefix="reg_")
ae.REGISTRY = reg
with open(os.path.join(reg, "forged.json"), "w") as f:
    json.dump({"agent": "forged", "repo": "lovii-core", "branch": "x", "task": "SZ-1",
               "status": "working", "started_at": "2026-10-12T00:00:00Z",
               "updated_at": "2099-01-01T00:00:00Z"}, f)
section("A-4 P0-1: heartbeat с updated_at в 2099")
print("\n".join(l for l in ae.collect().splitlines() if "forged" in l))

# ---- A-4 P1-2: наивный timestamp и кардинальность ----
with open(os.path.join(reg, "naive.json"), "w") as f:
    json.dump({"agent": "naive", "repo": "r", "branch": "b", "task": "t", "status": "working",
               "started_at": "2026-10-12T00:00:00", "updated_at": "2026-10-12T00:00:00"}, f)
section("A-4 P1-2: наивный timestamp (сдвиг зависит от TZ экспортёра; запустить с TZ=Europe/Amsterdam и TZ=UTC)")
print([l for l in ae.collect().splitlines() if "naive" in l and "stale" in l])
