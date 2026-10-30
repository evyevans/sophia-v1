"""Allowlisted release integrity, local link/pattern checks and deterministic ZIP.

This pattern scan complements a dedicated secret scanner; it cannot replace one.
Private denylist values may be supplied from outside the release. Never echo them.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote
import zipfile

ROOT=Path(__file__).resolve().parents[1]
IGNORED={'__pycache__','demo-output','research-output','.git'}

def allowed(root):
    root=Path(root).resolve()
    values=json.loads((root/'ALLOWLIST.json').read_text())
    if not isinstance(values,list) or len(set(values))!=len(values): raise ValueError('Invalid allowlist.')
    for name in values:
        p=PurePosixPath(name)
        if not isinstance(name,str) or p.is_absolute() or '..' in p.parts or '\\' in name or str(p)!=name:
            raise ValueError('Unsafe allowlist path.')
        target=root/name
        if any(part.startswith('.') and part not in ('.github','.gitignore') for part in p.parts): raise ValueError('Unexpected hidden path.')
        if target.is_symlink() or any(parent.is_symlink() for parent in target.parents if parent!=root and root in parent.parents): raise ValueError('Symlinks are excluded.')
    if 'ALLOWLIST.json' not in values or 'RELEASE_FILES.json' not in values: raise ValueError('Release metadata must be allowlisted.')
    return values

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def make_manifest(root):
    root=Path(root)
    names=allowed(root)
    hashes={name:sha(root/name) for name in names if name!='RELEASE_FILES.json'}
    (root/'RELEASE_FILES.json').write_text(json.dumps(dict(schema_version=1,product='Floatglass Research',version='0.2.0',
        files=hashes,self_hash_excluded='RELEASE_FILES.json is covered by the archive checksum, not its own hash.'),indent=2,sort_keys=True)+'\n')

def scan_text(body):
    findings=[]
    patterns=[r'AKIA[0-9A-Z]{16}',r'gh[pousr]_[A-Za-z0-9]{30,}',r'xox[abpr]-[A-Za-z0-9-]{10,}',
              r'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}',r'sk_(?:live|test)_[A-Za-z0-9]{10,}',
              r'sbp_[a-f0-9]{20,}',r'-----BEGIN [A-Z ]*PRIVATE KEY-----']
    if any(re.search(p,body) for p in patterns): findings.append('credential_pattern')
    if re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',body): findings.append('email')
    if re.search(r'/(?:Users|home)/[^\s/]+/',body): findings.append('local_path')
    if re.search(r'https://[a-z0-9]{15,}\.supabase\.co',body,re.I): findings.append('private_project_endpoint')
    relationship_terms=['au'+'nt','au'+'ntie','nep'+'hew','ni'+'ece']
    if re.search(r'\b(?:'+'|'.join(relationship_terms)+r')\b',body,re.I): findings.append('relationship_context')
    return findings

def check(root,private_terms=()):
    root=Path(root); names=allowed(root); errors=[]
    manifest=json.loads((root/'RELEASE_FILES.json').read_text())
    if set(manifest['files'])!=set(names)-{'RELEASE_FILES.json'}: errors.append('manifest_file_set')
    for p in root.rglob('*'):
        relative=p.relative_to(root)
        if set(relative.parts)&IGNORED or p.name=='.DS_Store' or p.suffix=='.pyc': continue
        if p.is_symlink(): errors.append('symlink:'+str(relative))
        elif p.is_file() and relative.as_posix() not in names: errors.append('unlisted_file:'+str(relative))
    for name in names:
        p=root/name
        if not p.is_file(): errors.append('missing_file:'+name); continue
        if name!='RELEASE_FILES.json' and sha(p)!=manifest['files'].get(name): errors.append('hash_mismatch:'+name)
        try: body=p.read_text(encoding='utf-8')
        except UnicodeError: errors.append('binary_file:'+name); continue
        if '\x00' in body: errors.append('binary_file:'+name)
        errors.extend(f'{finding}:{name}' for finding in scan_text(body))
        if any(re.search(r'(?<![A-Za-z0-9])'+re.escape(term)+r'(?![A-Za-z0-9])',body,re.I) for term in private_terms if term): errors.append('private_term:'+name)
        if p.suffix=='.md':
            for link in re.findall(r'\]\(([^\s)]+)(?:\s+"[^"]*")?\)',body):
                if link.startswith(('https://','http://','mailto:','#')): continue
                target=(p.parent/unquote(link.split('#')[0])).resolve()
                if not target.is_relative_to(root.resolve()) or not target.exists(): errors.append('broken_link:'+name)
    return errors

def archive(root,path):
    root=Path(root).resolve(); path=Path(path).resolve()
    checksum_path=path.with_suffix(path.suffix+'.sha256')
    if path.is_relative_to(root) or checksum_path.resolve().is_relative_to(root):
        raise ValueError('Archive and checksum must be outside the source tree.')
    issues=check(root)
    if issues: raise ValueError('Release check failed: '+','.join(issues))
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as out:
        for name in sorted(allowed(root)):
            info=zipfile.ZipInfo('floatglass-research/'+name,date_time=(2026,10,30,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16
            out.writestr(info,(root/name).read_bytes())
    checksum=sha(path)
    checksum_path.write_text(checksum+'  '+path.name+'\n')
    return checksum

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['manifest','check','archive'])
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--private-terms',type=Path,help='External JSON string list, never bundled')
    p.add_argument('--archive',type=Path,default=ROOT.parent/'floatglass-research-0.2.0.zip')
    args=p.parse_args()
    try:
        if args.command=='manifest': make_manifest(args.root)
        else:
            terms=json.loads(args.private_terms.read_text()) if args.private_terms else []
            issues=check(args.root,terms)
            if issues:
                for issue in issues: print(issue)
                return 1
            if args.command=='archive': print('Archive SHA-256:',archive(args.root,args.archive))
        print('PASS: allowlist, hashes, UTF-8, local links and pattern checks.' if args.command!='manifest' else 'Manifest updated; review changes before distribution.')
        return 0
    except (ValueError,OSError,KeyError,TypeError):
        print('Release metadata or filesystem error; no release assertion made.',file=sys.stderr); return 2

if __name__=='__main__': raise SystemExit(main())
