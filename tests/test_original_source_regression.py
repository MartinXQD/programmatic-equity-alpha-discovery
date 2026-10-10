"""Compare portable numerical outputs to a captured original-source synthetic fixture."""
from pathlib import Path
import ast,hashlib,json
import numpy as np
import pytest
from alpha_discovery.local_first_evaluator import DualEvaluator
from test_local_first import SmallPanel

ROOT=Path(__file__).resolve().parents[1]

def canonical_ast_dump(node):
    """Retain the recorded Python 3.13 AST format on Python 3.12 as well.

    Parsed AST list fields use the same empty-list omission on both versions;
    line attributes are excluded, while all populated fields retain their order.
    """
    if isinstance(node, ast.AST):
        fields=[]
        for name,value in ast.iter_fields(node):
            if isinstance(value,list) and not value:
                continue
            if value is None and getattr(type(node),name,...) is None:
                continue
            fields.append(f'{name}={canonical_ast_dump(value)}')
        return f'{type(node).__name__}({", ".join(fields)})'
    if isinstance(node,list):
        return '['+', '.join(canonical_ast_dump(value) for value in node)+']'
    return repr(node)

def test_extracted_numerical_ast_unchanged():
    provenance=json.loads((ROOT/'docs/source_provenance.json').read_text())
    checked=0
    for row in provenance:
        expected=row.get('unchanged_ast_hashes',{})
        if not expected:continue
        tree=ast.parse((ROOT/row['target']).read_text())
        actual={x.name:hashlib.sha256(canonical_ast_dump(x).encode()).hexdigest() for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
        for name,value in expected.items():
            assert actual[name]==value;checked+=1
    assert checked>=30

def test_original_dual_synthetic_golden_metrics_and_daily_path():
    expected=json.loads((ROOT/'tests/fixtures/original_dual_synthetic.json').read_text())
    panel=SmallPanel();result,daily=DualEvaluator(panel,37).compute(panel.fields['volume'],{'candidate_id':'SYNTHETIC_GOLDEN'})
    assert result['fixed_direction']==expected['fixed_direction']
    for key,value in expected['selection_metrics'].items():
        got=result['selection_metrics'][key]
        if isinstance(value,(float,int)) and not isinstance(value,bool):assert got==pytest.approx(value,abs=1e-12,rel=1e-10)
        else:assert got==value
    for e in expected['daily_examples']:
        row=daily[daily.date==e['date']].iloc[0]
        assert str(row.return_end.date())==e['return_end']
        for key,value in e.items():
            if key not in ['date','return_end']:assert row[key]==pytest.approx(value,abs=1e-12,rel=1e-10)
