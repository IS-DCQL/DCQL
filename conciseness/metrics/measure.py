#!/usr/bin/env python3
"""Measure §6.2 syntactic-conciseness metrics over the 7 languages x 16 workloads.

Metrics (per language, summed over the 16 workload statements):
  * LOC             - non-blank, non-comment lines (also broken down by life-cycle
                      stage T1..T4 for Figure 5a).
  * Syntactic noise - character-level punctuation density: special (non-alphanumeric,
                      non-underscore, non-CJK) characters over all non-whitespace
                      characters, comments excluded.
  * Halstead E      - effort, E = (n1/2) * (N2/n2) * (N1+N2) * log2(n1+n2), where
                      n1/n2 = distinct operators/operands, N1/N2 = their totals;
                      computed per statement and summed.

Token classification (uniform across languages):
  operands  (business) = identifiers that are not keywords, and literals (strings/numbers)
  operators (noise)    = punctuation/symbols, reserved keywords, words used as $-operators
                         (MongoDB) or as function names (a word immediately before "(").
Comments are excluded.  Output: metrics_results.csv (+ metrics_by_file.csv).
"""
import os, re, csv, math, glob

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
LANGS = ["SQL", "OQL", "MQL", "N1QL", "XQuery", "JSONiq", "DCQL"]
EXT = {"SQL": "sql", "OQL": "jpql", "MQL": "js", "N1QL": "n1ql",
       "XQuery": "xq", "JSONiq": "jq", "DCQL": "dcql"}
# Extra extensions a language may use for some cells. OQL's organic-polymer T2/T3 are
# written as native SQL run through Hibernate, so they carry the ".sql" extension.
ALT_EXT = {"OQL": ["sql"]}

def dialect(lang, path):
    """The parsing dialect (comment style + keyword set) for a file. OQL's native-SQL
    cells are tokenized as SQL but still attributed to OQL."""
    if lang == "OQL" and path.endswith(".sql"):
        return "SQL"
    return lang
LINE_COMMENT = {"SQL": "--", "N1QL": "--", "OQL": "//", "MQL": "//", "DCQL": "//"}  # XQuery/JSONiq: none
BLOCK_COMMENT = {"XQuery", "JSONiq"}

# reserved clause keywords (lowercased) per language; function/constructor names are
# detected separately by the "word immediately before '(' " rule, so are omitted here.
KW = {
 "SQL": set("select distinct from where and or not in is null like ilike group by having order asc desc as exists join inner left outer on create table drop alter rename column to references primary key default delete insert into values update set union intersect all between".split()),
 "N1QL": set("select distinct from where and or not in is null missing like group by having order asc desc as unnest nest any every satisfies end for when create collection drop alter update set infer with array meta raw".split()),
 "MQL": set("true false null".split()),
 "XQuery": set("for let where return some every in satisfies and or not as into insert delete rename replace node nodes value of with db math xs fn json".split()),
 "JSONiq": set("for let where return some every in satisfies and or not eq ne lt gt le ge true false null".split()),
 "DCQL": set("select distinct from template templates dataset where and or not in is null like exist every any all top bottom startwith endwith create drop insert into values delete update set alter add table array container generator string number range choice image file unit type option optiongroup error multiple describe group by having order asc desc as schema".split()),
 "OQL": set("select from where and or not in for new class public private return void true false null this".split()),
}

MULTI = ["<=", ">=", "<>", "!=", "==", "&&", "||", "::", "//"]   # // = XQuery descendant axis
SINGLE = set("=<>!()[]{},;.:&|@+-*/%")

def tokenize(text, lang):
    """Yield (kind, text) tokens; kind in {STR,NUM,WORD,SYM}. Comments skipped."""
    i, n = 0, len(text)
    lc = LINE_COMMENT.get(lang)
    block = lang in BLOCK_COMMENT
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1; continue
        if block and text.startswith("(:", i):                       # (: ... :)
            j = text.find(":)", i+2); i = (j+2) if j >= 0 else n; continue
        if lc and text.startswith(lc, i):                            # line comment
            j = text.find("\n", i); i = (j if j >= 0 else n); continue
        if c in "\"'`":                                              # string literal
            q = c; j = i+1
            while j < n and text[j] != q:
                j += 2 if (text[j] == "\\" and q != "`") else 1
            yield ("STR", text[i:j+1]); i = j+1; continue
        if c.isdigit():                                              # number
            j = i
            while j < n and (text[j].isdigit() or text[j] == "."):
                j += 1
            yield ("NUM", text[i:j]); i = j; continue
        if c.isalpha() or c in "_$" or "一" <= c <= "鿿":    # word (ident/keyword/$op)
            j = i+1
            while j < n and (text[j].isalnum() or text[j] in "_$-" or "一" <= text[j] <= "鿿"):
                j += 1
            yield ("WORD", text[i:j]); i = j; continue
        for m in MULTI:                                             # multi-char symbol
            if text.startswith(m, i):
                yield ("SYM", m); i += len(m); break
        else:
            if c in SINGLE:
                yield ("SYM", c)
            i += 1

def classify(tokens, lang):
    """Return (operators, operands) as lists of token texts."""
    kw = KW[lang]
    ops, opnds = [], []
    for idx, (kind, t) in enumerate(tokens):
        if kind == "SYM":
            ops.append(t)
        elif kind in ("STR", "NUM"):
            opnds.append(t)
        else:  # WORD
            low = t.lower()
            is_func = (idx+1 < len(tokens) and tokens[idx+1] == ("SYM", "("))
            if low in kw or t.startswith("$") or is_func:
                ops.append(low if low in kw else t)
            else:
                opnds.append(t)
    return ops, opnds

def halstead(ops, opnds):
    n1, n2 = len(set(ops)), len(set(opnds))
    N1, N2 = len(ops), len(opnds)
    if n1 == 0 or n2 == 0:
        return 0.0
    return (n1/2) * (N2/n2) * (N1+N2) * math.log2(n1+n2)

def loc(text, lang):
    if lang in BLOCK_COMMENT:
        text = re.sub(r"\(:.*?:\)", " ", text, flags=re.S)
    lc = LINE_COMMENT.get(lang)
    count = 0
    for ln in text.split("\n"):
        if lc:
            p = ln.find(lc)
            if p >= 0:
                ln = ln[:p]
        if ln.strip():
            count += 1
    return count

def char_noise(text, lang):
    """Character-level punctuation density: (#special chars, #non-whitespace chars)."""
    if lang in BLOCK_COMMENT:
        text = re.sub(r"\(:.*?:\)", " ", text, flags=re.S)
    lc = LINE_COMMENT.get(lang)
    if lc:
        text = "\n".join(ln[:ln.find(lc)] if lc in ln else ln for ln in text.split("\n"))
    nonws = punct = 0
    for ch in text:
        if ch.isspace():
            continue
        nonws += 1
        if not (ch.isalnum() or ch == "_" or "一" <= ch <= "鿿"):
            punct += 1
    return punct, nonws

def stage(task):                       # T1-1/T1-2 -> T1 ; T3-1/T3-2 -> T3
    return "T" + task[1]

def main():
    by_file, agg = [], {}
    for lang in LANGS:
        a = {"loc": 0, "T1": 0, "T2": 0, "T3": 0, "T4": 0,
             "punct_ch": 0, "nonws_ch": 0, "halstead": 0.0}
        files = []
        for e in [EXT[lang]] + ALT_EXT.get(lang, []):
            files += glob.glob(os.path.join(ROOT, lang, "*", "*." + e))
        for f in sorted(set(files)):
            d = dialect(lang, f)
            text = open(f, encoding="utf-8").read()
            task = os.path.splitext(os.path.basename(f))[0]
            ops, opnds = classify(list(tokenize(text, d)), d)
            L = loc(text, d); H = halstead(ops, opnds)
            pc, nw = char_noise(text, d)
            a["loc"] += L; a[stage(task)] += L
            a["punct_ch"] += pc; a["nonws_ch"] += nw; a["halstead"] += H
            by_file.append({"language": lang, "domain": os.path.basename(os.path.dirname(f)),
                            "task": task, "loc": L,
                            "noise": round(pc/nw, 4) if nw else 0,
                            "halstead": round(H, 1)})
        a["noise"] = round(a["punct_ch"]/a["nonws_ch"], 4) if a["nonws_ch"] else 0
        a["halstead"] = round(a["halstead"], 1)
        agg[lang] = a

    with open(os.path.join(HERE, "metrics_results.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["language", "loc_total", "loc_T1", "loc_T2", "loc_T3", "loc_T4",
                    "syntactic_noise", "halstead"])
        for lang in LANGS:
            a = agg[lang]
            w.writerow([lang, a["loc"], a["T1"], a["T2"], a["T3"], a["T4"], a["noise"], a["halstead"]])
    with open(os.path.join(HERE, "metrics_by_file.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["language", "domain", "task", "loc", "noise", "halstead"])
        w.writeheader(); w.writerows(by_file)

    print(f"{'lang':7} {'LOC':>4} (T1 T2 T3 T4){'':4}{'noise':>7} {'halstead':>10}")
    for lang in LANGS:
        a = agg[lang]
        print(f"{lang:7} {a['loc']:>4} ({a['T1']:>2} {a['T2']:>2} {a['T3']:>2} {a['T4']:>2}) "
              f"{a['noise']:>7} {a['halstead']:>10}")

if __name__ == "__main__":
    main()
