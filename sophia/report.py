"""Escaped local evidence reports. No scripts, external assets or URL navigation."""
from html import escape
import json
import os
from pathlib import Path
import tempfile

def render_html(results):
    e=lambda v:escape(str(v),quote=True)
    sections=[]
    for i,r in enumerate(results,1):
        gates=''.join(f'<li><code>{e(g["code"])}</code> {e(g["explanation"])}</li>' for g in r['gates']) or '<li>All supplied evidence passed the declared research checks. This establishes no investment merit.</li>'
        markets=''.join(f'<tr><td>{e(m["venue"])}</td><td>{e(m["mid_quote"])}</td><td>{e(m["quote"]["symbol"])}</td><td>{e(m["spread_bps"])}</td><td>{e(m["bid_depth_usd"])}</td><td>{e(m["ask_depth_usd"])}</td></tr>' for m in r['markets'])
        lenses=''.join(f'<details><summary>{e(l["id"])} <span>{e(l["status"])}</span></summary><p>{e(l["explanation"])}</p><pre>{e(json.dumps(l,indent=2))}</pre></details>' for l in r['lenses'])
        sources=''.join(f'<tr><td>{e(s["id"])}</td><td>{e(s["publisher"])}</td><td>{e(", ".join(s["upstreams"]))}</td><td>{e(s["observed_at"])}</td><td>{e(s["verification"])}</td></tr>' for s in r['evidence'])
        sections.append(f'''<section id="scenario-{i}"><p class="eyebrow">Scenario {i} / {e(r['evidence_status'])}</p><h2>{e(r['status'])}</h2>
<p><strong>{e(r['asset']['symbol'])}</strong> <code>{e(r['asset_key'])}</code></p><p>Evaluated {e(r['as_of'])}</p><ul>{gates}</ul>
<h3>Observed market evidence</h3><div class="scroll"><table><thead><tr><th>Venue</th><th>Midpoint</th><th>Quote</th><th>Spread / bps</th><th>Bid depth / USD</th><th>Ask depth / USD</th></tr></thead><tbody>{markets}</tbody></table></div><p class="muted">Depth is limited to 1% from midpoint. These are supplied observations, never executable fills.</p>
<h3>Seven research lenses</h3>{lenses}<details><summary>Inspect source lineage and hashes</summary><div class="scroll"><table><thead><tr><th>Source</th><th>Publisher</th><th>Upstreams</th><th>Observed / UTC</th><th>Evidence label</th></tr></thead><tbody>{sources}</tbody></table></div><p class="hash">Input SHA-256 {e(r['input_sha256'])}<br>Policy SHA-256 {e(r['policy_sha256'])}</p><p>Source payload hashes and facts are retained in results.json. Hashes establish consistency; they do not authenticate a publisher.</p></details>
<h3>Operator notes / untrusted text</h3><p class="notes">{e(r['notes'])}</p></section>''')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; base-uri 'none'; form-action 'none'"><title>Sophia Research / Evidence report</title><style>
:root{color-scheme:light}*{box-sizing:border-box}body{font:16px/1.6 system-ui,sans-serif;color:#17252b;background:#f4f5ef;margin:0}main{max-width:1100px;margin:auto;padding:48px 28px}header{padding-bottom:32px;border-bottom:2px solid #17252b}h1{font-size:clamp(32px,5vw,56px);line-height:1.1;letter-spacing:-2px;max-width:820px;margin:16px 0}h2{font-size:28px;overflow-wrap:anywhere}h3{font-size:17px;margin-top:28px}.eyebrow{font:12px monospace;letter-spacing:2px;text-transform:uppercase;color:#356357}.lede{max-width:780px;font-size:20px}.boundary{background:#e0e8df;padding:16px 20px;border-left:3px solid #356357}section{padding:32px 0 40px;border-bottom:1px solid #aebbb3}li{padding:4px 0}code,pre,.hash{font:12px/1.7 ui-monospace,monospace;overflow-wrap:anywhere}pre{white-space:pre-wrap;background:#e9ece4;padding:16px}details{padding:12px 0;border-bottom:1px solid #ccd3cb}summary{cursor:pointer;font-weight:600}summary span{float:right;font:12px monospace;color:#356357}table{border-collapse:collapse;width:100%;font-size:13px;text-align:left}th,td{padding:10px 12px 10px 0;border-bottom:1px solid #ccd3cb;vertical-align:top}.scroll{overflow-x:auto}.muted,footer{color:#4e625a;font-size:13px}.notes{white-space:pre-wrap;overflow-wrap:anywhere}footer{padding-top:28px}a{color:inherit}
</style></head><body><main><header><p class="eyebrow">Sophia Research / local evidence review</p><h1>Make the evidence visible.<br>Keep uncertainty attached.</h1><p class="lede">Deterministic crypto research checks across asset identity, source lineage, liquidity and critical risk.</p><p class="boundary"><strong>RESEARCH ONLY · EXECUTION DISABLED · DISPATCH DISABLED</strong><br>SYNTHETIC examples are authored demonstrations. Real-mode inputs remain OPERATOR ATTESTED, never independently verified by this program.</p></header>''' + ''.join(sections) + '<footer>No orders, wallets, email, model calls, portfolio ledger or financial backtest. No performance or suitability claim. Review the JSON evidence and the project limitations before interpreting any qualification.</footer></main></body></html>\n'

def write_bundle(results, directory):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    bundle=dict(product='Sophia Research',version='0.2.0',results=results)
    files={'results.json':json.dumps(bundle,indent=2,sort_keys=True,allow_nan=False)+'\n','report.html':render_html(results)}
    # Atomic per-file replacement. There is no transaction ledger and no execution.
    for name,body in files.items():
        path=None
        try:
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=directory,delete=False) as temp:
                path=Path(temp.name); temp.write(body)
            os.replace(path,directory/name)
        finally:
            if path is not None and path.exists(): path.unlink()
    return bundle
