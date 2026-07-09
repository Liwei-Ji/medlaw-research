# pipeline — 資料產生流程

本資料夾保存**產生 `../data/` 全部資料集與 `../crosstab.html` 的所有腳本**（純 Python 標準庫，無第三方套件）。
資料來源：司法院裁判書查詢系統 `https://judgment.judicial.gov.tw/FJUD/`。
資料快照：**2026-07-07**（裁判日期 112/1/1–115/12/31；115 年僅至 7 月）。

## 更新資料(一鍵)

設定集中在 **`config.py`**(法規、裁判日期範圍 `START`/`END`、檔名後綴、路徑)。**`update.py`** 依序跑完整條管線並把產物寫進正確位置。

```
python3 pipeline/update.py            # 只重建衍生資料(用現有 raw_/全文;不連網,約 25 秒)
python3 pipeline/update.py --scrape   # 另外重新爬清單(連司法院)
python3 pipeline/update.py --download  # 另外重新下載每篇全文(慢,約 30–40 分)
python3 pipeline/update.py --full      # = --scrape --download,完整更新
```

- **改法規/日期範圍**:編輯 `config.py`(例如納入 116 年就改 `END` 與 `SUFFIX`),再跑 `--full`。
- 完成後:`git add -A && git commit -m "update data" && git push`(GitHub Pages 自動更新)。
- 各腳本已改為以 `config.py` 提供的**絕對路徑**讀寫,不再依賴 cwd;`update.py` 會以 `pipeline/` 為工作目錄執行。

以下為各腳本細節(update.py 即依此順序串接)。

## 執行順序與輸入→輸出

### 1. 探索與計數（一次性，理解機制用）
| 腳本 | 作用 |
|------|------|
| `probe.py`, `probe2.py` | 摸清 FJUD 的 POST→結果清單機制、分頁與 data.aspx id 結構（可忽略） |
| `counts.py` | 統計各法「全文(jud_kw)」與「案由(jud_title)」筆數 → 得出全文 14,850 vs 案由 ~2,484 的取捨依據 |

### 2. 抓取清單（結果清單層級，解析案號/法院/日期/案由/摘要）
| 腳本 | 輸入 | 輸出 |
|------|------|------|
| `scrape2.py` | （線上查詢）案由「違反X」：醫材法/醫療法/醫師法＋藥師法全文 | `raw_cause.json` |
| `scrape3.py` | （線上查詢）藥事法「違反藥事法」，自適應日期切分繞過 500 筆上限 | `raw_yaoshifa_full.json` |
| `scrape4.py` | （線上查詢）**全文檢索**藥事法，自適應日期切分 | `raw_fulltext_藥事法.json` |
| `ft_rest.py` | 匯入 `scrape4` 的函式，跑其餘四法（醫療/醫師/醫材/藥師） | `raw_fulltext_rest.json` |
| `scrape.py` | （早期版，已被 scrape2 取代；輸出 `raw_藥師法.json` 為單法測試） | — |

### 3. 建索引（清單 → data/ 的 JSON/CSV）
| 腳本 | 輸入 | 輸出（應置於 `../data/`） |
|------|------|------|
| `build_index.py` | `raw_cause.json` + `raw_yaoshifa_full.json` | `醫藥五法_判決索引_112-115.{json,csv,_分類.json}`（案由式，2,545 筆） |
| `build_full.py` | `raw_fulltext_*.json`（並用案由集標記「據該法起訴」） | `醫藥五法_全文總索引_112-115.{json,csv,_分類.json}`（全文式，14,031 筆去重） |

### 4. 下載全文 + 解析結構欄位
| 腳本 | 輸入 | 輸出 |
|------|------|------|
| `download_full.py` | `醫藥五法_全文總索引_112-115.json`（逐筆 data.aspx） | `fulltext.jsonl` = `../data/醫藥五法_判決全文_112-115.jsonl`（275MB，含全文＋適用條號/主文/判決結果/法官…） |
| `build_enriched.py` | `fulltext.jsonl` | `醫藥五法_結構化_112-115.{json,csv}` ＋統計（條號分布、刑度、緩刑…） |

### 5. 產生視覺化與示範對話框
| 腳本 | 輸入 | 輸出 |
|------|------|------|
| `build_heatmap_html.py` | `heatmap_data.json` | `../crosstab.html`（法院×年度×類別 熱力圖） |
| `build_chat_html.py` | `demo_data.json` | 舊版單檔對話框（**已被 `../medlaw-qa/` 拆檔專案取代**，保留為原始出處） |

## 中繼檔（已隨附，讓 build 步驟免重抓即可重跑）
`raw_cause.json`、`raw_yaoshifa_full.json`、`raw_fulltext_藥事法.json`、`raw_fulltext_rest.json`、`raw_藥師法.json`、
`heatmap_data.json`、`demo_data.json`。

## FJUD 查詢重點（重抓時）
- 進階查詢 `Default_AD.aspx` 需帶 `__VIEWSTATE`/`__EVENTVALIDATION` 並保留 session cookie。
- 欄位：`jud_kw`=全文、`jud_title`=裁判案由、`dy1/dm1/dd1`–`dy2/dm2/dd2`=裁判日期區間。
- **結果清單每查詢僅開放前 500 筆分頁**；超過需把裁判日期區間遞迴對半切到每段 ≤500 再合併（見 `scrape3/scrape4`）。
