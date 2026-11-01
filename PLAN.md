# Project 2 Plan: Lockesmith

A deep research agent that tells a Pokémon Emerald player which Pokémon to catch next, and where, to beat the rest of the game. It works for normal runs, Nuzlocke and custom-ruleset runs, and randomized runs (via an uploaded randomizer spoiler log).

Course: IEOR E4570 Agentic AI, Project 2 (Deep Research path). Solo. Due **Wed Nov 11, 11:59pm ET**.

---

## 0. Instructions for Claude Code

- Read this whole file before writing code, then the assignment page in `docs/assignment.html`.
- The course reference starter (`wikipedia-deep-research`) is **not available yet**. Build without it. If it later appears in `reference/wikipedia-deep-research/`, read it and tell me where this plan's structure differs before changing anything.
- Until then, keep the agent framework behind a thin layer (`agent/runtime.py`: one function to run an agent with tools and return output + tool calls) so swapping frameworks later only touches that file.
- The `/chat` contract in section 8 is fixed by Project 1 and the assignment text, so build to it now.
- Items marked **OPEN** are decisions I haven't made. Ask me before resolving them.
- Every phase in section 13 has acceptance checks. Don't mark a phase done until they pass.
- Keep scope tight. Out of scope: other games, ROM hacks, the Battle Frontier and other postgame content, team-building for competitive play.

---

## 1. Product

**Who it's for:** someone partway through Emerald (often a Nuzlocke or randomizer challenge) who wants to know what to catch next to get through the remaining gyms, Elite Four and Champion.

**What it does:** given the run state (starter, badges, party with levels, current location, ruleset, optional randomizer log), it:
1. figures out which major battles are left and what threatens the current party in each,
2. finds what's actually catchable before each battle (respecting HM gates and challenge rules),
3. checks what candidates and current party members can learn in time (level-up, TMs obtainable by then, tutors),
4. recommends specific catches with where, when and why, each claim cited to the data.

**Why tools matter here:** base models know Pokémon broadly but get specifics wrong: Emerald vs Ruby/Sapphire differences (Juan is the 8th gym leader, Wallace is Champion, boss teams and levels differ), Gen 3 mechanics (physical/special is decided by move type, so Crunch is special; no Fairy type, so Gardevoir is pure Psychic), exact encounter tables, and anything in a randomized game. The README's baseline comparison should show these failures.

---

## 2. Grading map (what each requirement maps to)

| Requirement | Where it's covered |
|---|---|
| Data the model doesn't know deeply; tools to reach it | Offline-built Gen 3 DuckDB, decomp trainer data, randomizer log, guide corpus (§4) |
| Combine evidence into a supported claim | Writer synthesizes researcher findings into cited recommendations (§6) |
| States when data can't answer | Scope check in Clarifier + explicit "not in data" handling (§6, §9) |
| Show its work: `/chat` shape from Project 1, sub-agent tool calls in `tool_calls` with an `agent` field | §8 |
| Front end saying what/who/how | §10 |
| Deployed to Cloud Run | §12 |
| ≥3 agent shapes with different jobs | Clarifier, Lead, 3 Researchers, Writer (+ deterministic Verifier) |
| Lead fans out to several Researchers in one turn, parallel, fresh contexts | `dispatch_researchers` tool (§6) |
| Lead goes back for more on gaps, up to a turn cap | Gap loop with `MAX_RESEARCH_ROUNDS` (§6) |
| Vague questions require clarification | Clarifier gatekeeper (§6) |
| Output accurately cited | Evidence ledger + citation check (§7) |
| README: project, user, data provenance, 3 sample queries with expected answer + source, no-tools baseline answers | §11 |
| `submission.json` with `deploy_url`, `authors`, `path: "research"` | §12 |
| Peer rubric: usefulness, ambition, originality | Verifier, Nuzlocke/randomizer support, run-state UI, trace panel |

---

## 3. Architecture

```
User message + run state
        │
        ▼
  ┌───────────┐  missing badges/party/starter, out of scope, or vague?
  │ Clarifier │──────────────► ask a targeted question / explain scope
  └─────┬─────┘
        ▼
  ┌───────────┐  dispatch_researchers([...]) in ONE call → asyncio.gather
  │   Lead    │─────────────────────────────────────────────┐
  └─────┬─────┘                                             ▼
        │        ┌──────────────────┬──────────────────┬──────────────────┐
        │        │ Battle Researcher│ Catch Researcher │ Moves Researcher │  (fresh contexts, parallel)
        │        └──────────────────┴──────────────────┴──────────────────┘
        │◄──────────── findings + evidence ids ─────────────────┘
        ▼
  Lead drafts candidate recommendations (structured JSON)
        ▼
  ┌───────────┐  deterministic, no LLM
  │ Verifier  │── violations ──► Lead re-dispatches (gap loop, ≤ MAX_RESEARCH_ROUNDS)
  └─────┬─────┘
        ▼ verified candidates + evidence
  ┌───────────┐
  │  Writer   │── cited answer + structured plan + coverage chart spec
  └─────┬─────┘
        ▼
  Citation check (deterministic) → /chat response
```

Caps (tune later): `MAX_RESEARCH_ROUNDS = 3`, researcher `max_turns = 8`, whole request budget ≈ 120 s (graders wait up to 5 min; aim well under).

---

## 4. Data layer (offline build)

All of this runs in `build/` and produces `data/emerald.duckdb` plus a few checked-in files. Record source commit SHAs in `data/sources.lock.json`.

### 4.1 Sources

| Source | What we use | Kind |
|---|---|---|
| PokeAPI CSVs (`github.com/PokeAPI/pokeapi`, `data/v2/csv`) | Species, types, stats, moves, Emerald encounters (version_id 9, all methods incl. rods/surf/Rock Smash/statics/gifts/Feebas tiles) with slot rarities, Emerald learnsets (version_group 6: level-up, machine, tutor, egg), TM/HM list, evolutions | structured |
| pret/pokeemerald decompilation | `src/data/trainer_parties.h` + `src/data/trainers.h` (854 parties: all gym leaders incl. rematch variants, E4, Wallace, rival per starter per location, Wally, Maxie/Archie/admins), `include/constants/opponents.h` (trainer IDs) | structured (C structs) |
| Universal Pokémon Randomizer ZX spoiler log (user upload) | Randomized wild sets, trainer teams, TM moves, base stats/types, evolutions, starters, statics | semi-structured text |
| Emerald guide corpus (**OPEN**: Bulbapedia via MediaWiki API, Emerald walkthrough + TM/item location pages only, CC BY-NC-SA attribution in README) | Facts tables don't hold well: how to obtain Feebas, where each TM is found or given, story context | unstructured |

Already verified on Nov 1: PokeAPI has all 34 Hoenn routes and 81 Emerald locations (1,647 encounter rows), 58 TM/HMs, ~19k Emerald learnset rows. pokeemerald trainer data parses cleanly (e.g. `sParty_Juan1`: Luvdisc 41, Whiscash 41, Sealeo 43, Crawdaunt 43, Kingdra 46). UPR log trainer indices match decomp constants (`TRAINER_ROXANNE_1 = 265` ↔ `#265 (ROXANNE)`).

### 4.2 Gen 3 correction layer (important)

PokeAPI stores **modern** data. Apply its history tables to get Emerald-accurate values:
- Types: `pokemon_types_past.csv` (no Fairy; Gardevoir = Psychic, Azumarill = Water).
- Base stats: `pokemon_stats_past.csv`.
- Abilities: `pokemon_abilities_past.csv`; no hidden abilities in Gen 3.
- Moves: `move_changelog.csv`. Revert power/accuracy/PP/type changes made after the Emerald version group.
- Damage class: derive from **move type**, not PokeAPI's `damage_class_id`. Physical: Normal, Fighting, Flying, Poison, Ground, Rock, Bug, Ghost, Steel. Special: Fire, Water, Grass, Electric, Psychic, Ice, Dragon, Dark. Status moves stay status.
- Type chart: `type_efficacy.csv` adjusted with `type_efficacy_past.csv` for Gen 3 (e.g. Steel resists Ghost and Dark; no Fairy row/column).
- Restrict to National Dex #1–386 and moves introduced in Gen 1–3.

Write these as tests (`tests/test_gen3_facts.py`) before building agents. Minimum facts: Crunch is special; Gardevoir is pure Psychic; Steel resists Dark; Route 119 has Feebas via tile fishing; Juan_1's team is exactly the five above.

### 4.3 Trainer teams

- Parse every party from `trainer_parties.h`. Parties use either custom movesets (bosses, mostly) or default moves. For default moves, compute the game's rule: the last four level-up moves learned at or below that level (from Emerald learnsets).
- Table `trainer_mons(trainer_const, trainer_id, slot, species, level, held_item, moves[], iv)`.

### 4.4 Progression file (hand-built, reviewed by me)

The data doesn't say *when* each fight happens. Build `data/progression.yaml`: an ordered list of ~40 key battles (all 8 gyms, E4, Champion, every rival/Wally/Maxie/Archie fight), each with:
```yaml
- id: gym7_tate_liza
  order: 22
  label: "Mossdeep Gym: Tate & Liza"
  badges_before: 6
  trainer_consts: [TRAINER_TATE_AND_LIZA_1]
  battle_format: double          # single | double | multi
  starter_variants: null         # or {treecko: TRAINER_..., torchic: ..., mudkip: ...}
  location: mossdeep-city
  hm_gates_open: [cut, flash, rock-smash, strength, surf, fly]
  areas_reachable: [<PokeAPI location slugs reachable by this point>]
  source: "guide:Walkthrough:Pokemon_Emerald/Part_X"
```
Draft it from the guide corpus and the decomp, then **stop and ask me to review it** before agents depend on it. Note that some double/multi battles (e.g. the Space Center fight) are set up by map scripts, not the trainer struct, so `battle_format` must come from this file.

### 4.5 Randomizer log parser (`agent/randomizer_log.py`)

- Sections: `--Wild Pokemon--`, `--Trainers Pokemon--`, `--TM Moves--`, `--Pokemon Base Stats & Types--`, `--Randomized Evolutions--`, starters, `--Static Pokemon--`. Sections only appear for what was randomized, so fall back to vanilla tables for anything missing.
- Wild sets look like `Set #N - ROUTE 104 Grass/Cave (rate=20)` followed by `Species Lv4-5   HP .. ATK ..` lines. Map UPR map names to PokeAPI location slugs with a mapping table.
- Fishing is one 10-slot set. Split by slot: Old Rod 0–1, Good Rod 2–4, Super Rod 5–9 (**verify** by parsing a log with wild Pokémon left unchanged and comparing to PokeAPI).
- Trainers: `#265 (ROXANNE) - Geodude Lv12, ...` (compact) or one line per Pokémon with moves/ability if the user enabled moveset logging. Join on trainer index ↔ decomp constant value.
- Store parsed data as per-session overlay tables that take precedence over vanilla.
- I'll generate a test log from my own ROM dump and put it in `tests/fixtures/` (gitignored if large). Never commit ROMs.

### 4.6 Entity matching

Fuzzy-match user-typed names (species, moves, locations, trainers) to canonical IDs with RapidFuzz before any lookup ("mr mime", "farfetchd", "rt 119", "tate and liza"). This is the named-entity-matching pattern from the Text2SQL lecture.

---

## 5. Tools

Every tool returns rows plus a `source_id` per row (see §7). Tools read run state from the run context; the model doesn't pass state it already has (tool-calling lecture: offload known arguments).

| Tool | Used by | Returns |
|---|---|---|
| `get_remaining_battles()` | Battle | Ordered upcoming battles from progression + current badges/starter |
| `get_trainer_team(battle_id)` | Battle | Team with levels, moves, items, format (randomizer overlay aware) |
| `threat_matrix(battle_id)` | Battle | Deterministic Gen 3 matchup grid: party vs each opposing mon, plus uncovered threats |
| `get_catchable(before_battle_id, methods?)` | Catch | Species catchable in areas reachable before that battle, with levels and encounter odds; applies Nuzlocke used-route and dupes rules |
| `encounter_odds(location, method)` | Catch | Slot-rarity-based probabilities for that area (first-encounter odds for Nuzlockes) |
| `species_info(name)` | All | Gen 3 types, stats, abilities, evolution method/level |
| `get_learnset(species, max_level)` | Moves | Level-up moves by that level, TM/HM/tutor compatibility |
| `get_tm_availability(before_battle_id)` | Moves | TMs obtainable by that point and where (needs the **OPEN** TM-location source) |
| `search_guide(query)` | All | Top guide passages with page/section ids |
| `query_db(sql)` | Catch, Moves (fallback) | Read-only SQL over `emerald.duckdb` with schema map + enum values in the tool description |

`query_db` is an escape hatch, not the main path. Use a read-only DuckDB connection.

---

## 6. Agents

Framework: default to the OpenAI Agents SDK through LiteLLM (covered in the agent-frameworks lecture), wrapped by `agent/runtime.py`. Revisit if the reference starter turns out to use something else. Models configured by env vars via LiteLLM; a cheap/fast model for researchers, a stronger one for Lead and Writer. **OPEN**: Gemini on Vertex vs Anthropic API key.

**Clarifier (gatekeeper).** Checks the request against the run state. Asks one targeted question when it lacks what the answer depends on (badges or last gym beaten, party species + levels, starter for rival teams, ruleset if the user mentions a challenge). Declines out-of-scope requests clearly (other games, ROM hacks, postgame, competitive sets), saying what it does cover. Vague example: "what should I catch?" with no state → asks for badges and party. The front-end form should make clarification rare for normal use.

**Lead.** Plans sub-questions and calls `dispatch_researchers(tasks: list[ResearchTask])` once per round. That tool runs each researcher with `Runner.run` (or the starter's equivalent) in a fresh context via `asyncio.gather`, and returns their findings. After each round the Lead checks a coverage checklist (every remaining boss has a planned answer; every candidate has an obtainability and moves finding) and drafts candidate recommendations as structured JSON. Then the Verifier runs. Gaps or violations → another round, up to `MAX_RESEARCH_ROUNDS`. If the cap is hit, the answer says what's still unresolved.

**Researchers** (3 shapes, each with its own tool subset and instructions):
- *Battle Researcher*: remaining battles, opposing teams, threats to the current party, what types/roles are needed per battle.
- *Catch Researcher*: candidates obtainable in time, where, at what level, with what odds; challenge-rule filtering.
- *Moves Researcher*: what candidates and party members learn by each battle (level-up, obtainable TMs, tutors), evolution timing.

Each returns a structured finding: claims, each with the `source_id`s backing it.

**Verifier (deterministic code, no LLM).** Same idea as the plan evaluator I built for Lou. Checks each candidate recommendation and returns violation codes:
- `NOT_OBTAINABLE_BEFORE`: species not catchable in areas reachable before the target battle
- `EVOLUTION_NOT_REACHABLE`: relies on an evolution not achievable in time (level, stone, trade)
- `MOVE_NOT_LEARNABLE`: move not learnable by then (level or TM not yet obtainable)
- `GEN3_SPLIT_MISMATCH` (warning): e.g. recommending a special-type move as a physical attacker's main attack
- `GEN3_ANACHRONISM`: Fairy type, post-Gen-3 moves/abilities/species
- `NUZLOCKE_ROUTE_USED`, `NUZLOCKE_DUPE`, `RULESET_TYPE_VIOLATION`, `OVER_LEVEL_CAP`
- `UNCITED_CLAIM`, `CITATION_NOT_IN_EVIDENCE`

Violations go back to the Lead as structured feedback. Unit-test every code.

**Writer.** Turns verified candidates + evidence into: (a) a readable answer: top picks with where/when/why, per-battle notes, and what the data can't answer; (b) a structured plan for the UI; (c) a Vega-Lite spec for a type-coverage heatmap (party before vs after). Every factual sentence carries citation markers `[n]`.

---

## 7. Citations and the evidence ledger

- Every tool row gets a `source_id`, e.g. `pokeapi:encounters#4821`, `decomp:trainer_parties.h#sParty_Juan1`, `log:wild#Set42`, `guide:Route_119#Feebas`, `rules:gen3_type_chart`.
- The run context (`RunContextWrapper` or equivalent) holds an evidence ledger of everything any tool returned this request.
- Writer output cites ledger ids. A final deterministic check confirms every cited id exists in the ledger and every recommendation has at least one citation; failures get one Writer retry, then are flagged in the response.
- The response includes a `citations` list mapping `[n]` to a human-readable source (file/table/row or guide page link).

---

## 8. API contract

Keep Project 1's shape (from the tool-calling lecture): request `{message, session_id}`, response `{response, session_id, tool_calls}`.

- `POST /chat` request: `{message, session_id?, run_state?}`.
- Response:
```json
{
  "response": "markdown answer with [n] markers",
  "session_id": "...",
  "tool_calls": [
    {"agent": "lead", "name": "dispatch_researchers", "args": {...}, "result": "..."},
    {"agent": "catch_researcher", "name": "get_catchable", "args": {...}, "result": "..."},
    {"agent": "verifier", "name": "verify", "args": {...}, "result": "..."}
  ],
  "citations": [{"n": 1, "source_id": "...", "label": "..."}],
  "plan": {...},
  "chart": {...vega-lite...}
}
```
- Capture sub-agent tool calls with run hooks (`RunHooks` / callbacks) tagged by agent name.
- Also `GET /history`, `POST /clear` (chatbot lecture convention), `POST /run_state`, `POST /upload_log`.
- Truncate large tool results in `tool_calls` (e.g. first N rows + count) so responses stay readable.

---

## 9. Run state and rulesets

Pydantic models in `agent/state.py`:
- `RunState`: `starter`, `badges` (0–8), `party` (≤6: species, level, optional moves), `current_location` (optional; default from badges), `ruleset`, `randomizer_log_id` (optional).
- `Ruleset`: `nuzlocke` (bool), `used_routes` (list), `dupes_clause` (bool), `level_caps` (bool: cap = next boss's highest level), `monotype` (type or null), `banned_species` (list).

Things the agent must say it can't answer: anything outside Emerald, ROM hacks, postgame/Battle Frontier, trainer movesets when the randomizer log lacks them, and exact damage rolls (we don't model the damage formula; matchups are type/level-based).

---

## 10. Front end

Served by FastAPI from `static/`. Must say what it explores, who it's for and how to use it, at the top.
- Run-state panel: starter, badges, party builder (species autocomplete + level), ruleset toggles, used-routes picker, optional randomizer log upload.
- Example query buttons (vanilla, Nuzlocke, randomizer, out-of-scope).
- Answer view: recommendation cards (where/when/why with citations), per-battle plan, coverage heatmap (render the Vega-Lite spec with vega-embed).
- Trace panel: tool calls grouped by agent, with the parallel researchers shown side by side per round, plus Verifier violations and how the Lead responded.
- Loading state: requests take a while, so show progress text.

Must look clearly different from the starter's front end.

---

## 11. README, baseline and observability

README sections:
1. What it is, who it's for, how to use it.
2. Architecture diagram and agent roles.
3. Data: each source, where it came from (with commit SHAs), license/attribution, how to rebuild (`uv run python build/build_db.py`).
4. Three sample queries, each with the expected answer and the file/table/endpoint it comes from, next to the no-tools baseline answer and the agent's answer. Candidates:
   - Vanilla mid-game: a specific party heading into Tate & Liza (double battle, Emerald-specific team).
   - Nuzlocke: used routes + level caps + dupes clause, heading into Juan or the E4.
   - Randomizer: uploaded log, asking what to catch before a randomized gym.
   Fill expected answers from DuckDB queries, not from memory.
5. A short "what it can't answer" section with an example.
6. Tracing screenshots and per-query cost from LangFuse (free cloud tier).

`scripts/baseline.py`: same model as Lead/Writer, no tools, no system prompt; saves outputs to `docs/baseline/`. `scripts/run_samples.py`: runs the agent on the same queries and saves full traces.

---

## 12. Deployment and submission

- Cloud Run with continuous deploy from GitHub. Deploy a hello-world `app.py` in Phase 0 to remove deploy risk early.
- Ship `data/emerald.duckdb` in the repo if it stays under 100 MB (expected: a few MB); otherwise load from GCS at startup.
- Raise the Cloud Run request timeout (e.g. 600 s) and keep request budgets well below it.
- Root of repo: `app.py`, `pyproject.toml`, `uv.lock`, `README.md`, `submission.json`:
```json
{ "deploy_url": "https://<service>.run.app", "authors": ["kc3936"], "path": "research" }
```
- Add the course GitHub accounts as collaborators if the repo is private (list is in `docs/assignment.html`).
- Keep the service running until grades are released.

---

## 13. Phases and timeline

**Phase 0: setup and spikes (Sun Nov 1 – Mon Nov 2)**
- Scaffold with uv; prepare a hello-world `app.py` and Dockerfile/Cloud Run config, and give me the exact steps to connect continuous deploy (I'll do the GCP console part).
- Spike: TM/item location source (**OPEN**: decomp map data vs guide pages vs hand-curated CSV of the 50 TMs). Recommend the fastest accurate option.
- Spike: guide corpus fetch via MediaWiki API for Emerald pages only, cached to `data/guide/`.
- Spike: randomizer log join using my fixture log.
- ✅ Acceptance: hello-world runs locally and deploy steps are written up; a recommendation on each OPEN item.

**Phase 1: data layer (Mon Nov 2 – Wed Nov 4)**
- `build/` scripts → `data/emerald.duckdb`; Gen 3 corrections; trainer parsing incl. default moves; entity matching; draft `progression.yaml` (I review); randomizer log parser + overlays.
- ✅ Acceptance: `tests/test_gen3_facts.py` and `tests/test_log_parser.py` pass; progression reviewed by me.

**Phase 2: agents (Wed Nov 4 – Fri Nov 6)** (Thu Nov 5 evening is a guest lecture)
- Tools, three researchers, Lead with `dispatch_researchers`, Clarifier, Writer, `/chat` contract with agent-tagged `tool_calls`.
- ✅ Acceptance: a vanilla query runs end to end locally with parallel researchers visible in `tool_calls`; a vague query triggers clarification; an out-of-scope query is declined clearly.

**Phase 3: verification and challenge modes (Fri Nov 6 – Sun Nov 8)**
- Verifier + gap loop; evidence ledger + citation check; Nuzlocke rules; randomizer flow end to end.
- ✅ Acceptance: `tests/test_verifier.py` covers every violation code; a seeded bad candidate gets rejected and replaced in the gap loop; citations all resolve.

**Phase 4: front end, README, deploy (Sun Nov 8 – Tue Nov 10)**
- Front end; LangFuse tracing; baseline + sample runs; README; final deploy.
- ✅ Acceptance: all three sample queries work on the deployed URL in under ~2 minutes each; README complete; `submission.json` valid.

**Wed Nov 11:** buffer, collaborators, submit the repo URL on Courseworks.

---

## 14. Repo layout

```
app.py                      # FastAPI entry (required at root)
pyproject.toml  uv.lock  README.md  submission.json  PLAN.md
reference/                  # course starter, if/when it's released (read-only reference)
docs/assignment.html  docs/baseline/
build/                      # offline build: fetch_sources.py, build_db.py, gen3_corrections.py,
                            # parse_decomp_trainers.py, build_guide_corpus.py
data/                       # emerald.duckdb, progression.yaml, guide/, sources.lock.json
agent/
  runtime.py                # thin wrapper around the agent framework
  state.py  evidence.py  randomizer_log.py  entities.py
  tools/  battles.py  encounters.py  moves.py  guide.py  sql.py
  clarifier.py  lead.py  researchers.py  verifier.py  writer.py
static/                     # index.html, app.js, style.css
tests/                      # test_gen3_facts.py, test_verifier.py, test_log_parser.py, fixtures/
scripts/                    # baseline.py, run_samples.py
```

---

## 15. Risks

- **Progression file accuracy** is the biggest manual risk. Keep it reviewed and cited.
- **PokeAPI's modern defaults** silently leaking into answers. Mitigated by §4.2 tests and the `GEN3_ANACHRONISM` check.
- **Latency** with three parallel researchers and up to three rounds. Cap turns, use a fast researcher model, truncate tool results.
- **Fishing slot split and map-name mapping** in the log parser. Verify against an unrandomized-wild log.
- **Guide source licensing**: attribute in README; keep the corpus limited to what's needed.
