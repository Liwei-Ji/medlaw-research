#!/usr/bin/env python3
"""Bundle the split source into a single self-contained preview.html for
Artifact/CSP hosting (external css/js are blocked, so everything is inlined).

The Artifact preview inlines the 2,000-record SUBSET (data/search-index.subset.js)
to keep the single file a reasonable size; the real app (index.html) loads the
full 14,031-record index via <script src="data/search-index.js">.

Usage:  python3 build.py        -> writes preview.html
Edit the split files (index.html / styles.css / app.js / search.js); the data
files come from ../pipeline/build_search_index.py. Re-run to regenerate."""
import re, pathlib
here   = pathlib.Path(__file__).parent
css    = (here/"styles.css").read_text(encoding="utf-8")
subset = (here/"data"/"search-index.subset.js").read_text(encoding="utf-8")  # window.SEARCH_INDEX (2000)
stats  = (here/"data"/"stats.js").read_text(encoding="utf-8")                # window.STATS
search = (here/"search.js").read_text(encoding="utf-8")                      # SearchEngine
app    = (here/"app.js").read_text(encoding="utf-8")
html   = (here/"index.html").read_text(encoding="utf-8")

# extract ONLY the #app div from the standalone document (drop <head>, <script src>, </body>)
m = re.search(r'(<div id="app".*</div>)\s*<script', html, re.S) or re.search(r'(<div id="app".*</div>)', html, re.S)
markup = m.group(1).strip()

bundle = (
    "<style>\n" + css + "\n</style>\n" +
    markup + "\n" +
    "<script>\n" + subset + stats + search + "\n" + app + "\n</script>\n"
)
out = here/"preview.html"
out.write_text(bundle, encoding="utf-8")
print("wrote", out, round(len(bundle)/1e6,2), "MB")
