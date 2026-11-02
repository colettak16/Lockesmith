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
