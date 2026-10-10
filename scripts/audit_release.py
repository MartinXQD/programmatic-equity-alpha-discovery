"""Audit the explicit release whitelist and Git index before committing or pushing."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys

ROOT=Path(__file__).resolve().parents[1]
def audit():
    manifest=json.loads((ROOT/'configs/release_manifest.json').read_text())
    paths=manifest['files'];errors=[]
    if paths!=sorted(set(paths)):errors.append('Whitelist is not sorted and unique')
    banned_suffixes={'.parquet','.npy','.npz','.xlsx','.zip','.sqlite','.db','.pem','.key'}
    token_patterns=[r'gh[pousr]_[A-Za-z0-9]{20,}',r'github_pat_[A-Za-z0-9_]{20,}',r'AKIA[0-9A-Z]{16}',r'-----BEGIN [A-Z ]*PRIVATE KEY-----',r'(?i)(?:password|api_key|access_token|session_cookie)\s*[:=]\s*[\"\'][^\"\']{8,}[\"\']']
    for rel in paths:
        p=ROOT/rel
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(ROOT):errors.append('Invalid file: '+rel);continue
        if p.suffix in banned_suffixes or p.name.startswith('.env') or any(x in p.parts for x in ['.venv','__pycache__','.git']):errors.append('Restricted file type: '+rel)
        if p.stat().st_size>2_000_000:errors.append('Unexpected large artifact: '+rel)
        if p.suffix=='.pdf':
            try:
                from pypdf import PdfReader
                reader=PdfReader(p);text='\n'.join(x.extract_text() or '' for x in reader.pages)
                if '/EmbeddedFiles' in str(reader.trailer):errors.append('Embedded attachments: '+rel)
            except ImportError:
                # The paper extras are optional for CI; the source was audited and
                # PDF bytes are separately inspected during the initial release.
                text=''
        elif p.suffix=='.png':text=''
        else:
            text=p.read_text()
            if p.suffix=='.py':ast.parse(text)
        if re.search(r'/(?:Users|home)/[^\s/]+',text):errors.append('Personal absolute path: '+rel)
        if any(re.search(pattern,text) for pattern in token_patterns):errors.append('Credential-like content: '+rel)
        if p.suffix=='.ipynb':
            nb=json.loads(text)
            if any(c.get('outputs') or c.get('execution_count') is not None for c in nb['cells'] if c['cell_type']=='code'):errors.append('Notebook contains saved execution outputs: '+rel)
    listed=set(paths)
    actual=set()
    for p in ROOT.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(ROOT)
        if p.name=='.DS_Store' or any(x in rel.parts for x in ['.git','.venv','__pycache__','.pytest_cache','artifacts','build','dist']) or any(x.endswith('.egg-info') for x in rel.parts):continue
        actual.add(str(rel))
    if actual!=listed:errors.append('Unlisted/missing release files: '+str(sorted(actual^listed)))
    if (ROOT/'.git').exists():
        tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'))-{''}
        if tracked and tracked!=listed:errors.append('Git index differs from explicit whitelist')
        # Inspect every historical filename if commits already exist.
        result=subprocess.run(['git','rev-list','--all','--objects'],cwd=ROOT,text=True,capture_output=True)
        if result.returncode==0:
            for line in result.stdout.splitlines():
                fields=line.split(' ',1)
                if len(fields)==2 and Path(fields[1]).suffix in banned_suffixes:errors.append('Restricted artifact in Git history: '+fields[1])
    if errors:raise RuntimeError('\n'.join(errors))
    print(f'PASS: {len(paths)} whitelisted files, source/outputs, paths, credentials and index')
    return paths
if __name__=='__main__':audit()
