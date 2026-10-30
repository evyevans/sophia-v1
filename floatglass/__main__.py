"""python3 -m floatglass demo | evaluate LOCAL_JSON [--as-of UTC]."""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import sys
import json
from .contracts import InputError, load_json
from .core import evaluate
from .demo import run_demo
from .report import write_bundle

def main(argv=None):
    parser=argparse.ArgumentParser(description='Floatglass Research: offline crypto evidence checks; no execution or dispatch.')
    commands=parser.add_subparsers(dest='command',required=True)
    demo=commands.add_parser('demo',help='Three authored synthetic scenarios; no network or keys')
    demo.add_argument('--output',type=Path,default=Path('demo-output'))
    live=commands.add_parser('collect-btc',help='Opt-in public GET BTC/USD capture and research report; no credentials')
    live.add_argument('--output',type=Path,default=Path('live-output'))
    check=commands.add_parser('evaluate',help='Evaluate a local operator-supplied snapshot')
    check.add_argument('snapshot',type=Path)
    check.add_argument('--as-of',help='Explicit historical evaluation time; default: current UTC')
    check.add_argument('--output',type=Path,default=Path('research-output'))
    args=parser.parse_args(argv)
    try:
        if args.command=='collect-btc':
            from .live import collect
            snapshot,receipts,failures=collect()
            args.output.mkdir(parents=True,exist_ok=True)
            (args.output/'snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n')
            (args.output/'capture.json').write_text(json.dumps(dict(receipts=receipts,failures=failures),indent=2)+'\n')
            results=[evaluate(snapshot,as_of=datetime.now(timezone.utc).isoformat())]
        else:
            results=run_demo() if args.command=='demo' else [evaluate(load_json(args.snapshot),as_of=args.as_of or datetime.now(timezone.utc).isoformat())]
        write_bundle(results,args.output)
    except (InputError,OSError,ValueError,TypeError,KeyError,OverflowError,RecursionError,ArithmeticError):
        print('Input/output error. Check the input contract, timestamps and output permissions. No fallback data was used.',file=sys.stderr)
        return 2
    for r in results:
        print(f'{r["status"]:18} | {r["evidence_status"]} | {r["asset"]["symbol"]} | execution disabled')
        for g in r['gates']: print(f'  {g["code"]}: {g["explanation"]}')
    print('Saved report.html and results.json in the selected local output directory.')
    return 0

if __name__=='__main__': raise SystemExit(main())
