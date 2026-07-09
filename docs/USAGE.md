# 使用與部署

## 本機使用

- **交叉統計**:直接開 `crosstab.html`。
- **檢索問答 — A 快搜**:雙擊 `medlaw-qa/index.html` 即可(離線,`file://` 亦可)。
- **檢索問答 — B1 全文深搜**:需 http 伺服器(`fetch` 在 `file://` 受限)。
  **從專案根目錄**(medlaw-qa 的上一層)起伺服器,再開 `/medlaw-qa/`——這樣「交叉統計」按鈕的 `../crosstab.html` 才對得到,且與 GitHub Pages 路徑一致:
  ```
  python3 -m http.server 8000        # 在專案根目錄執行
  # 開 http://localhost:8000/medlaw-qa/  → 切「全文深搜」
  ```
  (從 `medlaw-qa/` 裡面起會使 `../crosstab.html` 變 404。埠被占用:換埠或 `lsof -ti:8000 | xargs kill`。)

## 重建資料

見 [`../pipeline/README.md`](../pipeline/README.md):爬取 → 建索引 → 下載全文 → 產生視覺化。

## 部署到 GitHub Pages

Pages 本身就是 https 靜態伺服器,因此**線上訪客不需要自己跑 `http.server`**,A 快搜與 B1 全文深搜都能直接用。

要點:
- **來源資料夾**只能選「repo 根目錄」或「/docs」。最簡單用根目錄發佈 → App 網址為 `https://<user>.github.io/<repo>/medlaw-qa/`;交叉統計為 `.../<repo>/crosstab.html`。App 內全用相對路徑,子路徑下照常運作。
- **App 執行期用的全文檔要一般 commit**:`medlaw-qa/data/fulltext.json.gz`(78MB,全 14,031 筆)必須是普通 git 檔——**GitHub Pages 不服務 Git LFS 檔**,若放 LFS 會抓到指標文字而非資料。
- **原始語料**:未壓縮的 262MB `.jsonl` 已 `gitignore`;repo 內保存**壓縮版 `data/*.jsonl.gz`(80MB,一般 commit)**,因此**不需 Git LFS**。`.db` 中繼檔亦 gitignore。
- 單檔上限 100MB:78MB 與 80MB 的 gz 均未超過,可正常 commit。
- Pages 站台軟上限約 1GB、每月流量約 100GB;實際負載遠低於此。
- 想讓 App 在站台根(更短的網址),再考慮搬檔或用 `gh-pages` 分支,非必要。
