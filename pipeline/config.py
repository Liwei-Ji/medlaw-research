#!/usr/bin/env python3
"""集中設定:未來要更新資料,主要就改這裡(法規、裁判日期範圍),再跑 update.py。"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
APP_DATA = os.path.join(ROOT, "medlaw-qa", "data")
CROSSTAB = os.path.join(ROOT, "crosstab.html")

# 醫藥五法(順序影響顯示)
LAWS = ["藥事法", "醫療器材管理法", "醫療法", "醫師法", "藥師法"]

# 裁判日期範圍(民國年/月/日)。要延長期間(例如納入 116)就改 END,並同步改 SUFFIX。
START = (112, 1, 1)
END   = (115, 12, 31)
SUFFIX = f"{START[0]}-{END[0]}"          # 檔名後綴,如 112-115

# canonical 檔案路徑(由 SUFFIX 推導,改期間會自動跟著換名)
FULLTEXT_JSONL   = os.path.join(DATA, f"醫藥五法_判決全文_{SUFFIX}.jsonl")      # download_full 產出(committed 為 .gz)
CAUSE_INDEX      = os.path.join(DATA, f"醫藥五法_判決索引_{SUFFIX}.json")        # build_index
FULLTEXT_INDEX   = os.path.join(DATA, f"醫藥五法_全文總索引_{SUFFIX}.json")      # build_full
STRUCTURED       = os.path.join(DATA, f"醫藥五法_結構化_{SUFFIX}.json")          # build_enriched

def open_jsonl(path):
    """讀 .jsonl;若不存在則讀同名 .gz(repo 內保存的是壓縮版)。"""
    import gzip
    if os.path.exists(path): return open(path, encoding="utf-8")
    if os.path.exists(path + ".gz"): return gzip.open(path + ".gz", "rt", encoding="utf-8")
    raise FileNotFoundError(path + "(.gz)")
