"""Section 2 (C claims): the core game data, Ruby/Sapphire vs Emerald.

    uv run python -m audit.core_data

Compares species base data, moves, level-up learnsets, TM/HM compatibility, egg moves,
evolutions, the type chart and the encounter slot rates between pret/pokeruby and
pret/pokeemerald, and prints what differs.
"""

import json
import re

from audit.sources import tree


def main() -> list[str]:
    RUBY, EMER = tree("pokeruby"), tree("pokeemerald")
    out: list[str] = []

    def say(*args):
        out.append(" ".join(str(a) for a in args))


    def read(root, rel):
        return (root / rel).read_text(encoding="utf-8", errors="replace")


    def strip(t):
        t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
        return re.sub(r"//[^\n]*", "", t)


    def blocks(text, prefix):
        out = {}
        for m in re.finditer(r"\[(" + prefix + r"\w+)\]\s*=\s*\{", text):
            depth, i = 1, m.end()
            while depth:
                depth += {"{": 1, "}": -1}.get(text[i], 0)
                i += 1
            out[m.group(1)] = text[m.end(): i - 1]
        return out


    def fields(body):
        return {k: v.strip() for k, v in re.findall(r"\.(\w+)\s*=\s*(\{[^}]*\}|[^,\n]+)", body)}


    def bl(v):
        return [x.strip() for x in v.strip("{} ").split(",") if x.strip()]


    # ---- species
    def species_ruby():
        text = strip(read(RUBY, "src/data/pokemon/base_stats.h"))
        # expand OLD_UNOWN_BASE_STATS macro uses: they're placeholder slots 252-276, skip
        out = {}
        for const, body in blocks(text, "SPECIES_").items():
            f = fields(body)
            if "baseHP" not in f:
                continue
            out[const] = (f["type1"], f["type2"], *(f[k] for k in ("baseHP", "baseAttack", "baseDefense", "baseSpAttack", "baseSpDefense", "baseSpeed")),
                          f.get("ability1"), f.get("ability2"), f.get("catchRate"), f.get("expYield"), f.get("growthRate"), f.get("genderRatio"),
                          f.get("item1"), f.get("item2"), f.get("friendship"), f.get("eggGroup1"), f.get("eggGroup2"))
        return out


    def species_emer():
        text = strip(read(EMER, "src/data/pokemon/species_info.h"))
        out = {}
        for const, body in blocks(text, "SPECIES_").items():
            f = fields(body)
            if "baseHP" not in f:
                continue
            t = bl(f["types"]); a = bl(f["abilities"]); eg = bl(f.get("eggGroups", "{}")) or [None, None]
            items = (f.get("itemCommon"), f.get("itemRare"))
            out[const] = (t[0], t[1], *(f[k] for k in ("baseHP", "baseAttack", "baseDefense", "baseSpAttack", "baseSpDefense", "baseSpeed")),
                          a[0], a[1], f.get("catchRate"), f.get("expYield"), f.get("growthRate"), f.get("genderRatio"),
                          items[0], items[1], f.get("friendship"), eg[0], eg[1])
        return out


    LABELS = ["type1", "type2", "hp", "atk", "def", "spa", "spd", "spe", "ability1", "ability2", "catchRate", "expYield",
              "growthRate", "genderRatio", "item1", "item2", "friendship", "eggGroup1", "eggGroup2"]


    def norm(v):
        return None if v is None else re.sub(r"\s+", "", v)


    r, e = species_ruby(), species_emer()
    say(f"species: ruby {len(r)} emerald {len(e)}")
    diffs = {}
    for k in sorted(set(r) & set(e)):
        for lab, a, b in zip(LABELS, r[k], e[k]):
            if norm(a) != norm(b):
                diffs.setdefault(lab, []).append((k, a, b))
    for lab, rows in diffs.items():
        say(f"  {lab}: {len(rows)} differ, e.g. {rows[:4]}")
    say("  only in ruby:", sorted(set(r) - set(e))[:10], " only in emerald:", sorted(set(e) - set(r))[:10])

    # ---- moves
    def moves(root, rel):
        out = {}
        for const, body in blocks(strip(read(root, rel)), "MOVE_").items():
            f = fields(body)
            out[const] = {k: norm(f.get(k)) for k in ("effect", "power", "type", "accuracy", "pp", "secondaryEffectChance", "target", "priority", "flags")}
        return out


    rm, em = moves(RUBY, "src/data/battle_moves.c"), moves(EMER, "src/data/battle_moves.h")
    say(f"moves: ruby {len(rm)} emerald {len(em)}")
    md = [(k, f, rm[k][f], em[k][f]) for k in sorted(set(rm) & set(em)) for f in rm[k] if rm[k][f] != em[k][f]]
    byf = {}
    for k, f, a, b in md:
        byf.setdefault(f, []).append((k, a, b))
    for f, rows in byf.items():
        say(f"  {f}: {len(rows)} differ: {rows[:12]}")


    # ---- level-up learnsets
    def learnsets(root, ptr_symbol_re):
        text = strip(read(root, "src/data/pokemon/level_up_learnsets.h"))
        sets = {sym: re.findall(r"LEVEL_UP_MOVE\(\s*(\d+),\s*(MOVE_\w+)\)", body)
                for sym, body in re.findall(r"const u16 (\w+LevelUpLearnset)\[\]\s*=\s*\{(.*?)\};", text, flags=re.S)}
        ptrs = strip(read(root, "src/data/pokemon/level_up_learnset_pointers.h"))
        pairs = re.findall(r"\[(SPECIES_\w+)\]\s*=\s*(\w+LevelUpLearnset)", ptrs)
        if not pairs:  # ruby: positional array
            syms = re.findall(r"(g\w+LevelUpLearnset)", ptrs)
            return {i: sets.get(s) for i, s in enumerate(syms)}, "positional"
        return {c: sets.get(s) for c, s in pairs}, "keyed"


    rl, rmode = learnsets(RUBY, None)
    el, emode = learnsets(EMER, None)
    say(f"learnsets: ruby {len(rl)} ({rmode}) emerald {len(el)} ({emode})")
    if rmode == "positional":
        # map index -> species const using species.h enum order
        sp = re.findall(r"#define (SPECIES_\w+) (\d+)", read(RUBY, "include/constants/species.h"))
        idx = {int(v): k for k, v in sp}
        rl = {idx.get(i, i): v for i, v in rl.items()}
    ld = [k for k in sorted(set(rl) & set(el), key=str) if rl[k] != el[k]]
    say(f"  differ: {len(ld)}")
    for k in ld[:20]:
        a, b = rl[k], el[k]
        say(f"   {k}: ruby-only {[x for x in a if x not in b]} emerald-only {[x for x in b if x not in a]}" + ("  (same moves, order differs)" if sorted(a) == sorted(b) else ""))


    # ---- TM/HM compatibility
    def tmhm_ruby():
        text = strip(read(RUBY, "src/data/pokemon/tmhm_learnsets.h"))
        out = {}
        for c, body in re.findall(r"\[(SPECIES_\w+)\]\s*=\s*TMHM_LEARNSET\((.*?)\)\s*,?\s*(?=\[SPECIES_|\};)", text, flags=re.S):
            out[c] = {re.sub(r"^(TM|HM)\d+_", "", x) for x in re.findall(r"TMHM\((\w+)\)", body)}
        return out


    def tmhm_emer():
        text = strip(read(EMER, "src/data/pokemon/tmhm_learnsets.h"))
        out = {}
        for c, body in blocks(text, "SPECIES_").items():
            out[c] = set(re.findall(r"\.(\w+)\s*=\s*TRUE", body))
        return out


    rt, et = tmhm_ruby(), tmhm_emer()
    td = [(k, sorted(rt[k] - et[k]), sorted(et[k] - rt[k])) for k in sorted(set(rt) & set(et)) if rt[k] != et[k]]
    say(f"tm/hm compat: ruby {len(rt)} emerald {len(et)} differ {len(td)}: {td[:10]}")


    # ---- egg moves
    def eggs(root):
        text = strip(read(root, "src/data/pokemon/egg_moves.h"))
        return {s: [m.strip() for m in body.split(",") if m.strip()] for s, body in re.findall(r"egg_moves\((\w+),(.*?)\)", text, flags=re.S)}


    re_, ee = eggs(RUBY), eggs(EMER)
    eg = [(k, sorted(set(re_[k]) ^ set(ee[k]))) for k in set(re_) & set(ee) if set(re_[k]) != set(ee[k])]
    say(f"egg moves: ruby {len(re_)} emerald {len(ee)} differ {len(eg)}: {eg[:10]}; only ruby {sorted(set(re_)-set(ee))} only emerald {sorted(set(ee)-set(re_))}")


    # ---- evolutions
    def evos(root):
        text = strip(read(root, "src/data/pokemon/evolution.h"))
        return {c: re.findall(r"\{\s*(EVO_\w+),\s*(\w+),\s*(SPECIES_\w+)\s*\}", body) for c, body in blocks(text, "SPECIES_").items()}


    rv, ev = evos(RUBY), evos(EMER)
    vd = [(k, rv.get(k), ev.get(k)) for k in sorted(set(rv) | set(ev)) if rv.get(k) != ev.get(k)]
    say(f"evolutions: ruby {len(rv)} emerald {len(ev)} differ {len(vd)}: {vd[:10]}")

    # ---- type chart
    rtc = re.findall(r"\.byte\s+(TYPE_\w+),\s*(TYPE_\w+),\s*(\d+)", read(RUBY, "data/type_effectiveness.inc"))
    body = re.search(r"gTypeEffectiveness\[\d*\]\s*=\s*\{(.*?)\};", strip(read(EMER, "src/battle_main.c")), flags=re.S).group(1)
    tok = [t.strip() for t in body.split(",") if t.strip()]
    mul = {"TYPE_MUL_NO_EFFECT": "0", "TYPE_MUL_NOT_EFFECTIVE": "5", "TYPE_MUL_SUPER_EFFECTIVE": "20", "TYPE_MUL_NORMAL": "10"}
    etc = [(a, d, mul.get(m, m)) for a, d, m in zip(tok[0::3], tok[1::3], tok[2::3])]
    rtc = [(a, d, str(int(m))) for a, d, m in rtc]
    say(f"type chart: ruby {len(rtc)} entries, emerald {len(etc)} entries, identical in order: {[(a,d,str(int(m)) if m.isdigit() else m) for a,d,m in etc] == rtc}")
    say("  set diff:", sorted(set(rtc) ^ {(a, d, str(int(m)) if m.isdigit() else m) for a, d, m in etc}))

    # ---- encounter slot rates
    def rates(root):
        d = json.loads(read(root, "src/data/wild_encounters.json"))
        g = next(x for x in d["wild_encounter_groups"] if x["label"] == "gWildMonHeaders")
        return {f["type"]: (f["encounter_rates"], f.get("groups")) for f in g["fields"]}


    say("slot rates equal:", rates(RUBY) == rates(EMER))
    for k, v in rates(RUBY).items():
        say("  ruby", k, v)
    return out


if __name__ == "__main__":
    print("\n".join(main()))
