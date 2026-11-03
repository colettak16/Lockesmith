# LockeSmith: Pokémon Ruby & Sapphire facts for cross-checking (draft 3)

Assembled 2026-11-02 from scratch extraction scripts run against the **pret/pokeruby** decompilation (`5784633ce4ef`, which builds both Ruby and Sapphire), compared with **pret/pokeemerald** (`731ad5bfd6e6`, the commit LockeSmith's Emerald build pins) and **PokeAPI** (`6b8db7f3cb31`). UPR ZX facts are from its source (master `7f00eb8`). Bulbapedia text is CC BY-NC-SA 2.5.

**How this differs from the Emerald packet.** LockeSmith has no Ruby/Sapphire database yet. The Emerald packet (`docs/review_packet.md`) was generated from the built database and went through two review rounds. This packet is the fact base a Ruby/Sapphire build would start from, and it is written as a **delta from Emerald**:
- section 2: what carries over unchanged
- sections 3 to 8: what differs
- a draft story order for each version

**ID prefixes**: C carries over from Emerald, X differs from Emerald, P progression, E story events, A area unlocks, N never reachable, K trainer teams, L wild encounters, SE special encounters, TM machines, R randomizer, D data findings, Q questions.

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

You are a second reviewer for **LockeSmith**, a research agent that answers questions about Pokémon games: what to catch, where, and how to beat the rest of the main story, including Nuzlocke and randomized runs. It currently covers Emerald. This packet covers **Pokémon Ruby and Pokémon Sapphire (English, Gen 3, GBA, unmodified)**. Postgame is out of scope, except where a claim says "postgame" to mark something unreachable.

Everything below is what the agent would treat as fact for Ruby and Sapphire. Each claim has an ID. Please check as many as you can, prioritising:
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
- **X-16** `[decomp]` **Roamer: Latios in Ruby, Latias in Sapphire**, Lv40, after the Hall of Fame (`ROAMER_SPECIES` in `constants/species.h`). Southern Island has the other one at Lv50 with the Eon Ticket (event-only).
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
- **P-R3** The Emerald area rule (Emerald P-R2), HM rule (P-R3) and badge-order note (P-R4, C-13) carry over unchanged.
- **P-R4** Rival fights: the rival takes the starter with the type advantage over yours (Treecko → rival Torchic, Torchic → Mudkip, Mudkip → Treecko), from the `VAR_STARTER_MON` switch in each map script. The rival is May if you play Brendan and vice versa (X-06).
- **P-R5** Order is from the decomp's story gates, below, and Emerald's reviewed order. It hasn't yet been matched against Bulbapedia's Ruby/Sapphire walkthrough (23 parts) the way Emerald's was.

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
| E-09 | Hall of Fame | | Sky Pillar, the Beldum gift and the roamer | `FLAG_SYS_GAME_CLEAR` and `hall_of_fame.inc` |

### Area unlocks: changes to Emerald's reviewed list (A)

- **A-01** `[diff]` For every step not listed below, the areas newly reachable before it are those of the matching Emerald step in `data/progression.yaml`, because the overworld is wired the same (C-14). The removed Emerald steps opened no areas of their own, except the Magma Hideout (A-05).
  - **Caveat (round 1):** the same map connections don't prove the same event gates; the hideout (X-11) shows why.
  - The event-controlled entrances in E were checked in pokeruby's scripts.
  - The other copied unlocks still need a script check before a build relies on them (Q-08).
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

### Never reachable before the Champion (N)

- **N-01** Postgame (`FLAG_SYS_GAME_CLEAR` or Hall of Fame scripts):
  - Sky Pillar, all floors (X-10)
  - the Beldum gift in Steven's house (`hall_of_fame.inc` unhides it)
  - the roaming Latios/Latias (X-16)
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
- **SE-08** Roamer: see X-16.
- **SE-09** Feebas (C-11). Mirage Island has only Wynaut, as in Emerald.

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
- **D-03** **Roamer conditions are inverted.** PokeAPI puts the Hall of Fame condition on the roaming-*water* rows only, the reverse of Emerald (Emerald data finding 11). Both rows should carry it; Ruby/Sapphire have no TV-choice condition.
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

Still open:
- **Q-06** R-13: if you've seen a real Ruby or Sapphire UPR log, how do town names print in wild-set labels?
- **Q-08** A-01: besides the E-table events, are there other event-script gates where Ruby/Sapphire differ from Emerald on the same map? Candidates: a route or entrance that opens at a different story point, or an NPC that blocks a path in one game and not the other.
  - Round 2 found no further conflicting gate in targeted checks (including Route 119's bridge grunts before the Weather Institute), but didn't establish equivalence everywhere.
  - Planned for the build: a mechanical comparison, per shared map, of every progression-related object flag, `checkflag`/`goto_if_set`, `compare` on a story variable, and conditional layout change. Flags were renamed between the two decomps, so it has to match by script position and effect rather than by name.
- **Q-01 follow-up** (round 2): the `REVISION` audit supports Q-01. The full guarantee is a hash comparison of the extracted trainer, wild, item and event tables built for revisions 0, 1 and 2, which the build can do cheaply.
