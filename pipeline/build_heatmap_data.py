#!/usr/bin/env python3
# 從全文總索引重算交叉統計(法院×年度×類別)資料 -> pipeline/heatmap_data.json
# (build_heatmap_html.py 的輸入。之前這步是手動做的,現補成正式腳本。)
import json, collections, os
import config

OUT = os.path.join(config.HERE, "heatmap_data.json")
recs = json.load(open(config.FULLTEXT_INDEX, encoding="utf-8"))["records"]

def ry(j):
    try:
        y = int(j[:4]) - 1911
        return y if config.START[0] <= y <= config.END[0] else None
    except Exception:
        return None

YEARS = list(range(config.START[0], config.END[0] + 1))
CATS = ["刑事", "民事", "行政", "懲戒", "憲法法庭"]
cube = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
total = collections.Counter()
for r in recs:
    y = ry(r["jdate"])
    if y is None: continue
    c = r["category"]; c = c if c in CATS else "其他"
    ct = r["court"]
    cube[ct][y][c] += 1; total[ct] += 1
courts = [c for c, _ in total.most_common()]
data = {"years": YEARS, "cats": CATS, "courts": courts,
        "cube": {ct: {str(y): dict(cube[ct][y]) for y in YEARS} for ct in courts}}
json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
print(f"heatmap_data.json: courts={len(courts)} total={sum(total.values())} -> {OUT}")
