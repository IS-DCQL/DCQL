#!/usr/bin/env python3
"""Compute several syntactic-noise schemes side by side, so the most suitable
definition can be chosen. Reuses the tokenizer/keyword sets from measure.py."""
import os, glob, re
import measure as M

PATHNAV = (".", "[", "]")

def strip_comments(text, lang):
    if lang in M.BLOCK_COMMENT:
        text = re.sub(r"\(:.*?:\)", " ", text, flags=re.S)
    lc = M.LINE_COMMENT.get(lang)
    if lc:
        out = []
        for ln in text.split("\n"):
            p = ln.find(lc)
            out.append(ln[:p] if p >= 0 else ln)
        text = "\n".join(out)
    return text

def analyze(text, lang):
    toks = list(M.tokenize(text, lang))
    kw = M.KW[lang]
    n_sym = n_kwfunc = n_operand = n_pathnav_sym = 0
    for idx, (kind, t) in enumerate(toks):
        if kind == "SYM":
            n_sym += 1
            if t in PATHNAV:
                n_pathnav_sym += 1
        elif kind in ("STR", "NUM"):
            n_operand += 1
        else:  # WORD
            low = t.lower()
            is_func = (idx+1 < len(toks) and toks[idx+1] == ("SYM", "("))
            if low in kw or t.startswith("$") or is_func:
                n_kwfunc += 1
            else:
                n_operand += 1
    total = n_sym + n_kwfunc + n_operand
    # char level
    s = strip_comments(text, lang)
    nonws = punct = pathnav_ch = 0
    for ch in s:
        if ch.isspace():
            continue
        nonws += 1
        if ch.isalnum() or ch == "_" or "一" <= ch <= "鿿":
            pass
        else:
            punct += 1
            if ch in PATHNAV:
                pathnav_ch += 1
    return dict(total=total, sym=n_sym, kwfunc=n_kwfunc, operand=n_operand,
                pathnav_sym=n_pathnav_sym, nonws=nonws, punct=punct, pathnav_ch=pathnav_ch)

def main():
    agg = {l: dict(total=0, sym=0, kwfunc=0, operand=0, pathnav_sym=0,
                   nonws=0, punct=0, pathnav_ch=0) for l in M.LANGS}
    for lang in M.LANGS:
        for f in glob.glob(os.path.join(M.ROOT, lang, "*", "*." + M.EXT[lang])):
            a = analyze(open(f, encoding="utf-8").read(), lang)
            for k in agg[lang]:
                agg[lang][k] += a[k]

    def sch(a, name):
        t = a["total"]; c = a["nonws"]
        return {
          "A":(a["sym"]+a["kwfunc"])/t,                                   # keywords+punct (token)
          "B":(a["sym"]+a["kwfunc"]-a["pathnav_sym"])/t,                  # A, path-nav = business
          "C":a["sym"]/t,                                                 # punctuation only (token)
          "D":(a["sym"]-a["pathnav_sym"])/t,                              # C, path-nav excluded
          "E":a["punct"]/c,                                               # char-level punct density
          "F":(a["punct"]-a["pathnav_ch"])/c,                             # E, path-nav chars excluded
        }[name]

    schemes = {
      "A":"keywords + punctuation as noise  (token ratio; paper-literal)",
      "B":"A, but path-nav . [ ] counted as business",
      "C":"punctuation-only as noise        (keywords NOT noise; token ratio)",
      "D":"C, but path-nav . [ ] excluded",
      "E":"character-level punctuation density (special chars / non-ws chars)",
      "F":"E, but path-nav chars . [ ] excluded",
    }
    print(f"{'':2} {'logic':52} | " + " ".join(f"{l:>6}" for l in M.LANGS) + " | DCQL rank")
    print("-"*135)
    for s, desc in schemes.items():
        vals = {l: sch(agg[l], s) for l in M.LANGS}
        rank = sorted(M.LANGS, key=lambda l: vals[l]).index("DCQL")+1
        print(f"{s:2} {desc:52} | " + " ".join(f"{vals[l]:6.3f}" for l in M.LANGS) + f" |  {rank}/7")
    print("\ncolumns:", "  ".join(M.LANGS))
    print("DCQL rank = position of DCQL when sorted ascending (1 = least noisy).")

if __name__ == "__main__":
    main()
