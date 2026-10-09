"""Portable configuration and local artifact paths. No credentials or remote calls."""
from pathlib import Path
from importlib.resources import files
import datetime, hashlib, json, os

ROOT = Path(os.environ.get('ALPHA_WORK_DIR', 'artifacts')).expanduser().resolve()
DATA = Path(os.environ.get('ALPHA_DATA_ROOT', ROOT/'licensed_data')).expanduser().resolve()
R1 = DATA.parent
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
def read_json(rel):
    rel=Path(rel)
    if rel.parts[0]=='configs':
        override=os.environ.get('ALPHA_CONFIG_DIR')
        p=Path(override)/rel.name if override else files('alpha_discovery').joinpath('_configs',rel.name)
    else: p=ROOT/rel
    return json.loads(p.read_text())
def write_json(rel,obj):
    p=(ROOT/rel).resolve()
    if not p.is_relative_to(ROOT): raise PermissionError('Output outside ALPHA_WORK_DIR')
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+'.tmp')
    q.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n');q.replace(p)
def state(**values):
    p=ROOT/'PROJECT_STATE.json';s=json.loads(p.read_text()) if p.exists() else {}
    s.update(values);s['updated_at']=now();write_json('PROJECT_STATE.json',s)
def source_guard():
    # This distribution never imports or executes the original research tree.
    return None
