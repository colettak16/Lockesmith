# LockeSmith: Pokémon Ruby & Sapphire facts for cross-checking (draft 5)

Assembled 2026-11-02 from scratch extraction scripts run against the **pret/pokeruby** decompilation (`5784633ce4ef`, which builds both Ruby and Sapphire), compared with **pret/pokeemerald** (`731ad5bfd6e6`, the commit LockeSmith's Emerald build pins) and **PokeAPI** (`6b8db7f3cb31`). UPR ZX facts are from its source (master `7f00eb8`). Bulbapedia text is CC BY-NC-SA 2.5. Drafts 4 and 5 updated 2026-11-03.

**How this differs from the Emerald packet.** The Emerald packet (`docs/review_packet.md`) was generated from the built database and went through two review rounds. This packet was written first, as the fact base for the Ruby/Sapphire build, and LockeSmith's Ruby and Sapphire databases and story files have since been built from it. It is a **delta from Emerald**:
- section 2: what carries over unchanged
- sections 3 to 8: what differs
- the story order for each version
- section 12: a mechanical check that Ruby/Sapphire open areas when the story file says (new in draft 4)

**ID prefixes**: C carries over from Emerald, X differs from Emerald, P progression, E story events, A area unlocks, CL areas that close, N never reachable, K trainer teams, L wild encounters, SE special encounters, TM machines, R randomizer, D data findings, Q questions, V area-unlock verification.

**Draft 5 (2026-11-03): what's new for this review.** Review round 3 checked draft 4. Each of its points was re-checked in pokeruby and pokeemerald before anything changed.
- **Corrected:**
  - **E-09 / X-16 / SE-08 / D-03:** the Hall of Fame doesn't start the roaming Lati by itself. It sets `FLAG_SYS_TV_LATI`. The roamer starts when you check the TV on your house's 1F, which runs `InitRoamer` (`tv.inc`). This is now its own event, **E-10**.
    - In Emerald the same report plays by itself when you enter the house, and Mom asks which color you saw.
    - In Ruby/Sapphire nothing plays automatically; the TV just turns on, and the version picks the species.
- **Added:**
  - **Areas that close (P-R6, CL-01 to CL-02).** The story file can now close an area. The tools stop offering its encounters after the closing battle, flag them as missable until then, and warn about the closing in "next steps".
    - CL-01: the hideout after Tate & Liza.
    - CL-02: the forced legendary's static once its battle is over. Draft 4's build still offered Groudon/Kyogre as catchable before Wallace, after the required battle; the reviewer's point found that too.
    - Emerald got the same fix for Cave of Origin, which is open only during the crisis, and a missable flag for Mirage Tower, which falls when you take a fossil.
  - **V-11:** three more abilities only matter outside battle in Emerald:
    - Compound Eyes's held-item boost
    - Suction Cups/Sticky Hold's fishing boost
    - Flame Body/Magma Armor's faster egg hatching

    The agent's per-game brief now carries all of these, and the encounter abilities, for Ruby/Sapphire.
  - **SE-10 / Q-10:** every script that starts an encounter was compared with Emerald's. Only two things differ, the roamer (E-10) and gifts when your party is full. Ruby/Sapphire's Castform and fossil givers wait until you have room; Emerald sends the Pokémon to the PC.
  - Before/after checks in the test suite at the story steps the reviewer named: the Oceanic Museum, the hideout admin, Tate & Liza, the Seafloor Cavern and the legendary.
- **Narrowed:** V-00 and V-15 now say what section 12 covers: movement and story blockers. It doesn't cover every script that starts an encounter; the Lati TV report is one of those.
- **Already handled:** the randomizer parser records, for each kind of data, whether the log's section was parsed, left unparsed, Metronome Only or unchanged. That was fixed in Emerald's review round 2, so a recognised ROM isn't taken as proof that everything was read.
- **Confirmed by the reviewer:**
  - V-11's Sootopolis block and encounter abilities, V-14
  - X-11/X-18/E-05/E-06, TM-01/HM08
  - the teams of Tate & Liza, Wallace, Steven and the Lilycove rival
  - R-10, R-11 and R-14 (configuration only), X-10/A-09
- **Still open, all needing ROMs:** real UPR logs for R-12 to R-14 (Q-06), table hashes across revisions (R-17), and emulator checks of section 12's gates.

**Draft 4 (2026-11-03).** The build exists now, and the open question about area unlocks (Q-08) has been worked through mechanically.
- **Added: section 12.** Ruby/Sapphire were compared with Emerald on every shared map. The comparison covers:
  - reachability under each set of field moves
  - every story NPC standing on a chokepoint
  - step triggers
  - scripts that change the map
  - the C engine rules behind movement, field moves, bikes, Fly, tides and wild encounters

  **Result:** no gate differs beyond those already in E, X and A. The section also found three things:
  - an Emerald-only encounter block in Sootopolis (V-11)
  - Emerald-only encounter abilities, e.g. Synchronize (V-11)
  - a Lilycove Department Store gate that holds in all three games (V-14)
- **Changed:**
  - A-01's caveat now points to section 12, and Q-08 is answered.
  - D-08 gains two extraction pitfalls that draft 4's own first pass fell into.
  - The build now has V-14's store requirement and V-11's Emerald Sootopolis note.
- **Unchanged:** the rest of sections 2 to 10, as reviewed in rounds 1 and 2.

**Review round 1 (2026-11-02).** A second model reviewed draft 1. Each of its points was re-checked in pokeruby and pokeemerald before anything changed.
- **Corrected:**
  - **X-11 / P-18 / A-05:** the hideout opens after the **Slateport Harbor submarine theft**, not the Mt. Pyre orb theft alone. Two grunts block its entrance until then, and the orb flag I cited only changes their dialogue.
  - **X-14:** the Sealed Chamber order is **reversed** in Emerald (Wailord first, Relicanth last). Draft 1 wrongly said "same as Emerald".
- **Added:**
  - **X-18:** the hideout closes for good after the Mind Badge, so its Master Ball and Electrode are missable.
  - **Story events (E-01 to E-09)** as prerequisites in their own right, separate from battles.
  - Regi navigation gates (X-14).
  - Nuzlocke and level-cap facts for the forced legendary (P-22).
  - ROM identity (R-17).
  - Answers to Q-01 to Q-05 and Q-07, folded into the claims they settle.
- **Confirmed by the reviewer:** C-10, X-03, X-04, X-08 to X-12, X-14's puzzles, X-15, Roxanne's, Tate & Liza's and Steven's teams, A-08, D-07.
- **Still unverified:** R-12 to R-14, which need real Ruby/Sapphire UPR logs.

**Review round 2 (2026-11-02).** Re-checked in the decomp before applying.
- **Corrected:**
  - **TM-01 / HM08:** the Steven's-house Dive item ball is not a second story source. It's hidden at new game and appears only after the Hall of Fame, and only if Steven's gift was never taken (`hall_of_fame.inc`, `ShowHM08`). The reviewer called it dormant; the Hall of Fame script is the part it missed.
  - **R-14:** Birch's first-battle Pokémon is **Poochyena** Lv2 in Ruby/Sapphire, not Zigzagoon.
  - **P-R1:** 28 trainer-battle steps but 29 individual trainer battles (P-06 is two).
  - **L-01:** Route 102 vs 114 wording.
- **Added:**
  - mass outbreaks (L-08)
  - the Feebas tile quirks (C-11)
  - an extraction check for object flags (D-08)
- **Confirmed by the reviewer:** C-12, X-01/R-15, X-11/E-04, X-18/E-06, X-14's chamber order, E-01, P-14, L-03 (Routes 102/114), SE-06's Kecleon, TM-02 (Pacifidlog), X-12/A-03, R-10/R-11.
- **Still open:** R-12 to R-14 need real logs (Q-06), and A-01 needs a mechanical check of event gates (Q-08).

## How to review this packet

You are a second reviewer for **LockeSmith**, a research agent that answers questions about Pokémon games: what to catch, where, and how to beat the rest of the main story, including Nuzlocke and randomized runs. It covers Emerald, Ruby and Sapphire. This packet covers **Pokémon Ruby and Pokémon Sapphire (English, Gen 3, GBA, unmodified)**. Postgame is out of scope, except where a claim says "postgame" to mark something unreachable.

Everything below is what the agent treats as fact for Ruby and Sapphire. Each claim has an ID. Please check as many as you can, prioritising:
- **what's new in draft 5:** E-10, the closings (P-R6, CL-01, CL-02), SE-10 and Q-10's script comparison, V-11's additions, and Q-11
- **section 12** (new in draft 4): whether its method could miss a gate (Q-09, answered in round 3)
- **section 4**, story order, especially the Ruby/Sapphire split and the steps that differ from Emerald
- **section 5**, trainer teams
- **X-** claims

**About sources.**
- `[decomp]` claims were read from the game's code or data, so if you disagree, say what you think was misread.
- `[pokeapi]` and `[guide]` (Bulbapedia) as in the Emerald packet.
- `[inferred]` marks a conclusion drawn from code that we did not see run.
- `[diff]` marks a claim checked by mechanically comparing the two decompilations.

**Common false alarms.**
- Memory of **Emerald**: Juan as 8th leader, Wallace as Champion, both teams in one story, the Space Center battle, Mirage Tower, Battle Frontier, move tutors.
- Memory of the 2014 3DS remakes **Omega Ruby / Alpha Sapphire**: Fairy type, Mega Evolution, Primal Groudon/Kyogre, the Delta Episode, different teams and levels.

Please check that a disagreement applies to the GBA Ruby/Sapphire specifically.

**Answer in this format:**

1. **Disagreements**: a table with columns `ID | our claim (short) | what you believe instead | confidence (high/medium/low) | evidence (named source, or "memory") | suggested fix`.
2. **Unsure**: the same table, for claims you suspect but can't confirm.
3. **Missing**: facts, caveats or battles the agent should know that this packet omits, with the section they belong in.
4. **Answers to the open questions** (section 11, `Q-` IDs).
5. **Agreed**: the IDs or ID ranges you checked and agree with. Leave out IDs you didn't check.

Skip wording and formatting nitpicks. "Unsure" is a useful answer; a confident wrong correction costs more than a missed one.

## 1. Sources and method

- **One source tree, two games** `[decomp]`. pokeruby builds Ruby or Sapphire from the same files (`make ruby` / `make sapphire`). Version-specific content is encoded in four ways:
  1. **Wild tables.** Every map has a `<Map>_Ruby` and a `<Map>_Sapphire` table in `src/data/wild_encounters.json`: 97 maps, 179 tables per version.
  2. **Version aliases.** `constants/version.inc` maps neutral names to per-version targets, e.g. `TRAINER_MT_CHIMNEY_GRUNT_3` is `TRAINER_MAXIE_3` in Ruby and `TRAINER_ARCHIE_3` in Sapphire. The same applies to `SPECIES_GROUDON_OR_KYOGRE`, `ITEM_RED_OR_BLUE_ORB` and `SPECIES_LATIAS_OR_LATIOS`.
  3. **Script conditionals.** `.ifdef SAPPHIRE` blocks in map scripts.
  4. **Map swaps.**
     - Lilycove's hideout entrance leads to separate Magma Hideout maps in Ruby and Aqua Hideout maps in Sapphire.
     - Cave of Origin B4F switches layout by version.
     - Route 131 switches layout after the Hall of Fame.
- **Trainer data is shared** `[decomp]`. `src/data/trainer_parties.h` and `src/data/trainers_en.h` hold every trainer of both versions (693, numbered #1 to #693). Which ones you fight is decided only by the aliases and scripts above. Version-specific map scripts never name a villain trainer directly; every Team Magma/Aqua story battle goes through an alias.
- **Trainer teams** were parsed from those files. Trainers with default moves got the `GiveBoxMonInitialMoveset` rule (C-09) over pokeruby's own learnsets. Abilities are the species' first ability (C-08).
- **Story battles** were found by listing every `trainerbattle` command naming a gym leader, Elite Four member, champion, rival, Wally or villain alias, and resolving aliases per version.
- **ROM revision.** pokeruby builds revision 0 by default (`ruby_rev1`, `ruby_rev2` and the Sapphire equivalents also exist). This packet describes rev 0. Q-01 asks whether any later revision changes game data.

## 2. What carries over from Emerald unchanged (C)

Each was checked by diffing pokeruby against pokeemerald. Differences that were only constant names (`70` vs `STANDARD_FRIENDSHIP`, `SOLARBEAM` vs `SOLAR_BEAM`, `EFFECT_FLY` vs `EFFECT_SEMI_INVULNERABLE`, `EGG_GROUP_UNDISCOVERED` vs `EGG_GROUP_NO_EGGS_DISCOVERED`) are ignored. So the Emerald packet's tables M-03 (type chart), MV (moves), SP (species), LG (later-gen relatives) and EV (evolutions) apply to Ruby/Sapphire as they stand.

- **C-01** `[diff]` Species data is identical for all 386 species: types, base stats, abilities, catch rate, EXP yield, growth rate, gender ratio, wild held items, base friendship, egg groups (`base_stats.h` vs `species_info.h`).
- **C-02** `[diff]` Move data is identical for all 354 moves: type, power, accuracy, PP, priority, secondary-effect chance, target and flags (`battle_moves.c` vs `battle_moves.h`). The physical/special split by type (Emerald M-01) is the same engine rule.
- **C-03** `[diff]` The type chart is identical: the same 110 non-neutral entries in the same order (`data/type_effectiveness.inc` vs `gTypeEffectiveness` in `battle_main.c`), including Steel resisting Ghost and Dark. There's no Fairy type.
- **C-04** `[diff]` Level-up learnsets are identical for every species except **Deoxys**. Ruby/Sapphire have the Normal Forme learnset (Teleport 10, Snatch 30, Cosmic Power 35, Hyper Beam 50), Emerald the Speed Forme one. Deoxys is event-only, so this is out of scope.
- **C-05** `[diff]` The same 50 TMs and 8 HMs teach the same moves, and TM/HM compatibility is identical for all 386 species (`tmhm_learnsets.h`).
- **C-06** `[diff]` Egg moves are identical (166 species). The evolution table is identical: all 184 evolution pairs with the same methods and parameters.
- **C-07** `[decomp]` Friendship evolutions need **220** (`pokemon_3.c`: `friendship >= 220` for `EVO_FRIENDSHIP`, `_DAY`, `_NIGHT`). The Day/Night variants use the real-time clock (12:00–23:59 day, 00:00–11:59 night).
- **C-08** `[decomp]` Story-trainer Pokémon always have their first ability. Trainer IVs are `iv * 31 / 255` for all six stats. Both come from `CreateNPCTrainerParty` (`battle_main.c`): personality `0x80`/`0x78`/`0x88` plus `nameHash << 8`, then `CreateMon(..., fixedIV, ...)`. These are Emerald's M-09 and M-16.
- **C-09** `[decomp]` Default trainer movesets use the same rule as Emerald M-08 (`GiveBoxMonInitialMoveset`, `pokemon_1.c`): walk the learnset in ROM order up to the level, skip known moves, drop the oldest move when four are known.
- **C-10** `[diff]` Encounter slot rates are identical (Emerald M-10). The fishing table is one 10-slot list split Old Rod 0–1, Good Rod 2–4, Super Rod 5–9 (Emerald M-11).
- **C-11** `[decomp]` Feebas: **up to 6** tiles on Route 119, Lv20–25 (`wild_encounter.c`, `CheckFeebas`, `NUM_FEEBAS_SPOTS 6`).
  - Each of the six is `FeebasRandom() % 447` (0 becomes 447). Tile numbers 1–3 are re-rolled; pokeemerald's comment says those spots are inaccessible. Duplicates aren't re-rolled, so there can be fewer than six distinct tiles. We haven't checked that every tile from 4 to 447 can be fished.
  - The seed is the current Dewford trendy phrase (`easyChatPairs[0]`), so **the tiles move when that phrase changes**.
  - On a Feebas tile, Feebas comes up 50% of the time; otherwise the normal fishing table is used.
  - The agent shouldn't promise exactly six usable spots. Emerald's code is the same (round 2).
- **C-12** `[decomp]` **Field-move badges, now checked in code for all eight.**
  - `pokemon_menu.c` lists field moves in the order Cut, Flash, Rock Smash, Strength, Surf, Fly, Dive, Waterfall (`sPokeMenuFieldMoves`) and blocks move *i* unless `FLAG_BADGE01_GET + i` is set.
  - So: Cut needs the Stone Badge, Flash Knuckle, Rock Smash Dynamo, Strength Heat, Surf Balance, Fly Feather, Dive Mind, Waterfall Rain.
  - `field_control_avatar.c` repeats the checks for Surf (badge 5), Waterfall (badge 8) and Dive (badge 7). pokeemerald has the same gate at `party_menu.c:3725`.
  - This upgrades Emerald's M-12, where only Waterfall had been checked in code.
- **C-13** `[decomp]` **Norman's gym opens after the first four badges, in any order.** Rustboro, Dewford, Mauville and Lavaridge each add 1 to `VAR_PETALBURG_GYM_STATE`, and Norman battles at 6. This is Emerald P-R4, so Brawly can still be deferred.
- **C-14** `[diff]` **The overworld is wired the same.**
  - Of the 348 maps the two games share, map-to-map connections and warps match, except:
    - dive connections, which point to differently named underwater maps (L-07)
    - Safari Zone map renames (L-06)
    - Seafloor Cavern's internal room warps
  - Warps to places only one game has: Emerald's Mirage Tower, Trainer Hill, Terra Cave, Altering Cave, Desert Underpass, Steven's cave in Meteor Falls and the Magma Hideout at Jagged Pass; Ruby/Sapphire's contest halls and Battle Tower.
  - This is why Emerald's reviewed area unlocks are reused (section 4, A-01).

## 3. What differs from Emerald: game systems and story beats (X)

- **X-01** `[decomp]` **No move tutors.** pokeruby has no tutor learnset table, and UPR's `hasMoveTutors()` is false for Ruby/Sapphire. The "move tutor" menu (`move_tutor_menu.c`, used from `FallarborTown_House2`) is the **Move Relearner** (Heart Scale), which Emerald also has. Emerald's ten one-time Hoenn tutors don't exist: Swagger, Rollout, Fury Cutter, Mimic, Metronome, Sleep Talk, Substitute, Dynamic Punch, Double-Edge, Explosion.
- **X-02** `[decomp]` **693 trainers** (Emerald's table has 855 entries), numbered #1–#693 like Emerald's `opponents.h`, e.g. Roxanne #265 in both.
  - There are **no gym-leader rematch parties**: one `TRAINER_ROXANNE`, not `_1`…`_5`.
  - #272 is Wallace (8th gym) where Emerald has Juan; #335 is Steven (Champion) where Emerald has Wallace.
- **X-03** `[decomp]` **The 8th gym leader is Wallace** (Sootopolis, Water), and **the Champion is Steven** (Steel/Rock line-up).
- **X-04** `[decomp]` **One villain team per version.** Ruby's story fights are all Team Magma (Maxie, Tabitha, Courtney); Sapphire's are all Team Aqua (Archie, Matt, Shelly). Neither version has a story battle against the other team (section 1). Emerald has both teams.
- **X-05** `[decomp]` **Only one story double battle** (Tate & Liza, `doubleBattle = TRUE`) and **no multi battle**: there's no Mossdeep Space Center fight.
- **X-06** `[decomp]` **Four rival fights, not five.**
  - There's no Rustboro rival fight; the Lilycove fight is optional (`FLAG_DECLINED_RIVAL_BATTLE_LILYCOVE`).
  - May's and Brendan's teams are identical except one lead: on Route 110 against a Mudkip player, May leads with Wailmer and Brendan with Numel.
  - Emerald's two species differences (Rustboro for Torchic, Route 119 for Mudkip) don't exist.
- **X-07** `[decomp]` **Wally's Mauville battle is required**, as in Emerald. He stands on the tile in front of the gym door, (8,6) with the gym warp at (8,5) in both games, until you beat him; declining just makes him ask again.
- **X-08** `[decomp]` **Groudon (Ruby) / Kyogre (Sapphire) Lv45 is a required story encounter before the 8th gym.**
  - It's in Cave of Origin B4F (`setwildbattle SPECIES_GROUDON_OR_KYOGRE, 45`).
  - Sootopolis's doors, including the gym's, stay shut until `FLAG_LEGENDARY_BATTLE_COMPLETED` (`SootopolisCity_EventScript_LockCityDoors`).
  - The flag is set after the battle whatever the outcome (caught, knocked out or fled), and Wallace then appears in his gym.
  - It's one encounter: the trigger is disabled afterwards (`VAR_CAVE_OF_ORIGIN_B4F_STATE`).
- **X-09** `[decomp]` **HM07 Waterfall is an item ball in Cave of Origin B3F**, picked up on the way to the legendary. Emerald's is a gift in Sootopolis. It's still usable in the field only with the Rain Badge (C-12).
- **X-10** `[decomp]` **Rayquaza and Sky Pillar are postgame.** Route 131 switches to a layout with the Sky Pillar approach only once `FLAG_SYS_GAME_CLEAR` is set (`Route131_MapScripts`, `setmaplayoutindex 320`). `[inferred]` from the layout swap. In Emerald, Sky Pillar is part of the story.
- **X-11** `[decomp]` **The Lilycove hideout is the only hideout.**
  - Ruby enters at (71,5) into the Magma Hideout maps; Sapphire at (70,5) into the Aqua Hideout maps.
  - Ruby retiles the entrance in `LilycoveCity_OnLoad` under `.ifndef SAPPHIRE`; that Sapphire's open door is (70,5) is `[inferred]`.
  - The two map sets have different layouts but share scripts (double labels) and trainers via aliases.
  - **Entry gate** (corrected in round 1):
    - Two grunts stand across the 1F entrance: (13,11)/(14,11) in the Aqua Hideout, (13,19)/(14,19) in the Magma Hideout.
    - They are hidden by `FLAG_HIDE_GRUNT_1_BLOCKING_HIDEOUT` and `FLAG_HIDE_GRUNT_2_BLOCKING_HIDEOUT`, which only the **Slateport Harbor submarine-theft scene** sets (`SlateportCity_Harbor_EventScript_EvilTeamEscapeScene`, E-04).
    - That scene triggers on entering the harbor once Mt. Pyre's summit event has set `VAR_SLATEPORT_HARBOR_STATE` to 1 (E-03).
    - The `FLAG_MT_PYRE_ORB_STOLEN` check in the 1F script only changes what the two grunts say.
  - There is no Magma Hideout at Jagged Pass and no Magma Emblem step.
- **X-12** `[decomp]` **Fossils come from the Route 111 desert**: pick one of the Root Fossil (Lileep) or Claw Fossil (Anorith) from the ground (Go-Goggles needed). Picking one hides the other. They're revived at Devon Corp in Rustboro at Lv20. There's no Mirage Tower.
- **X-13** `[decomp]` **The Pokéblock Case comes from the Slateport Contest Lobby** (`SlateportCity_ContestLobby`). The Safari Zone entrance still checks for it (`Route121_SafariZoneEntrance`: `checkitem ITEM_POKEBLOCK_CASE`). Contest halls are in Slateport, Verdanturf, Fallarbor and Lilycove; Emerald has only Lilycove's, with Battle Tents in the other three towns.
- **X-14** `[decomp]` **Regi puzzles differ from Emerald's** (`braille_puzzles.c`):
  - **Sealed Chamber**: Dig, then **Relicanth first and Wailord last** in the party (`CheckRelicanthWailord`). **Emerald reverses it**: Wailord first, Relicanth last (pokeemerald `braille_puzzles.c`). Corrected in round 1.
  - **Regirock**: Strength in Desert Ruins
  - **Registeel**: Fly in Ancient Tomb
  - **Regice**: wait two minutes in Island Cave without pressing a button. It's a 7,200-frame counter, not the real-time clock, so a dead battery doesn't block it.
  - Emerald's are Rock Smash, Flash and walking around the room.
  - **Getting there**:
    - Sealed Chamber: Surf to Route 134, then Dive.
    - Desert Ruins: in Route 111's desert (Go-Goggles).
    - Island Cave: on Route 105 (Surf).
    - Ancient Tomb: on Route 120.
    - Strength and Fly also need their badges for field use (C-12).
    - All of these are held by the Dive step (A-07) in the standard order, but a build should check them as conditions, not assume them.
- **X-15** `[decomp]` **In-game trades** (3; Emerald has 4):
  - **Rustboro** (`RustboroCity_House1`): Makuhita "MAKIT" @ X Attack for your Slakoth
  - **Fortree** (`FortreeCity_House1`): Skitty "SKITIT" @ Glitter Mail for your Pikachu
  - **Pacifidlog** (`PacifidlogTown_House3`): Corsola "COROSO" @ Tropic Mail for your Bellossom
  - Emerald's Seedot, Plusle, Horsea and Meowth trades don't exist.
- **X-16** `[decomp]` **Roamer: Latios in Ruby, Latias in Sapphire**, Lv40 (`ROAMER_SPECIES` in `constants/species.h`). It starts after the Hall of Fame, once you check the TV news at home (E-09, then E-10; corrected in draft 5). Emerald plays that report by itself and asks for a color, which picks the species. Southern Island has the other one at Lv50 with the Eon Ticket (event-only).
- **X-17** `[decomp]` Places that **don't exist** in Ruby/Sapphire:
  - Mirage Tower, the Jagged Pass Magma Hideout, Trainer Hill, the Battle Frontier and Battle Tents
  - Altering Cave, Desert Underpass, Terra Cave, Marine Cave, Artisan Cave
  - the Safari Zone expansion, Meteor Falls' Steven room, Faraway/Birth/Navel islands
  - Postgame Johto starters are absent too.
  - Ruby/Sapphire have the **Battle Tower** (postgame) and Cave of Origin floors B2F–B4F, which Emerald only keeps as unused maps.
- **X-18** `[decomp]` **The hideout closes for good after the Mind Badge.**
  - `LilycoveCity_OnLoad` calls `LilycoveCity_EventScript_RemoveEvilTeamBaseEntrance` once `FLAG_BADGE07_GET` is set, which retiles the entrance to rock wall.
  - Everything inside is then **permanently missable**:
    - the **Master Ball**, Max Elixir and Nugget (B1F)
    - the Nest Ball (B2F)
    - the two **Electrode** statics (B1F)
    - any trainer not yet beaten
  - The admin battle (P-18) comes before Tate & Liza in the standard order, so a normal run passes through. A player who skips the hideout's side rooms loses them.
  - Emerald's Lilycove has no such closure.

## 4. Story progression (draft for both versions)

- **P-R1** **29 story steps** from the first rival fight to the Champion. Ruby and Sapphire share the order; the villain fights differ by version.
  - **28 trainer-battle steps holding 29 individual trainer battles**, because P-06 is two museum grunts in a row: all 8 gyms, the Elite Four, the Champion, 4 rival fights (Lilycove optional), both Wally fights, both leader fights (Mt. Chimney, Seafloor Cavern), four admin fights, and three early grunt steps (Petalburg Woods, Rusturf Tunnel, the museum pair).
  - One required wild battle: Groudon/Kyogre (X-08).
- **P-R2** Steps that **don't exist** in Ruby/Sapphire compared with Emerald's 32:
  - the Rustboro rival fight
  - Tabitha and Maxie at the Magma Hideout (two battles)
  - the Space Center multi battle
- **P-R3** The Emerald area rule (Emerald P-R2), HM rule (P-R3) and badge-order note (P-R4, C-13) carry over unchanged. The area rule now also applies closings (P-R6).
- **P-R4** Rival fights: the rival takes the starter with the type advantage over yours (Treecko → rival Torchic, Torchic → Mudkip, Mudkip → Treecko), from the `VAR_STARTER_MON` switch in each map script. The rival is May if you play Brendan and vice versa (X-06).
- **P-R5** Order is from the decomp's story gates, below, and Emerald's reviewed order. It hasn't yet been matched against Bulbapedia's Ruby/Sapphire walkthrough (23 parts) the way Emerald's was.
- **P-R6** **Areas that close (new in draft 5).** "Reachable before X" is the areas opened up to X, minus those that closed after an earlier battle. A closing tied to a battle removes the area for every later battle; until then the tools flag its encounters as missable, and "next steps" warns before that battle. A closing with no battle (one the player triggers) is only flagged. The list is CL below.

### Steps in order

| # | id | Step | Ruby | Sapphire | Badges | Format | Compared with Emerald |
|---|---|---|---|---|---|---|---|
| P-01 | rival1_route103 | Route 103: Rival | May/Brendan `_4/_7/_1` | same | 0 | single | same fight |
| P-02 | grunt_petalburg_woods | Petalburg Woods: Grunt | Magma `GRUNT_36` | Aqua `GRUNT_9` | 0 | single | Emerald: Aqua in both |
| P-03 | gym1_roxanne | Rustboro Gym: Roxanne | `ROXANNE` | same | 0 | single | team differs |
| P-04 | grunt_rusturf_tunnel | Rusturf Tunnel: Grunt | Magma `GRUNT_42` | Aqua `GRUNT_15` | 1 | single | |
| — | — | *(Emerald's optional Rustboro rival)* | — | — | | | doesn't exist |
| P-05 | gym2_brawly | Dewford Gym: Brawly | `BRAWLY` | same | 1 | single | team differs |
| P-06 | grunts_oceanic_museum | Oceanic Museum: 2 Grunts | Magma `GRUNT_46`, `_47` | Aqua `GRUNT_19`, `_20` | 2 | single ×2 | |
| P-07 | rival2_route110 | Route 110: Rival | `_5/_8/_2` | same | 2 | single | |
| P-08 | wally_mauville | Mauville: Wally | `WALLY_2` | same | 2 | single | same team |
| P-09 | gym3_wattson | Mauville Gym: Wattson | `WATTSON` | same | 2 | single | team differs |
| P-10 | admin_mt_chimney | Mt. Chimney: Admin | Tabitha `TABITHA_2` | Matt `MATT_2` | 3 | single | Emerald: Tabitha |
| P-11 | leader_mt_chimney | Mt. Chimney: Leader | Maxie `MAXIE_3` | Archie `ARCHIE_3` | 3 | single | Emerald: Maxie |
| P-12 | gym4_flannery | Lavaridge Gym: Flannery | `FLANNERY` | same | 3 | single | team differs |
| P-13 | gym5_norman | Petalburg Gym: Norman | `NORMAN` | same | 4 | single | team differs |
| P-14 | admin_weather_institute | Weather Institute: Admin | Courtney `COURTNEY_1` | Shelly `SHELLY_1` | 5 | single | Emerald: Shelly |
| P-15 | rival3_route119 | Route 119: Rival | `_6/_9/_3` | same | 5 | single | |
| P-16 | gym6_winona | Fortree Gym: Winona | `WINONA` | same | 5 | single | team differs |
| P-17 | rival4_lilycove | Lilycove: Rival (optional) | `*_LILYCOVE_<your starter>` | same | 6 | single | |
| — | — | *(Emerald's Magma Hideout: Tabitha, Maxie)* | — | — | | | doesn't exist |
| P-18 | admin_hideout | Lilycove hideout: Admin | Tabitha `TABITHA_1` (Magma Hideout maps) | Matt `MATT_1` (Aqua Hideout maps) | 6 | single | Emerald: Matt, Aqua Hideout |
| P-19 | gym7_tate_liza | Mossdeep Gym: Tate & Liza | `TATE_AND_LIZA` | same | 6 | **double** | 2 Pokémon, not 4 |
| — | — | *(Emerald's Space Center multi battle)* | — | — | | | doesn't exist |
| P-20 | admin_seafloor_cavern | Seafloor Cavern: Admin | Courtney `COURTNEY_2` | Shelly `SHELLY_2` | 7 | single | Emerald: Shelly |
| P-21 | leader_seafloor_cavern | Seafloor Cavern: Leader | Maxie `MAXIE_2` | Archie `ARCHIE_2` | 7 | single | Emerald: Archie |
| P-22 | legendary_cave_of_origin | Cave of Origin B4F: Groudon / Kyogre Lv45 | Groudon | Kyogre | 7 | wild | **new step** (X-08) |
| P-23 | gym8_wallace | Sootopolis Gym: Wallace | `WALLACE` | same | 7 | single | Emerald: Juan |
| P-24 | wally_victory_road | Victory Road: Wally | `WALLY_1` | same | 8 | single | same team |
| P-25–28 | e4_* | Elite Four: Sidney, Phoebe, Glacia, Drake | | same | 8 | single | 3 small team differences |
| P-29 | champion_steven | Champion: Steven | `STEVEN` | same | 8 | single | Emerald: Wallace |

Notes per step:
- **P-06** `[decomp]` The museum script hides the grunt line across Route 110 at y=83 (x=7–10), via `FLAG_HIDE_EVIL_TEAM_ROUTE110` in `SlateportCity_OceanicMuseum_2F`. That is the same staged Route 110 as Emerald's P-R9.
- **P-10/P-11** Mt. Chimney also has one grunt per version (Ruby `GRUNT_40`, Sapphire `GRUNT_13`), as a note like Emerald's P-R8.
- **P-14** The Weather Institute has four grunts before the admin (Ruby `GRUNT_43`, `_52`, `_44`, `_45`; Sapphire `GRUNT_16`, `_25`, `_17`, `_18`). Castform is the reward (SE-03).
- **P-18** `[decomp]`
  - Two story events come first, in order:
    - Mt. Pyre's summit event (E-03; three grunts: Ruby `GRUNT_49`–`_51`, Sapphire `GRUNT_22`–`_24`)
    - the Slateport Harbor submarine theft (E-04), which removes the grunts blocking the hideout entrance (X-11)
  - Neither checks a badge. Before Winona the player has to walk back to Slateport, since Fly needs the Feather Badge.
  - The hideout also has grunts on 1F, B1F and B2F. It closes after the Mind Badge (X-18).
  - Clearing the hideout sets `FLAG_EVIL_TEAM_ESCAPED_IN_SUBMARINE`, which removes the Wailmer blocking Lilycove's eastern sea (`LilycoveCity_EventScript_SetWailmerMetatiles`). This is the same gate as Emerald's.
- **P-20/P-21** Seafloor Cavern has two grunts before the admin (Room 1) and one between the admin and the leader (Room 4).
- **P-22** `[decomp]` Cave of Origin's entrance is blocked by an Expert until `FLAG_LEGEND_ESCAPED_SEAFLOOR_CAVERN` (set at the end of P-21). See also X-08 and X-09.
  - **For challenge runs** (added in round 1). The agent should report three separate facts and not pick a rule for the player:
    - **The battle is required**: the story needs the encounter resolved, but not the catch.
    - **Catch eligibility depends on the player's rules.** B4F is part of the same location (`cave-of-origin`) as the wild floors 1F–B3F (Zubat, Golbat, Mawile/Sableye). Under a strict first-encounter-per-location rule, an earlier wild encounter there uses up the location, unless the player counts statics separately. LockeSmith's default doesn't count them (docs/decisions.md D11).
    - **Its level is above the next cap.** At Lv45 it is over Wallace's ace (Milotic, Lv43), so under a next-leader level cap it can't be used against Wallace without breaking the cap.
- **P-23** Wallace gives TM03 Water Pulse. Sootopolis's other doors (TM31 Brick Break's house among them) also open only after P-22.

### Story events (E)

Non-battle milestones that gate areas or encounters, added in round 1. The battle list alone can imply that an area opens straight after an unrelated boss. A build should store these as prerequisites in the progression file, not only as notes. All are `[decomp]`.

| ID | Event | Requires | Opens / changes | Flag or variable |
|---|---|---|---|---|
| E-01 | Meteor Falls scene (no battle) | Route 114 | The two grunts blocking Route 112's cable car leave, so Mt. Chimney can be reached | `FLAG_HIDE_GRUNTS_BLOCKING_CABLE_CAR` (`MeteorFalls_1F_1R`) |
| E-02 | Oceanic Museum battle (P-06) | Slateport | The grunt line on Route 110 at y=83 goes | `FLAG_HIDE_EVIL_TEAM_ROUTE110` |
| E-03 | Mt. Pyre summit orb theft | reach the summit (no badge check) | Arms the Slateport Harbor scene | `FLAG_MT_PYRE_ORB_STOLEN`, `VAR_SLATEPORT_HARBOR_STATE` = 1 |
| E-04 | Slateport Harbor submarine theft | E-03, then enter the harbor | The hideout's entrance grunts go | `FLAG_HIDE_GRUNT_1/2_BLOCKING_HIDEOUT` |
| E-05 | Hideout cleared (P-18) | E-04 | The Wailmer blocking Lilycove's eastern sea leave | `FLAG_EVIL_TEAM_ESCAPED_IN_SUBMARINE` |
| E-06 | Mind Badge (P-19) | | The hideout entrance is walled off for good (X-18) | `FLAG_BADGE07_GET` |
| E-07 | Seafloor Cavern leader (P-21) | | The Expert at Cave of Origin steps aside | `FLAG_LEGEND_ESCAPED_SEAFLOOR_CAVERN` |
| E-08 | Groudon/Kyogre battle (P-22) | E-07 | Sootopolis's doors and gym open; Wallace appears | `FLAG_LEGENDARY_BATTLE_COMPLETED` |
| E-09 | Hall of Fame | | Sky Pillar, the Beldum gift, the S.S. Tidal, and the TV news that starts the roamer (corrected in draft 5) | `FLAG_SYS_GAME_CLEAR`; `FLAG_SYS_TV_LATI`, set only while no Lati roams yet (`hall_of_fame.inc`) |
| E-10 | Lati TV report (new in draft 5) | E-09, then check the TV on your house's 1F | The roaming Latios (Ruby) / Latias (Sapphire) starts (`InitRoamer`). The TV just turns on and nothing plays until you check it; there is no color question | `FLAG_LATIOS_OR_LATIAS_ROAMING` (`tv.inc`, `EventScript_1A6F0B`) |

### Area unlocks: changes to Emerald's reviewed list (A)

- **A-01** `[diff]` For every step not listed below, the areas newly reachable before it are those of the matching Emerald step in `data/progression.yaml`, because the overworld is wired the same (C-14). The removed Emerald steps opened no areas of their own, except the Magma Hideout (A-05).
  - **Caveat (round 1):** the same map connections don't prove the same event gates; the hideout (X-11) shows why.
  - **Checked mechanically in draft 4 (section 12, answers Q-08):** per-map reachability, every story blocker on a chokepoint, step triggers, conditional map changes and the engine's movement and field-move rules. No gate differs beyond the ones already in E, X and A-02 to A-10, so the copied unlocks stand.
- **A-02** Before P-02 and P-03: as Emerald.
  - Routes 101–104, Petalburg, Petalburg Woods.
  - Then Rustboro, Route 116, the west of Rusturf Tunnel, and Route 115's beach for fishing only.
- **A-03** Before P-13 (Norman): Route 111's desert grass (Go-Goggles from the rival in Lavaridge after Flannery) as in Emerald, but **no Mirage Tower**. The desert has the fossil choice instead (X-12).
- **A-04** The **Pokéblock Case** is held from Slateport onward (X-13), which changes the Safari Zone's *item* gate, not when it can be reached. The Safari Zone, Lilycove and Mt. Pyre open before Winona as in Emerald, since the Devon Scope is the only gate on Route 120.
- **A-05** Before P-16 (Winona):
  - Emerald lists `magma-hideout` (Jagged Pass) here; it doesn't exist in Ruby/Sapphire.
  - The Lilycove hideout has **no wild Pokémon**; its only encounters are two **Electrode Lv30 statics in B1F**, in both versions.
  - The hideout can be entered once **E-03 then E-04** are done (Mt. Pyre summit, then Slateport Harbor). Neither checks a badge, so it is listed here like Emerald's Magma Hideout. Corrected in round 1: draft 1 named only the Mt. Pyre event.
  - It **closes after the Mind Badge** (X-18), so its Electrode and items are reachable only from here until P-19.
- **A-06** Before P-19 (Tate & Liza): as Emerald.
  - Routes 124–134, Mossdeep, Shoal Cave, Mirage Island and Pacifidlog, by Surf once the Wailmer leave.
- **A-07** Before P-20 (Dive, after Tate & Liza): as Emerald.
  - Underwater Routes 124 and 126 (seaweed), Seafloor Cavern, Sootopolis (by Dive), and the three Regi caves via the Sealed Chamber.
  - The Regi puzzles need Strength, Fly and waiting (X-14), all available by then.
- **A-08** **New, before P-22** (after P-21): Cave of Origin **1F, B1F, B2F, B3F**. Walk tables: Zubat, Golbat, plus Mawile (Ruby) / Sableye (Sapphire). B4F holds the legendary.
  - Emerald opens only the entrance, 1F and B1F, and before Juan; its B2F/B3F are unused leftover maps (Emerald data finding 5).
- **A-09** Before P-23 (Wallace): **remove Sky Pillar** (1F, 3F, 5F, top), which Emerald opens here. It's postgame in Ruby/Sapphire (X-10).
- **A-10** Before P-24: as Emerald. Ever Grande City, Victory Road, and Meteor Falls' back rooms with Waterfall (Bagon).

### Areas that close for good (CL), new in draft 5

- **CL-01** The hideout (`team-magma-hideout` in Ruby, `team-aqua-hideout` in Sapphire) is gone after P-19, Tate & Liza: E-06 walls it off. Its two Electrode are offered only up to P-19 and flagged as missable.
- **CL-02** Cave of Origin B4F's static (Groudon/Kyogre) is gone after P-22, the battle itself. The rest of the cave stays open: the Expert doesn't come back after the battle, and HM07 is still on B3F.
- Emerald's file gains Cave of Origin, gone after Juan (open only during the crisis), and Mirage Tower, flagged as missable because it falls when you take a fossil.

### Never reachable before the Champion (N)

- **N-01** Postgame (`FLAG_SYS_GAME_CLEAR` or Hall of Fame scripts):
  - Sky Pillar, all floors (X-10)
  - the Beldum gift in Steven's house (`hall_of_fame.inc` unhides it)
  - the roaming Latios/Latias (X-16; after E-09, then E-10)
  - the Battle Tower
  - the S.S. Tidal (TM49)
- **N-02** Event-only: Southern Island (Eon Ticket).
- **N-03** Emerald's `never_reachable` entries for places that don't exist in Ruby/Sapphire (X-17) drop out. Littleroot is reachable and has no postgame gift (Emerald's Johto starters).

## 5. Trainer teams for the story battles (K)

Parsed from pokeruby's `trainer_parties.h` and `trainers_en.h` (section 1). `(custom)` movesets are written in the party data; `(default)` ones are computed by C-09. IVs are the stat value after C-08's formula. Where a step differs by version, both teams are listed.

**For contrast with Emerald** (so Emerald memory is easy to spot):
- Roxanne: Geodude 12, Geodude 12, Nosepass 15.
- Tate & Liza: Claydol 41, Xatu 41, Lunatone 42 and Solrock 42, the last two holding Sitrus Berries. Ruby/Sapphire's Lunatone and Solrock hold nothing.
- Wally (both fights) is identical in all three games.
- Elite Four differences: Sidney has Crawdaunt 48 where Ruby/Sapphire have Sharpedo 48; Glacia's first two slots are swapped; Drake has Kingdra 53 where Ruby/Sapphire have a second Flygon 53.
- Archie at Seafloor Cavern is identical to Sapphire's. Shelly there is Lv37 in Emerald, Lv38 in Sapphire.

### K-rival1_route103: Route 103: Rival (first battle)

*Player chose Treecko:* May and Brendan identical.
- **Rival May** `TRAINER_MAY_4` (#532); bag: none
  - Lv5 Torchic, Blaze, IVs 0: Scratch / Growl (default)
  - Brendan: `TRAINER_BRENDAN_4` (#523), same team

*Player chose Torchic:* May and Brendan identical.
- **Rival May** `TRAINER_MAY_7` (#535); bag: none
  - Lv5 Mudkip, Torrent, IVs 0: Tackle / Growl (default)
  - Brendan: `TRAINER_BRENDAN_7` (#526), same team

*Player chose Mudkip:* May and Brendan identical.
- **Rival May** `TRAINER_MAY_1` (#529); bag: none
  - Lv5 Treecko, Overgrow, IVs 0: Pound / Leer (default)
  - Brendan: `TRAINER_BRENDAN_1` (#520), same team

### K-grunt_petalburg_woods: Petalburg Woods: Grunt

*Ruby:*
- **Team Magma Grunt** `TRAINER_GRUNT_36` (#575); bag: none
  - Lv9 Poochyena, Run Away, IVs 0: Tackle / Howl / Sand Attack (default)
*Sapphire:*
- **Team Aqua Grunt** `TRAINER_GRUNT_9` (#10); bag: none
  - Lv9 Poochyena, Run Away, IVs 0: Tackle / Howl / Sand Attack (default)

### K-gym1_roxanne: Rustboro Gym: Roxanne

- **Leader Roxanne** `TRAINER_ROXANNE` (#265); bag: Potion, Potion
  - Lv14 Geodude, Rock Head, IVs 18: Tackle / Defense Curl / Rock Throw / Rock Tomb (custom)
  - Lv15 Nosepass, Sturdy, IVs 24: Tackle / Harden / Rock Throw / Rock Tomb (custom)

### K-grunt_rusturf_tunnel: Rusturf Tunnel: Grunt (Devon Goods)

*Ruby:*
- **Team Magma Grunt** `TRAINER_GRUNT_42` (#581); bag: none
  - Lv11 Poochyena, Run Away, IVs 0: Tackle / Howl / Sand Attack (default)
*Sapphire:*
- **Team Aqua Grunt** `TRAINER_GRUNT_15` (#16); bag: none
  - Lv11 Poochyena, Run Away, IVs 0: Tackle / Howl / Sand Attack (default)

### K-gym2_brawly: Dewford Gym: Brawly

- **Leader Brawly** `TRAINER_BRAWLY` (#266); bag: Super Potion, Super Potion
  - Lv17 Machop, Guts, IVs 18: Leer / Karate Chop / Seismic Toss / Bulk Up (custom)
  - Lv18 Makuhita, Thick Fat, IVs 24: Arm Thrust / Knock Off / Sand Attack / Bulk Up (custom)

### K-grunts_oceanic_museum: Oceanic Museum: two Grunts

*Ruby:*
- **Team Magma Grunt** `TRAINER_GRUNT_46` (#585); bag: none
  - Lv15 Numel, Oblivious, IVs 0: Growl / Tackle / Ember (default)
- **Team Magma Grunt** `TRAINER_GRUNT_47` (#586); bag: none
  - Lv14 Zubat, Inner Focus, IVs 0: Leech Life / Supersonic / Astonish (default)
  - Lv14 Numel, Oblivious, IVs 0: Growl / Tackle / Ember (default)
*Sapphire:*
- **Team Aqua Grunt** `TRAINER_GRUNT_19` (#20); bag: none
  - Lv15 Carvanha, Rough Skin, IVs 0: Leer / Bite / Rage / Focus Energy (default)
- **Team Aqua Grunt** `TRAINER_GRUNT_20` (#21); bag: none
  - Lv14 Zubat, Inner Focus, IVs 0: Leech Life / Supersonic / Astonish (default)
  - Lv14 Carvanha, Rough Skin, IVs 0: Leer / Bite / Rage / Focus Energy (default)

### K-rival2_route110: Route 110: Rival

*Player chose Treecko:* May and Brendan identical.
- **Rival May** `TRAINER_MAY_5` (#533); bag: none
  - Lv18 Wailmer, Water Veil, IVs 6: Splash / Growl / Water Gun / Rollout (default)
  - Lv18 Shroomish, Effect Spore, IVs 6: Tackle / Stun Spore / Leech Seed / Mega Drain (default)
  - Lv20 Combusken, Blaze, IVs 12: Focus Energy / Ember / Double Kick / Peck (default)
  - Brendan: `TRAINER_BRENDAN_5` (#524), same team

*Player chose Torchic:* May and Brendan identical.
- **Rival May** `TRAINER_MAY_8` (#536); bag: none
  - Lv18 Shroomish, Effect Spore, IVs 6: Tackle / Stun Spore / Leech Seed / Mega Drain (default)
  - Lv18 Numel, Oblivious, IVs 6: Growl / Tackle / Ember (default)
  - Lv20 Marshtomp, Torrent, IVs 12: Water Gun / Bide / Mud Shot / Foresight (default)
  - Brendan: `TRAINER_BRENDAN_8` (#527), same team

*Player chose Mudkip:* May and Brendan differ (lead order).
- **Rival May** `TRAINER_MAY_2` (#530); bag: none
  - Lv18 Wailmer, Water Veil, IVs 6: Splash / Growl / Water Gun / Rollout (default)
  - Lv18 Numel, Oblivious, IVs 6: Growl / Tackle / Ember (default)
  - Lv20 Grovyle, Overgrow, IVs 12: Absorb / Quick Attack / Fury Cutter / Pursuit (default)
- **Rival Brendan** `TRAINER_BRENDAN_2` (#521); bag: none
  - Lv18 Numel, Oblivious, IVs 6: Growl / Tackle / Ember (default)
  - Lv18 Wailmer, Water Veil, IVs 6: Splash / Growl / Water Gun / Rollout (default)
  - Lv20 Grovyle, Overgrow, IVs 12: Absorb / Quick Attack / Fury Cutter / Pursuit (default)

### K-wally_mauville: Mauville City: Wally

- **Pokemon Trainer 3 Wally** `TRAINER_WALLY_2` (#656); bag: none
  - Lv16 Ralts, Synchronize, IVs 3: Growl / Confusion / Double Team / Teleport (default)

### K-gym3_wattson: Mauville Gym: Wattson

- **Leader Wattson** `TRAINER_WATTSON` (#267); bag: Super Potion, Super Potion
  - Lv22 Magnemite, Magnet Pull, IVs 24: Supersonic / Sonic Boom / Thunder Shock / Thunder Wave (custom)
  - Lv20 Voltorb, Soundproof, IVs 24: Rollout / Self Destruct / Spark / Sonic Boom (custom)
  - Lv23 Magneton, Magnet Pull, IVs 30: Supersonic / Sonic Boom / Shock Wave / Thunder Wave (custom)

### K-admin_mt_chimney: Mt. Chimney: Admin (Tabitha / Matt)

*Ruby:*
- **Magma Admin Tabitha** `TRAINER_TABITHA_2` (#597); bag: none
  - Lv20 Numel, Oblivious, IVs 6: Growl / Tackle / Ember / Magnitude (default)
  - Lv20 Poochyena, Run Away, IVs 6: Howl / Sand Attack / Bite / Odor Sleuth (default)
  - Lv20 Numel, Oblivious, IVs 6: Growl / Tackle / Ember / Magnitude (default)
*Sapphire:*
- **Aqua Admin Matt** `TRAINER_MATT_2` (#31); bag: none
  - Lv20 Carvanha, Rough Skin, IVs 6: Bite / Rage / Focus Energy / Scary Face (default)
  - Lv20 Poochyena, Run Away, IVs 6: Howl / Sand Attack / Bite / Odor Sleuth (default)
  - Lv20 Carvanha, Rough Skin, IVs 6: Bite / Rage / Focus Energy / Scary Face (default)

### K-leader_mt_chimney: Mt. Chimney: Leader (Maxie / Archie)

*Ruby:*
- **Magma Leader Maxie** `TRAINER_MAXIE_3` (#602); bag: Super Potion, Super Potion
  - Lv24 Mightyena, Intimidate, IVs 18: Sand Attack / Bite / Odor Sleuth / Roar (default)
  - Lv24 Golbat, Inner Focus, IVs 18: Supersonic / Astonish / Bite / Wing Attack (default)
  - Lv25 Camerupt, Magma Armor, IVs 18: Tackle / Ember / Magnitude / Focus Energy (default)
*Sapphire:*
- **Aqua Leader Archie** `TRAINER_ARCHIE_3` (#35); bag: Super Potion, Super Potion
  - Lv24 Mightyena, Intimidate, IVs 18: Sand Attack / Bite / Odor Sleuth / Roar (default)
  - Lv24 Golbat, Inner Focus, IVs 18: Supersonic / Astonish / Bite / Wing Attack (default)
  - Lv25 Sharpedo, Rough Skin, IVs 18: Rage / Focus Energy / Scary Face / Crunch (default)

### K-gym4_flannery: Lavaridge Gym: Flannery

- **Leader Flannery** `TRAINER_FLANNERY` (#268); bag: Hyper Potion, Hyper Potion
  - Lv26 Slugma, Magma Armor, IVs 24: Overheat / Smog / Light Screen / Sunny Day (custom)
  - Lv26 Slugma, Magma Armor, IVs 24: Flamethrower / Rock Slide / Light Screen / Sunny Day (custom)
  - Lv28 Torkoal, White Smoke, IVs 30: Overheat / Body Slam / Flail / Attract (custom)

### K-gym5_norman: Petalburg Gym: Norman

- **Leader Norman** `TRAINER_NORMAN` (#269); bag: Hyper Potion, Hyper Potion
  - Lv28 Slaking, Truant, IVs 24: Encore / Facade / Yawn / Faint Attack (custom)
  - Lv30 Vigoroth, Vital Spirit, IVs 24: Slash / Faint Attack / Facade / Encore (custom)
  - Lv31 Slaking, Truant, IVs 30: Focus Punch / Slack Off / Facade / Faint Attack (custom)

### K-admin_weather_institute: Weather Institute: Admin (Courtney / Shelly)

*Ruby:*
- **Magma Admin Courtney** `TRAINER_COURTNEY_1` (#599); bag: none
  - Lv28 Numel, Oblivious, IVs 6: Tackle / Ember / Magnitude / Focus Energy (default)
  - Lv28 Mightyena, Intimidate, IVs 6: Bite / Odor Sleuth / Roar / Swagger (default)
*Sapphire:*
- **Aqua Admin Shelly** `TRAINER_SHELLY_1` (#32); bag: none
  - Lv28 Carvanha, Rough Skin, IVs 6: Focus Energy / Scary Face / Crunch / Screech (default)
  - Lv28 Mightyena, Intimidate, IVs 6: Bite / Odor Sleuth / Roar / Swagger (default)

### K-rival3_route119: Route 119: Rival

*Player chose Treecko:* May and Brendan identical.
- **Rival May** `TRAINER_MAY_6` (#534); bag: none
  - Lv29 Wailmer, Water Veil, IVs 12: Rollout / Whirlpool / Astonish / Water Pulse (default)
  - Lv29 Shroomish, Effect Spore, IVs 12: Leech Seed / Mega Drain / Headbutt / Poison Powder (default)
  - Lv31 Combusken, Blaze, IVs 18: Double Kick / Peck / Sand Attack / Bulk Up (default)
  - Brendan: `TRAINER_BRENDAN_6` (#525), same team

*Player chose Torchic:* May and Brendan identical.
- **Rival May** `TRAINER_MAY_9` (#537); bag: none
  - Lv29 Shroomish, Effect Spore, IVs 12: Leech Seed / Mega Drain / Headbutt / Poison Powder (default)
  - Lv29 Numel, Oblivious, IVs 12: Ember / Magnitude / Focus Energy / Take Down (default)
  - Lv31 Marshtomp, Torrent, IVs 18: Mud Shot / Foresight / Mud Sport / Take Down (default)
  - Brendan: `TRAINER_BRENDAN_9` (#528), same team

*Player chose Mudkip:* May and Brendan identical.
- **Rival May** `TRAINER_MAY_3` (#531); bag: none
  - Lv29 Numel, Oblivious, IVs 12: Ember / Magnitude / Focus Energy / Take Down (default)
  - Lv29 Wailmer, Water Veil, IVs 12: Rollout / Whirlpool / Astonish / Water Pulse (default)
  - Lv31 Grovyle, Overgrow, IVs 18: Fury Cutter / Pursuit / Screech / Leaf Blade (default)
  - Brendan: `TRAINER_BRENDAN_3` (#522), same team

### K-gym6_winona: Fortree Gym: Winona

- **Leader Winona** `TRAINER_WINONA` (#270); bag: Hyper Potion, Hyper Potion
  - Lv31 Swellow, Guts, IVs 24: Quick Attack / Aerial Ace / Double Team / Endeavor (custom)
  - Lv30 Pelipper, Keen Eye, IVs 24: Water Gun / Supersonic / Protect / Aerial Ace (custom)
  - Lv32 Skarmory, Keen Eye, IVs 24: Sand Attack / Fury Attack / Steel Wing / Aerial Ace (custom)
  - Lv33 Altaria, Natural Cure, IVs 30: Earthquake / Dragon Breath / Dragon Dance / Aerial Ace (custom)

### K-rival4_lilycove: Lilycove City: Rival (optional)

*Player chose Treecko* (constants are named by the player's starter):
- **Rival May** `TRAINER_MAY_LILYCOVE_TREECKO` (#665); bag: none
  - Lv31 Swellow, Guts, IVs 18: Quick Attack / Wing Attack / Double Team / Endeavor (default)
  - Lv32 Wailmer, Water Veil, IVs 18: Whirlpool / Astonish / Water Pulse / Mist (default)
  - Lv32 Shroomish, Effect Spore, IVs 18: Leech Seed / Mega Drain / Headbutt / Poison Powder (default)
  - Lv34 Combusken, Blaze, IVs 24: Peck / Sand Attack / Bulk Up / Quick Attack (default)
  - Brendan: `TRAINER_BRENDAN_LILYCOVE_TREECKO` (#662), same team

*Player chose Torchic* (constants are named by the player's starter):
- **Rival May** `TRAINER_MAY_LILYCOVE_TORCHIC` (#666); bag: none
  - Lv31 Swellow, Guts, IVs 18: Quick Attack / Wing Attack / Double Team / Endeavor (default)
  - Lv32 Shroomish, Effect Spore, IVs 18: Leech Seed / Mega Drain / Headbutt / Poison Powder (default)
  - Lv32 Numel, Oblivious, IVs 18: Magnitude / Focus Energy / Take Down / Amnesia (default)
  - Lv34 Marshtomp, Torrent, IVs 24: Mud Shot / Foresight / Mud Sport / Take Down (default)
  - Brendan: `TRAINER_BRENDAN_LILYCOVE_TORCHIC` (#663), same team

*Player chose Mudkip* (constants are named by the player's starter):
- **Rival May** `TRAINER_MAY_LILYCOVE_MUDKIP` (#664); bag: none
  - Lv31 Swellow, Guts, IVs 18: Quick Attack / Wing Attack / Double Team / Endeavor (default)
  - Lv32 Numel, Oblivious, IVs 18: Magnitude / Focus Energy / Take Down / Amnesia (default)
  - Lv32 Wailmer, Water Veil, IVs 18: Whirlpool / Astonish / Water Pulse / Mist (default)
  - Lv34 Grovyle, Overgrow, IVs 24: Fury Cutter / Pursuit / Screech / Leaf Blade (default)
  - Brendan: `TRAINER_BRENDAN_LILYCOVE_MUDKIP` (#661), same team

### K-admin_hideout: Lilycove hideout: Admin (Tabitha / Matt)

*Ruby:*
- **Magma Admin Tabitha** `TRAINER_TABITHA_1` (#596); bag: Super Potion
  - Lv32 Numel, Oblivious, IVs 6: Magnitude / Focus Energy / Take Down / Amnesia (default)
  - Lv32 Mightyena, Intimidate, IVs 6: Odor Sleuth / Roar / Swagger / Scary Face (default)
  - Lv32 Camerupt, Magma Armor, IVs 6: Magnitude / Focus Energy / Take Down / Amnesia (default)
*Sapphire:*
- **Aqua Admin Matt** `TRAINER_MATT_1` (#30); bag: Super Potion
  - Lv32 Carvanha, Rough Skin, IVs 6: Scary Face / Crunch / Screech / Take Down (default)
  - Lv32 Mightyena, Intimidate, IVs 6: Odor Sleuth / Roar / Swagger / Scary Face (default)
  - Lv32 Sharpedo, Rough Skin, IVs 6: Focus Energy / Scary Face / Crunch / Screech (default)

### K-gym7_tate_liza: Mossdeep Gym: Tate & Liza

- **Leader Tate&Liza** (double) `TRAINER_TATE_AND_LIZA` (#271); bag: Hyper Potion, Hyper Potion, Hyper Potion, Hyper Potion
  - Lv42 Lunatone, Levitate, IVs 30: Light Screen / Psychic / Hypnosis / Calm Mind (custom)
  - Lv42 Solrock, Levitate, IVs 30: Sunny Day / Solar Beam / Psychic / Flamethrower (custom)

### K-admin_seafloor_cavern: Seafloor Cavern: Admin (Courtney / Shelly)

*Ruby:*
- **Magma Admin Courtney** `TRAINER_COURTNEY_2` (#600); bag: none
  - Lv38 Camerupt, Magma Armor, IVs 6: Take Down / Amnesia / Rock Slide / Earthquake (default)
  - Lv38 Mightyena, Intimidate, IVs 6: Roar / Swagger / Scary Face / Take Down (default)
*Sapphire:*
- **Aqua Admin Shelly** `TRAINER_SHELLY_2` (#33); bag: none
  - Lv38 Sharpedo, Rough Skin, IVs 6: Crunch / Screech / Slash / Taunt (default)
  - Lv38 Mightyena, Intimidate, IVs 6: Roar / Swagger / Scary Face / Take Down (default)

### K-leader_seafloor_cavern: Seafloor Cavern: Leader (Maxie / Archie)

*Ruby:*
- **Magma Leader Maxie** `TRAINER_MAXIE_2` (#601); bag: Super Potion, Super Potion
  - Lv41 Mightyena, Intimidate, IVs 18: Roar / Swagger / Scary Face / Take Down (default)
  - Lv41 Crobat, Inner Focus, IVs 18: Bite / Wing Attack / Confuse Ray / Air Cutter (default)
  - Lv43 Camerupt, Magma Armor, IVs 18: Take Down / Amnesia / Rock Slide / Earthquake (default)
*Sapphire:*
- **Aqua Leader Archie** `TRAINER_ARCHIE_2` (#34); bag: Super Potion, Super Potion
  - Lv41 Mightyena, Intimidate, IVs 18: Roar / Swagger / Scary Face / Take Down (default)
  - Lv41 Crobat, Inner Focus, IVs 18: Bite / Wing Attack / Confuse Ray / Air Cutter (default)
  - Lv43 Sharpedo, Rough Skin, IVs 18: Screech / Slash / Taunt / Swagger (default)

### K-gym8_wallace: Sootopolis Gym: Wallace

- **Leader Wallace** `TRAINER_WALLACE` (#272); bag: Hyper Potion, Hyper Potion
  - Lv40 Luvdisc, Swift Swim, IVs 24: Water Pulse / Attract / Sweet Kiss / Flail (custom)
  - Lv42 Whiscash, Oblivious, IVs 24: Rain Dance / Water Pulse / Amnesia / Earthquake (custom)
  - Lv40 Sealeo, Thick Fat, IVs 24: Encore / Body Slam / Aurora Beam / Water Pulse (custom)
  - Lv42 Seaking, Swift Swim, IVs 24: Water Pulse / Rain Dance / Fury Attack / Horn Drill (custom)
  - Lv43 Milotic, Marvel Scale, IVs 30: Water Pulse / Twister / Recover / Ice Beam (custom)

### K-wally_victory_road: Victory Road: Wally

- **Pokemon Trainer 3 Wally** `TRAINER_WALLY_1` (#519); bag: Super Potion, Super Potion
  - Lv44 Altaria, Natural Cure, IVs 18: Aerial Ace / Safeguard / Dragon Breath / Dragon Dance (custom)
  - Lv43 Delcatty, Cute Charm, IVs 18: Sing / Assist / Charm / Faint Attack (custom)
  - Lv44 Roselia, Natural Cure, IVs 18: Magical Leaf / Leech Seed / Giga Drain / Toxic (custom)
  - Lv41 Magneton, Magnet Pull, IVs 18: Supersonic / Thunderbolt / Tri Attack / Screech (custom)
  - Lv45 Gardevoir, Synchronize, IVs 30: Double Team / Calm Mind / Psychic / Future Sight (custom)

### K-e4_sidney: Elite Four: Sidney

- **Elite Four Sidney** `TRAINER_SIDNEY` (#261); bag: Full Restore, Full Restore
  - Lv46 Mightyena, Intimidate, IVs 30: Roar / Take Down / Sand Attack / Crunch (custom)
  - Lv48 Shiftry, Chlorophyll, IVs 30: Fake Out / Double Team / Swagger / Extrasensory (custom)
  - Lv46 Cacturne, Sand Veil, IVs 30: Leech Seed / Faint Attack / Needle Arm / Cotton Spore (custom)
  - Lv48 Sharpedo, Rough Skin, IVs 30: Crunch / Swagger / Surf / Slash (custom)
  - Lv49 Absol @ Sitrus Berry, Pressure, IVs 31: Aerial Ace / Snatch / Swords Dance / Slash (custom)

### K-e4_phoebe: Elite Four: Phoebe

- **Elite Four Phoebe** `TRAINER_PHOEBE` (#262); bag: Full Restore, Full Restore
  - Lv48 Dusclops, Pressure, IVs 30: Shadow Punch / Confuse Ray / Curse / Future Sight (custom)
  - Lv49 Banette, Insomnia, IVs 30: Shadow Ball / Spite / Will O Wisp / Faint Attack (custom)
  - Lv50 Sableye, Keen Eye, IVs 30: Shadow Ball / Psychic / Attract / Faint Attack (custom)
  - Lv49 Banette, Insomnia, IVs 30: Shadow Ball / Psychic / Toxic / Skill Swap (custom)
  - Lv51 Dusclops @ Sitrus Berry, Pressure, IVs 31: Shadow Ball / Ice Beam / Confuse Ray / Earthquake (custom)

### K-e4_glacia: Elite Four: Glacia

- **Elite Four Glacia** `TRAINER_GLACIA` (#263); bag: Full Restore, Full Restore
  - Lv50 Glalie, Inner Focus, IVs 30: Light Screen / Crunch / Hail / Ice Beam (custom)
  - Lv50 Sealeo, Thick Fat, IVs 30: Surf / Body Slam / Hail / Ice Ball (custom)
  - Lv52 Sealeo, Thick Fat, IVs 30: Attract / Dive / Hail / Blizzard (custom)
  - Lv52 Glalie, Inner Focus, IVs 30: Shadow Ball / Crunch / Hail / Ice Beam (custom)
  - Lv53 Walrein @ Sitrus Berry, Thick Fat, IVs 31: Surf / Body Slam / Blizzard / Sheer Cold (custom)

### K-e4_drake: Elite Four: Drake

- **Elite Four Drake** `TRAINER_DRAKE` (#264); bag: Full Restore, Full Restore
  - Lv52 Shelgon, Rock Head, IVs 30: Rock Tomb / Dragon Claw / Protect / Crunch (custom)
  - Lv54 Altaria, Natural Cure, IVs 30: Take Down / Dragon Breath / Dragon Dance / Refresh (custom)
  - Lv53 Flygon, Levitate, IVs 30: Dig / Dragon Breath / Fly / Sandstorm (custom)
  - Lv53 Flygon, Levitate, IVs 30: Flamethrower / Crunch / Dragon Breath / Sand Attack (custom)
  - Lv55 Salamence @ Sitrus Berry, Intimidate, IVs 31: Flamethrower / Dragon Claw / Fly / Crunch (custom)

### K-champion_steven: Champion: Steven

- **Champion Steven** `TRAINER_STEVEN` (#335); bag: Full Restore, Full Restore, Full Restore, Full Restore
  - Lv57 Skarmory, Keen Eye, IVs 31: Toxic / Aerial Ace / Spikes / Steel Wing (custom)
  - Lv55 Claydol, Levitate, IVs 31: Reflect / Light Screen / Ancient Power / Earthquake (custom)
  - Lv56 Aggron, Sturdy, IVs 31: Thunder / Earthquake / Solar Beam / Dragon Claw (custom)
  - Lv56 Cradily, Suction Cups, IVs 31: Giga Drain / Ancient Power / Sludge Bomb / Confuse Ray (custom)
  - Lv56 Armaldo, Battle Armor, IVs 31: Water Pulse / Ancient Power / Aerial Ace / Slash (custom)
  - Lv58 Metagross @ Sitrus Berry, Clear Body, IVs 31: Earthquake / Psychic / Meteor Mash / Hyper Beam (custom)

## 6. Wild encounters (L)

All tables are `[decomp]` (`src/data/wild_encounters.json`). PokeAPI matches them exactly (D-01).

- **L-01** **Version-exclusive wild species** (present in one version's tables only):
  - **Ruby**:
    - Seedot (Routes 102 and 114)
    - Nuzleaf and Zangoose (Route 114 only)
    - Mawile (Granite Cave B1F/B2F, Cave of Origin, Victory Road B2F)
    - Solrock (Meteor Falls)
    - Dusclops (Sky Pillar, postgame)
  - **Sapphire**:
    - Lotad (Routes 102 and 114)
    - Lombre and Seviper (Route 114 only)
    - Sableye (the same caves as Mawile)
    - Lunatone (Meteor Falls)
    - Banette (Sky Pillar, postgame)
  - "Exclusive" means absent from the other version's **normal** tables; see L-08 for outbreaks.
- **L-02** **Rate and level swaps** (both versions have the species, with different slots or levels). Ruby's common slots come first:
  - Fiery Path: Koffing vs Grimer
  - Route 110: Minun vs Plusle
  - Route 117: Illumise vs Volbeat
  - Mt. Pyre 4F–6F and summit: Duskull vs Shuppet
  - Jagged Pass: Ruby Lv18–19, Sapphire Lv20–21
  - Route 129's surfing Wailord: Ruby Lv35–40, Sapphire Lv25–30
  - Safari Zone SW Doduo: Ruby Lv25, Sapphire Lv27
- **L-03** **Differences from Emerald**, by map and method. `+` means present in that version but not in Emerald, `−` the reverse. 38 pairs differ; every other table shared with Emerald matches on species.

| Map | Method | Ruby vs Emerald | Sapphire vs Emerald |
|---|---|---|---|
| Cave Of Origin 1F | walk | +Mawile; −Sableye | same |
| Granite Cave B1F | walk | +Mawile; −Sableye | same |
| Granite Cave B2F | walk | +Mawile; −Sableye | same |
| Meteor Falls 1F 1R | surf | same | +Lunatone; −Solrock |
| Meteor Falls 1F 1R | walk | same | +Lunatone; −Solrock |
| Meteor Falls 1F 2R | surf | same | +Lunatone; −Solrock |
| Meteor Falls 1F 2R | walk | same | +Lunatone; −Solrock |
| Meteor Falls B1F 1R | surf | same | +Lunatone; −Solrock |
| Meteor Falls B1F 1R | walk | same | +Lunatone; −Solrock |
| Meteor Falls B1F 2R | surf | same | +Lunatone; −Solrock |
| Meteor Falls B1F 2R | walk | same | +Lunatone; −Solrock |
| Mt Pyre 1F | walk | +Duskull; −Shuppet | same |
| Mt Pyre 2F | walk | +Duskull; −Shuppet | same |
| Mt Pyre 3F | walk | +Duskull; −Shuppet | same |
| Mt Pyre Exterior | walk | +Duskull, +Meditite; −Shuppet | +Meditite |
| Petalburg Woods | walk | +Zigzagoon; −Poochyena | +Zigzagoon; −Poochyena |
| Route102 | surf | +Surskit; −Goldeen | +Surskit; −Goldeen |
| Route102 | walk | +Surskit; −Lotad | +Surskit; −Seedot |
| Route104 | walk | +Zigzagoon; −Marill, −Poochyena | +Zigzagoon; −Marill, −Poochyena |
| Route110 | walk | +Zigzagoon; −Poochyena | +Zigzagoon; −Poochyena |
| Route111 | surf | +Surskit; −Goldeen | +Surskit; −Goldeen |
| Route112 | walk | +Machop; −Marill | +Machop; −Marill |
| Route113 | walk | +Sandshrew; −Slugma | +Sandshrew; −Slugma |
| Route114 | surf | +Surskit; −Goldeen | +Surskit; −Goldeen |
| Route114 | walk | +Seedot, +Surskit, +Zangoose; −Lombre, −Lotad, −Seviper | +Surskit; −Nuzleaf |
| Route116 | walk | +Zigzagoon; −Abra, −Poochyena | +Zigzagoon; −Abra, −Poochyena |
| Route117 | surf | +Surskit; −Goldeen | +Surskit; −Goldeen |
| Route117 | walk | +Roselia, +Surskit, +Zigzagoon; −Poochyena, −Seedot | +Roselia, +Surskit, +Zigzagoon; −Poochyena, −Seedot |
| Route120 | surf | +Surskit; −Goldeen | +Surskit; −Goldeen |
| Route120 | walk | +Linoone, +Surskit, +Zigzagoon; −Mightyena, −Poochyena, −Seedot | +Linoone, +Surskit, +Zigzagoon; −Mightyena, −Poochyena, −Seedot |
| Route121 | walk | +Duskull, +Linoone, +Zigzagoon; −Mightyena, −Poochyena, −Shuppet | +Linoone, +Zigzagoon; −Mightyena, −Poochyena |
| Route123 | walk | +Duskull, +Linoone, +Zigzagoon; −Mightyena, −Poochyena, −Shuppet | +Linoone, +Zigzagoon; −Mightyena, −Poochyena |
| Sky Pillar 1F | walk | +Dusclops, +Mawile; −Banette, −Sableye | same |
| Sky Pillar 3F | walk | +Dusclops, +Mawile; −Banette, −Sableye | same |
| Sky Pillar 5F | walk | +Dusclops, +Mawile; −Banette, −Sableye | same |
| Sootopolis City | fishing | −Tentacool | same |
| Victory Road B1F | walk | +Medicham, +Meditite; −Mawile | +Medicham, +Meditite; −Mawile |
| Victory Road B2F | walk | +Medicham; −Sableye | +Medicham; −Mawile |

Ruby/Sapphire also have walk tables for Cave of Origin B1F, B2F and B3F (A-08).

- **L-04** Wild in Ruby/Sapphire but **not in Emerald** at all:
  - Surskit (surfing on Routes 102, 111, 114, 117, 120, plus grass on Routes 102, 114, 117, 120)
  - Roselia (Route 117)
  - Meditite (Mt. Pyre exterior, Victory Road)
  - Medicham (Victory Road)
  - Zangoose (Ruby)
  - Lunatone (Sapphire)
  - Dusclops (Ruby, postgame)
- **L-05** Wild in Emerald but **not in Ruby/Sapphire**:
  - Story-relevant: Mightyena (Emerald Routes 120/121/123), and Poochyena on the routes listed in L-03. Ruby/Sapphire have wild Poochyena only on Routes 101–103.
  - Others: Marill on Routes 104/112, Abra on Route 116, Slugma on Route 113, Goldeen where Ruby/Sapphire have Surskit.
  - Everything else is Emerald-only places: the Johto Safari expansion, Desert Underpass (Ditto), Artisan Cave (Smeargle), Altering Cave.
- **L-06** `[diff]` **Safari Zone map names differ.**
  - Ruby/Sapphire's four areas are `SAFARI_ZONE_NORTHWEST`, `_NORTHEAST`, `_SOUTHWEST` and `_SOUTHEAST`.
  - pokeemerald renamed `_NORTHEAST` to `_NORTH` and `_SOUTHEAST` to `_SOUTH`, and reused the old names for its postgame Johto expansion.
  - By content, Ruby/Sapphire's Safari Zone equals Emerald's base four areas.
  - Comparing by map id mixes them up.
- **L-07** `[decomp]` **Underwater maps.**
  - Ruby/Sapphire's dive maps are `MAP_UNDERWATER1`–`4`, under Routes 124, 126, 127 and 128 (the dive connections).
  - pokeruby's region-map constants for them read `MAPSEC_UNDERWATER_124`, `_125`, `_126`, `_127`, so for 2–4 the constant name is not the route above.
  - Only UNDERWATER1 and UNDERWATER2 (Routes 124 and 126) have wild (seaweed) tables, as in Emerald.
  - Routes 105, 125 and 129 have no dive spots in Ruby/Sapphire; Emerald added underwater maps there.
- **L-08** `[decomp]` **Mass outbreaks (swarms)** can add species to a route's grass for a while, after a TV report (`gPokeOutbreakSpeciesList`, `tv.c`). Added in round 2.
  - **Ruby/Sapphire's list**: Surskit on Route 102 (Lv3), Route 114 (Lv15), Route 117 (Lv15) and Route 120 (Lv28); Skitty on Route 116 (Lv15).
  - **Emerald's list**: Seedot on Routes 102, 117 and 120, Nuzleaf on Route 114, Skitty on Route 116.
  - Outbreak reports also travel by **record mixing** between Ruby, Sapphire and Emerald saves. So a Sapphire player can get an Emerald Seedot outbreak, and an Emerald player a Surskit one.
  - "Not in X" in L-01, L-04 and L-05 means not in X's normal tables. Outbreaks are random and can't be planned for, so the agent should mention them only as a possibility, not recommend relying on them.

## 7. Special encounters (SE)

- **SE-01** Starters: Treecko, Torchic or Mudkip at Lv5, from Birch's bag on Route 101.
- **SE-02** Wynaut egg from the old woman in Lavaridge (`giveegg SPECIES_WYNAUT`).
- **SE-03** Castform Lv25 @ Mystic Water, Weather Institute 2F, after the admin (P-14).
- **SE-04** Lileep or Anorith Lv20, revived at Devon Corp from the Route 111 fossil (X-12; one per save).
- **SE-05** Beldum Lv5, Steven's house, postgame (N-01).
- **SE-06** Statics, with the step after which each can be reached:

  | Species | Level | Where | Count | Reachable |
  |---|---|---|---|---|
  | Voltorb | 25 | New Mauville | 3 | Wattson gives the Basement Key once he leaves his gym after Norman; Surf |
  | Electrode | 30 | Lilycove hideout B1F | 2 | After E-04, both versions; **missable** after the Mind Badge (X-18) |
  | Kecleon | 30 | Route 119 ×2, Route 120 ×6 | 8 | Devon Scope, from Steven on Route 120 |
  | Regirock, Regice, Registeel | 40 | Desert Ruins, Island Cave, Ancient Tomb | 1 each | After Dive (A-07), puzzles per X-14 |
  | Groudon (R) / Kyogre (S) | 45 | Cave of Origin B4F | 1 | Required at P-22 (X-08) |
  | Rayquaza | 70 | Sky Pillar top | 1 | Postgame (X-10) |
  | Latias (R) / Latios (S) | 50 | Southern Island | 1 | Event only (Eon Ticket) |

  Fortree's Kecleon (the one blocking the gym) flees when revealed and can't be battled.
- **SE-07** In-game trades: see X-15.
- **SE-08** Roamer: see X-16. It needs E-10 (the home TV report), not only the Hall of Fame.
- **SE-09** Feebas (C-11). Mirage Island has only Wynaut, as in Emerald.
- **SE-10** `[diff]` **Gifts need a free party slot** (new in draft 5).
  - In Ruby/Sapphire, Castform (`Route119_WeatherInstitute_2F`) and the revived fossil (`RustboroCity_DevonCorp_2F`) are handed over only if you have fewer than six Pokémon. Their scripts check `getpartysize` and send nothing to the PC; talk to the giver again with room.
  - Emerald's `givemon` sends them to the PC (`MON_GIVEN_TO_PC`).
  - The Wynaut egg needs room in all three games. The progression notes for the Weather Institute and the desert now say this.

## 8. TM/HM sources (TM)

- **TM-01** `[diff]` All 58 TM/HM labels have sources, with 66 source rows: item balls, hidden items, gifts, marts (Slateport, Lilycove Department Store 4F) and the Mauville Game Corner (TM32, TM29, TM35, TM24, TM13). They match Emerald's reviewed `tm_locations` table row for row, except:

  | Label | Ruby/Sapphire source | Emerald source |
  |---|---|---|
  | HM07 Waterfall | item ball, Cave of Origin B3F (X-09) | gift in Sootopolis |
  | HM08 Dive | gift from Steven in Mossdeep. A fallback item ball in the same house is hidden at new game (`new_game.inc`) and shown only after the Hall of Fame if the gift was never taken (`hall_of_fame.inc`, `ShowHM08`), so it's postgame (corrected in round 2) | gift |
  | TM27 Return | gift in `FallarborTown_House1` (Prof. Cozmo, after the Meteorite) | `FallarborTown_CozmosHouse`: the same NPC, renamed map |
  | TM41 Torment | gift in the Slateport Contest Hall, no condition | Slateport Battle Tent lobby |
  | TM45 Attract | gift in the Verdanturf Contest Lobby, no condition | Verdanturf Battle Tent lobby |
- **TM-02** `[decomp]` Emerald's hand-checked gates (its D1/D7) hold in pokeruby's scripts:
  - TM10 and TM43 from Slateport's salesman only after Route 111's Secret Power gift (`secret_power_tm.inc` clears `FLAG_HIDE_TM_SALESMAN_SLATEPORT`)
  - TM21 and TM27 in Pacifidlog weekly by friendship (`FLAG_RECEIVED_FANCLUB_TM_THIS_WEEK`, `GetLeadMonFriendshipScore`)
  - TM19 needs a Grass-type in the party (`IsGrassTypeInParty`)
  - TM13 needs the Storage Key (`FLAG_USED_STORAGE_KEY`)
  - TM24 comes from Wattson after New Mauville
  - The item-ball gates (TM02 Waterfall, TM06 Strength, TM07 low tide, TM11 and TM18 Surf/Dive, TM26 Seafloor Cavern) are the same maps.
  - TM49 is postgame.
- **TM-03** `[decomp]` **Sootopolis's TMs come after P-22**: TM31 Brick Break (`SootopolisCity_House1`) and Wallace's TM03 Water Pulse, because the city's doors stay shut until the legendary battle (X-08).
- **TM-04** No move tutors (X-01).

## 9. Randomizer log format (Universal Pokémon Randomizer ZX)

From UPR ZX's source (master `7f00eb8`, `Gen3RomHandler.java`, `Randomizer.java`, `gen3_offsets.ini`). No real Ruby/Sapphire log has been run. The Emerald packet's R-01 to R-09 apply except:

- **R-10** Ruby and Sapphire use the same Gen 3 handler as Emerald (ini sections `Ruby (U)`, `Sapphire (U)`; CRC32 `F0815EE7` and `554DEDC4`).
  - Section names, line formats, wild-set numbering in ROM header order, starter order and TM lines are shared code.
- **R-11** Trainers are **#1–#693** (`TrainerCount=0x2B6`, inherited by Sapphire via `CopyFrom`). There's **no partner pseudo-trainer**: Steven's Space Center entry is added only when `romType == RomType_Em` (`getTrainers`).
- **R-12** Wild sets: 179 per version (68 grass, 54 surfing, 5 Rock Smash, 52 fishing) in ROM header order.
  - No two Ruby/Sapphire tables share a data pointer, so none should be skipped. `[inferred]` from the decomp.
- **R-13** **Town and city names in wild-set labels may print oddly.** pokeruby's region-map names embed a `{NAME_END}` control code ("PETALBURG{NAME_END} CITY"); Emerald's are plain. Given UPR's `readString` and its character table, the label likely prints as `PETALBURG\c  CITY`. `[inferred]` This affects 8 places: Petalburg, Slateport, Lilycove, Mossdeep, Sootopolis, Ever Grande, Dewford and Pacifidlog.
- **R-14** `--Static Pokemon--` has 20 lines for Ruby/Sapphire (Emerald 26):
  - Ruby: Lileep, Anorith, **Groudon**, the three Regis, **Latias** (Southern Island), Rayquaza, the Kecleon, Voltorb ×3, Electrode ×2, the Wynaut egg, Beldum and Castform, then the first-battle **Poochyena** (Birch's rescue, Lv2: `CreateMon(..., SPECIES_POOCHYENA, 2, ...)` in `battle_controllers.c`; UPR patches it through `StaticFirstBattleTweak=hardcoded_statics/rs_firstbattle`), then the **roamer (Latios)** on its own line. Emerald's first battle is Zigzagoon; draft 2 had that by mistake.
  - Sapphire swaps in Kyogre and Southern Island Latios, with a Latias roamer.
- **R-15** **No tutor section** and no "Move Tutor Moves" status line (`hasMoveTutors()` is false for R/S).
- **R-16** The game is named only in the footer, `Randomization of Ruby (U) completed.`, between two 66-dash lines, and by the ROM CRC32 under `--ROM Diagnostics--`. A parser has to detect the game from these.
- **R-17** **ROM identity** (added in round 1).
  - Record the game, region and revision a log came from, and whether its parse succeeded.
  - The CRC32s in R-10 are revision 0's. A later revision has a different CRC but, per Q-01, the same game data.
  - A CRC the parser doesn't recognise should produce a warning, not a silent "rev 0".
  - R-12 to R-14 stay predictions until Ruby and Sapphire spoiler-log fixtures confirm them. Fixtures should cover: wild-set count and first/last map, trainer count, the version's villain teams, the static list (grouped Kecleon, the legendary, the roamer line) and town-name rendering.

## 10. Data findings (D)

From comparing PokeAPI's Ruby (version 7) and Sapphire (version 8) rows, version group 5, with pokeruby. Maps were matched to PokeAPI locations by region-map-section index.

- **D-01** **PokeAPI's Ruby/Sapphire wild data is correct.** In each version, all 283 decomp tables match a PokeAPI area slot for slot (species, levels, rarities). The 37 tables that differ between the versions are filed under the right version.
- **D-02** **Static rows with errors:**
  - Ruby: New Mauville has 6 Voltorb rows where the ROM has 3 (duplicates), plus 2 Electrode rows that belong in the hideout; the correct hideout pair is also present.
  - Sapphire: 2 Electrode rows sit at `team-magma-hideout`, the wrong version's hideout; the correct Aqua pair is also present.
  - Emerald had the same kinds of error (Emerald data finding 3).
- **D-03** **Roamer conditions are inverted.** PokeAPI puts the Hall of Fame condition on the roaming-*water* rows only, the reverse of Emerald (Emerald data finding 11). Both rows should carry it. Ruby/Sapphire have no color choice. The Hall of Fame is still not enough: the roamer starts only after the TV report at home (E-10), so PokeAPI's Hall of Fame condition is necessary but not sufficient.
- **D-04** **Friendship threshold**: PokeAPI shows 160 on 8 rows; the ROM uses 220 (C-07). This is Emerald data finding 10 again. pokeruby hard-codes 220 rather than using Emerald's `FRIENDSHIP_EVO_THRESHOLD` constant.
- **D-05** PokeAPI's learnsets for version group 5 are correct:
  - level-up rows match all 386 species, with Deoxys filed under `deoxys-normal`
  - the 58 machine rows and all compatibility match
  - there are no tutor rows
  - egg moves (979 rows) match, plus extra rows on Castform's alternate forms
- **D-06** **Location-mapping traps** for a build written for Emerald:
  - Region-map index 66 lists both `team-aqua-hideout` and `team-magma-hideout`; Ruby needs the Magma one, Sapphire the Aqua one (X-11).
  - Index 51 is `MAPSEC_UNDERWATER_125` in pokeruby, but PokeAPI files that map as Route 126 underwater (L-07).
  - Index 58 lists both the Battle Tower and the Battle Frontier.
  - Keeping only areas with Emerald encounters drops `cave-of-origin/b4f` (the Groudon/Kyogre static).
- **D-07** `[decomp]` PokeAPI lists in-game trade levels as ranges (5–100; Corsola 21–100). The ROM gives the received Pokémon the level of the one you hand over: `trade.c` reads the player's Pokémon's `MON_DATA_LEVEL` and passes it to `CreateMon`. The reviewer confirmed this from Bulbapedia.
- **D-08** `[decomp]` **Pitfalls in the decomp for extraction:**
  - `data/item_ball_scripts.inc` has an unlabeled `finditem ITEM_HM08_DIVE` block that no object uses (a naive label parser attaches it to Victory Road B2F's ball).
  - **An attached item ball isn't necessarily obtainable.** Steven's house has a Dive item ball whose object flag starts set at new game and is cleared only by a postgame script (TM-01). A build should check every item-ball and gift source against its object flag's initial value (`new_game.inc`) and every script that changes it, not just against the script attached to the object. Added in round 2.
  - `data/scripts/debug.inc` gives Lv99 Barboach and Shroomish; these must be excluded.
  - The two hideouts share scripts via double labels, so their trainers appear once, under `AquaHideout_*`.
  - Villain trainers appear only through the aliases in `constants/version.inc` (section 1).
  - **Two branch syntaxes** (added in draft 4). pokeruby writes variable branches as `compare VAR, VALUE` followed by a one-argument `goto_if_eq LABEL` (about 1,200 one-argument branches in map scripts); pokeemerald writes `goto_if_eq VAR, VALUE, LABEL`. A parser written for one misses the other's conditions. Draft 4's first gate pass did, and it was re-run (section 12, V-04).
  - **`removeobject` hides an object for good** by setting the object's own flag (`RemoveObjectEventByLocalIdAndMap` calls `FlagSet`, `event_object_movement.c` in both decomps), with no `setflag` in the script. Draft 4's first blocker pass searched only for `setflag` and missed blockers removed this way, e.g. Emerald's Route 120 Kecleon. The chokepoint pass (V-02) counts both.

## 11. Open questions

Answered in round 1 and folded into the claims:
- **Q-01** Revisions 1 and 2 don't change the game data in this packet.
  - The reviewer cites Bulbapedia's version history: 1.1 fixes non-English names on evolution, 1.2 is the Berry Program Update.
  - The decomp agrees: pokeruby's `REVISION` conditionals appear only in graphics, Pokédex text, fonts, strings, TV/cable-club text and decoration code, never in trainer, wild, item or map-script data. See R-17.
- **Q-02** There's no single Nuzlocke convention for the forced legendary; see P-22's three facts.
- **Q-03** No missed story battles:
  - Route 112's cable-car grunts don't battle (E-01).
  - Meteor Falls is a cutscene.
  - Mt. Chimney is grunt, admin, leader, as listed.
- **Q-04** No: Sky Pillar is postgame (X-10 confirmed).
- **Q-05** Confirmed (X-11). The hideouts differ in layout and in the version's villain team; both have two Lv30 Electrode.
- **Q-07** Answered with the navigation gates in X-14.

Answered in draft 4:
- **Q-08** A-01: besides the E-table events, are there other event-script gates where Ruby/Sapphire differ from Emerald on the same map? **No; see section 12.** That section is a mechanical comparison, per shared map, of reachability, story blockers on chokepoints, step triggers, conditional map changes and the engine rules behind them. Every difference is an Emerald-only beat or a gate already in this packet. It also turned up one fact that holds in all three games (V-14).

Answered in round 3 (draft 5):
- **Q-10** (raised and answered in draft 5) `[diff]` Does any encounter's activation script differ from Emerald, the way E-10 does?
  - **Method:** every script in pokeruby that starts an encounter was compared with its Emerald counterpart: `setwildbattle`, `givemon`, `giveegg` and `InitRoamer`. There are 16 outside the debug scripts. The flags and items checked before each one were compared too.
  - **The same in both games:**
    - the Regis, behind the puzzles (X-14)
    - New Mauville's three Voltorb: Wattson stands in Mauville from Norman's gym onward in both, and gives the Basement Key
    - the eight Kecleon, which need the Devon Scope (`checkitem ITEM_DEVON_SCOPE`)
    - the hideout's two Electrode
    - the Wynaut egg, which needs a free party slot in both games
    - Beldum and Rayquaza, both postgame in Ruby/Sapphire
    - Southern Island (an event)
  - **Differences:**
    - the roamer (E-10)
    - the forced legendary (X-08)
    - **gifts with a full party** (new, SE-10)

  Emerald-only encounters (Sudowoodo, the Johto starters, the Pichu egg, Terra and Marine Cave) have no Ruby/Sapphire counterpart.
- **Q-09** Section 12's geography held up. The reviewer found no area or path that opens at a different point. It did find an encounter-activation step that section 12 doesn't look at: the roaming Lati's TV report (E-10). Its point that areas also close led to CL and the closing logic (P-R6).

Still open:
- **Q-06** R-13: if you've seen a real Ruby or Sapphire UPR log, how do town names print in wild-set labels?
- **Q-01 follow-up** (round 2): the `REVISION` audit supports Q-01. The full guarantee is a hash comparison of the extracted trainer, wild, item and event tables built for revisions 0, 1 and 2. Not done: it needs the three revisions built, with pret's agbcc toolchain (not installed here), or dumped from cartridges.
- **Q-11** (new) Are there other places in Ruby or Sapphire that close for good before the Champion, besides CL-01 and CL-02? Draft 5 found none in section 12's map-change list (V-09).

## 12. Area-unlock verification (V), new in draft 4

This answers Q-08: does Ruby or Sapphire open any area at a different story point from Emerald, beyond what sections 3 and 4 already say? Claims are `[diff]` unless marked.

Scratch scripts compared pret/pokeruby `5784633ce4ef` with pret/pokeemerald `731ad5bfd6e6` over the 348 map ids both games have. pokeruby was read once as Ruby and once as Sapphire, with `.ifdef SAPPHIRE` blocks resolved. The scripts aren't part of the repo.

- **V-00 Result.**
  - Every difference in when an area opens is either an Emerald-only story beat (P-R2, X-17) or a Ruby/Sapphire gate already listed (X-08, X-10, X-11, X-18, E-01 to E-09).
  - **Ruby and Sapphire have identical gates** (V-13).
  - No change to section 4's story order or area unlocks was needed. `data/progression_rs.yaml` changed only in one note (V-14).
  - Two engine-level differences turned up, both Emerald-only (V-11): Sootopolis's water encounters are blocked during Emerald's crisis, and Emerald alone has the encounter abilities (Synchronize and others).
  - One new fact applies to all three games (V-14).
  - **Scope (narrowed in draft 5):** this checks where the player can move and what blocks them. It doesn't check every script that starts an encounter. Round 3 found one such step, the Lati TV report (E-10), and areas that close again (CL).

### What was compared

- **V-01 Reachability per map.**
  - **Tile data.** Each layout block gives a metatile, collision and elevation. Metatile behaviors come from each game's tileset attribute files, and the encounter and surfable bits from `sTileBitAttributes`.
  - **Flood fill.** From every entrance (each warp tile, and each map edge with a connection), a flood fill runs under six sets of field abilities:
    - none
    - Cut
    - plus Rock Smash and both bikes
    - plus Strength
    - plus Surf
    - plus Waterfall
  - **Recorded:** which exits are reached, and whether walkable encounter tiles, surfable water and fishable water are reached.
  - **Movement rules,** taken from the engine and the same in both games (V-10):
    - Collision blocks, except that a ledge is jumped (two tiles, in its arrow direction only) before collision is applied, as `ShouldJumpLedge` does.
    - An elevation mismatch blocks: the player's elevation is nonzero, the tile's isn't 0 or 15, and they differ. Stepping onto elevation 0 resets the player's elevation; 15 keeps it (`ObjectEventUpdateElevation`).
    - Bike-only tiles (muddy slopes, cracked floors, rails, bumpy slopes) need a bike.
    - **Surf** starts only from elevation-3 land, facing water that has no collision and a different elevation (`IsPlayerFacingSurfableFishableWater`). It ends only onto an elevation-3 tile with no object (`CanStopSurfing`). Fishing from land uses the same test as starting Surf (`CanFish`). Arriving by a warp onto water starts you surfing.
    - Waterfalls are climbed only with Waterfall; going down one needs nothing.
    - **Animated doors** are solid tiles entered by moving north into them (`TryDoorWarp`), so a door counts as an exit when the tile below it is reached.
  - **The rules above are the corrected model.** Draft 4's first run missed door exits and allowed surfing at any elevation. The re-run with the engine's rules found about 200 more door exits per game and the same 9 differing maps (V-06).
  - **Obstacles:** Cut trees, Rock Smash rocks and Strength boulders need their move. Other NPCs are left to V-02.
  - **Ignored:** exits to maps only one game has.
- **V-02 Story blockers on chokepoints.**
  - **Candidates:** every object visible at a new game (its flag isn't set by `new_game.inc`), except item balls and field-move obstacles. That includes objects removed by `setflag`, objects removed by `removeobject` (D-08) and objects that never leave.
  - **Test:** objects that share a hide flag are walled off together, and the rest one at a time. A candidate is a chokepoint if walling it costs any entrance an exit, grass or water, even with every field ability.
  - **Matching:** chokepoints are matched across games by map and tiles, and for each match the scripts that remove it were compared.
  - **The rest:** 476 `setflag`-removed blockers stand on the same tile in both games, and 451 of them are removed by a script in the same map. The other 25 are:
    - Mt. Chimney's scene (22) and Meteor Falls' Cozmo, which Ruby/Sapphire run from the shared `magma_chimney.inc` and Emerald from `MtChimney`
    - two that a truncated name in the comparison's output hid: the Lilycove rooftop sale woman and the Oceanic Museum 1F grunt. Both are hidden by their own map's script in both games.
- **V-03 Step triggers.** Every coordinate trigger on a story variable whose tile is in only one game, with its script read.
- **V-04 Conditional map changes.** For every conditional branch in a map's scripts, the target label was checked for:
  - metatile changes
  - layout swaps
  - permanent NPC moves (`setobjectxyperm`)
  - warp changes

  The two games' sets were then compared. Both branch syntaxes are read (D-08). The first pass read only pokeemerald's three-argument form and missed pokeruby's `compare` plus one-argument branches, so it was re-run. The re-run found no new difference, and it confirmed that New Mauville's door (Basement Key, 6 tiles) and Sootopolis's gym puzzle match.
- **V-05 Engine code.** The C rules that the model above assumes, and the engine-level gates map data doesn't show: V-10 and V-11.

### Results

- **V-06 Reachability.** 127 of the 348 shared maps have some differing blocks, but only **9** differ in what is reachable from some entrance under some set of field abilities:

| Map | Difference | Why it doesn't change any unlock |
|---|---|---|
| Jagged Pass | Emerald reaches the Magma Hideout entrance | Emerald-only place (X-17) |
| Mossdeep Game Corner 1F | Ruby/Sapphire reach a B1F room that Emerald walls off | the room has no encounters or items, only one object with no script |
| Mossdeep Gym | puzzle layout | gym interior |
| Trick House Puzzle 7 | puzzle layout | no encounters |
| Route 115 | Emerald has a few walkable tiles at the east edge (the Route 114 connection) that lead nowhere | a dead end |
| Route 121 Safari Zone entrance, Safari Zone Southeast | map renames: Ruby/Sapphire's "Southeast" is Emerald's "South", and Emerald's "Southeast" is its postgame expansion | matched by role, the only difference is Emerald's connection to the expansion (L-06, X-17) |
| Seafloor Cavern Room 3 | without Strength, Ruby/Sapphire's three entrances don't connect to each other | with Strength they do, as in Emerald, and Strength is usable from the Heat Badge, long before Dive |
| Sky Pillar, outside | Ruby/Sapphire's door is open in the layout; Emerald opens it by script | Sky Pillar is postgame in Ruby/Sapphire (X-10) |

- **V-07 Story blockers on chokepoints.** 14 groups in Ruby/Sapphire, 20 in Emerald (corrected model, V-01).

**In both games, on the same tile, removed by the same script.** Where it matters, the condition was compared line by line.

| Map (tile) | Blocker | Leaves when |
|---|---|---|
| Route 110 (7–10, 83), (8, 82) | villain grunt line | the Oceanic Museum battle (E-02) |
| Route 112 (26–27, 30) | two grunts at the cable car | the Meteor Falls scene (E-01) |
| Slateport (20–31, 26–27) | villain queue: 8 tiles, 11 in Emerald | you talk to Dock in Stern's Shipyard; the same `FLAG_DOCK_REJECTED_DEVON_GOODS` branch in both |
| Route 116 (38, 9) | Black Belt at the Tunnelers' Rest House | the same Devon Corp 3F script in both |
| Mauville (8, 6) | Wally at the gym door | after his battle (X-07) |
| Route 111 (13, 114) | Victor Winstrate | Route 111's own script (`removeobject`) |
| Route 120 (20, 11) | Kecleon on the way to the Scorched Slab | Devon Scope. Draft 4's first pass listed it as Ruby/Sapphire-only because Emerald removes it with `removeobject` (D-08) |
| Fortree (25, 8) | Kecleon in front of the gym | Devon Scope |
| Lilycove (27, 7) | the rival, below the Department Store door | after the battle, not after declining (V-14) |
| Lilycove Museum 1F (16, 2) | the curator | the same Contest Lobby and museum scripts |
| Safari Zone (32, 34) | a camper who never moves (the map is "Southeast" in Ruby/Sapphire, "South" in Emerald) | never, in both games |
| the hideout's B2F | grunts, walled off together as one group | Ruby/Sapphire: never, since the entrance is walled off at the Mind Badge (X-18); Emerald hides its grunts at the Mind Badge |

**Emerald only:**
- the Jagged Pass guard
- the Magma Hideout 4F
- Team Aqua at Mt. Pyre's summit (Emerald's scene)
- the grunt at Seafloor Cavern's entrance, gone once Steven gives Dive, which you need to get there anyway
- the Safari Zone construction workers (postgame expansion)
- a Trick House statue
- the Battle Frontier's lobby NPC (Ruby/Sapphire's Battle Tower has the same NPC)

**Same gate, placed differently:**
- The Expert at (31, 18) blocks the Cave of Origin until the Seafloor Cavern leader (E-07).
- Emerald puts him there in its map data.
- Ruby/Sapphire move him there by script while `FLAG_LEGEND_ESCAPED_SEAFLOOR_CAVERN` is unset (`SootopolisCity_EventScript_ExpertBlockCaveOfOrigin`).
- **V-08 Step triggers in one game only.** All of them start scenes; none pushes the player back or blocks a path.
  - **Emerald only:**
    - the Littleroot rival introduction
    - Scott in Petalburg and outside Slateport's Battle Tent
    - Birch's PokéNav call on Route 110
    - the Rustboro and Route 104 rival battle (P-R2)
    - the Mt. Pyre summit, Jagged Pass and Mossdeep Space Center scenes
    - Route 114's Fossil Maniac tunnel
    - the top of Sky Pillar
  - **Ruby/Sapphire only:**
    - Steven leading you to Wallace in Sootopolis, at (25, 6)
    - the screen shakes in Cave of Origin 1F and B1F
  - **Same trigger, different tile:**
    - Wally at Victory Road 1F: (34, 3–5) in Ruby/Sapphire, (2–3, 23) in Emerald
    - the Mauville and Mossdeep gym puzzles
- **V-09 Conditional map changes that differ.**
  - **Ruby/Sapphire only:**
    - Lilycove's hideout entrance is walled off at the Mind Badge (X-18).
    - Route 131 switches to the Sky Pillar layout after the Hall of Fame (X-10).
    - Sootopolis's doors stay shut until `FLAG_LEGENDARY_BATTLE_COMPLETED` (X-08). Emerald shuts the same 9 tiles until `FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE`.
    - NPC placements in Lavaridge, Littleroot, Petalburg Gym, Mossdeep Game Corner and the Safari Zone, none of them a gate.
  - **Emerald only:**
    - the Jagged Pass hideout, Mirage Tower, Sky Pillar and the Space Center
    - Sootopolis's legends-battle layout
    - postgame changes in Meteor Falls, Route 103, Route 114's tunnel and Birch's lab
  - **The same in both:**
    - the Wailmer east of Lilycove (12 tiles, cleared with the hideout, E-05)
    - Shoal Cave's tides
    - Mirage Island's layout swap on Route 130
    - the Sealed Chamber's dive warp
    - New Mauville's door
    - Route 120's tiles after the Devon Scope
    - the Regi doors
    - the Abandoned Ship's key doors
    - the Mauville gym barriers (25 tiles vs 26, a puzzle detail)
- **V-10 Engine: movement and field moves.** `[decomp]`
  - **The movement engine is the same in both games.** The function bodies were compared, not just the names. Emerald's `BUGFIX` and Ruby/Sapphire's `DEBUG` branches were left out, since neither ships.
    - **The same in both:**
      - the elevation-mismatch test
      - the collision order in `GetCollisionAtCoords`
      - directional impassable tiles
      - ledges (`GetLedgeJumpDirection`)
      - every forced-movement tile: ice, arrows, currents, waterfalls pushing south, muddy slopes
      - object collision
      - map-edge handling
    - **Surfing:** starting and stopping (V-01) and the surfable bit for all 240 behavior values.
    - **Dive:** `TrySetDiveWarp`, emerge or dive connection first, then the map's fixed dive warp. The no-surfacing tiles are 0x19 and 0x2A in both.
    - **Waterfall:** you climb it while surfing north with the move.
    - **Bikes:** `bike.c` differs only in names, plus an Emerald check for Faraway Island's Mew. That covers Mach Bike slopes and cracked floors, and Acro Bike rails, side jumps, hops and bumpy slopes.
  - **Metatile behaviors** have the same numbers, 0x00–0xEF, in both games. Every predicate the model uses has the same body once constants are resolved. The only extra predicates are Emerald's bridge types 0x7A–0x7F, used for encounters under bridges, battle backgrounds, reflections and the Itemfinder, not for movement.
  - **Field-move conditions in C** are the same for Cut, Rock Smash, Strength (boulder pushing), Flash, Waterfall and Dive. Emerald's Hyper Cutter only widens Cut's grass area.
  - **Fly and Teleport** use the same map-type test. Escape Rope and Dig differ in how they're decided (V-11). The Sealed Chamber and the three Regi caves are underground maps in both games, so Dig works there in Ruby/Sapphire.
  - **Warp tiles.** Emerald's `IsWarpMetatileBehavior` also fires on 0x0E (Mossdeep Gym warp pads) and 0x70 (Union Room). No Ruby/Sapphire warp sits on either behavior, so nothing changes.
  - **Rotating gates are hard-coded in C**, so the map comparison can't see them (`rotating_gate.c`):
    - Fortree Gym has 7 gates in Ruby/Sapphire and 8 in Emerald.
    - Trick House puzzle 6 has 14 and 11.
    - The gate logic is the same. Both are puzzles you solve in place; neither changes what the story opens.
  - **Regi puzzles** are as X-14 says.
- **V-11 Engine: map headers, Fly, timed gates and the encounter engine.** `[decomp]`
  - **Bike, Escape Rope, Dig and running permissions are decided differently, but agree wherever they matter.**
    - **Ruby/Sapphire** have no per-map permission bits.
      - Biking (`Overworld_IsBikingAllowed`, `overworld.c`) is always allowed in the Cycling Road gatehouses. Elsewhere it's banned on indoor, secret-base and underwater maps and in two hardcoded rooms, Seafloor Cavern Room 9 and Cave of Origin B4F, and allowed everywhere else.
      - Escape Rope and Dig need an underground map type.
      - Running is off indoors.
    - **Emerald** reads `allow_cycling`, `allow_escaping` and `allow_running` from each map header.
    - **Where cycling differs** among the 348 shared maps, no bike is needed:
      - Sky Pillar's top
      - Cave of Origin B1F
      - the unused Route 104 prototype
      - underwater maps, where you can't ride anyway
      - `MAGMA_HIDEOUT_1F`, which is a different place in each game (X-11)
    - **Every map where a bike matters has the same values:** Granite Cave, Jagged Pass, Mt. Pyre, the Cycling Road, Route 119, the Safari Zone, Sky Pillar 1F–5F, Meteor Falls and Victory Road.
  - **Map types** match apart from names (`MAP_TYPE_6` is `MAP_TYPE_OCEAN_ROUTE`) and `MAGMA_HIDEOUT_1F`. Fly and Teleport use the same map-type test in both.
  - **Darkness.** Cave of Origin 1F and B1F are dark (Flash helps you see) in Ruby/Sapphire only. Darkness doesn't block movement.
  - **Route 111's sandstorm** is a script in both: a coordinate trigger runs `checkitem ITEM_GO_GOGGLES` and turns you back without them, on the same tiles.
  - **Fly destinations.**
    - Towns open by `FLAG_VISITED_*`, with the same heal locations in both.
    - Southern Island is never a Fly target.
    - The Pokémon League sub-destination uses the same system flag in both, set on entering the League building.
    - Only the postgame special target differs: the Battle Tower vs the Battle Frontier.
  - **Timed gates.**
    - Shoal Cave's tide table is identical (`time_events.c`): high tide 00–02, 09–14 and 21–23, low tide 03–08 and 15–20.
    - Mirage Island's rule is identical too: it appears when a party Pokémon's personality (low 16 bits) matches the daily Mirage value (high 16 bits).
  - **Regi puzzles** differ exactly as X-14 says (`braille_puzzles.c`).
  - **The wild-encounter engine** is the same for Feebas (C-11), roamers (X-16), the Safari Zone (30 balls, 500 steps), Repel, the flutes and the Cleanse Tag.
    - **One encounter gate is Emerald-only.** Emerald blocks Sootopolis's surfing and Sweet Scent water encounters while `FLAG_LEGENDARIES_IN_SOOTOPOLIS` is set (`AreLegendariesInSootopolisPreventingEncounters`, `wild_encounter.c`). That runs from the Seafloor Cavern leader until the crisis ends. Ruby/Sapphire have no such check, so Sootopolis's water encounters stay available during their crisis. Fishing isn't blocked in either game. Emerald's story file now notes this on the Archie step.
    - **Encounter abilities:** Ruby/Sapphire's `wild_encounter.c` knows only **Stench and Illuminate**. Emerald adds Synchronize and Cute Charm (wild nature and gender), Magnet Pull and Static (type bias), Keen Eye and Intimidate (low levels filtered), Hustle, Vital Spirit and Pressure (higher levels), Arena Trap, Sand Veil and White Smoke (encounter rate), and Suction Cups and Sticky Hold (fishing). They change odds, not which species can appear. **The agent must not suggest a Synchronize lead for natures in Ruby/Sapphire.**
    - **Other field abilities (added in draft 5) are Emerald-only too:**
      - **Held items.** Ruby/Sapphire's `SetWildMonHeldItem` (`pokemon_3.c`) always rolls 45% none, 50% common, 5% rare. Emerald's `pokemon.c` changes that to 20/60/20 with a Compound Eyes lead.
      - **Fishing.** Suction Cups and Sticky Hold, above, live in Emerald's `field_player_avatar.c`; Ruby/Sapphire's has no ability check.
      - **Eggs.** Flame Body and Magma Armor halve egg steps only in Emerald (`egg_hatch.c`). Ruby/Sapphire's `daycare.c` counts egg cycles with no ability check.
    - **In the build:** the agent's per-game brief for Ruby and Sapphire now says that only Stench and Illuminate do anything outside battle. Every agent reads that brief.
  - **Transport.** The cable car and the S.S. Tidal's C code are the same. Mr. Briney's only C is the reset after a whiteout or Teleport, also the same.
  - **The Pokémon League's door guards check only `FLAG_BADGE06_GET`** in both games (`EverGrandeCity_PokemonLeague/scripts.inc` vs `EverGrandeCity_PokemonLeague_1F/scripts.inc`), not all eight badges. In practice you can't arrive without all eight, since reaching Ever Grande City takes Waterfall, which needs the Rain Badge.
- **V-12 Spot checks along the way.**
  - **Seafloor Cavern stays open after the legend escapes, in all three games.**
    - `Underwater_SeafloorCavern`'s only change on the escape flag replaces the parked submarine's tiles with rock wall and floor.
    - No tile there is no-surfacing, and the map has no emerge connection, so surfacing still uses its fixed dive warp into `SEAFLOOR_CAVERN_ENTRANCE`.
    - Its wild encounters stay available after P-21.
  - Mr. Briney's boat and cottage check the same flags in both decomps (`FLAG_DELIVERED_STEVEN_LETTER`, `FLAG_DELIVERED_DEVON_GOODS`).
  - Route 111 north of Mauville needs Rock Smash in both: two breakable rocks at (18, 101) and (19, 100).
  - Ruby/Sapphire-only maps on the story path need nothing beyond Surf to get in. These are Ruby's Magma Hideout maps (`MAGMA_HIDEOUT_B1F`/`B2F`) and Cave of Origin B2F–B4F.
  - The obstacle scripts' badge checks are identical: Cut badge 1, Rock Smash 3, Strength 4 (`data/field_move_scripts.inc` vs `data/scripts/field_move_scripts.inc`), as is C-12.
- **V-13 Ruby vs Sapphire.** V-02 to V-04 give identical output when pokeruby is read as Ruby and as Sapphire. V-01 doesn't depend on the version, except for the hideout maps (X-11) and Cave of Origin B4F.
- **V-14 New, all three games: the Lilycove Department Store needs the rival battle.** `[decomp]`
  - **The block:** the rival stands at (27, 7), the only walkable tile below the store's door at (27, 6). Collision blocks both sides of the door, in both decomps.
  - **Declining doesn't clear it.** It sets `FLAG_DECLINED_RIVAL_BATTLE_LILYCOVE` and leaves the rival in place (`LilycoveCity_EventScript_DeclineMayBattle` and the Brendan equivalent).
  - **What clears it:** only the end of the battle (`LilycoveCity_EventScript_RivalFlyAway`, `removeobject`), until the Hall of Fame hides the rival.
  - **Effect:** the store's eight TMs (TM14, 15, 16, 17, 20, 25, 33, 38) need P-17, which is optional only if you skip the store.
  - **Fixed in draft 4's build.** LockeSmith's TM table had listed these TMs with no requirement in all three databases. They now carry the rival-battle requirement, and the Lilycove rival steps' notes in both story files say so.
- **V-15 Limits.**
  - The reachability model ignores NPCs that wander. It walls off together all trainers that share a hide flag, which can only add chokepoints, never hide one.
  - The model doesn't check an arrow warp's direction, and it counts any warp event on a tile it reaches. Rotating gates and tiles changed by scripts aren't modeled; V-04 and V-10 cover them instead.
  - V-04 follows each branch one label deep.
  - Conditions inside the removing scripts were compared by hand only for chokepoint blockers (V-07). The other same-tile blockers were checked only for being removed from the same map.
  - The engine checks (V-10, V-11) read the C source; nothing was run in an emulator.
  - Real Ruby/Sapphire randomizer logs remain open (Q-06, R-12 to R-14).
  - **Added in draft 5:** this is an audit of movement and story blockers, not a proof over every game state. Scripts that start an encounter without blocking a path weren't compared; E-10 was found that way, by the reviewer. Emulator checks at the main gates would cover what reading the code can't.
