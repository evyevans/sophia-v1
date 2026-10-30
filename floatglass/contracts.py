"""Strict local data primitives. Nothing here fetches or authenticates a source."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

class InputError(ValueError):
    """Malformed input; details intentionally exclude operator data."""

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def obj(value):
    if not isinstance(value,dict): raise InputError('Expected an object.')
    return value

def text(value, maximum=4096):
    if not isinstance(value,str) or not value.strip() or len(value)>maximum or any(ord(c)<32 and c!='\n' or ord(c)==127 for c in value):
        raise InputError('Expected bounded printable text.')
    return value

def decimal(value, *, zero=False):
    if not isinstance(value,str) or not re.fullmatch(r'-?\d{1,30}(?:\.\d{1,18})?',value):
        raise InputError('Decimal values must be bounded plain decimal strings.')
    try: result=Decimal(value)
    except InvalidOperation: raise InputError('Invalid decimal.') from None
    if not result.is_finite() or result<0 or (result==0 and not zero): raise InputError('Decimal outside allowed range.')
    return result

def stamp(value):
    try:
        t=datetime.fromisoformat(value.replace('Z','+00:00'))
        if t.tzinfo is None: raise ValueError
        return t.astimezone(timezone.utc)
    except (ValueError,TypeError,AttributeError,OverflowError): raise InputError('Expected an ISO timestamp with timezone.') from None

def bounded_tree(value, depth=0):
    if depth>18: raise InputError('Input nesting exceeds limit.')
    if isinstance(value,dict):
        if len(value)>100: raise InputError('Object exceeds limit.')
        for k,v in value.items(): text(k,128); bounded_tree(v,depth+1)
    elif isinstance(value,list):
        if len(value)>4000: raise InputError('Array exceeds limit.')
        for v in value: bounded_tree(v,depth+1)
    elif isinstance(value,str): text(value)
    elif value is not None and type(value) not in (bool,int): raise InputError('Unsupported JSON value; monetary floats are prohibited.')
    elif type(value) is int and abs(value)>10**12: raise InputError('Integer exceeds limit.')

def asset_key(asset):
    a=obj(asset)
    if not re.fullmatch(r'[a-z0-9-]{2,32}:[A-Za-z0-9-]{1,64}',text(a.get('chain_id'),100)): raise InputError('Invalid chain ID.')
    aid=text(a.get('asset_id'),128)
    if not re.fullmatch(r'(native|erc20|token):[A-Za-z0-9._-]{1,100}',aid): raise InputError('Invalid native or contract asset ID.')
    if a['chain_id'].startswith('eip155:') and aid.startswith('erc20:') and not re.fullmatch(r'erc20:0x[0-9a-fA-F]{40}',aid): raise InputError('Invalid EVM contract ID.')
    if type(a.get('decimals')) is not int or not 0<=a['decimals']<=36: raise InputError('Invalid asset decimals.')
    if a.get('representation') not in ('native','canonical','wrapped','bridged','liquid_staked'): raise InputError('Unknown representation.')
    if not re.fullmatch(r'[A-Z0-9._-]{1,20}',text(a.get('symbol'),20)): raise InputError('Invalid display symbol.')
    if not obj(a.get('provider_ids')): raise InputError('Provider IDs are required.')
    for k,v in a['provider_ids'].items(): text(k,64); text(v,128)
    return a['chain_id']+'/'+aid

def valid_asset_key(value):
    """Check a full chain/asset key without guessing a provider symbol mapping."""
    if not isinstance(value,str) or value.count('/')!=1: return False
    chain,aid=value.split('/')
    if not re.fullmatch(r'[a-z0-9-]{2,32}:[A-Za-z0-9-]{1,64}',chain): return False
    if not re.fullmatch(r'(native|erc20|token):[A-Za-z0-9._-]{1,100}',aid): return False
    return not (chain.startswith('eip155:') and aid.startswith('erc20:') and not re.fullmatch(r'erc20:0x[0-9a-fA-F]{40}',aid))

def load_json(path):
    if path.stat().st_size>8_000_000: raise InputError('Input exceeds 8 MB.')
    def pairs(items):
        out={}
        for k,v in items:
            if k in out: raise InputError('Duplicate JSON key.')
            out[k]=v
        return out
    def invalid(_): raise InputError('Nonfinite JSON value.')
    try: return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs,parse_constant=invalid)
    except (ValueError,RecursionError,UnicodeError): raise InputError('Invalid JSON input.') from None
