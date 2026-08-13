#!/usr/bin/env python3
"""Generate a single-file labelling page from calibration/pairs.jsonl.

The corpus is embedded rather than fetched, because a page opened from the filesystem cannot read a
sibling file. The output is one HTML file with no network dependency: open it, label, export.

    python3 calibration/build_labeller.py
    open calibration/label.html

Labels are held in the browser's local storage as they are made, so closing the tab does not lose the
session. Export writes `pairs-labelled.jsonl` in the same schema as the input, with `label` set.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

PAGE = """<!doctype html>
<meta charset="utf-8">
<title>Calibration labelling</title>
<style>
 :root { --bg:#fbfbfa; --fg:#1a1a18; --dim:#6b6b66; --line:#e0e0dc; --same:#1a6b3c; --diff:#8a2a2a; --unsure:#7a6a1a; }
 @media (prefers-color-scheme: dark) {
   :root { --bg:#16161a; --fg:#e8e8e4; --dim:#9a9a94; --line:#2e2e34; --same:#5fd08a; --diff:#e58080; --unsure:#d8c46a; }
 }
 * { box-sizing:border-box; }
 body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
 header { position:sticky; top:0; background:var(--bg); border-bottom:1px solid var(--line); padding:12px 20px; display:flex; gap:18px; align-items:baseline; flex-wrap:wrap; }
 header b { font-size:15px; } header span { color:var(--dim); font-size:13px; }
 main { padding:20px; max-width:1400px; margin:0 auto; }
 .meta { color:var(--dim); font-size:13px; margin-bottom:12px; }
 .cols { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
 @media (max-width:900px) { .cols { grid-template-columns:1fr; } }
 .card { border:1px solid var(--line); border-radius:6px; overflow:hidden; }
 .card h3 { margin:0; padding:8px 12px; font-size:13px; font-weight:600; border-bottom:1px solid var(--line); }
 .card .where { color:var(--dim); font-weight:400; }
 pre { margin:0; padding:12px; overflow-x:auto; font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace; white-space:pre; }
 .actions { margin-top:18px; display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
 button { font:inherit; padding:8px 16px; border:1px solid var(--line); background:transparent; color:var(--fg); border-radius:5px; cursor:pointer; }
 button:hover { border-color:var(--fg); }
 button.same { color:var(--same); } button.diff { color:var(--diff); } button.unsure { color:var(--unsure); }
 kbd { font:11px ui-monospace,monospace; border:1px solid var(--line); border-radius:3px; padding:1px 5px; color:var(--dim); }
 .bar { height:4px; background:var(--line); border-radius:2px; overflow:hidden; margin-top:10px; }
 .bar i { display:block; height:100%; background:var(--same); }
 .done { color:var(--same); } .q { color:var(--dim); font-size:13px; margin:14px 0 4px; }
</style>
<header>
  <b>Calibration labelling</b>
  <span id="pos"></span>
  <span id="tally"></span>
  <span style="margin-left:auto"><kbd>s</kbd> same &nbsp; <kbd>d</kbd> different &nbsp; <kbd>u</kbd> unsure &nbsp; <kbd>&larr;</kbd> back</span>
</header>
<main>
  <div class="q">If one of these needed a behaviour change, would the other need the same change?</div>
  <div class="meta" id="meta"></div>
  <div class="cols">
    <div class="card"><h3 id="ah"></h3><pre id="asrc"></pre></div>
    <div class="card"><h3 id="bh"></h3><pre id="bsrc"></pre></div>
  </div>
  <div class="actions">
    <button class="same"   onclick="label('same')">same <kbd>s</kbd></button>
    <button class="diff"   onclick="label('different')">different <kbd>d</kbd></button>
    <button class="unsure" onclick="label('unsure')">unsure <kbd>u</kbd></button>
    <button onclick="back()">back</button>
    <button onclick="save()" style="margin-left:auto">export jsonl</button>
  </div>
  <div class="bar"><i id="prog"></i></div>
</main>
<script>
const PAIRS = __PAIRS__;
const KEY = "coherence-calibration-labels-v1";
let labels = JSON.parse(localStorage.getItem(KEY) || "{}");
let i = PAIRS.findIndex((p, n) => labels[n] === undefined);
if (i < 0) i = PAIRS.length - 1;

function render() {
  const p = PAIRS[i];
  document.getElementById("pos").textContent = `${i + 1} of ${PAIRS.length}`;
  const c = {same: 0, different: 0, unsure: 0};
  Object.values(labels).forEach(v => c[v] !== undefined && c[v]++);
  const n = Object.keys(labels).length;
  document.getElementById("tally").textContent =
    `${n} labelled — ${c.same} same, ${c.different} different, ${c.unsure} unsure`;
  document.getElementById("prog").style.width = (100 * n / PAIRS.length) + "%";
  document.getElementById("meta").innerHTML =
    `${p.library} &nbsp;·&nbsp; jaccard <b>${p.jaccard}</b>` +
    (labels[i] ? ` &nbsp;·&nbsp; <span class="done">already: ${labels[i]}</span>` : "");
  document.getElementById("ah").innerHTML = `${p.a} <span class="where">${p.a_file || ""}:${p.a_line || ""}</span>`;
  document.getElementById("bh").innerHTML = `${p.b} <span class="where">${p.b_file || ""}:${p.b_line || ""}</span>`;
  document.getElementById("asrc").textContent = p.a_src || "(source not captured)";
  document.getElementById("bsrc").textContent = p.b_src || "(source not captured)";
  window.scrollTo(0, 0);
}
function label(v) {
  labels[i] = v;
  localStorage.setItem(KEY, JSON.stringify(labels));
  if (i < PAIRS.length - 1) i++;
  render();
}
function back() { if (i > 0) i--; render(); }
function save() {
  const out = PAIRS.map((p, n) => {
    const r = Object.assign({}, p);
    r.label = labels[n] === undefined ? null : labels[n];
    return JSON.stringify(r);
  }).join("\\n") + "\\n";
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([out], {type: "application/jsonl"}));
  a.download = "pairs-labelled.jsonl";
  a.click();
}
addEventListener("keydown", e => {
  if (e.key === "s") label("same");
  else if (e.key === "d") label("different");
  else if (e.key === "u") label("unsure");
  else if (e.key === "ArrowLeft") back();
});
render();
</script>
"""


def main() -> None:
    src = os.path.join(HERE, "pairs.jsonl")
    rows = [json.loads(line) for line in open(src, encoding="utf-8") if line.strip()]
    out = os.path.join(HERE, "label.html")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(PAGE.replace("__PAIRS__", json.dumps(rows)))
    print(f"{len(rows)} pairs -> {out}")
    print("open it, label with s / d / u, then export and run:")
    print("  coherence-ratchet calibrate score calibration/pairs-labelled.jsonl")


if __name__ == "__main__":
    main()
