# medlaw-qa — 醫藥五法判決檢索問答

對話式介面，**執行期不呼叫任何 AI**（純 JS 檢索），資料來源：司法院裁判書
（藥事法・醫材法・醫療法・醫師法・藥師法，裁判日期 112–115，共 14,031 筆）。

## 兩層檢索

| | A 快搜 | B1 全文深搜 |
|---|---|---|
| 對象 | 結構欄位 + 條號 + 案由 + 判決結果摘要 | 裁判書整篇全文 |
| 引擎 | `search.js`（bigram 倒排索引） | `fts.js`（直接掃描 brute-force 子字串） |
| 範圍 | 全 14,031 筆 | 全 14,031 筆（整篇全文） |
| 執行 | 離線可用（含 `file://`） | 需 http 伺服器（載入 78MB 全文） |

- **A 快搜（`search.js`）**：中文 bigram 倒排索引，對結構欄位＋條號＋案由＋判決結果摘要做檢索、排序、篩選（法規／條號／法院／年度／類別／據案由起訴）。意圖解析把問題轉成篩選＋關鍵字，回傳統計＋排序命中，支援「載入更多」與「縮小範圍」。全 14,031 筆，離線可用（含 `file://`）。
- **B1 全文深搜（`fts.js`）**：對**全部 14,031 筆判決的整篇全文**做任意字/片語檢索，結果附**命中片段高亮**，右側抽屜顯示**整篇全文**並高亮；可再依年度／法院／類別／法規篩選。
  - 純 JS、無 WASM。載入 `data/fulltext.json.gz`（78MB）→ 原生 `DecompressionStream` 解壓 → **直接掃描**（不建索引，每次查詢約數十毫秒；首次載入較久、記憶體較高）。
  - **需以 http 伺服器開啟**（`fetch` 在 `file://` 受限），且從**專案根目錄**起、開 `/medlaw-qa/`（讓「交叉統計」的 `../crosstab.html` 對得到，亦與 GitHub Pages 一致）：
    ```
    python3 -m http.server 8000     # 在專案根目錄執行 → 開 http://localhost:8000/medlaw-qa/
    ```
  - 上方「快搜 / 全文深搜」切換；`file://` 直接雙擊時仍可用「快搜」，切到深搜會提示需開伺服器。

## 體積與取捨

全文檢索原想用 sql.js FTS5，但其預建版**不含 FTS5**；且對全 14,031 筆建 trigram 索引，DB 高達 **755MB**，無法載入瀏覽器。改自製純 JS 引擎後，也發現「載入後在瀏覽器建 bigram 索引」對全量約需 30–40 秒、太慢。最終方案:**只帶全文 body、gzip 後 78MB、瀏覽器端解壓後直接以 `indexOf` 掃描**（每次查詢約數十毫秒，免索引）——無 WASM、涵蓋全 14,031 筆。代價是首次下載 78MB、記憶體約 400MB（桌機順、行動裝置較吃力）。完整取捨過程見 [`../docs/NOTES.md`](../docs/NOTES.md)。

## 檔案

| 檔案 | 用途 |
|------|------|
| `index.html` | 頁面結構；載入 data、`fts.js`、`search.js`、`app.js` |
| `styles.css` | 全部樣式（預設淺色） |
| `search.js` | A 快搜引擎（倒排索引＋排序＋篩選） |
| `fts.js` | B1 全文引擎（載入全文、掃描搜尋、snippet） |
| `app.js` | 互動、意圖解析、答案組裝、來源卡、右側全文預覽抽屜 |
| `data/search-index.js` | `window.SEARCH_INDEX`：全 14,031 筆精簡索引（4.9MB） |
| `data/stats.js` | `window.STATS`：預先算好的統計 |
| `data/fulltext.json.gz` | B1 全文（全 14,031 筆，78MB，gzip） |
| `data/search-index.subset.js` | 2,000 筆子集，供 Artifact 單檔預覽內聯 |
| `build.py` | 打包 → `preview.html`（僅內聯 A 子集；B1 因體積不進單檔預覽） |
| `preview.html` | 打包產物（Artifact/CSP 用；線上預覽僅 A 快搜） |

> `data/*` 由 `../pipeline/` 產生：`build_search_index.py`（A 索引＋stats）、`build_fulltext_bodies.py`（B1 全文）。

## 部署

- **完整體驗（A＋B1）**：把整個 `medlaw-qa/` 放到任何靜態主機，或本機 `python3 -m http.server`。
- **Artifact 線上預覽**：僅 A 快搜 2,000 筆子集（B1 的 78MB 全文無法內聯進單檔、且受 CSP 限制）。
