# Decisions log

PLAN.md marks three items **OPEN**. For each one: the options, what the Phase 0 spike found, the recommendation, and what is now built on it. Each pick is provisional until you sign off, and the last line of each says what switching would cost. D4–D6 record places where the build departs from PLAN.md.

PLAN.md §0 says to ask before resolving OPEN items. Your Nov 1 instruction was to write the recommendation, pick it and keep going, so that's what I did. Nothing here is hard to reverse.

---

## D1. TM/item location source (PLAN §5, §13) — **decomp map data**

| Option | Finding |
|---|---|
| **pokeemerald map data** | Every TM/HM source is machine-readable: item balls (`object_events` → `item_ball_scripts.inc`), hidden items (`bg_events`), NPC gifts (`giveitem` in map scripts), marts (`pokemart` lists) and Game Corner prizes. Extraction found **all 58 TM/HMs (65 source rows)** with no hand edits, and each row is tied to a map → region map section → PokeAPI location. Gym TMs are tagged with their leader automatically. |
| Bulbapedia TM pages | Per-game location text sits inside all-games wikitext tables. Parsing them is real work, the result is prose rather than map IDs, and it adds licensing surface. |
| Hand-curated CSV | Fastest to type, but it would come from memory with no provenance, and memory is exactly what this project is trying not to trust. |

**Recommendation and pick: decomp.** It's the fastest accurate option, and it's already built: `build/tm_locations.py` creates the `tm_locations` table, plus `move_tutors` for the 10 Hoenn tutors (each one-time in Emerald; the other 20 are at the postgame Battle Frontier).

**Still manual (Phase 2, for review alongside progression):** some sources sit behind something map-level reachability can't see:
- HMs given after a story beat. These are already covered by `hm_gates_open` in progression.yaml.
- Items inside a map that need an HM to reach: TM02 Dragon Claw (Meteor Falls back room, Waterfall), TM26 Earthquake (Seafloor Cavern), TM07 Hail (Shoal Cave ice room), TM11 Sunny Day (Scorched Slab, Surf), TM18 Rain Dance (Abandoned Ship hidden floor, Dive).
- Conditional gifts: TM21/TM27 in Pacifidlog depend on friendship; TM19 Giga Drain needs a Grass Pokémon; TM12 Taunt is a Trick House reward; TM49 Snatch is on the S.S. Tidal (postgame).

Done in the second cross-check (D7): `tm_locations.requires` holds 17 hand-checked gates, and the extractor now also finds gifts given by shared scripts that a map refers to from `map.json` (TM43 on Route 111).

*Switching cost:* low. `get_tm_availability` reads one table.

## D2. Guide corpus (PLAN §4.1) — **Bulbapedia via MediaWiki API, Emerald walkthrough only**

Spike result: the API serves all 21 walkthrough parts. `build/build_guide_corpus.py` caches raw wikitext with revision IDs in `data/guide/pages/` and writes **400 section chunks (~165K characters)** to `data/guide/chunks.jsonl`, each with an id like `guide:Walkthrough:Pokemon_Emerald/Part_10#Finding_Feebas` and a deep link.

Things to know:
- Bulbapedia's edge returns **403 to httpx** and 200 to curl and Python's urllib, so the fetcher uses urllib. Requests are 1/s with a project User-Agent.
- The walkthrough's `{{Party}}` templates turned out to be the best evidence for the progression file: each one names a battle in story order, and matching its species and levels to decomp parties found the trainer constant for every battle (D5).
- I didn't fetch TM pages (D1 makes them unnecessary). Feebas, Sealed Chamber and similar topics are all in the walkthrough.
- License: CC BY-NC-SA 2.5. The README needs an attribution line naming Bulbapedia, the page titles and revision IDs (stored per page).

**Recommendation and pick: walkthrough only**, as PLAN suggested. For `search_guide` in Phase 2 I'd use plain BM25 in Python over the 400 chunks. DuckDB's FTS extension would need downloading or bundling on Cloud Run, which isn't worth it at this size.

*Switching cost:* adding pages is one list entry in `TITLES`.

## D3. Model provider (PLAN §6) — **Vertex AI (Gemini), model IDs in env vars**

| | Gemini on Vertex | Anthropic API key |
|---|---|---|
| Auth on Cloud Run | The service account gets *Vertex AI User*. No secret. | Key in Secret Manager, exposed as an env var |
| Billing | Same GCP project (and course credits, if any) | Separate account and card |
| Tool calling via LiteLLM + Agents SDK | Works. Gemini's function-calling schema is stricter about JSON Schema features, so tool schemas may need flattening. | Works. Claude models are strong at multi-step tool use and at following citation formats. |
| Latency/cost for 3 parallel researchers | Flash-tier is fast and cheap | Haiku-tier is fast; Sonnet/Opus-tier for Lead/Writer costs more |

**Recommendation and pick: Vertex AI with Gemini.** A Flash-tier model for researchers and a Pro-tier model for Lead/Writer, all named only in `LOCKESMITH_*_MODEL` env vars. The deciding reasons are operational: no secret to manage, one bill, and it's the platform you're already deploying on.

Two caveats I couldn't settle without credentials:
1. Run a 15-minute spike at the start of Phase 2: one agent, one tool, through LiteLLM on Vertex. If the Agents SDK's strict tool schemas trip Gemini, the fallback is **Claude on Vertex** (Model Garden). That keeps the same auth and billing, and Claude is the stronger tool user. Model Garden access can need a quota request, so enabling it early costs nothing.
2. If the course gives you an Anthropic key or credits, the Anthropic route is equally good and is a config change.

*Checked 2026-11-01 with local ADC on project `lockesmith`:* Gemini answers on location **`global`** only. `gemini-3.5-flash` and `gemini-3.8-flash` respond; `gemini-2.5-flash` is in the model catalog but returns 404, and the regional `us-east4` endpoint returns 404 for every model tried. So `VERTEXAI_LOCATION=global`, and the Phase 2 spike picks between the current 3.x Flash models and `gemini-3.1-pro-preview` for the Lead.

*Switching cost:* env vars only, since `agent/runtime.py` isolates the framework.

---

## D4. Randomizer log spike — **parser built to PLAN §4.5, real-log checks pending**

There's no fixture in `tests/fixtures/` yet, so `agent/randomizer_log.py` is written from PLAN.md's format description. Its 5 fixture tests skip until a log appears. 9 format tests run against a hand-written log built from PLAN.md's examples.

What was verified without a log:
- **Fishing split**: the decomp's `wild_encounters.json` states the rod groups explicitly (Old 0–1, Good 2–4, Super 5–9). This confirms the ROM side of PLAN's "verify". The log side (that UPR prints the 10 slots in ROM order) still needs an unrandomized-wild log. `test_fixture_unrandomized_wild_matches_vanilla` does that check automatically.
- **Set-to-map alignment**: UPR names sets by region map section, and several sets share a name (every Granite Cave floor is "GRANITE CAVE"; both underwater areas are "UNDERWATER"). The build stores the ROM's wild-header order (`wild_headers`, 209 sets), so the parser pins set N to an exact map and checks the name and method agree. A mismatch becomes a warning and falls back to a name lookup.
- **Trainer join**: trainer ids come straight from `opponents.h` (`TRAINER_ROXANNE_1 = 265`).

Things a real log has to confirm: name casing; `Lv4-5` vs `Lvs 4-5`; whether the trainer label is `(ROXANNE)` or `(LEADER ROXANNE)` (the parser only joins on the number); the moveset-logging line format; and the section names for starters and statics. Ideally drop in two logs: one with wild Pokémon unchanged, one with wild Pokémon and trainers randomized and moveset logging on. One gap: if a log randomizes **learnsets** (`--Pokemon Movesets--`), the parser doesn't read it yet and records it in `unparsed_sections`, so the agent can say it can't answer.

## D5. progression.yaml schema changes (PLAN §4.4)

The draft keeps PLAN's fields and changes or adds these. All of them are needed for correctness:
- **`starter_variants` is keyed by starter, then rival** (`{torchic: {may: ..., brendan: ...}}`). May's and Brendan's teams differ in two fights (Rustboro if you chose Torchic: Torkoal vs Slugma; Route 119 if you chose Mudkip: Lombre vs Pelipper), and the Route 110 lead differs for Mudkip players. **`RunState` will need `rival` (or player gender)** in Phase 2.
- **`areas_new` replaces a hand-written `areas_reachable`.** Each battle lists only what opened since the last one, which is far easier to review; `agent/progression.py` accumulates it into `areas_reachable`.
- **Area-level specs** (`location/area`, `location/main`), because some areas need an HM that the rest of their location doesn't. Bagon is only in `meteor-falls/backsmall-room` (Waterfall), the Castform gift is in the `weather-institute` area (after Shelly), and Dive opens the `underwater` areas.
- **`key_items`** (rods, Devon Scope, Go-Goggles) because encounter methods depend on them. **`optional`**, **`partner`** (Steven in the Space Center multi battle), **`notes`**, and **`review`** flags on every judgement call.
- **`never_reachable`**: 18 areas PokeAPI lists with Emerald encounters that you can't reach before the Champion (postgame, event islands, unused maps), each with a reason. That lets tools answer "postgame" instead of "not in the data".

**Review flags resolved (2026-11-01).** The 8 `review:` flags were settled from the decomp's event scripts plus Bulbapedia, and each battle's `notes` cites the evidence. Six placements moved:
- Route 116 and Rusturf Tunnel open before Roxanne.
- Slateport and Routes 107–109 open before Brawly, because Briney only checks `FLAG_DELIVERED_STEVEN_LETTER`.
- Lilycove, Mt. Pyre, the Safari Zone and the Magma Hideout open before Winona, because the Devon Scope is the only gate.
- The Lilycove rival moved to the first visit, right after Winona.
- Rayquaza opens before Juan.

Two placements held: Bagon still needs Juan's badge for Waterfall, and Route 115's grass is still reached only through Meteor Falls. The areas rule is now stated in the file's header: each area is listed at the first battle it can be reached before, having fought only the battles above it.

**Badge order is looser than the file's order.** Only Norman's gym checks earlier badges, and it opens after the first four in any order. So Brawly can be deferred until Norman, and nothing from Fortree to the Magma Hideout checks Winona's badge. The file keeps the standard order. **`RunState` should therefore record which battles are done, not just a badge count.** `Progression.remaining(badges)` is a fallback for when only the count is known.

32 battles, not ~40: all 8 gyms, the Elite Four, the Champion, all 5 rival fights, both Wally fights, every Maxie/Archie fight, the Magma/Aqua admins, and the three early grunt fights that block the story. I left out the hideouts' generic grunts.

## D6. The decompilation is ground truth where PokeAPI disagrees

PLAN builds from PokeAPI plus its history tables. Cross-checking every table against the ROM data (`tests/test_gen3_facts.py`, cross-check group) found gaps the history tables don't cover, so the build now reconciles:
- **Moves**: type, power, accuracy and PP are patched to `battle_moves.h`. The patched fields are recorded in `moves.rom_patched`: six real changelog gaps (finding 1 below), Spit Up (the ROM stores 100 power where PokeAPI has null), and 32 moves where only accuracy differs (the ROM stores 100 where PokeAPI uses null for "can't miss").
- **Static encounters**: checked against the ROM's `setwildbattle` scripts (duplicates and misplaced rows removed).
- **Default trainer movesets**: computed from the decomp's level-up learnsets, because ROM order breaks ties within a level.
- **Deoxys's learnset**: taken from the form PokeAPI files Emerald's data under (Speed Forme).

PokeAPI stays the primary source for everything else (encounter slots and rarities, gifts, learnset methods, evolutions, names). Its species stats, types, abilities, learnsets, evolutions and wild tables now match the ROM exactly.

## Smaller choices

- `data/emerald.duckdb` (~7 MB) and `data/guide/` (~0.9 MB) are committed, as PLAN §12 allows.
- The build runs in memory and copies the final tables out, so the file doesn't carry dropped staging pages.
- `agent/db.py` `connect_session()` attaches the shipped DB read-only and keeps randomizer overlays in memory per session.
- Cloud Run region `us-east4` (as deployed), 600 s request timeout, max 3 instances (docs/deploy.md).

## D8. Phase 2 scope and design (agreed 2026-11-01)

These widen PLAN.md §1, §6 and §9. They were agreed in conversation before Phase 2 started.

- **Models:** Gemini on Vertex, location `global`.
  - `gemini-3.5-flash` for the Clarifier and researchers; `gemini-3.1-pro-preview` for the Lead and Writer.
  - Model names live only in env vars (`LOCKESMITH_FAST_MODEL`, `LOCKESMITH_STRONG_MODEL`).
  - **Claude Sonnet/Opus must stay a one-setting switch.** In Project 1, Gemini Flash gave poor results, so prompts and tool schemas must not depend on Gemini quirks.
- **Framework:** OpenAI Agents SDK through LiteLLM, behind `agent/runtime.py`. The SDK's own tracing is disabled, so nothing goes to OpenAI.
- **Run state:**
  - Required: which gym badges you hold (a list, so a deferred Brawly works) and your starter.
  - Optional: rival (May/Brendan), last major battle, current party.
  - The Clarifier asks up front only when an answer can't be given without the missing piece. Otherwise the answer states its assumptions and lists follow-up questions the researchers raised.
- **Question types:** catch recommendations, what to do next in the story, a longer plan to the Champion, and specific lookups. The Clarifier labels the type, and the Lead dispatches only the researchers it needs.
  - A fourth researcher, **Story**, works from the progression file, the walkthrough and the TM sources.
  - The Writer formats each answer to its question type.
- **Self-imposed rules:**
  - Presets: single type, no legendaries/mythicals, banned species, Nuzlocke + dupes clause, level caps, allowed obtain methods.
  - Free-text rules map to presets where possible. Anything else becomes a note the agents follow and the answer marks as not checked automatically.
  - Single type counts dual types and warns when an evolution drops the type.
- **Backup plans and revisions:**
  - Every recommendation carries one or two runner-ups that passed the same checks.
  - Sessions keep the last plan, its evidence, rejected picks and rules learned in conversation.
  - A specific objection becomes a session rule. A vague one gets a genuinely different plan plus a short "what didn't work?".
  - Hard enforcement of exclusions comes with the Verifier (Phase 3).
- **Deploy:** sessions live in memory, so Cloud Run needs session affinity once `/chat` is wired up.

## D9. Phase 2 tuning, from live runs (2026-11-01)

Measured with `scripts/phase2_acceptance.py`; the outputs are in `docs/phase2_runs/`.

- **Researchers loop on tools.** Gemini Flash often calls a tool once per species and runs into `max_turns`. Agents that hit the limit now get one more turn with tools switched off and report what they found (the SDK's `max_turns` error handler); the trace shows `turn_limit_wrap_up`. Before this, every scenario lost researchers to `MaxTurnsExceeded`.
- **Vertex quota is the main latency risk.** Four parallel researchers trip "429 Resource exhausted". The runner retries 429/5xx with exponential backoff (2 s doubling to 20 s, 5 retries), so nothing fails, but one slow researcher can push a request from about 90 s to about 240 s. A quota increase, or switching to Claude (D8), are the levers if this hurts.
- **Thinking effort is low for the Lead and Writer.** At default effort the Lead spent around 8k tokens and a minute or more per request; low effort kept the picks specific and cited.
- **Research rounds are capped at 2** until Phase 3's Verifier drives the gap loop. The Lead repeated answered tasks when allowed 3.
- **Tools default to the next *required* battle,** not an optional rival fight. Raw SQL is removed from the Catch researcher, because raw encounter rows skip the reachability and HM gates.
- **Typical times:** vague and out-of-scope questions take 3–4 s; next steps about 60 s; catch and revision questions 100–240 s. The request budget is 270 s, inside the graders' 5 minutes. (Superseded by D10.)

## D10. Faster research without handing researchers the answers, and long-term value (2026-11-01)

The user judged 100–240 s unacceptable; even a minute is long. We considered computing everything in code and handing researchers a fact sheet, but that would turn them into summarizers. It would also weaken the deep-research story: researchers exploring in parallel, and a Lead that goes back for gaps. The line we drew instead: **code does the arithmetic, agents decide what to investigate.**

- **Composite tools.** One call answers a whole investigative step, so researchers make one or two rounds of calls instead of nine small ones:
  - `scout_battle`: team plus matchups and level gap.
  - `get_catchable` with several types at once.
  - `moves_outlook`: several species in one call.
  - `assess_candidates` and `gauntlet_overview`: long-term value (below).

  Researchers still choose which battle to scout, which types to hunt and which candidates to assess.
- **Long-term value (user requirement).** Picks are judged over the whole remaining run, not just the next battle.
  - `gauntlet_overview` profiles every remaining battle through the Champion.
  - `assess_candidates` gives a species' final form, its evolution path (trade evolutions are flagged as impossible solo), final stats, coverage against every remaining opponent, and overlap with the party.
  - Each recommendation has a `horizon` ("core" through the Champion, or "situational" for one fight) and a `long_term` line. In live runs Absol was correctly called situational: Dark moves are special in Gen III, so its 130 Attack is wasted on its own STAB.
- **No waiting out rate limits.** A 429 goes straight to a fallback Gemini model (`LOCKESMITH_FALLBACK_MODEL`, default `gemini-3.8-flash`) with its own capacity. Only after that does a short retry (1–4 s, 2 tries) kick in. With fewer calls, the last runs saw no 429s at all.
- **Thinking effort was the biggest cost.** At default effort, Flash spent about 20 s thinking per researcher turn. At low effort the same battle task took about 9 s, with identical tool calls. Researchers, the Clarifier, the Lead and the Writer all run at low effort.
- **Other changes:**
  - The Writer moved to Flash: formatting and citing take about 4 s.
  - The researcher turn cap is 4, still with the forced wrap-up.
  - The Battle researcher lost `search_guide`, which it used to wander.
- **The Lead stays on Pro.** On Flash it saved only about 5 s (46 s vs 51 s), but it dispatched an unneeded fourth researcher, ignoring the instructions.
- **Result** (`scripts/phase2_acceptance.py`): catch plan 51 s with 14 model calls (down from about 31); revision 51 s; next steps 39 s; vague and out-of-scope 2 s. All five scenarios pass. Phase 4's front end will stream progress so the wait is visible.

## D11. Phase 3: the Verifier, the gap loop, rulesets and randomized runs (2026-11-01)

**Verifier (`agent/verifier.py`).** Code, no LLM. It checks every pick and every backup against the data:
- obtainable before its battle, through the same gates as `get_catchable`
- evolution reachable in time; trade evolutions fail, and items get a warning
- key moves learnable by then: level-up within the level limit, a TM reachable or a gym reward already won, or a reachable tutor
- the player's rules (below)
- Gen III facts: no Fairy type, no species or moves past Gen III, and a warning when a move's category doesn't suit the Pokémon's stronger attacking stat
- citations: every source id came from a tool this request

Each violation has a code (`CODES`) and a severity. Errors send the pick back; warnings go to the Writer, which mentions them where they matter.

**Gap loop (`pipeline.verify_and_repair`).**
1. A failing pick whose backup passes is swapped for the backup. This costs no model call; it's why the Lead writes complete backups.
2. Picks still failing send the Lead back once, with the Verifier's errors. It may run one targeted researcher round, so PLAN's cap of 3 rounds holds.
3. Whatever still fails is dropped, and the reason goes in `unresolved`.

The Writer's citations are then checked (unknown ids, or a pick whose section cites nothing), with one retry.

**Rulesets.** We default to the common Nuzlocke conventions and let the player change each one, in the form or in chat ("gifts count", "caps at the ace's level +2"):
- first encounter per **location**, with `encounter_scope: area` for the stricter per-room reading
- gifts and statics don't use up an area unless the player says so
- dupes clause off unless asked
- level caps at the next leader's ace, plus an offset

Anything the fields can't express goes in `notes`, and the Lead is told to respect those. Rules and rejected picks learned in conversation persist across turns, even when the form resends its own state.

**Randomized runs (`POST /upload_log`, `agent/overlay.py`).** After a log is parsed into overlay tables, the session's database gets **views with the vanilla tables' names**:
- `encounters`, `trainer_mons`, `species`, `evolutions`, `machines`, `move_tutors`, `learnsets`
- the session's search path (and DuckDB's view resolution) finds these before `base.*`

So every tool and the Verifier read the randomized game with no code changes, and other sessions keep vanilla. Details, each checked against UPR ZX's source:
- **Wild slots.** Converted to the vanilla numbering (1-based per method, fishing split by rod), with Gen III slot rates. A set the parser couldn't place is dropped, not answered from vanilla.
- **Starters and statics.** Starters follow `gStarterMons` order. Statics are remapped by species. When one vanilla species became several randomized ones at several places, the rows carry a "place unknown" condition.
- **In-game trades.** An unread trades section removes the vanilla trades.
- **Trainers.**
  - Randomized trainers get their new species' level-up moves at their level: UPR sets `resetMoves` (`AbstractRomHandler.randomizeTrainerPokes`, `Gen3RomHandler.setTrainers`).
  - Metronome-only mode gives every trainer Metronome.
- **TMs and tutors.** TM and tutor moves keep each slot's compatibility, as UPR does.
- **Evolutions.**
  - Random evolutions keep each vanilla evolution's method and change only the target (`new Evolution(fromPK, picked, ev.carryStats, ev.type, ev.extraInfo)`).
  - Targets follow `evolution.h` order, which differs from dex order only for Eevee and Tyrogue.
  - Evolution families are recomputed, so the dupes clause sees the new ones.
  - UPR's method changes and the 160 friendship threshold apply on top.
- **What the log changed but Lockesmith can't read.** This covers level-up movesets, TM/tutor compatibility, move data, shops and anything new. It isn't answered from vanilla:
  - tools leave it out with an `unknown` note, or refuse (`move_info`)
  - the Verifier downgrades an unprovable move to a `MOVE_UNVERIFIABLE` warning instead of rejecting the pick
  - the brief tells every agent what's unknown
  - `search_guide` warns that the walkthrough describes the vanilla game

Limits: wild sets from the log map to whole locations, not rooms (the vanilla table has the same grain for most places), and no real Emerald log has been through the parser yet (D4).

**Found in the live runs** (`scripts/phase3_acceptance.py`, outputs in `docs/phase3_runs/`):
- **Towns with no wild Pokémon were never "reachable."** Mauville City, Verdanturf, Fallarbor, Mt. Chimney and Scorched Slab weren't in any `areas_new`, so their TMs and tutors were never available. The Verifier wrongly rejected Lanturn with Thunderbolt and Starmie with Psychic before Juan, since TM24 and TM29 are both in Mauville. Each now opens at the step its route does. A test checks that every TM and tutor place opens somewhere; the one exception is the S.S. Tidal, whose ticket comes after the Hall of Fame.
- **A promoted backup left the headline naming the old pick.** When the final picks differ from the Lead's, the headline is blanked and the Writer opens from the final picks.

**Results** (Gemini, after both fixes):
- Nuzlocke into Juan (dupes clause, level caps, 23 used areas): 102 s, 22 model calls. The Verifier rejected a Gyarados backup that relied on Dragon Dance (Lv50, above the Lv46 cap). Running the Verifier again on the final plan found no errors.
- Water monotype with no legendaries, stated in chat: 77 s, 15 calls. Both rules were learned and every pick is Water-type.
- Randomized Tate & Liza from an uploaded log (a Fire-type team): 61 s, 14 calls. The answer named the log's team, recommended Water and Ground types, and cited `log:trainers#271`.
- A first run, before the town fix, also exercised the repair round: 118 s, with one Lead repair. The gap loop costs about 40 s when a repair is needed, and nothing when a backup is promoted.

## D12. Phase 4: front end, tracing and the baseline (2026-11-01)

Agreed with the user:
- **Field-journal look** (paper, emerald, pick cards) over a retro GBA style. The user liked GBA, but long cited answers must stay readable. The live-progress box borrows a GBA text-box frame as a nod.
- **One-click examples are required**, at least three. The user lost points in Project 1 without them. Each example fills both the question and the run state it needs, and the randomizer one loads the sample log too. `agent/examples.py` is the single list behind the buttons, `scripts/run_samples.py`, `scripts/baseline.py` and the README. The three README samples were marked on the page until 2026-11-04, when the user asked for the marks to come off.
- **The fuller synthetic randomizer log is backlogged** until the professor answers about real logs. The demo uses the small hand-made Tate & Liza log, labeled as such in its header.

Design choices:
- **Live progress without changing `/chat`.** `POST /chat/stream` sends server-sent events (`agent_start`, `tool_start`, `tool_call`), then the unchanged `/chat` body. Events come from the run hooks and from `tool_calls` itself, which is a list that reports each append. The page draws one lane per agent, so the parallel researchers fill in side by side. It falls back to `/chat` if the stream won't open, and waits on `/history` if the stream drops midway.
- **The `chart` is built in code** (`agent/chart.py`), not by the model. It's a Vega-Lite heatmap of how many of each remaining major battle's team the party's and the picks' STAB types hit super-effectively. It reads the session's tables, so it follows a loaded log.
- **The form follows the conversation.** After every answer the page reloads `/run_state` and flashes the panel if the Clarifier learned something ("I just beat Juan"). The form's next submission then doesn't undo it.
- **Readable citations.** Cited database rows get plain labels ("PokeAPI: Spheal at Shoal Cave (walk)"), computed only for ids the answer actually cites.
- **LangFuse through OpenInference.** With keys set, the Agents SDK's tracing is switched on with OpenInference's processor as its only processor (exclusive mode), so spans reach LangFuse and never OpenAI.
  - Audited the way LangFuse's agent skill prescribes: run a real request, fetch the trace back through the API, and check it against their best-practices page, read fresh on 2026-11-02.
  - The first trace had model, tokens and cost on every generation and correct nesting. Its gaps: generic names ("chat", six "Agent workflow" spans), JSON blobs as the root's input and output, no tags or environment, and the Verifier invisible.
  - Fixed:
    - Each agent run gets a verb-first workflow name (`classify-request`, `lead-research`, `research-catches`, `write-answer`, `wrap-up`) under one `run-agents` workflow and an `answer-question` root.
    - The root's input and output are the question and the answer; intent, picks, cost and rules go in metadata.
    - Tags are set at creation from the run state (`vanilla`/`randomized`, `nuzlocke`, `custom-rules`). Environment is `production` on Cloud Run and `development` locally.
    - The Verifier's steps are observations: `verify-picks`, `correct-places` and `check-citations` as evaluators, `promote-backups` as a span, errors at level ERROR.
    - The user id is a hash of IAP's opaque user id, so no email reaches LangFuse.
  - **What the first production trace showed.** A Nuzlocke question took 2 min 10 s. Three researchers finished in 11.5–21.9 s, but the story researcher took 78 s, because its first model call stalled for 68 s on a 76-token reply; its other four calls took 2–3 s. Across all 46 traced calls so far:
    - Flash: median 3.7 s, slowest normal call 14.6 s (even with 2,800 output tokens); the two outliers (68 s, 29 s) were tiny replies, i.e. stalls.
    - Pro: up to 33 s.

    So every call now has a time limit (`CALL_TIMEOUT_S`: 25 s for Flash, 60 s for Pro), and a call that hits it goes to the fallback model, as a rate-limited one already did. That turns a 68 s stall into about 25 s plus one fallback call.
  - **Most deployed turns never reached LangFuse.**
    - **Symptom:** traces were missing for 6 of 9 live turns, with no error anywhere. Locally every turn traced. The pattern looked tied to the question (Nuzlocke arrived, Tate & Liza didn't), but it wasn't.
    - **Finding it:** a per-turn log line with a count of exported spans showed `(0, 0)`: the spans never reached the exporter. Every logged trace id equalled the trace id Cloud Run had assigned the request.
    - **Cause:** FastAPI 0.162 has built-in OpenTelemetry tracing that turns itself on once any tracer provider is configured, which LangFuse does. It makes each request's `traceparent` header the parent of everything the request does. Google's front end sends that header on every Cloud Run request, usually marked "not sampled", so the parent-based sampler recorded nothing for those turns.
    - **Proof:** reproduced locally by adding such a header to a request: the trace took the header's id and exported `(0, 0)`.
    - **Fix:** `FastAPI(telemetry={"tracing": False, ...})`. With the same header, the turn then got its own trace id, exported 7 of 7 spans, and arrived. A test pins the setting.
    - The export counter and per-turn log line stay as cheap diagnostics.
  - Left as is: OpenInference's own `turn` and `generation` span names (generic but stable; the step above each says what it is). Gemini's thinking isn't captured, because thought summaries are off and turning them on means more output tokens per call.
- **Cost.** LangFuse's built-in prices don't match LiteLLM's `vertex_ai/` names or these Gemini versions. Prices live in `agent/pricing.py`, read from Google's pricing page on 2026-11-01:
  - 3.5 Flash: $1.50 / $9.00 per 1M input / output tokens
  - 3.1 Pro: $2.00 / $12.00
  - 3.8 Flash: $0.75 / $3.75 introductory through 2026, then $1.50 / $7.50

  Each usage entry records its cost, and `scripts/langfuse_prices.py` registers the same prices in LangFuse. Third-party pages disagreed on the newer Flash prices; the page renders its tables with JavaScript, so they were read with headless Edge.
- **Baseline.** Gemini 3.1 Pro, the Lead's model and the strongest in the pipeline, with no system prompt and no tools. The run state is written out in words, and the randomizer sample pastes in the log.

**Found by checking the README sample answers against the data** (agent and baseline alike):
- **A wrong "where" passed the Verifier.** The Lead wrote "Route 119, Good Rod … 100%" for Carvanha. That's the Super Rod's rate; the Good Rod's is 20%. The pick was obtainable, so no check failed, but the place line is the answer's core claim. New step, `correct_places` (code, after the gap loop): parse each pick's and backup's `where` for place names, method words and percentages, compare them with the encounter rows before the battle under the player's rules, and rewrite a wrong line from the data with that row cited. Picks already in the party are skipped.
- **"Rules I followed" was written by the Writer**, which marked the Nuzlocke rules and level caps "not checked automatically" although the Verifier checks them. It is now written in code from the ruleset: "(checked by the Verifier)" for rules with checks, "(not checked automatically)" for free-text notes.
- **Type multipliers made up in prose.** A battle note said "Psychic does 4x to Breloom" (it's 2x). After the first fixes, a rerun had picks claiming that Lanturn "double-resists Water" (0.5x) and that Lileep is "neutral to Ice" (Ice does 2x to Rock/Grass). The Lead and Writer are now told to take multipliers from the tools. A new check, `TYPE_CLAIM_WRONG`, reads each pick's and backup's text for matchups it states *about the pick*: "resists", "double-resists", "immune to", "neutral to", "weak to", "4x weak", "1/4x from". It checks each against the Gen III chart for the pick and the form it evolves into, and skips sentences about the opponents. A wrong claim goes to the Writer as a correction to fix or drop. Battle notes, whose subjects vary, still aren't checked in code.
- **A where line naming an extra place.** A backup said Voltorb is in "New Mauville or Team Aqua Hideout"; the hideout has Electrode, not Voltorb. `correct_places` now also flags any location name in the line where the species can't be had before the battle.
- **The randomized-run brief now says what the log left vanilla** (wild Pokémon, statics, TMs and so on). An answer had asked the player whether wild Pokémon were randomized, which the log already answers.
- **The baseline knows Emerald's well-known fights well.** Every checked fact in its Tate & Liza answer matched the data. In the Nuzlocke answer it gave Kingdra a fifth move (Sleep Talk), called Shock Wave TM39 (TM39 is Rock Tomb; Shock Wave is TM34), and said Magneton resists Water (it's neutral).

---

## Data findings

Surprises in the data, kept here for the README's data section:

1. **PokeAPI's move changelog misses later-generation changes.** Rest, Soft-Boiled, Milk Drink and Slack-Off show 5 PP (Gen 3: 10), Luster Purge shows 95 power (Gen 3: 70), and Mind Reader shows 40 PP (Gen 3: 5).
2. **PokeAPI's evolution table mixes regional-form methods into base species**: Alolan Raticate at night, Ice Stone Sandslash and Ninetales, Legends: Arceus's Quilava at level 17, Prism Scale Feebas. Without the version-group filter, a Gen 3 answer would include them. Seven Gen 4 baby pre-evolutions (Munchlax → Snorlax, etc.) also needed cutting.
3. **PokeAPI's Emerald statics are wrong in places.** New Mauville's three Voltorb are listed twice, and the Aqua Hideout's two Electrode also appear in New Mauville and at `team-magma-hideout`. In Emerald, the only Electrode statics are in Aqua Hideout B1F.
4. **Emerald's Aqua Hideout region section has no PokeAPI Gen 3 index.** The old index points at Ruby's Magma Hideout.
5. **PokeAPI lists Emerald encounters for Cave of Origin B2F/B3F**, which are leftover Ruby/Sapphire maps you can't enter in Emerald.
6. **Emerald's Deoxys is the Speed Forme.** PokeAPI files its Emerald learnset under that form, and the ROM keeps Normal Forme base stats in its table and swaps in Speed Forme stats at runtime. The DB stores the table values. This is postgame and event-only, so out of scope, but worth knowing.
7. **May's and Brendan's teams aren't always mirrors** (D5), and **the Space Center multi battle shows as two single battles** in the trainer structs, as PLAN anticipated.
8. **Emerald has five rival fights**, two of them optional (Rustboro, Lilycove), not the three or four people usually remember.
9. Apart from the other findings here, PokeAPI agrees with the ROM on everything checked: types, stats, abilities (after the past-table corrections), all 386 level-up learnsets, all 184 evolution pairs, the full type chart and every wild table (216 of 219 location/method pairs match outright; the other three are explained by the `seaweed` method and Mirage Island living inside the Route 130 map).
10. **PokeAPI stores the Gen 8+ friendship threshold (160)** for eight of Emerald's nine friendship evolutions. Emerald's is 220 (`FRIENDSHIP_EVO_THRESHOLD` in `pokemon.c`). The original cross-check compared evolution pairs, not thresholds, so it missed this.
11. **PokeAPI puts the Hall of Fame and TV-choice conditions on the roaming-grass rows only.** The roaming-water rows for the same Latias/Latios had none.
12. **Hidden Power and Weather Ball have no fixed category.** Damage takes physical/special from the type the move has in battle (`typeOverride` in `pokemon.c`), so `damage_class` is `varies`.
13. **Trainer Pokémon always have their first ability.** `CreateNPCTrainerParty` gives them even personality values, and the ability slot is `personality & 1`. `trainer_mons.ability` records it.

## D7. Second-model cross-check (2026-11-01)

The review packet (`docs/review_packet.md`) went to GPT. Before changing anything, each of its claims was re-checked in the decomp, Bulbapedia, or UPR ZX's own source.

**Confirmed and applied:**
- Findings 10–13.
- Wurmple's and Shedinja's evolution conditions.
- Feebas's 6 tiles and 50% roll (`wild_encounter.c`).
- The grunt fights at Mt. Chimney, the Weather Institute and Mt. Pyre, added as notes.
- Progression:
  - Routes 105/107/108 need Surf, because Briney's boat ride is a cutscene.
  - Route 115's grass is in its Surf-only north. My earlier reading that the Meteor Falls exit reaches it was wrong.
  - The eastern sea opens by Surf after the Aqua Hideout.
  - Sootopolis and the Regi caves open with Dive.

  To express Route 115 properly, the progression schema gained method-limited area specs.

**Partly right:** the randomizer format. UPR's source (`Randomizer.java`, `Gen3RomHandler.java`) shows:
- Trainer Pokémon print as `Name@Item LvN`.
- Moveset logging puts the header on its own line and adds `, Ability: X`.
- Statics carry `(2)` repeat counts.

GPT's sample log was from Pokémon X, though. Its "Surf/Old Rod" set labels don't apply: Gen 3 prints `Grass/Cave`, `Surfing`, `Rock Smash` and `Fishing`. The parser now follows the source.

**Unverified in its report but now settled:**
- UPR numbers trainers by ROM table index, which matches the decomp IDs.
- UPR numbers wild sets in ROM header order. No two Emerald sets share a table, so none are skipped.

**Found while verifying, not in its report:**
- UPR adds Steven's Space Center team as pseudo-trainer #855. The parser marks it as a partner.
- Cave of Origin is enterable only during the crisis: an Expert blocks it unless `VAR_SOOTOPOLIS_CITY_STATE` is 2–3.
- Routes 132–134 only flow west (Bulbapedia), so they can't be reached from Slateport before the eastern sea opens.

**Second round.** Every claim checked out after verification, with one placement corrected. Applied:
- **Routes that open in stages.**
  - Route 110's first grass lies south of the Team Aqua line (grunts at y=83, the Route 103 junction at y=60–80). It opens with Slateport, before Brawly; GPT had said P-07, but Slateport already opens at P-06.
  - Route 111's pond and Rock Smash rocks open from Mauville. Its grass is desert-only, behind the Go-Goggles.
- **TM gates:** `tm_locations.requires` (see D1). Highlights:
  - TM43 is first a gift from Route 111's Secret Power man. That gift also makes the Slateport TM salesman appear (`secret_power_tm.inc`).
  - TM06 needs Strength.
  - TM13 needs the Storage Key.
  - TM24 comes after New Mauville; TM27 after returning the Meteorite.
  - The Pacifidlog friendship TM is **weekly** (`FLAG_RECEIVED_FANCLUB_TM_THIS_WEEK`), not daily as I first said.
- **Encounter conditions PokeAPI lacks**, in the `rom_conditions` table:
  - Regis: the Sealed Chamber, then Regirock's Rock Smash, Regice's walking and Registeel's Flash puzzles (`braille_puzzles.c`, `fldeff_rocksmash.c`, `fldeff_flash.c`)
  - Rayquaza's return to Sky Pillar
  - Mirage Island's daily personality match (`time_events.c`)
- **The Safari Zone checks for the Pokéblock Case**, which the Lilycove Contest Hall gives out.
- **Method-limited `never_reachable`:** Littleroot and Steven's house are reachable; only their gifts are postgame.
- **Battle notes:** the Winstrates' four battles with no healing, and a warning about hideout grunts.
- **Randomizer changes outside the obvious sections**, confirmed in UPR's `Randomizer.java`:
  - three evolution-method sections, including the friendship threshold dropping to 160
  - `X: Unchanged.` and `X: Metronome Only.` status lines

  The parser now reads both and keeps a per-kind `changes` record, so tools only answer from vanilla when the log never mentions that data or says it's unchanged.

Still open, with no verdict possible without a real Emerald log: whether real logs match the R-03/R-05 numbering and the exact grammar across UPR versions.

## D13. Ruby and Sapphire support (2026-11-02 to 11-03)

The user asked for Ruby and Sapphire after the Emerald build was finished. Both are built as a **delta from Emerald**:
- `docs/review_packet_rs.md` lists what carries over unchanged (C), what differs (X) and a draft story order per version, all read from pret/pokeruby.
- It went through two GPT review rounds, each point re-checked in the decomp before anything changed.
- Round 1 caught a wrong hideout gate (the Slateport Harbor scene, not Mt. Pyre, opens it), a reversed Sealed Chamber order, and the hideout closing for good after the Mind Badge.
- Round 2 caught a Birch's-rescue species error (Poochyena, not Zigzagoon) and a postgame-only HM08 item ball.

**What carries over is checked, not assumed.** Diffing pokeruby against pokeemerald shows identical:
- species (types, stats, abilities)
- moves (type, power, accuracy, PP)
- the type chart and slot rates
- egg moves, evolutions and TM compatibility
- the trainer IV, ability and default-moveset rules
- every level-up learnset except Deoxys (Normal Forme in Ruby/Sapphire)

The Gen 3 correction layer and its tests therefore apply as they stand, and `tests/test_rs_facts.py` cross-checks each Ruby/Sapphire database against the decomp the same way Emerald's are.

**Data: one database per game** (`agent/games.py`).
- `data/emerald.duckdb`, `ruby.duckdb` and `sapphire.duckdb` share one schema, so every tool, the Verifier and the randomizer overlays read whichever one the session attached. Two game columns in one database would have touched every query.
- `build_db.py` builds all three, or one with `--game`.
- pokeruby compiles either version from one tree, so the parsers take the version:
  - wild tables come in `_Ruby`/`_Sapphire` pairs
  - scripts branch on `.ifdef SAPPHIRE` (`decomp.script_lines`)
  - `constants/version.inc` aliases resolve, e.g. `TRAINER_MT_CHIMNEY_GRUNT_3` is Maxie in Ruby and Archie in Sapphire, and `SPECIES_GROUDON_OR_KYOGRE`
  - the Lilycove hideout exists as two map sets, and each version keeps its own
- The same data lives in different files and syntax:
  - `base_stats.h`, `battle_moves.c`, `*_en.h` text, asm `.inc` tables
  - positional arrays for learnset pointers, trainer classes and ability names
  - `gTrainerParty_X` with `.level` and unbraced move lists
  - `TMHMMoves[]`, and `ITEM_TM01_FOCUS_PUNCH` item names
- **Emerald's database is unchanged:** rebuilt with the refactored code, it matches the earlier build table for table, apart from a new `build_info` row naming the game.

**PokeAPI for Ruby (version 7) and Sapphire (8), version group 5.** Its wild tables match the decomp slot for slot, when maps are matched by region-map index. Fixed in the build:
- **Statics:** Ruby lists New Mauville's Voltorb twice and Electrode under New Mauville; Sapphire puts Electrode in the Magma Hideout. `reconcile_statics_with_rom` now:
  - resolves version branches and aliases
  - counts shared scripts (`static_pokemon.inc`) for the maps that reach them, following `goto` chains (Route 119's Kecleon go through three labels)
- **Roamers:** the Hall of Fame condition sits on the water rows only, the reverse of Emerald, so every roaming row now gets the union of its species' conditions.
- **Friendship:** 160 is corrected to 220, which pokeruby hard-codes in `pokemon_3.c`.
- **Location mapping (`MAPSEC_OVERRIDES`):**
  - one region-map section holds whichever hideout the version has
  - pokeruby's `MAPSEC_UNDERWATER_125` is the map under Route 126
  - index 58 is the Battle Tower, not the Frontier
- **Encounter conditions** (`RS_ROM_CONDITIONS`):
  - the Ruby/Sapphire Regi puzzles: Strength, a two-minute wait, Fly
  - Relicanth first and Wailord last in the Sealed Chamber (Emerald's order is the reverse)
  - postgame Sky Pillar
  - the one-time Cave of Origin legendary

**Story: `data/progression_rs.yaml`, one file for both versions.**
- Any value written as `{ruby: ..., sapphire: ...}` resolves when the file is loaded for a version, so the 29 steps, areas and notes aren't duplicated.
- Steps are Emerald's reviewed ones minus the Rustboro rival, the Magma Hideout and the Space Center. Areas carry over because map connections and warps match on all 348 shared maps.
- New fields:
  - `wild` makes the required Lv45 Groudon/Kyogre a step; `tools.battles.team` presents it as a one-Pokémon team with its level-up moves
  - `events` lists the non-battle gates (cable car, museum, Mt. Pyre, Slateport Harbor, the hideout closing, Cave of Origin, the Hall of Fame), as round 1 asked
- Walkthrough citations point at Bulbapedia's 23-part Ruby and Sapphire walkthrough, in `data/guide_rs`. Its chunks list the versions they describe, so Sapphire searches skip Ruby-only sections.

**Agent: the run state names the game** (`RunState.game`, default `emerald`).
- **Session:** it reconnects when the game changes, and drops a loaded log, since that was for the other game.
- **Context and citations:** the request context derives its progression, name index and ledger from the game. Citations link to that game's decomp and walkthrough.
- **Badges:** they map to the game's gyms. Leader names are per game, because Wallace is Emerald's Champion but Ruby/Sapphire's 8th leader.
- **Clarifier:** it covers all three games and reads "I'm playing Sapphire" into the state. It still declines Omega Ruby/Alpha Sapphire and FireRed/LeafGreen.
- **Prompts:** they no longer name Emerald. The run-state brief opens with a line on how the player's game differs.
- **Page:** the front end has a Game picker, and the examples list has a Sapphire and a Ruby Nuzlocke question. The README samples stay Emerald.

**Randomizer.**
- UPR ZX prints the ROM's name only in its closing footer, so the parser reads the game there. Uploading a Sapphire log makes the session a Sapphire run.
- Steven's partner pseudo-trainer is Emerald-only.
- Wild-set names are compared after removing the `\c` that UPR's text table probably prints for pokeruby's `{NAME_END}` code.
- No real Ruby or Sapphire log has been parsed. The test log is hand-made from UPR's source, so the set count, static list and name rendering (packet R-12 to R-14) stay predictions.

**Found for Emerald along the way, now fixed in `data/progression.yaml`:**
- Its Aqua Hideout has the same harbor gate: two entrance grunts until the Slateport submarine scene, which the Magma Hideout arms. The note now says so; the placement was already right.
- "6 Feebas tiles" is "up to 6". The six draws aren't de-duplicated, and they move when the Dewford trendy phrase changes.

**Not done yet:**
- live model runs of the Ruby/Sapphire examples
- a script-level comparison of the remaining event gates between the two decomps (packet Q-08)
- real Ruby and Sapphire randomizer logs
- deploying the two new databases (about 7 MB each) and `data/guide_rs`

Tests: 332 pass, 5 skipped. New ones are in `tests/test_rs_facts.py`, `test_progression_rs.py`, `test_rs_agent.py` and `test_rs_randomizer.py`.

## D14. Ruby/Sapphire live runs and the fixes they prompted (2026-11-03)

D13's first and last open items are done: both databases are deployed, and the two Ruby/Sapphire examples ran live (`docs/samples/`, `docs/baseline/`). Their story facts checked out against the databases: Wallace's team, Groudon's Lv45 against Milotic's 43, and Courtney before Maxie in Seafloor Cavern. Three problems turned up, each now fixed in code.

- **The Clarifier asked when nothing was missing.** A live Sapphire run had the starter, six badges and a party, and the Clarifier still asked where the player was and which routes they'd used, with no Nuzlocke on. Now:
  - When the starter, badges and party are all set, its "ask" is overridden. The research trace shows it as `ask_overridden`.
  - Its prompt rules out asking about story position or used routes.
- **The baseline was told the wrong game.** `scripts/baseline.py` opened every prompt with "I'm playing Pokémon Emerald", so the Sapphire baseline answered for Emerald. It now names the example's game; the Emerald prompts are unchanged.
- **Wrong multipliers in battle notes and ability claims.**
  - The Ruby run's battle note said Ice Beam does 4x to Breloom (Grass/Fighting: 2x), and the Writer repeated it. D12's check read only the picks' own text, so notes weren't checked.
  - The Sapphire run said Chinchou's Volt Absorb "absorbs Water".
  - The original Ruby draft's correct "Lanturn has immunity to Electric" (Volt Absorb) was flagged as wrong, because the check knew only the type chart.

  `TYPE_CLAIM_WRONG` now does three things:
  - It reads battle notes and steps as well as picks.
  - It reads claims about any Pokémon named before the claim word, not just the pick.
  - It reads multiplier phrasing: "Ice Beam hits Breloom for 4x damage", "Earthquake deals 2x damage to Manectric", "2x against Electric types", "super-effective", "not very effective".

  Abilities count: Levitate, Volt/Water Absorb, Flash Fire, Thick Fat and Wonder Guard. A claim that holds under any reading of its sentence passes, so only clear mistakes go to the Writer as corrections.

  Run over the 9 saved drafts, it flags exactly the two real errors and nothing else.

## D15. Hedged Flash calls; invented citation ids dropped, not repaired (2026-11-03)

The live Ruby and Sapphire runs took 186 s and 127 s, against about 80 s for the Emerald samples. LangFuse's record of 185 successful Flash calls shows where the extra time went:
- **Rate limits cost almost nothing.** A 429 fails in about 0.5–1 s and goes straight to the fallback model.
- **Stalls cost the most.** The longest real answers (1,000+ tokens) all finished within 14.6 s. Everything slower was a short reply that had stalled (68 s for 76 tokens). A stall past 25 s hit the timeout, and the call started over on the fallback model. A stall under 25 s, like Sapphire's 21 s Clarifier call, just waited.
- **Ruby also lost about 50 s to a repair round.** The Lead cited `assess_candidates#Lanturn` and `#Magneton`, which no tool returned. Both picks failed the citation check, and the repair returned the same picks.

Fixes:
- **Hedging** (`runtime.FallbackModel`, `HEDGE_AFTER_S`). A Flash call with no answer after 12 s (13% of calls) also goes to the fallback model. The first answer wins, and the other is cancelled.
  - The original keeps running, so a long answer that's nearly done still wins. Nothing is cut off.
  - The cost is the extra tokens on hedged calls.
  - The 25 s timeout stays as a backstop.
  - Pro isn't hedged: it hasn't stalled, and its fallback is a weaker model.
  - Lowering the timeout to 15 s was the simpler option. It was rejected because it throws away a nearly-done answer and doesn't help with 12–15 s stalls.
- **Invented citation ids.** A pick that cites real sources plus an invented id keeps the real ones. The invented id is dropped and recorded in the trace as `drop_unknown_citations`. Only a pick with no real source left goes back to the Lead.

**After both fixes,** the same two examples ran live in 50 s (Sapphire) and 92 s (Ruby):
- **Sapphire:** no call stalled.
- **Ruby:**
  - One hedge fired; the original answered first.
  - A Pro call was rate-limited and went to the fallback, as before.
  - There was no repair round.
- **The Verifier:** its extended matchup check (D14) caught a new wrong claim, "Magneton resists Water" (Water does 1x to Electric/Steel).

One run each can't separate the fixes from Vertex's load that day. The 25 s timeout cost is gone by construction; the latency gain needs more runs to measure.

**The Lead stays on Pro.** In the post-fix Ruby run, one 429 on Pro sent a Lead call to Flash. That was D10's rule for every tier, but the Lead plans the research and drafts the picks, so the user wants it on Pro wherever possible.
- A rate-limited Pro call is now retried after 1, 2, 4 and 8 s, about 15 s at most, before Flash. A 429 comes back in under a second.
- A stalled Pro call (60 s) is retried once. Pro hasn't stalled in any recorded call, and one retry still fits the 270 s request budget.
- Flash calls still fall back at once.

## D16. FireRed and LeafGreen (2026-11-03, branch `firered-leafgreen`)

The user wants LockeSmith to grow past the class, so FireRed/LeafGreen went in as the first game outside Hoenn, and the game-specific parts became data where that was cheap.

**Built from pret/pokefirered** (commit `ce6406d8`), which keeps pokeemerald's layout. `build/decomp.py` tells the three decomp families apart by layout (`family`). For FireRed/LeafGreen it handles:
- the version flags and `_FireRed`/`_LeafGreen` wild tables
- Hoenn's unnamed leftover map sections
- the friendship threshold, read only from the `EVO_FRIENDSHIP` case
- the TM list in `data/party_menu.h`

The databases match the decomp on every cross-check: species, moves, type chart, learnsets, evolutions, every wild table (`tests/test_frlg_facts.py`). Emerald, Ruby and Sapphire rebuild row-for-row identical, apart from a new empty `move_tutors.requires` column.

**What FireRed/LeafGreen add, each read from the code:**
- **National Dex gate.** Until the National Dex (Oak gives it after the Hall of Fame once you've caught 60 species and visited One Island), any evolution into a species past #151 is cancelled: level-up, friendship and trade (`evolution_scene.c`). The party menu also refuses stones that would do it (`MonCanEvolve`). Espeon and Umbreon never evolve, since the day/night friendship cases are commented out.
  - Games carry this as `evolution_limit`.
  - `assess_candidates` stops evolution lines there.
  - The Verifier fails a pick that needs a gated evolution.
- **TMs.**
  - Gym TMs and gifts come from `giveitem_msg`.
  - The Celadon prize room sells TMs.
  - The Celadon roof girl trades three TMs for drinks.
  - TM10 has no map source: Pickup is the only way (`sPickupItems`, 5%). The game line says so.
- **Tutors.**
  - 15 one-time tutors, found through the maps that call their scripts.
  - Cape Brink's ultimate moves need a lead starter with friendship exactly 255 (`CapeBrinkGetMoveToTeachLeadPokemon`).
- **Rival.** The rival takes the starter strong against yours. The trainer constants are named after the rival's starter. The stored name "TERRY" never shows in battle, which prints the player-given name, so those trainers have no name in the database.
- **Field abilities.** As in Ruby/Sapphire, only Stench and Illuminate matter outside battle (`wild_encounter.c`).

**Per-game cast.** Each game in `agent/games.py` names:
- its starters
- the rival choice: May/Brendan, or none in Kanto
- its badges in `FLAG_BADGE0x_GET` order, with each one's gym battle and leader names

The run state, the Clarifier schema, the catalog and the form all read the cast. Switching region in chat drops the other region's starter, badges, rival and party unless they're restated.

**Story order** (`data/progression_frlg.yaml`, 23 steps, drafted from the decomp and Bulbapedia's walkthrough). Gates read from the code:
- HM badges: `FLAG_BADGE01_GET + field move`.
- Viridian Gym: needs badges 2–7.
- Route 23: a guard per badge.
- Saffron: the gatehouses want Tea, and a Rocket blocks Sabrina's door until Silph Co.
- Route 22 rivals: the early one is a detour; the late one is armed by Viridian Gym.
- The optional Sevii errand: Bill can be declined, and the ferry home opens only after it.

Every encounter area is either opened by a step or marked never reachable.

**Walkthrough corpus.** Bulbapedia's 20-part FireRed/LeafGreen walkthrough (360 passages). Its version marks render as "(FireRed)" and "(LeafGreen)".

**Review.** `docs/review_packet_frlg.md` goes through Codex (ChatGPT) rounds, run from an empty folder with decomp excerpts in the packet. Every claim gets checked in the decomp before anything changes.

**Review round 1** (`docs/review_frlg_round1_codex.md`). Codex confirmed 20 of the 21 claims. Each correction below was checked at the pinned commit before it was applied:
- **PC storage.** The PC comes back at Three Isle Port (`ThreeIsland_Port` clears `FLAG_SYS_PC_STORAGE_DISABLED`), not in the postgame.
- **National Dex.** Oak gives it only once you've caught 60 species and visited One Island (`PalletTown_ProfessorOaksLab`).
- **New steps:**
  - Mt. Moon's Super Nerd Miguel.
  - Pokémon Tower 7F's three Rockets. Rescuing Mr. Fuji gives the Poké Flute and opens Silph Co.'s door (`FLAG_RESCUED_MR_FUJI` in `SaffronCity`).
  - Three Island's bikers and Cue Ball Paxton, before Bond Bridge and Berry Forest.
- **Earlier access:**
  - Cerulean's exits open with Bill's S.S. Ticket (`FLAG_GOT_SS_TICKET`), so Route 5 south, Vermilion and the S.S. Anne's dock come before Misty.
  - Cut opens Route 16's north branch, Celadon's Tea, Saffron's Fighting Dojo and Route 12's north-end fishing before Surge.
  - Route 19's shore fishing comes before Koga.
  - Cinnabar's lab, the Card Key and the Secret Key come with Surf.
- **Postgame.** Three Isle Port's grass is behind the Dunsparce Tunnel, dug out only with the National Dex.
- **Rainbow Pass.** It comes from Celio for the Ruby, which needs the National Dex.
- **Tri-Pass.** It stays a key item after the Sevii steps.

Not applied:
- **Route 23 mid-game.** Its badge guards let you fish and surf part of it before eight badges. That's not modeled; the whole route opens with the League.
- **Mt. Ember's area names.** Codex would also compare levels and slots, not only species. It's left as a `review:` note.

**Review round 2** (`docs/review_frlg_round2_codex.md`). Codex confirmed all 14 round-1 changes and found no HM listed too early. Applied after checking each:
- **S.S. Anne.** The ship leaves when you step off it after the Captain's HM01: he sets Vermilion's scene to 1, and the dock's `ExitSSAnne` runs on it. The `closes` entry already had that timing; its reason now says so.
- **Pokémon Tower.** The ghost Marowak on 6F blocks the stairs (two trigger tiles) and is now named in the Tower step.
- **Card Key.** It can be had before Koga, since Silph Co. opens with Mr. Fuji's rescue.
- **Mimic.** The tutor also takes a Poké Doll (`EventScript_MimicTutor`).
- **Sevii.** Once you take Bill's trip, both Sevii steps are the way back to Kanto.

Not changed, since Codex misread them:
- `pallet-town` is excluded only for the starter gift; its fishing opens at the Route 22 step.
- `kanto-route-3/pokemon-center` is marked as PokeAPI's duplicate of the Route 4 Magikarp salesman.
- Key items stay the ones the tools gate on, not every key item.

## D17. Conversation memory: the Lead sees earlier turns, and the run state keeps the player's PC (2026-11-03)

A live FireRed conversation, read in LangFuse:
- **Turn 1.** The player listed what was in their PC (Snorlax, Growlithe, ...). The answer recommended Snorlax and Growlithe.
- **Turn 2.** The player asked a follow-up, and the Clarifier classed it as a lookup. The Lead got only the new message, the Clarifier's brief and the run state. It had no earlier turns, since the previous answer went to the Lead only on revisions, and the PC wasn't part of the run state. So it offered Snorlax again as a new catch, "if you haven't fainted or caught both static encounters".

Fixes:
- **Earlier turns.** On every follow-up, the Lead gets EARLIER IN THIS CONVERSATION: the player's recent messages and the previous answer's picks. Its prompt says to build on them, not start over.
- **The PC in the run state.** `owned` holds Pokémon the player has outside the party.
  - The Clarifier fills it from chat (merged, not replaced, with names resolved to species).
  - The form shows it as "Also in your PC".
  - The brief tells every agent not to send the player out to catch them.
  - The Verifier counts them as already obtained, and as caught for a dupes clause.

**Moves a party Pokémon already knows** (same day). In a live FireRed answer, the Lead's plan said "Consider TM26 Earthquake or HM04 Strength" for a Snorlax whose moves the player had given as Strength, Yawn, Snore and Rest. The brief listed them, but the Moves researcher suggested Strength anyway, and the Lead copied it.
- **The check.** A new Verifier check, `MOVE_ALREADY_KNOWN`, reads steps and battle notes for a move offered to a party member: a TM/HM label, "teach [Pokémon]", or "teach X to [Pokémon]". It aims the suggestion at the Pokémon named in the phrase, else the last party member the sentence names, else the step's title. It flags the suggestion when that member's given moves already include the move.
- **How it's fixed.** Like `TYPE_CLAIM_WRONG`, the finding goes to the Writer as a correction to fix in the text.
- **Prompts.** The Moves researcher and the Lead are told to check the party's moves and to name the move a new one replaces.

## D18. Follow-ups reuse earlier research (2026-11-03)

A live FireRed conversation, read in LangFuse:
- **Turn 1** ("what do I need before the Elite Four?"). The battle researcher scouted all five Elite Four battles.
- **Turn 2.** The Lead had asked which TMs Arcanine could learn, and the player answered: "I have Dig, Fire Blast, Aerial Ace and Overheat". This took 67 s:
  - 2 s Clarifier, 9 s Lead plan, 26 s research, 25 s Lead draft, 5 s Writer.
  - The Clarifier classed the answer as a revision. The Lead sent the Moves researcher for the four moves, plus the Battle researcher to scout the same five battles again.
  - The Lead only had turn 1's headline and picks, not its findings.

Fixes:
- **Findings carry over.** Each turn's researcher findings are kept in the session for the last 3 turns (`pipeline.keep_research`).
  - Each finding keeps its summary, claims and candidates, with only the source ids a tool returned.
  - A follow-up's Lead gets them as RESEARCH FROM EARLIER TURNS, newest first, up to 16k characters. A turn's findings run 3–7k.
  - Their ids go back into the ledger, so citing them passes the Verifier and the Writer's citation check.
  - Findings count only for the game and randomizer log they were researched on.
- **The Lead reuses them.** It's told to check those findings first, never research again what they cover, dispatch only for what's left open, and draft without dispatching when nothing is open.
- **Answers to the Lead's own questions aren't revisions.** The Clarifier is told to class them by what the player now wants (usually a lookup). A revision also gets EARLIER IN THIS CONVERSATION now, not only the previous plan.

**The replay** (same day). Both turns ran again locally, with the deployed code and the same models, at 74 s and then 53 s, down from 67 s for the follow-up:
- **The Clarifier** classed the TM answer as a lookup.
- **The Lead** got turn 1's findings. That run's battle finding named only some of each team and had no matchups for the four new moves, so the Lead still sent the Battle researcher. It ran beside the Moves researcher and finished first, so it cost tokens but not wall-clock time.
- **What remains of the follow-up's time:** Lead plan 10 s, research 14 s, Lead draft 15 s, Writer 9 s (a Flash 429 cost 4 s of that).

**An attack offered against a Pokémon it can't touch.** The replay's answer said Dig gives "a physical answer to Agatha's Poison-type Gengar and Haunter". Both have Levitate. No researcher said so: the Lead combined "Dig hits Poison super-effectively" with "Poison-type Gengar" itself. The matchup check missed it for two reasons:
- **The phrasing.** "An answer to X" isn't a claim word or a multiplier. A new shape in `matchup_errors` reads an attack offered against Pokémon: "answer to", "coverage against", "hits", "handles", "use it on". It flags the Pokémon the attack can't touch (0x for every ability they can have).
  - The attack is the one named before the phrase, or "with <move>" after the Pokémon, or, for a sentence starting "It", the attacks the text named before.
  - Any of those doing damage passes.
  - A sentence that says it doesn't work ("not", "avoid", "immune") passes.
- **Abilities.** `Target.takes` always counted the chart's multiplier beside the ability's, so even "Earthquake does 2x damage to Gengar" passed. An immunity that every member of the species has now replaces the chart. A damage-reducing ability (Thick Fat) still leaves the chart's figure right.

On 27 live Lead drafts from LangFuse and the 11 saved ones, the only new flags are the replay's two (Gengar, Haunter).
