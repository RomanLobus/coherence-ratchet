"""Queries over the derived self-model.

Answers the questions an agent (or a steward) asks before making a change:

  - "which sites compute <concept>?"        -> concept    (default)
  - "what is the canonical <entity> shape?" -> entity
  - "does a helper for <x> exist?"          -> helper
  - "what layer / deps is <module>?"        -> module
  - "what conventions govern <topic>?"      -> convention

The deterministic core needs no API key and no network. `--llm` adds an optional semantic matcher
(env-gated on ANTHROPIC_API_KEY) that ranks the derived candidates by meaning rather than shared
tokens; it is constrained to the derived model and falls back to the deterministic answer on any
failure, so the tool is never *dependent* on it.
"""
from __future__ import annotations

import json
import os
import re

from .selfmodel import _name_tokens

_STOP = {
    "which", "what", "where", "does", "do", "is", "the", "a", "an", "of", "for", "to", "in", "on",
    "sites", "site", "compute", "computes", "canonical", "shape", "exist", "exists", "already",
    "helper", "helpers", "reuse", "layer", "layers", "depend", "depends", "dependency", "module",
    "modules", "convention", "conventions", "constant", "value", "values", "govern", "governs",
    "entity", "shapes", "and", "diverge", "diverges", "how", "there", "any",
    "it", "its", "has", "have", "are", "with", "this", "that", "use", "used", "uses",
    "shared", "constants", "govern", "governs", "or", "across", "modules",
}


def _intent(q: str) -> str:
    ql = q.lower()
    if re.search(r"\bconvention|\bconstant|\bvalue", ql):
        return "convention"
    if re.search(r"\bentity|\bshape|\bcanonical", ql):
        return "entity"
    if re.search(r"\blayer|\bdepend|\bimport|\brole", ql):
        return "module"
    if re.search(r"\bhelper|\breuse|\bexist|\balready", ql):
        return "helper"
    return "concept"


def _subject_tokens(q: str) -> list[str]:
    toks = [t.lower() for t in re.split(r"[^A-Za-z0-9]+", q) if t]
    subj = []
    for t in toks:
        if t in _STOP:
            continue
        subj.extend(_name_tokens(t))
    # No fallback to all tokens: an all-stopword question (e.g. "what conventions are there?") should
    # leave the subject empty, which the matchers read as "show everything of this kind".
    return subj


# --- deterministic matchers -------------------------------------------------

def _concept(model, subj):
    hits = []
    for f in model["functions"]:
        hay = set(f["tokens"]) | {t for c in f["calls"] for t in _name_tokens(c)}
        doc = f["doc"].lower()
        score = sum(1 for s in subj if s in hay) + sum(1 for s in subj if s in doc)
        if score:
            hits.append({"qualname": f["qualname"], "score": score, "doc": f["doc"]})
    hits.sort(key=lambda h: (-h["score"], h["qualname"]))
    # helpers that already consolidate this concept
    helpers = [h for h in model["helpers"] if any(s in _name_tokens(h["concept"]) or s == h["concept"] for s in subj)]
    return {"matches": hits, "helpers": helpers}


def _entity(model, subj):
    out = []
    for e in model["entities"]:
        name_toks = _name_tokens(e["name"])
        if not any(s in name_toks or s == e["name"].lower() for s in subj):
            continue
        if e["kind"] == "dict-shape":
            n = len(e["sites"])
            # The canonical shape is the contract every site agrees on: keys present in ALL sites.
            # Keys present in only some sites are the divergence the steward should look at.
            canonical = sorted(k for k, c in e["key_frequency"].items() if c == n)
            canon_set = set(canonical)
            divergent = {}
            for m, keys in e["per_site_keys"].items():
                missing = sorted(canon_set - set(keys))
                extra = sorted(set(keys) - canon_set)
                if missing or extra:
                    divergent[m] = {"missing": missing, "extra": extra}
            out.append({"name": e["name"], "kind": e["kind"], "canonical_keys": canonical,
                        "sites": e["sites"], "divergent_sites": divergent})
        else:
            out.append({"name": e["name"], "kind": e["kind"], "module": e["module"], "fields": e["fields"]})
    return {"matches": out}


def _helper(model, subj):
    hits = []
    for h in model["helpers"]:
        ctoks = _name_tokens(h["concept"])
        if any(s in ctoks or s == h["concept"] for s in subj):
            hits.append(h)
    # also surface single functions whose name matches, as reuse candidates
    fns = [f["qualname"] for f in model["functions"]
           if any(s in f["tokens"] for s in subj)]
    return {"matches": hits, "functions": fns}


def _module(model, subj):
    out = []
    for m in model["modules"]:
        mt = _name_tokens(m["module"])
        if any(s in mt or s in m["module"].lower() for s in subj):
            out.append(m)
    return {"matches": out}


def _convention(model, subj):
    out = []
    for c in model["conventions"]:
        hay = (c["value"] + " " + " ".join(c["modules"])).lower()
        if not subj or any(s in hay for s in subj):
            out.append(c)
    return {"matches": out}


_DISPATCH = {
    "concept": _concept, "entity": _entity, "helper": _helper,
    "module": _module, "convention": _convention,
}


def answer(model: dict, question: str, use_llm: bool = False) -> dict:
    intent = _intent(question)
    subj = _subject_tokens(question)
    result = _DISPATCH[intent](model, subj)
    result.update({"intent": intent, "subject": subj, "question": question, "matcher": "deterministic"})
    if use_llm:
        try:
            ranked = _llm_rerank(model, question, intent, result)
            if ranked is not None:
                result["llm"] = ranked
                result["matcher"] = "deterministic+llm"
        except Exception as exc:  # never let the optional layer break the query
            result["llm_error"] = str(exc)
    return result


# --- optional LLM matcher (env-gated, degrades gracefully) ------------------

def _llm_rerank(model, question, intent, det_result):
    """Ask an LLM to pick the best matches from the DERIVED candidates only. Returns None (silent
    fallback) if no key is configured. Constrained to the model — it may not invent sites."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    import urllib.request

    # Give the model only what the deterministic pass surfaced plus a small candidate pool, so it
    # ranks by meaning but cannot hallucinate a site that is not in the code.
    candidates = [f["qualname"] for f in model["functions"]]
    prompt = (
        "You are matching a question against a DERIVED code self-model. Choose only from the "
        "candidate list; never invent a name. Return strict JSON: "
        '{"best": [names], "why": "one sentence"}.\n\n'
        f"Question: {question}\nIntent: {intent}\n"
        f"Candidates: {json.dumps(candidates)}\n"
        f"Deterministic top matches: {json.dumps(det_result.get('matches', [])[:10])}\n"
    )
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    text = "".join(b.get("text", "") for b in payload.get("content", []))
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {"raw": text}


# --- rendering --------------------------------------------------------------

def render(result: dict) -> None:
    intent = result["intent"]
    print(f"[{intent}]  subject: {' '.join(result['subject']) or '(all)'}   matcher: {result['matcher']}")
    matches = result.get("matches", [])
    if not matches:
        print("  (no matches in the derived model)")
    elif intent == "concept":
        for h in matches[:12]:
            doc = f"  — {h['doc']}" if h["doc"] else ""
            print(f"  {h['qualname']}  (score {h['score']}){doc}")
        for h in result.get("helpers", []):
            print(f"  reuse: a '{h['concept']}' helper already exists -> {h['canonical']}"
                  + (f" (duplicated in {', '.join(h['duplicates'])})" if h["duplicates"] else ""))
    elif intent == "entity":
        for e in matches:
            if e["kind"] == "dict-shape":
                print(f"  {e['name']} (dict-shape) canonical keys (in every site): {', '.join(e['canonical_keys']) or '(none shared)'}")
                print(f"    seen in: {', '.join(e['sites'])}")
                for m, diff in e.get("divergent_sites", {}).items():
                    bits = []
                    if diff["missing"]:
                        bits.append(f"missing {', '.join(diff['missing'])}")
                    if diff["extra"]:
                        bits.append(f"extra {', '.join(diff['extra'])}")
                    print(f"    diverges in {m}: {'; '.join(bits)}")
            else:
                print(f"  {e['name']} ({e['kind']}) in {e['module']}: {', '.join(e['fields'])}")
    elif intent == "helper":
        for h in matches:
            print(f"  '{h['concept']}' -> reuse {h['canonical']}"
                  + (f" (duplicated in {', '.join(h['duplicates'])})" if h["duplicates"] else ""))
        if result.get("functions"):
            print(f"  candidate functions: {', '.join(result['functions'][:8])}")
    elif intent == "module":
        for m in matches:
            print(f"  {m['module']}  role={m['role']}  fan_in={m['fan_in']} fan_out={m['fan_out']}")
            if m["depends_on"]:
                print(f"    depends on: {', '.join(m['depends_on'])}")
    elif intent == "convention":
        for c in matches[:15]:
            print(f"  {c['value']}  in {', '.join(c['modules'])}")
    if result.get("llm"):
        print(f"\n  LLM match: {result['llm'].get('best')}  — {result['llm'].get('why', '')}")
    elif result.get("llm_error"):
        print(f"\n  (LLM matcher unavailable: {result['llm_error']})")
