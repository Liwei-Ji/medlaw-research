#!/usr/bin/env python3
"""一鍵更新資料管線。

用法:
    python3 pipeline/update.py            # 只重建衍生資料(用現有 raw_/全文;不連網,快)
    python3 pipeline/update.py --scrape   # 另外重新爬清單(連司法院)
    python3 pipeline/update.py --download  # 另外重新下載每篇全文(慢,約 30–40 分)
    python3 pipeline/update.py --full      # = --scrape --download,完整更新

要延長期間(例如納入 116 年):先改 pipeline/config.py 的 END 與 SUFFIX,再跑 --full。
完成後:git add -A && git commit -m "update data" && git push(GitHub Pages 自動更新)。
"""
import subprocess, sys, os, gzip, shutil, time
import config
HERE = config.HERE

def run(script, *args):
    path = script if os.path.isabs(script) else os.path.join(HERE, script)
    print(f"\n▶ {os.path.relpath(path, config.ROOT)} {' '.join(args)}", flush=True)
    t = time.time()
    r = subprocess.run([sys.executable, path, *args], cwd=HERE)
    if r.returncode != 0:
        sys.exit(f"✗ {script} 失敗 (exit {r.returncode})")
    print(f"  ✓ ({time.time()-t:.0f}s)", flush=True)

def gzip_file(src):
    with open(src, "rb") as f, gzip.open(src + ".gz", "wb", compresslevel=9) as g:
        shutil.copyfileobj(f, g)
    print(f"  ✓ gzip {os.path.basename(src)} -> {os.path.getsize(src+'.gz')/1e6:.0f}MB")

def main():
    a = set(sys.argv[1:])
    full = "--full" in a
    do_scrape = full or "--scrape" in a
    do_download = full or "--download" in a

    if do_scrape:                                   # 1) 重新爬清單 -> raw_*.json
        run("scrape2.py"); run("scrape3.py"); run("scrape4.py", "藥事法"); run("ft_rest.py")
    run("build_full.py"); run("build_index.py")     # 2) 建索引 -> data/
    if do_download:                                 # 3) 下載全文 -> data/*.jsonl(+gz)
        run("download_full.py"); gzip_file(config.FULLTEXT_JSONL)
    run("build_enriched.py")                        # 4) 結構化 + 統計 -> data/
    run("build_search_index.py")                    # 5) 前端 A 索引 -> medlaw-qa/data/
    run("build_fulltext_bodies.py")                 #    前端 B1 全文 -> medlaw-qa/data/
    run("build_heatmap_data.py")                    # 6) 交叉統計資料
    run("build_heatmap_html.py")                    #    -> crosstab.html
    run(os.path.join(config.ROOT, "medlaw-qa", "build.py"))  # 7) 打包 preview.html

    print("\n✅ 更新完成。接著:git add -A && git commit -m \"update data\" && git push")

if __name__ == "__main__":
    main()
