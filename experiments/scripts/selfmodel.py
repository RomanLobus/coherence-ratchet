"""Derive a self-model: which functions compute an order total, and the divergent line shapes.
Heuristic, deterministic — the point is it is DERIVED from code (stays fresh), not hand-authored.

NOTE: this is the original narrow seed used in the reframe-A experiment (kept for provenance). The
promoted, general version lives in `coherence_ratchet/selfmodel.py` and is what the CLI runs
(`coherence-ratchet selfmodel derive|query`). Prefer that for anything new."""
import ast, os, sys, json
def derive(root):
    sites=[]; shapes={}
    for dp,_,fs in os.walk(root):
        for fn in fs:
            if not fn.endswith(".py"): continue
            src=open(os.path.join(dp,fn)).read()
            try: tree=ast.parse(src)
            except: continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for sub in ast.walk(node):
                        # sum(<a>[k1] * <a>[k2] for <x> in order[field])
                        if isinstance(sub, ast.Call) and getattr(sub.func,"id","")=="sum":
                            for g in [a for a in sub.args if isinstance(a,(ast.GeneratorExp,ast.ListComp))]:
                                elt=g.elt
                                if isinstance(elt, ast.BinOp) and isinstance(elt.op, ast.Mult):
                                    keys=[s.slice.value for s in ast.walk(elt) if isinstance(s,ast.Subscript) and isinstance(getattr(s,'slice',None),ast.Constant)]
                                    field=None
                                    for comp in g.generators:
                                        it=comp.iter
                                        if isinstance(it,ast.Subscript) and isinstance(it.slice,ast.Constant): field=it.slice.value
                                    sites.append({"module":fn[:-3],"function":node.name,"line_field":field,"item_keys":sorted(set(keys))})
                                    if field: shapes[field]=sorted(set(keys))
    return {"total_sites":sites,"divergent_line_shapes":shapes}
if __name__=="__main__":
    print(json.dumps(derive(sys.argv[1]), indent=1))
