# Lockesmith: Pokémon Emerald facts for cross-checking

Generated 2026-11-01 by `build/review_packet.py` from the database built 2026-11-01: pokeemerald `731ad5bfd6e6`, PokeAPI `6b8db7f3cb31`. Bulbapedia text is CC BY-NC-SA 2.5.

**ID prefixes**: M mechanics, MV moves, SP species, LG later-gen relatives, EV evolutions, D data findings, P/N progression, K trainer teams, L locations, SE special encounters, TM/TU machines and tutors, R randomizer, Q questions.

## How to review this packet

You are a second reviewer for **Lockesmith**, a research agent that answers questions about
**Pokémon Emerald (English, Gen 3, unmodified)**: what to catch, where, and how to beat the rest
of the main story, including Nuzlocke and randomized runs. Postgame and the Battle Frontier are
out of scope except where a claim says "postgame" to mark something unreachable.

Everything below is what the agent will treat as fact. Each claim has an ID (`M-03`, `P-12`,
`MV-242`, ...). Please check as many as you can, prioritising sections 4 to 6 (progression,
trainers, locations), where judgement calls live.

**About sources.** Most data comes from the **pret/pokeemerald decompilation** (the game's own
code and data; claims tagged `[decomp]`) and **PokeAPI** (tagged `[pokeapi]`), with Bulbapedia's
Emerald walkthrough for story order (`[guide]`). A decomp-tagged claim was read from the game's
code, so if you disagree, say what you think was misread, not only what you remember. Memory
of Ruby/Sapphire, FireRed/LeafGreen or the 3DS remakes is a common source of false alarms, so
please check that a disagreement applies to Emerald specifically.

**Answer in this format:**

1. **Disagreements**: a table with columns `ID | our claim (short) | what you believe instead |
   confidence (high/medium/low) | evidence (named source, or "memory") | suggested fix`.
2. **Unsure**: the same table, for claims you suspect but can't confirm.
3. **Missing**: facts, caveats or battles the agent should know that this packet omits, with the
   section they belong in.
4. **Answers to the open questions** (section 9, `Q-` IDs).
5. **Agreed**: the IDs or ID ranges you checked and agree with. Leave out IDs you didn't check.

Skip wording and formatting nitpicks. "Unsure" is a useful answer; a confident wrong correction
costs more than a missed one.

## 1. Sources and method

- **Ground truth order**: decomp > PokeAPI > walkthrough. Where PokeAPI disagreed with the decomp,
  the build patches PokeAPI to match (see D-items). Tests cross-check species, moves, the type chart,
  all level-up learnsets, all evolutions and every wild table against the decomp.
- **Gen 3 correction layer** `[pokeapi]`: PokeAPI stores modern values plus history tables. For
  types, stats and abilities, a `*_past` row's `generation_id` is the *last* generation that value
  applied, so the build takes the earliest past row with `generation_id >= 3`. For moves, it takes
  the earliest `move_changelog` change after Gen 3 per field (the value before that change).
- **Scope of the database**: National Dex 1–386, moves 1–354, Gen 3 abilities, Emerald (version
  group 6) learnsets, Emerald (version 9) encounters, 855 trainer structs (854 with parties).

## 2. Battle mechanics and game rules

- **M-01** `[decomp]` A damaging move's category comes from its **type**, not the move: Normal, Fighting,
  Flying, Poison, Ground, Rock, Bug, Ghost and Steel moves are physical; Fire, Water, Grass,
  Electric, Psychic, Ice, Dragon and Dark moves are special. Status moves stay status whatever
  their type. So Crunch (Dark) is special and Shadow Ball (Ghost) is physical in Emerald; the
  full list of moves whose category differs from modern games is MV-category.
- **M-02** There are 17 types and **no Fairy type**. The `???` type exists only on Curse and has no
  matchups.
- **M-03** `[decomp]` Type chart: the generated chart below lists every non-neutral matchup. Versus
  Gen 6+, the differences are that Steel also resists Ghost and Dark, and nothing involves Fairy.
  (The ROM table also has Foresight-only entries letting Normal/Fighting hit Ghost; not modelled.)
- **M-04** No hidden abilities. Each species has one or two Gen 3 abilities (ability IDs 1–76).
- **M-05** `[decomp]` Species types, base stats and abilities are Gen 3's. Table SP lists every species
  whose Gen 3 values differ from the modern PokeAPI default form (e.g. Gardevoir is pure Psychic).
- **M-06** `[decomp]` Move type, power, accuracy and PP are Gen 3's. Table MV lists every move whose
  Gen 3 values differ from modern PokeAPI.
- **M-07** `[decomp]` Level-up learnsets are Emerald's and match the ROM exactly, in ROM order. TM/HM,
  tutor and egg moves come from PokeAPI's Emerald version group.
- **M-08** `[decomp]` **Default trainer movesets.** A trainer Pokémon whose party entry has no custom
  moves gets `GiveBoxMonInitialMoveset`: walk its level-up learnset in ROM order up to its level,
  skip moves it already knows, and when it already has four, drop the oldest (first) move and
  append the new one. Custom movesets are used as written.
- **M-09** `[decomp]` **Trainer IVs**: a party entry stores one IV byte 0–255; all six IVs are
  `iv * 31 / 255` (integer division). E.g. byte 200 -> 24.
- **M-10** `[pokeapi]` Encounter slot rates (generated below). Mirage Island's grass is stored as one
  Wynaut slot at 100%, because every slot there is Wynaut.
- **M-11** `[decomp]` Fishing: each map has one 10-slot fishing table split by rod: Old Rod slots 0–1,
  Good Rod 2–4, Super Rod 5–9 (`wild_encounters.json` groups).
- **M-12** `[decomp]` Field-move badge requirements (an HM is usable outside battle only with the
  badge): Cut: Stone, Flash: Knuckle, Rock Smash: Dynamo, Strength: Heat, Surf: Balance,
  Fly: Feather, Dive: Mind, Waterfall: Rain. Only Waterfall was checked in code
  (`field_control_avatar.c`: climbing needs `FLAG_BADGE08_GET`); the rest are from the walkthrough.
- **M-13** Deoxys in Emerald is the **Speed Forme** at runtime (the ROM's species table keeps Normal
  Forme stats and swaps them in battle). Event-only, so out of scope.
- **M-14** `[decomp]` Tate & Liza is a double battle (trainer struct flag). The Mossdeep Space Center
  fight is a multi battle with Steven as partner, set up by a map script; both opposing trainer
  structs say single.
- **M-15** No Gen 4+ relatives exist: table LG lists the pre-evolutions and evolutions that were
  removed, and table EV lists every Emerald evolution with its method.

**M-03 type chart** (attacker -> defenders; unlisted pairs are 1x):

| Attacking type | Category | 2x | 0.5x | 0x |
|---|---|---|---|---|
| normal | physical | — | rock, steel | ghost |
| fighting | physical | dark, ice, normal, rock, steel | bug, flying, poison, psychic | ghost |
| flying | physical | bug, fighting, grass | electric, rock, steel | — |
| poison | physical | grass | ghost, ground, poison, rock | steel |
| ground | physical | electric, fire, poison, rock, steel | bug, grass | flying |
| rock | physical | bug, fire, flying, ice | fighting, ground, steel | — |
| bug | physical | dark, grass, psychic | fighting, fire, flying, ghost, poison, steel | — |
| ghost | physical | ghost, psychic | dark, steel | normal |
| steel | physical | ice, rock | electric, fire, steel, water | — |
| fire | special | bug, grass, ice, steel | dragon, fire, rock, water | — |
| water | special | fire, ground, rock | dragon, grass, water | — |
| grass | special | ground, rock, water | bug, dragon, fire, flying, grass, poison, steel | — |
| electric | special | flying, water | dragon, electric, grass | ground |
| psychic | special | fighting, poison | psychic, steel | dark |
| ice | special | dragon, flying, grass, ground | fire, ice, steel, water | — |
| dragon | special | dragon | steel | — |
| dark | special | ghost, psychic | dark, fighting, steel | — |

**M-10 encounter slot rates**

| Method | Slot: rate |
|---|---|
| good-rod | 1: 60%, 2: 20%, 3: 20% |
| old-rod | 1: 70%, 2: 30% |
| rock-smash | 1: 60%, 2: 30%, 3: 5%, 4: 4%, 5: 1% |
| seaweed | 1: 60%, 2: 30%, 3: 5%, 4: 4%, 5: 1% |
| super-rod | 1: 40%, 2: 40%, 3: 15%, 4: 4%, 5: 1% |
| surf | 1: 60%, 2: 30%, 3: 5%, 4: 4%, 5: 1% |
| walk | 1: 20%, 2: 20%, 3: 10%, 4: 10%, 5: 10%, 6: 10%, 7: 5%, 8: 5%, 9: 4%, 10: 4%, 11: 1%, 12: 1% |

### Moves (MV)

Every move whose Gen 3 type, power, accuracy or PP differs from modern PokeAPI. `ROM-patched` names fields the build took from the decomp because PokeAPI's history tables missed the change.

| ID | Move | Gen 3 value (modern value) | ROM-patched |
|---|---|---|---|
| MV-14 | Swords Dance | PP 30 (now 20) | — |
| MV-19 | Fly | power 70 (now 90) | — |
| MV-20 | Bind | accuracy 75 (now 85) | — |
| MV-22 | Vine Whip | power 35 (now 45); PP 10 (now 25) | — |
| MV-26 | Jump Kick | power 70 (now 100); PP 25 (now 10) | — |
| MV-33 | Tackle | power 35 (now 40); accuracy 95 (now 100) | — |
| MV-35 | Wrap | accuracy 85 (now 90) | — |
| MV-37 | Thrash | power 90 (now 120); PP 20 (now 10) | — |
| MV-42 | Pin Missile | power 14 (now 25); accuracy 85 (now 95) | — |
| MV-50 | Disable | accuracy 55 (now 100) | — |
| MV-53 | Flamethrower | power 95 (now 90) | — |
| MV-56 | Hydro Pump | power 120 (now 110) | — |
| MV-57 | Surf | power 95 (now 90) | — |
| MV-58 | Ice Beam | power 95 (now 90) | — |
| MV-59 | Blizzard | power 120 (now 110) | — |
| MV-66 | Submission | PP 25 (now 20) | — |
| MV-71 | Absorb | PP 20 (now 25) | — |
| MV-72 | Mega Drain | PP 10 (now 15) | — |
| MV-74 | Growth | PP 40 (now 20) | — |
| MV-80 | Petal Dance | power 70 (now 120); PP 20 (now 10) | — |
| MV-83 | Fire Spin | power 15 (now 35); accuracy 70 (now 85) | — |
| MV-85 | Thunderbolt | power 95 (now 90) | — |
| MV-86 | Thunder Wave | accuracy 100 (now 90) | — |
| MV-87 | Thunder | power 120 (now 110) | — |
| MV-91 | Dig | power 60 (now 80) | — |
| MV-92 | Toxic | accuracy 85 (now 90) | — |
| MV-105 | Recover | PP 20 (now 5) | — |
| MV-107 | Minimize | PP 20 (now 10) | — |
| MV-112 | Barrier | PP 30 (now 20) | — |
| MV-122 | Lick | power 20 (now 30) | — |
| MV-123 | Smog | power 20 (now 30) | — |
| MV-126 | Fire Blast | power 120 (now 110) | — |
| MV-128 | Clamp | accuracy 75 (now 85); PP 10 (now 15) | — |
| MV-130 | Skull Bash | power 100 (now 130); PP 15 (now 10) | — |
| MV-135 | Soft-Boiled | PP 10 (now 5) | accuracy, pp |
| MV-136 | High Jump Kick | power 85 (now 130); PP 20 (now 10) | — |
| MV-137 | Glare | accuracy 75 (now 100) | — |
| MV-139 | Poison Gas | accuracy 55 (now 90) | — |
| MV-141 | Leech Life | power 20 (now 80); PP 15 (now 10) | — |
| MV-145 | Bubble | power 20 (now 40) | — |
| MV-148 | Flash | accuracy 70 (now 100) | — |
| MV-149 | Psywave | accuracy 80 (now 100) | — |
| MV-151 | Acid Armor | PP 40 (now 20) | — |
| MV-152 | Crabhammer | power 90 (now 100); accuracy 85 (now 90) | — |
| MV-156 | Rest | PP 10 (now 5) | pp |
| MV-168 | Thief | power 40 (now 60); PP 10 (now 25) | — |
| MV-173 | Snore | power 40 (now 50) | — |
| MV-174 | Curse | type ??? (now ghost) | — |
| MV-178 | Cotton Spore | accuracy 85 (now 100) | — |
| MV-184 | Scary Face | accuracy 90 (now 100) | — |
| MV-186 | Sweet Kiss | type normal (now fairy) | — |
| MV-192 | Zap Cannon | power 100 (now 120) | — |
| MV-198 | Bone Rush | accuracy 80 (now 90) | — |
| MV-200 | Outrage | power 90 (now 120); PP 15 (now 10) | — |
| MV-202 | Giga Drain | power 60 (now 75); PP 5 (now 10) | — |
| MV-204 | Charm | type normal (now fairy) | — |
| MV-207 | Swagger | accuracy 90 (now 85) | — |
| MV-208 | Milk Drink | PP 10 (now 5) | pp |
| MV-210 | Fury Cutter | power 10 (now 40) | — |
| MV-229 | Rapid Spin | power 20 (now 50) | — |
| MV-236 | Moonlight | type normal (now fairy) | — |
| MV-237 | Hidden Power | power None (now 60) | — |
| MV-248 | Future Sight | power 80 (now 120); accuracy 90 (now 100); PP 15 (now 10) | — |
| MV-249 | Rock Smash | power 20 (now 40) | — |
| MV-250 | Whirlpool | power 15 (now 35); accuracy 70 (now 85) | — |
| MV-251 | Beat Up | power 10 (now None) | — |
| MV-253 | Uproar | power 50 (now 90) | — |
| MV-254 | Stockpile | PP 10 (now 20) | — |
| MV-255 | Spit Up | power 100 (now None) | power |
| MV-257 | Heat Wave | power 100 (now 95) | — |
| MV-261 | Will-O-Wisp | accuracy 75 (now 85) | — |
| MV-265 | Smelling Salts | power 60 (now 70) | — |
| MV-267 | Nature Power | accuracy 95 (now None) | accuracy |
| MV-282 | Knock Off | power 20 (now 65) | — |
| MV-291 | Dive | power 60 (now 80) | — |
| MV-295 | Luster Purge | power 70 (now 95) | power |
| MV-296 | Mist Ball | power 70 (now 95) | — |
| MV-303 | Slack Off | PP 10 (now 5) | accuracy, pp |
| MV-309 | Meteor Mash | power 100 (now 90); accuracy 85 (now 90) | — |
| MV-314 | Air Cutter | power 55 (now 60) | — |
| MV-315 | Overheat | power 140 (now 130) | — |
| MV-317 | Rock Tomb | power 50 (now 60); accuracy 80 (now 95); PP 10 (now 15) | — |
| MV-326 | Extrasensory | PP 30 (now 20) | — |
| MV-328 | Sand Tomb | power 15 (now 35); accuracy 70 (now 85) | — |
| MV-330 | Muddy Water | power 95 (now 90) | — |
| MV-331 | Bullet Seed | power 10 (now 25) | — |
| MV-333 | Icicle Spear | power 10 (now 25) | — |
| MV-343 | Covet | power 40 (now 60); PP 40 (now 25) | — |
| MV-348 | Leaf Blade | power 70 (now 90) | — |
| MV-350 | Rock Blast | accuracy 80 (now 90) | — |
| MV-353 | Doom Desire | power 120 (now 140); accuracy 85 (now 100) | — |

**MV-category**: moves whose physical/special category differs from modern games because of M-01.

- Special in Gen 3, physical now (28): Fire Punch (fire), Ice Punch (ice), Thunder Punch (electric), Vine Whip (grass), Bite (dark), Razor Leaf (grass), Waterfall (water), Clamp (water), Crabhammer (water), Thief (dark), Flame Wheel (fire), Feint Attack (dark), Outrage (dragon), Spark (electric), Sacred Fire (fire), Pursuit (dark), Crunch (dark), Beat Up (dark), Knock Off (dark), Dive (water), Blaze Kick (fire), Ice Ball (ice), Needle Arm (grass), Bullet Seed (grass), Icicle Spear (ice), Dragon Claw (dragon), Volt Tackle (electric), Leaf Blade (grass)
- Physical in Gen 3, special now (26): Razor Wind (normal), Gust (flying), Sonic Boom (normal), Acid (poison), Hyper Beam (normal), Night Shade (ghost), Smog (poison), Sludge (poison), Swift (normal), Tri Attack (normal), Snore (normal), Aeroblast (flying), Sludge Bomb (poison), Mud-Slap (ground), Hidden Power (normal), Ancient Power (rock), Shadow Ball (ghost), Uproar (normal), Spit Up (normal), Hyper Voice (normal), Weather Ball (normal), Air Cutter (flying), Silver Wind (bug), Signal Beam (bug), Mud Shot (ground), Doom Desire (steel)

**MV-accuracy**: 36 moves the ROM stores with accuracy 100 where PokeAPI uses null (can't miss, or no accuracy check): Whirlwind, Roar, Mimic, Bide, Soft-Boiled, Struggle, Spider Web, Mind Reader, Conversion 2, Foresight, Lock-On, Mean Look, Pain Split, Vital Throw, Follow Me, Charge, Helping Hand, Role Play, Wish, Assist, Ingrain, Magic Coat, Recycle, Yawn, Skill Swap, Imprison, Refresh, Grudge, Snatch, Camouflage, Tail Glow, Mud Sport, Slack Off, Odor Sleuth, Block, Water Sport.

### Species (SP)

Every species whose Gen 3 types, base stats or (non-hidden) abilities differ from the modern PokeAPI default form. Hidden abilities don't exist in Gen 3 (M-04) and aren't listed.

| ID | Species | Gen 3 value (modern value) |
|---|---|---|
| SP-12 | Butterfree | stats SpA 80 (now 90) |
| SP-15 | Beedrill | stats Atk 80 (now 90) |
| SP-16 | Pidgey | abilities keen-eye (now keen-eye/tangled-feet) |
| SP-17 | Pidgeotto | abilities keen-eye (now keen-eye/tangled-feet) |
| SP-18 | Pidgeot | stats Spe 91 (now 101); abilities keen-eye (now keen-eye/tangled-feet) |
| SP-24 | Arbok | stats Atk 85 (now 95) |
| SP-25 | Pikachu | stats Def 30 (now 40), SpD 40 (now 50) |
| SP-26 | Raichu | stats Spe 100 (now 110) |
| SP-29 | Nidoran♀ | abilities poison-point (now poison-point/rivalry) |
| SP-30 | Nidorina | abilities poison-point (now poison-point/rivalry) |
| SP-31 | Nidoqueen | stats Atk 82 (now 92); abilities poison-point (now poison-point/rivalry) |
| SP-32 | Nidoran♂ | abilities poison-point (now poison-point/rivalry) |
| SP-33 | Nidorino | abilities poison-point (now poison-point/rivalry) |
| SP-34 | Nidoking | stats Atk 92 (now 102); abilities poison-point (now poison-point/rivalry) |
| SP-35 | Clefairy | type normal (now fairy); abilities cute-charm (now cute-charm/magic-guard) |
| SP-36 | Clefable | type normal (now fairy); stats SpA 85 (now 95); abilities cute-charm (now cute-charm/magic-guard) |
| SP-39 | Jigglypuff | type normal (now normal/fairy); abilities cute-charm (now cute-charm/competitive) |
| SP-40 | Wigglytuff | type normal (now normal/fairy); stats SpA 75 (now 85); abilities cute-charm (now cute-charm/competitive) |
| SP-45 | Vileplume | stats SpA 100 (now 110) |
| SP-46 | Paras | abilities effect-spore (now effect-spore/dry-skin) |
| SP-47 | Parasect | abilities effect-spore (now effect-spore/dry-skin) |
| SP-48 | Venonat | abilities compound-eyes (now compound-eyes/tinted-lens) |
| SP-49 | Venomoth | abilities shield-dust (now shield-dust/tinted-lens) |
| SP-51 | Dugtrio | stats Atk 80 (now 100) |
| SP-52 | Meowth | abilities pickup (now pickup/technician) |
| SP-53 | Persian | abilities limber (now limber/technician) |
| SP-56 | Mankey | abilities vital-spirit (now vital-spirit/anger-point) |
| SP-57 | Primeape | abilities vital-spirit (now vital-spirit/anger-point) |
| SP-62 | Poliwrath | stats Atk 85 (now 95) |
| SP-65 | Alakazam | stats SpD 85 (now 95) |
| SP-66 | Machop | abilities guts (now guts/no-guard) |
| SP-67 | Machoke | abilities guts (now guts/no-guard) |
| SP-68 | Machamp | abilities guts (now guts/no-guard) |
| SP-71 | Victreebel | stats SpD 60 (now 70) |
| SP-76 | Golem | stats Atk 110 (now 120) |
| SP-83 | Farfetch’d | stats Atk 65 (now 90) |
| SP-85 | Dodrio | stats Spe 100 (now 110) |
| SP-86 | Seel | abilities thick-fat (now thick-fat/hydration) |
| SP-87 | Dewgong | abilities thick-fat (now thick-fat/hydration) |
| SP-90 | Shellder | abilities shell-armor (now shell-armor/skill-link) |
| SP-91 | Cloyster | abilities shell-armor (now shell-armor/skill-link) |
| SP-94 | Gengar | abilities levitate (now cursed-body) |
| SP-96 | Drowzee | abilities insomnia (now insomnia/forewarn) |
| SP-97 | Hypno | abilities insomnia (now insomnia/forewarn) |
| SP-101 | Electrode | stats Spe 140 (now 150) |
| SP-103 | Exeggutor | stats SpD 65 (now 75) |
| SP-106 | Hitmonlee | abilities limber (now limber/reckless) |
| SP-107 | Hitmonchan | abilities keen-eye (now keen-eye/iron-fist) |
| SP-109 | Koffing | abilities levitate (now levitate/neutralizing-gas) |
| SP-110 | Weezing | abilities levitate (now levitate/neutralizing-gas) |
| SP-114 | Tangela | abilities chlorophyll (now chlorophyll/leaf-guard) |
| SP-115 | Kangaskhan | abilities early-bird (now early-bird/scrappy) |
| SP-116 | Horsea | abilities swift-swim (now swift-swim/sniper) |
| SP-117 | Seadra | abilities poison-point (now poison-point/sniper) |
| SP-122 | Mr. Mime | type psychic (now psychic/fairy); abilities soundproof (now soundproof/filter) |
| SP-123 | Scyther | abilities swarm (now swarm/technician) |
| SP-124 | Jynx | abilities oblivious (now oblivious/forewarn) |
| SP-127 | Pinsir | abilities hyper-cutter (now hyper-cutter/mold-breaker) |
| SP-128 | Tauros | abilities intimidate (now intimidate/anger-point) |
| SP-133 | Eevee | abilities run-away (now run-away/adaptability) |
| SP-137 | Porygon | abilities trace (now trace/download) |
| SP-164 | Noctowl | stats SpA 76 (now 86) |
| SP-168 | Ariados | stats SpD 60 (now 70) |
| SP-173 | Cleffa | type normal (now fairy); abilities cute-charm (now cute-charm/magic-guard) |
| SP-174 | Igglybuff | type normal (now normal/fairy); abilities cute-charm (now cute-charm/competitive) |
| SP-175 | Togepi | type normal (now fairy) |
| SP-176 | Togetic | type normal/flying (now fairy/flying) |
| SP-181 | Ampharos | stats Def 75 (now 85) |
| SP-182 | Bellossom | stats Def 85 (now 95) |
| SP-183 | Marill | type water (now water/fairy) |
| SP-184 | Azumarill | type water (now water/fairy); stats SpA 50 (now 60) |
| SP-187 | Hoppip | abilities chlorophyll (now chlorophyll/leaf-guard) |
| SP-188 | Skiploom | abilities chlorophyll (now chlorophyll/leaf-guard) |
| SP-189 | Jumpluff | stats SpD 85 (now 95); abilities chlorophyll (now chlorophyll/leaf-guard) |
| SP-191 | Sunkern | abilities chlorophyll (now chlorophyll/solar-power) |
| SP-192 | Sunflora | abilities chlorophyll (now chlorophyll/solar-power) |
| SP-198 | Murkrow | abilities insomnia (now insomnia/super-luck) |
| SP-209 | Snubbull | type normal (now fairy) |
| SP-210 | Granbull | type normal (now fairy); abilities intimidate (now intimidate/quick-feet) |
| SP-211 | Qwilfish | stats Def 75 (now 85) |
| SP-212 | Scizor | abilities swarm (now swarm/technician) |
| SP-213 | Shuckle | abilities sturdy (now sturdy/gluttony) |
| SP-216 | Teddiursa | abilities pickup (now pickup/quick-feet) |
| SP-217 | Ursaring | abilities guts (now guts/quick-feet) |
| SP-219 | Magcargo | stats HP 50 (now 60), SpA 80 (now 90) |
| SP-220 | Swinub | abilities oblivious (now oblivious/snow-cloak) |
| SP-221 | Piloswine | abilities oblivious (now oblivious/snow-cloak) |
| SP-222 | Corsola | stats HP 55 (now 65), Def 85 (now 95), SpD 85 (now 95) |
| SP-223 | Remoraid | abilities hustle (now hustle/sniper) |
| SP-224 | Octillery | abilities suction-cups (now suction-cups/sniper) |
| SP-226 | Mantine | stats HP 65 (now 85) |
| SP-230 | Kingdra | abilities swift-swim (now swift-swim/sniper) |
| SP-233 | Porygon2 | abilities trace (now trace/download) |
| SP-234 | Stantler | abilities intimidate (now intimidate/frisk) |
| SP-235 | Smeargle | abilities own-tempo (now own-tempo/technician) |
| SP-236 | Tyrogue | abilities guts (now guts/steadfast) |
| SP-237 | Hitmontop | abilities intimidate (now intimidate/technician) |
| SP-238 | Smoochum | abilities oblivious (now oblivious/forewarn) |
| SP-241 | Miltank | abilities thick-fat (now thick-fat/scrappy) |
| SP-261 | Poochyena | abilities run-away (now run-away/quick-feet) |
| SP-262 | Mightyena | abilities intimidate (now intimidate/quick-feet) |
| SP-263 | Zigzagoon | abilities pickup (now pickup/gluttony) |
| SP-264 | Linoone | abilities pickup (now pickup/gluttony) |
| SP-267 | Beautifly | stats SpA 90 (now 100) |
| SP-275 | Shiftry | abilities chlorophyll/early-bird (now chlorophyll/wind-rider) |
| SP-277 | Swellow | stats SpA 50 (now 75) |
| SP-278 | Wingull | abilities keen-eye (now keen-eye/hydration) |
| SP-279 | Pelipper | stats SpA 85 (now 95); abilities keen-eye (now keen-eye/drizzle) |
| SP-280 | Ralts | type psychic (now psychic/fairy) |
| SP-281 | Kirlia | type psychic (now psychic/fairy) |
| SP-282 | Gardevoir | type psychic (now psychic/fairy) |
| SP-284 | Masquerain | stats SpA 80 (now 100), Spe 60 (now 80) |
| SP-285 | Shroomish | abilities effect-spore (now effect-spore/poison-heal) |
| SP-286 | Breloom | abilities effect-spore (now effect-spore/poison-heal) |
| SP-295 | Exploud | stats SpD 63 (now 73) |
| SP-298 | Azurill | type normal (now normal/fairy) |
| SP-300 | Skitty | abilities cute-charm (now cute-charm/normalize) |
| SP-301 | Delcatty | stats Spe 70 (now 90); abilities cute-charm (now cute-charm/normalize) |
| SP-302 | Sableye | abilities keen-eye (now keen-eye/stall) |
| SP-303 | Mawile | type steel (now steel/fairy) |
| SP-313 | Volbeat | stats Def 55 (now 75), SpD 75 (now 85) |
| SP-314 | Illumise | stats Def 55 (now 75), SpD 75 (now 85); abilities oblivious (now oblivious/tinted-lens) |
| SP-322 | Numel | abilities oblivious (now oblivious/simple) |
| SP-323 | Camerupt | abilities magma-armor (now magma-armor/solid-rock) |
| SP-324 | Torkoal | abilities white-smoke (now white-smoke/drought) |
| SP-327 | Spinda | abilities own-tempo (now own-tempo/tangled-feet) |
| SP-337 | Lunatone | stats HP 70 (now 90) |
| SP-338 | Solrock | stats HP 70 (now 90) |
| SP-339 | Barboach | abilities oblivious (now oblivious/anticipation) |
| SP-340 | Whiscash | abilities oblivious (now oblivious/anticipation) |
| SP-349 | Feebas | abilities swift-swim (now swift-swim/oblivious) |
| SP-350 | Milotic | abilities marvel-scale (now marvel-scale/competitive) |
| SP-353 | Shuppet | abilities insomnia (now insomnia/frisk) |
| SP-354 | Banette | abilities insomnia (now insomnia/frisk) |
| SP-357 | Tropius | abilities chlorophyll (now chlorophyll/solar-power) |
| SP-358 | Chimecho | stats HP 65 (now 75), Def 70 (now 80), SpD 80 (now 90) |
| SP-359 | Absol | abilities pressure (now pressure/super-luck) |
| SP-361 | Snorunt | abilities inner-focus (now inner-focus/ice-body) |
| SP-362 | Glalie | abilities inner-focus (now inner-focus/ice-body) |
| SP-363 | Spheal | abilities thick-fat (now thick-fat/ice-body) |
| SP-364 | Sealeo | abilities thick-fat (now thick-fat/ice-body) |
| SP-365 | Walrein | abilities thick-fat (now thick-fat/ice-body) |

### Later-generation relatives that don't exist in Emerald (LG)

| ID | Species | Relation | Removed relative |
|---|---|---|---|
| LG-52 | Meowth | evolution | Perrserker |
| LG-57 | Primeape | evolution | Annihilape |
| LG-82 | Magneton | evolution | Magnezone |
| LG-83 | Farfetch’d | evolution | Sirfetchd |
| LG-108 | Lickitung | evolution | Lickilicky |
| LG-112 | Rhydon | evolution | Rhyperior |
| LG-113 | Chansey | pre-evolution | Happiny |
| LG-114 | Tangela | evolution | Tangrowth |
| LG-122 | Mr. Mime | pre-evolution | Mime Jr |
| LG-122 | Mr. Mime | evolution | Mr Rime |
| LG-123 | Scyther | evolution | Kleavor |
| LG-125 | Electabuzz | evolution | Electivire |
| LG-126 | Magmar | evolution | Magmortar |
| LG-133 | Eevee | evolution | Leafeon, Glaceon, Sylveon |
| LG-143 | Snorlax | pre-evolution | Munchlax |
| LG-176 | Togetic | evolution | Togekiss |
| LG-185 | Sudowoodo | pre-evolution | Bonsly |
| LG-190 | Aipom | evolution | Ambipom |
| LG-193 | Yanma | evolution | Yanmega |
| LG-194 | Wooper | evolution | Clodsire |
| LG-198 | Murkrow | evolution | Honchkrow |
| LG-200 | Misdreavus | evolution | Mismagius |
| LG-203 | Girafarig | evolution | Farigiraf |
| LG-206 | Dunsparce | evolution | Dudunsparce |
| LG-207 | Gligar | evolution | Gliscor |
| LG-211 | Qwilfish | evolution | Overqwil |
| LG-215 | Sneasel | evolution | Weavile, Sneasler |
| LG-217 | Ursaring | evolution | Ursaluna |
| LG-221 | Piloswine | evolution | Mamoswine |
| LG-222 | Corsola | evolution | Cursola |
| LG-226 | Mantine | pre-evolution | Mantyke |
| LG-233 | Porygon2 | evolution | Porygon Z |
| LG-234 | Stantler | evolution | Wyrdeer |
| LG-264 | Linoone | evolution | Obstagoon |
| LG-281 | Kirlia | evolution | Gallade |
| LG-299 | Nosepass | evolution | Probopass |
| LG-315 | Roselia | pre-evolution | Budew |
| LG-315 | Roselia | evolution | Roserade |
| LG-356 | Dusclops | evolution | Dusknoir |
| LG-358 | Chimecho | pre-evolution | Chingling |
| LG-361 | Snorunt | evolution | Froslass |

### Evolutions (EV), all 184

| ID | From | To | Method |
|---|---|---|---|
| EV-1 | Bulbasaur | Ivysaur | level-up, level 16 |
| EV-2 | Ivysaur | Venusaur | level-up, level 32 |
| EV-4 | Charmander | Charmeleon | level-up, level 16 |
| EV-5 | Charmeleon | Charizard | level-up, level 36 |
| EV-7 | Squirtle | Wartortle | level-up, level 16 |
| EV-8 | Wartortle | Blastoise | level-up, level 36 |
| EV-10 | Caterpie | Metapod | level-up, level 7 |
| EV-11 | Metapod | Butterfree | level-up, level 10 |
| EV-13 | Weedle | Kakuna | level-up, level 7 |
| EV-14 | Kakuna | Beedrill | level-up, level 10 |
| EV-16 | Pidgey | Pidgeotto | level-up, level 18 |
| EV-17 | Pidgeotto | Pidgeot | level-up, level 36 |
| EV-19 | Rattata | Raticate | level-up, level 20 |
| EV-21 | Spearow | Fearow | level-up, level 20 |
| EV-23 | Ekans | Arbok | level-up, level 22 |
| EV-25 | Pikachu | Raichu | use-item, item thunder-stone |
| EV-27 | Sandshrew | Sandslash | level-up, level 22 |
| EV-29 | Nidoran♀ | Nidorina | level-up, level 16 |
| EV-30 | Nidorina | Nidoqueen | use-item, item moon-stone |
| EV-32 | Nidoran♂ | Nidorino | level-up, level 16 |
| EV-33 | Nidorino | Nidoking | use-item, item moon-stone |
| EV-35 | Clefairy | Clefable | use-item, item moon-stone |
| EV-37 | Vulpix | Ninetales | use-item, item fire-stone |
| EV-39 | Jigglypuff | Wigglytuff | use-item, item moon-stone |
| EV-41 | Zubat | Golbat | level-up, level 22 |
| EV-42 | Golbat | Crobat | level-up, friendship >= 160 |
| EV-43 | Oddish | Gloom | level-up, level 21 |
| EV-44 | Gloom | Vileplume | use-item, item leaf-stone |
| EV-44 | Gloom | Bellossom | use-item, item sun-stone |
| EV-46 | Paras | Parasect | level-up, level 24 |
| EV-48 | Venonat | Venomoth | level-up, level 31 |
| EV-50 | Diglett | Dugtrio | level-up, level 26 |
| EV-52 | Meowth | Persian | level-up, level 28 |
| EV-54 | Psyduck | Golduck | level-up, level 33 |
| EV-56 | Mankey | Primeape | level-up, level 28 |
| EV-58 | Growlithe | Arcanine | use-item, item fire-stone |
| EV-60 | Poliwag | Poliwhirl | level-up, level 25 |
| EV-61 | Poliwhirl | Poliwrath | use-item, item water-stone |
| EV-61 | Poliwhirl | Politoed | trade, holding kings-rock, trade |
| EV-63 | Abra | Kadabra | level-up, level 16 |
| EV-64 | Kadabra | Alakazam | trade, trade |
| EV-66 | Machop | Machoke | level-up, level 28 |
| EV-67 | Machoke | Machamp | trade, trade |
| EV-69 | Bellsprout | Weepinbell | level-up, level 21 |
| EV-70 | Weepinbell | Victreebel | use-item, item leaf-stone |
| EV-72 | Tentacool | Tentacruel | level-up, level 30 |
| EV-74 | Geodude | Graveler | level-up, level 25 |
| EV-75 | Graveler | Golem | trade, trade |
| EV-77 | Ponyta | Rapidash | level-up, level 40 |
| EV-79 | Slowpoke | Slowbro | level-up, level 37 |
| EV-79 | Slowpoke | Slowking | trade, holding kings-rock, trade |
| EV-81 | Magnemite | Magneton | level-up, level 30 |
| EV-84 | Doduo | Dodrio | level-up, level 31 |
| EV-86 | Seel | Dewgong | level-up, level 34 |
| EV-88 | Grimer | Muk | level-up, level 38 |
| EV-90 | Shellder | Cloyster | use-item, item water-stone |
| EV-92 | Gastly | Haunter | level-up, level 25 |
| EV-93 | Haunter | Gengar | trade, trade |
| EV-95 | Onix | Steelix | trade, holding metal-coat, trade |
| EV-96 | Drowzee | Hypno | level-up, level 26 |
| EV-98 | Krabby | Kingler | level-up, level 28 |
| EV-100 | Voltorb | Electrode | level-up, level 30 |
| EV-102 | Exeggcute | Exeggutor | use-item, item leaf-stone |
| EV-104 | Cubone | Marowak | level-up, level 28 |
| EV-109 | Koffing | Weezing | level-up, level 35 |
| EV-111 | Rhyhorn | Rhydon | level-up, level 42 |
| EV-113 | Chansey | Blissey | level-up, friendship >= 160 |
| EV-116 | Horsea | Seadra | level-up, level 32 |
| EV-117 | Seadra | Kingdra | trade, holding dragon-scale, trade |
| EV-118 | Goldeen | Seaking | level-up, level 33 |
| EV-120 | Staryu | Starmie | use-item, item water-stone |
| EV-123 | Scyther | Scizor | trade, holding metal-coat, trade |
| EV-129 | Magikarp | Gyarados | level-up, level 20 |
| EV-133 | Eevee | Vaporeon | use-item, item water-stone |
| EV-133 | Eevee | Jolteon | use-item, item thunder-stone |
| EV-133 | Eevee | Flareon | use-item, item fire-stone |
| EV-133 | Eevee | Espeon | level-up, friendship >= 160, day |
| EV-133 | Eevee | Umbreon | level-up, friendship >= 160, night |
| EV-137 | Porygon | Porygon2 | trade, holding up-grade, trade |
| EV-138 | Omanyte | Omastar | level-up, level 40 |
| EV-140 | Kabuto | Kabutops | level-up, level 40 |
| EV-147 | Dratini | Dragonair | level-up, level 30 |
| EV-148 | Dragonair | Dragonite | level-up, level 55 |
| EV-152 | Chikorita | Bayleef | level-up, level 16 |
| EV-153 | Bayleef | Meganium | level-up, level 32 |
| EV-155 | Cyndaquil | Quilava | level-up, level 14 |
| EV-156 | Quilava | Typhlosion | level-up, level 36 |
| EV-158 | Totodile | Croconaw | level-up, level 18 |
| EV-159 | Croconaw | Feraligatr | level-up, level 30 |
| EV-161 | Sentret | Furret | level-up, level 15 |
| EV-163 | Hoothoot | Noctowl | level-up, level 20 |
| EV-165 | Ledyba | Ledian | level-up, level 18 |
| EV-167 | Spinarak | Ariados | level-up, level 22 |
| EV-170 | Chinchou | Lanturn | level-up, level 27 |
| EV-172 | Pichu | Pikachu | level-up, friendship >= 220 |
| EV-173 | Cleffa | Clefairy | level-up, friendship >= 160 |
| EV-174 | Igglybuff | Jigglypuff | level-up, friendship >= 160 |
| EV-175 | Togepi | Togetic | level-up, friendship >= 160 |
| EV-177 | Natu | Xatu | level-up, level 25 |
| EV-179 | Mareep | Flaaffy | level-up, level 15 |
| EV-180 | Flaaffy | Ampharos | level-up, level 30 |
| EV-183 | Marill | Azumarill | level-up, level 18 |
| EV-187 | Hoppip | Skiploom | level-up, level 18 |
| EV-188 | Skiploom | Jumpluff | level-up, level 27 |
| EV-191 | Sunkern | Sunflora | use-item, item sun-stone |
| EV-194 | Wooper | Quagsire | level-up, level 20 |
| EV-204 | Pineco | Forretress | level-up, level 31 |
| EV-209 | Snubbull | Granbull | level-up, level 23 |
| EV-216 | Teddiursa | Ursaring | level-up, level 30 |
| EV-218 | Slugma | Magcargo | level-up, level 38 |
| EV-220 | Swinub | Piloswine | level-up, level 33 |
| EV-223 | Remoraid | Octillery | level-up, level 25 |
| EV-228 | Houndour | Houndoom | level-up, level 24 |
| EV-231 | Phanpy | Donphan | level-up, level 25 |
| EV-236 | Tyrogue | Hitmonlee | level-up, level 20, Atk > Def |
| EV-236 | Tyrogue | Hitmonchan | level-up, level 20, Atk < Def |
| EV-236 | Tyrogue | Hitmontop | level-up, level 20, Atk = Def |
| EV-238 | Smoochum | Jynx | level-up, level 30 |
| EV-239 | Elekid | Electabuzz | level-up, level 30 |
| EV-240 | Magby | Magmar | level-up, level 30 |
| EV-246 | Larvitar | Pupitar | level-up, level 30 |
| EV-247 | Pupitar | Tyranitar | level-up, level 55 |
| EV-252 | Treecko | Grovyle | level-up, level 16 |
| EV-253 | Grovyle | Sceptile | level-up, level 36 |
| EV-255 | Torchic | Combusken | level-up, level 16 |
| EV-256 | Combusken | Blaziken | level-up, level 36 |
| EV-258 | Mudkip | Marshtomp | level-up, level 16 |
| EV-259 | Marshtomp | Swampert | level-up, level 36 |
| EV-261 | Poochyena | Mightyena | level-up, level 18 |
| EV-263 | Zigzagoon | Linoone | level-up, level 20 |
| EV-265 | Wurmple | Silcoon | level-up, level 7 |
| EV-265 | Wurmple | Cascoon | level-up, level 7 |
| EV-266 | Silcoon | Beautifly | level-up, level 10 |
| EV-268 | Cascoon | Dustox | level-up, level 10 |
| EV-270 | Lotad | Lombre | level-up, level 14 |
| EV-271 | Lombre | Ludicolo | use-item, item water-stone |
| EV-273 | Seedot | Nuzleaf | level-up, level 14 |
| EV-274 | Nuzleaf | Shiftry | use-item, item leaf-stone |
| EV-276 | Taillow | Swellow | level-up, level 22 |
| EV-278 | Wingull | Pelipper | level-up, level 25 |
| EV-280 | Ralts | Kirlia | level-up, level 20 |
| EV-281 | Kirlia | Gardevoir | level-up, level 30 |
| EV-283 | Surskit | Masquerain | level-up, level 22 |
| EV-285 | Shroomish | Breloom | level-up, level 23 |
| EV-287 | Slakoth | Vigoroth | level-up, level 18 |
| EV-288 | Vigoroth | Slaking | level-up, level 36 |
| EV-290 | Nincada | Ninjask | level-up, level 20 |
| EV-290 | Nincada | Shedinja | shed |
| EV-293 | Whismur | Loudred | level-up, level 20 |
| EV-294 | Loudred | Exploud | level-up, level 40 |
| EV-296 | Makuhita | Hariyama | level-up, level 24 |
| EV-298 | Azurill | Marill | level-up, friendship >= 160 |
| EV-300 | Skitty | Delcatty | use-item, item moon-stone |
| EV-304 | Aron | Lairon | level-up, level 32 |
| EV-305 | Lairon | Aggron | level-up, level 42 |
| EV-307 | Meditite | Medicham | level-up, level 37 |
| EV-309 | Electrike | Manectric | level-up, level 26 |
| EV-316 | Gulpin | Swalot | level-up, level 26 |
| EV-318 | Carvanha | Sharpedo | level-up, level 30 |
| EV-320 | Wailmer | Wailord | level-up, level 40 |
| EV-322 | Numel | Camerupt | level-up, level 33 |
| EV-325 | Spoink | Grumpig | level-up, level 32 |
| EV-328 | Trapinch | Vibrava | level-up, level 35 |
| EV-329 | Vibrava | Flygon | level-up, level 45 |
| EV-331 | Cacnea | Cacturne | level-up, level 32 |
| EV-333 | Swablu | Altaria | level-up, level 35 |
| EV-339 | Barboach | Whiscash | level-up, level 30 |
| EV-341 | Corphish | Crawdaunt | level-up, level 30 |
| EV-343 | Baltoy | Claydol | level-up, level 36 |
| EV-345 | Lileep | Cradily | level-up, level 40 |
| EV-347 | Anorith | Armaldo | level-up, level 40 |
| EV-349 | Feebas | Milotic | level-up, beauty >= 170 |
| EV-353 | Shuppet | Banette | level-up, level 37 |
| EV-355 | Duskull | Dusclops | level-up, level 37 |
| EV-360 | Wynaut | Wobbuffet | level-up, level 15 |
| EV-361 | Snorunt | Glalie | level-up, level 42 |
| EV-363 | Spheal | Sealeo | level-up, level 32 |
| EV-364 | Sealeo | Walrein | level-up, level 44 |
| EV-366 | Clamperl | Huntail | trade, holding deep-sea-tooth, trade |
| EV-366 | Clamperl | Gorebyss | trade, holding deep-sea-scale, trade |
| EV-371 | Bagon | Shelgon | level-up, level 30 |
| EV-372 | Shelgon | Salamence | level-up, level 50 |
| EV-374 | Beldum | Metang | level-up, level 20 |
| EV-375 | Metang | Metagross | level-up, level 45 |

## 3. Data findings (where sources disagree)

Copied from docs/decisions.md. PokeAPI was patched to the decomp for each of these.

- **D-1** **PokeAPI's move changelog misses later-generation changes.** Rest, Soft-Boiled, Milk Drink and Slack-Off show 5 PP (Gen 3: 10), Luster Purge shows 95 power (Gen 3: 70), and Mind Reader shows 40 PP (Gen 3: 5).
- **D-2** **PokeAPI's evolution table mixes regional-form methods into base species**: Alolan Raticate at night, Ice Stone Sandslash and Ninetales, Legends: Arceus's Quilava at level 17, Prism Scale Feebas. Without the version-group filter, a Gen 3 answer would include them. Seven Gen 4 baby pre-evolutions (Munchlax → Snorlax, etc.) also needed cutting.
- **D-3** **PokeAPI's Emerald statics are wrong in places.** New Mauville's three Voltorb are listed twice, and the Aqua Hideout's two Electrode also appear in New Mauville and at `team-magma-hideout`. In Emerald, the only Electrode statics are in Aqua Hideout B1F.
- **D-4** **Emerald's Aqua Hideout region section has no PokeAPI Gen 3 index.** The old index points at Ruby's Magma Hideout.
- **D-5** **PokeAPI lists Emerald encounters for Cave of Origin B2F/B3F**, which are leftover Ruby/Sapphire maps you can't enter in Emerald.
- **D-6** **Emerald's Deoxys is the Speed Forme.** PokeAPI files its Emerald learnset under that form, and the ROM keeps Normal Forme base stats in its table and swaps in Speed Forme stats at runtime. The DB stores the table values. This is postgame and event-only, so out of scope, but worth knowing.
- **D-7** **May's and Brendan's teams aren't always mirrors** (P-R5), and **the Space Center multi battle shows as two single battles** in the trainer structs, as PLAN anticipated.
- **D-8** **Emerald has five rival fights**, two of them optional (Rustboro, Lilycove), not the three or four people usually remember.
- **D-9** Apart from D-1 to D-6, PokeAPI agrees with the ROM on everything checked: types, stats, abilities (after the past-table corrections), all 386 level-up learnsets, all 184 evolutions, the full type chart and every wild table (216 of 219 location/method pairs match outright; the other three are explained by the `seaweed` method and Mirage Island living inside the Route 130 map).

What the build takes from the decomp instead of PokeAPI:

- **D-R1** **Moves**: type, power, accuracy and PP are patched to `battle_moves.h`. The patched fields are recorded in `moves.rom_patched`: six real changelog gaps (D-1), Spit Up (the ROM stores 100 power where PokeAPI has null), and 32 moves where only accuracy differs (the ROM stores 100 where PokeAPI uses null for "can't miss").
- **D-R2** **Static encounters**: checked against the ROM's `setwildbattle` scripts (duplicates and misplaced rows removed).
- **D-R3** **Default trainer movesets**: computed from the decomp's level-up learnsets, because ROM order breaks ties within a level.
- **D-R4** **Deoxys's learnset**: taken from the form PokeAPI files Emerald's data under (Speed Forme).

## 4. Story progression (data/progression.yaml)

This is the most judgement-heavy section and the one we most want checked.

- **P-R1** The progression lists **32 story battles**, from the first rival fight to the Champion: all
  8 gyms, the Elite Four, the Champion, all 5 rival fights (Rustboro and Lilycove optional), both
  Wally fights, every Maxie/Archie fight, the Magma/Aqua admins, and the three early grunt fights that
  block the story. Generic hideout grunts and route trainers are left out.
- **P-R2** **Area rule**: each encounter area is listed (`areas_new`) at the first battle it can be
  reached before, having fought only the battles above it in this order. Detours that need no listed
  battle count, so an area can open before the walkthrough visits it. "Reachable before X" is the
  accumulation of `areas_new` up to and including X. Method gates still apply on top (Surf, rods,
  Rock Smash, Dive for seaweed).
- **P-R3** An HM counts as open (`hm_gates_open`) when the player holds it *and* has the badge that
  allows its field use (M-12), at the point the walkthrough hands it over.
- **P-R4** `[decomp]` **Badge order is looser than this list.** Only Norman's gym checks earlier badges:
  each of the first four gyms adds 1 to `VAR_PETALBURG_GYM_STATE`, and Norman's gym opens at 6
  (i.e. after all four, in any order). Brawly can be deferred until Norman, and nothing from Fortree
  to the Magma Hideout checks Winona's badge. The file keeps the standard order.
- **P-R5** Rival fights depend on the player's starter (the rival takes the starter with the type
  advantage) and on which rival you have (May if you play Brendan, and vice versa). May's and
  Brendan's teams differ in species in two fights: Rustboro if you chose Torchic (Torkoal vs Slugma)
  and Route 119 if you chose Mudkip (Lombre vs Pelipper). The Route 110 lead also differs for Mudkip
  players.
- **P-R6** Nothing is catchable before the first rival fight: Birch hands out Poké Balls afterwards.
- **P-R7** The **eight placements that were judgement calls** were checked against decomp event
  scripts and Bulbapedia on 2026-11-01; each battle's notes cite the evidence (variable and flag
  names are the decomp's). These are P-03, P-04, P-06, P-07, P-09, P-11, P-17/P-18 and P-26/P-27.

### Battles in order

- **P-01** Route 103: Rival (first battle) (`rival1_route103`, at `hoenn-route-103`): badges before: 0, single, required.
  - Trainers: depend on starter and rival (teams: K-rival1_route103)
  - HMs usable: none; key items: none
  - Areas newly reachable before this battle: none
  - Notes: Rival's Lv5 starter has the type advantage. No Poké Balls yet, so nothing is catchable before this fight.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_1#Rival_Battle_1`
- **P-02** Petalburg Woods: Team Aqua Grunt (`grunt_petalburg_woods`, at `petalburg-woods`): badges before: 0, single, required.
  - Trainers: TRAINER_GRUNT_PETALBURG_WOODS (teams: K-grunt_petalburg_woods)
  - HMs usable: none; key items: none
  - Areas newly reachable before this battle: hoenn-route-101, hoenn-route-103, hoenn-route-102, petalburg-city, hoenn-route-104, petalburg-woods
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_2#The_Scuffle`
- **P-03** Rustboro Gym: Roxanne (`gym1_roxanne`, at `rustboro-city`): badges before: 0, single, required.
  - Trainers: TRAINER_ROXANNE_1 (teams: K-gym1_roxanne)
  - HMs usable: none; key items: none
  - Areas newly reachable before this battle: rustboro-city, hoenn-route-116, rusturf-tunnel
  - Notes: Route 116 and the west end of Rusturf Tunnel (Whismur) are open before the gym: nothing blocks Rustboro's east exit, and the Devon Goods theft only starts after this badge (RustboroCity_Gym sets VAR_RUSTBORO_CITY_STATE). The tunnel's far side stays behind Rock Smash boulders. Rustboro's gifts are the Devon fossil revivals (need a fossil from Mirage Tower, much later) and an in-game trade.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_2#Rustboro_Gym`
- **P-04** Rusturf Tunnel: Team Aqua Grunt (Devon Goods) (`grunt_rusturf_tunnel`, at `rusturf-tunnel`): badges before: 1, single, required.
  - Trainers: TRAINER_GRUNT_RUSTURF_TUNNEL (teams: K-grunt_rusturf_tunnel)
  - HMs usable: cut; key items: none
  - Areas newly reachable before this battle: none
  - Notes: The tunnel itself opened before Roxanne; this is the Devon Goods chase.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_2#The_Take-Down`
- **P-05** Rustboro City: Rival (optional) (`rival2_rustboro`, at `rustboro-city`): badges before: 1, single, optional.
  - Trainers: depend on starter and rival (teams: K-rival2_rustboro)
  - HMs usable: cut; key items: none
  - Areas newly reachable before this battle: none
  - Notes: Torchic players: May leads with Torkoal, Brendan with Slugma. Other variants are the same for both rivals.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_3#Rival_Battle_2_(optional)`
- **P-06** Dewford Gym: Brawly (`gym2_brawly`, at `dewford-town`): badges before: 1, single, required.
  - Trainers: TRAINER_BRAWLY_1 (teams: K-gym2_brawly)
  - HMs usable: cut; key items: old-rod
  - Areas newly reachable before this battle: hoenn-route-105, hoenn-route-106, dewford-town, granite-cave, hoenn-route-107, hoenn-route-108, hoenn-route-109, slateport-city
  - Notes: Old Rod comes from the Dewford fisherman before the gym. Granite Cave is reachable via Route 106; Flash (from its Hiker) needs this badge. Once Steven has his letter, Mr. Briney sails Dewford -> Slateport with no badge check (FLAG_DELIVERED_STEVEN_LETTER only), so Slateport and Routes 107-109 open before Brawly. Brawly can even be deferred until Norman: no other event checks his badge.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_3#Dewford_Gym`
- **P-07** Oceanic Museum: Team Aqua Grunts (`grunts_oceanic_museum`, at `slateport-city`): badges before: 2, single, required.
  - Trainers: TRAINER_GRUNT_MUSEUM_1, TRAINER_GRUNT_MUSEUM_2 (teams: K-grunts_oceanic_museum)
  - HMs usable: cut, flash; key items: old-rod
  - Areas newly reachable before this battle: none
  - Notes: Two separate single battles on the museum's second floor. Until this fight, Team Aqua grunts stand across Route 110 just north of Slateport; the museum script hides them (FLAG_HIDE_ROUTE_110_TEAM_AQUA).
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_4#Oceanic_Museum`
- **P-08** Route 110: Rival (`rival3_route110`, at `hoenn-route-110`): badges before: 2, single, required.
  - Trainers: depend on starter and rival (teams: K-rival3_route110)
  - HMs usable: cut, flash; key items: old-rod
  - Areas newly reachable before this battle: hoenn-route-110
  - Notes: Mudkip players: same team for both rivals, but May leads with Wingull and Brendan with Slugma.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_4#Rival_Battle_3`
- **P-09** Mauville City: Wally (`wally_mauville`, at `mauville-city`): badges before: 2, single, required.
  - Trainers: TRAINER_WALLY_MAUVILLE (teams: K-wally_mauville)
  - HMs usable: cut, flash; key items: old-rod
  - Areas newly reachable before this battle: hoenn-route-117, hoenn-route-118
  - Notes: Wally has one Lv16 Ralts. He only battles when you talk to him, but he stands in the gym doorway, so he comes before Wattson. Routes 117 and 118 (west bank) are open as soon as you reach Mauville. Bikes from Rydel's Cycles are available in Mauville before this.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_5#Wally's_Challenge`
- **P-10** Mauville Gym: Wattson (`gym3_wattson`, at `mauville-city`): badges before: 2, single, required.
  - Trainers: TRAINER_WATTSON_1 (teams: K-gym3_wattson)
  - HMs usable: cut, flash; key items: old-rod
  - Areas newly reachable before this battle: none
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_5#Mauville_Gym`
- **P-11** Mt. Chimney: Magma Admin Tabitha (`tabitha_mt_chimney`, at `mt-chimney`): badges before: 3, single, required.
  - Trainers: TRAINER_TABITHA_MT_CHIMNEY (teams: K-tabitha_mt_chimney)
  - HMs usable: cut, flash, rock-smash; key items: old-rod
  - Areas newly reachable before this battle: hoenn-route-112, fiery-path, hoenn-route-113, hoenn-route-114, meteor-falls/main, hoenn-route-115
  - Notes: Rock Smash (Mauville) clears the way north to Route 111/112. Route 111's grass is all inside the sandstorm, so it waits for the Go-Goggles. Route 115 borders Rustboro, but from there you only reach a beach; its grass is reached through the Meteor Falls exit (Bulbapedia: Route 115). A rod works from the beach earlier. Meteor Falls' other rooms need Waterfall.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_7#Challenge_Accepted!`
- **P-12** Mt. Chimney: Magma Leader Maxie (`maxie_mt_chimney`, at `mt-chimney`): badges before: 3, single, required.
  - Trainers: TRAINER_MAXIE_MT_CHIMNEY (teams: K-maxie_mt_chimney)
  - HMs usable: cut, flash, rock-smash; key items: old-rod
  - Areas newly reachable before this battle: none
  - Notes: Straight after Tabitha, with no Pokémon Center in between.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_7#VS_Maxie`
- **P-13** Lavaridge Gym: Flannery (`gym4_flannery`, at `lavaridge-town`): badges before: 3, single, required.
  - Trainers: TRAINER_FLANNERY_1 (teams: K-gym4_flannery)
  - HMs usable: cut, flash, rock-smash; key items: old-rod
  - Areas newly reachable before this battle: jagged-pass, lavaridge-town
  - Notes: Lavaridge's gift is an Egg (Wynaut) from the old woman by the sand baths; you need a free party slot.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_7#Lavaridge_Gym`
- **P-14** Petalburg Gym: Norman (`gym5_norman`, at `petalburg-city`): badges before: 4, single, required.
  - Trainers: TRAINER_NORMAN_1 (teams: K-gym5_norman)
  - HMs usable: cut, flash, rock-smash, strength; key items: old-rod, go-goggles
  - Areas newly reachable before this battle: hoenn-route-111, mirage-tower
  - Notes: Go-Goggles from the rival after Flannery open the Route 111 desert. Mirage Tower (fossil choice) needs the Mach Bike and Rock Smash.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_8#Petalburg_Gym`
- **P-15** Weather Institute: Aqua Admin Shelly (`shelly_weather_institute`, at `hoenn-route-119`): badges before: 5, single, required.
  - Trainers: TRAINER_SHELLY_WEATHER_INSTITUTE (teams: K-shelly_weather_institute)
  - HMs usable: cut, flash, rock-smash, strength, surf; key items: old-rod, good-rod, go-goggles
  - Areas newly reachable before this battle: abandoned-ship, new-mauville, hoenn-route-123, hoenn-route-119/main
  - Notes: Surf (Wally's father, after Norman) opens the water on earlier routes too. Good Rod: fisherman on Route 118's east bank. New Mauville needs Wattson's Basement Key. Feebas: Route 119 tile fishing.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_10#Looking_for_Answers`
- **P-16** Route 119: Rival (`rival4_route119`, at `hoenn-route-119`): badges before: 5, single, required.
  - Trainers: depend on starter and rival (teams: K-rival4_route119)
  - HMs usable: cut, flash, rock-smash, strength, surf; key items: old-rod, good-rod, go-goggles
  - Areas newly reachable before this battle: hoenn-route-119/weather-institute
  - Notes: Mudkip players: May has Lombre, Brendan has Pelipper. The rival gives HM02 Fly afterwards (usable from the 6th badge). Castform is the Weather Institute's thank-you gift for beating Shelly.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_10#Rival_Battle_4`
- **P-17** Fortree Gym: Winona (`gym6_winona`, at `fortree-city`): badges before: 5, single, required.
  - Trainers: TRAINER_WINONA_1 (teams: K-gym6_winona)
  - HMs usable: cut, flash, rock-smash, strength, surf; key items: old-rod, good-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: fortree-city, hoenn-route-120, hoenn-route-121, hoenn-route-122, lilycove-city, mt-pyre, hoenn-safari-zone/sw, hoenn-safari-zone/se, hoenn-safari-zone/nwmach-bike-area, hoenn-safari-zone/neacro-bike-area, magma-hideout
  - Notes: Steven hands over the Devon Scope on Route 120; it reveals the Kecleon blocking the gym (and the devon-scope encounters on Routes 119/120). The same scope opens the way east: Route 121, Lilycove, Mt. Pyre (Surf via Route 122) and, with the Magma Emblem from Mt. Pyre's summit, the Magma Hideout on Jagged Pass. None of it checks this badge. The Safari Zone's bike areas each need one bike (swap at Rydel's); its two expansion areas are postgame.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_11#Fortree_Gym`
- **P-18** Lilycove City: Rival (optional) (`rival5_lilycove`, at `lilycove-city`): badges before: 6, single, optional.
  - Trainers: depend on starter and rival (teams: K-rival5_lilycove)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly; key items: old-rod, good-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: none
  - Notes: The rival is in Lilycove from your first visit until the Hall of Fame (only the Hall of Fame script sets FLAG_HIDE_LILYCOVE_CITY_RIVAL), and the battle has no badge check; only the rival's parting line changes with your badges. Placed at the usual first visit, after Winona; it can come even before Winona once you have the Devon Scope. The walkthrough fights it after the Magma Hideout.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_13#Rival_Battle_5_(optional)`
- **P-19** Magma Hideout: Magma Admin Tabitha (`tabitha_magma_hideout`, at `magma-hideout`): badges before: 6, single, required.
  - Trainers: TRAINER_TABITHA_MAGMA_HIDEOUT (teams: K-tabitha_magma_hideout)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly; key items: old-rod, good-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: none
  - Notes: The Magma Emblem from Mt. Pyre's summit opens the hideout on Jagged Pass.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_12#VS_Tabitha`
- **P-20** Magma Hideout: Magma Leader Maxie (`maxie_magma_hideout`, at `magma-hideout`): badges before: 6, single, required.
  - Trainers: TRAINER_MAXIE_MAGMA_HIDEOUT (teams: K-maxie_magma_hideout)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly; key items: old-rod, good-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: none
  - Notes: Straight after Tabitha.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_12#VS_Maxie`
- **P-21** Aqua Hideout: Aqua Admin Matt (`matt_aqua_hideout`, at `team-aqua-hideout`): badges before: 6, single, required.
  - Trainers: TRAINER_MATT (teams: K-matt_aqua_hideout)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly; key items: old-rod, good-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: team-aqua-hideout
  - Notes: The hideout's two Electrode are disguised as items.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_13#Submarine_room_2`
- **P-22** Mossdeep Gym: Tate & Liza (`gym7_tate_liza`, at `mossdeep-city`): badges before: 6, double, required.
  - Trainers: TRAINER_TATE_AND_LIZA_1 (teams: K-gym7_tate_liza)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly; key items: old-rod, good-rod, super-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: hoenn-route-124/main, mossdeep-city/main, hoenn-route-125, shoal-cave
  - Notes: Double battle. Super Rod: Mossdeep fisherman, before the gym. Shoal Cave's tide rooms alternate every six hours.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_14#Mossdeep_Gym`
- **P-23** Mossdeep Space Center: Maxie & Tabitha (multi battle with Steven) (`space_center`, at `mossdeep-city`): badges before: 7, multi, required.
  - Trainers: TRAINER_MAXIE_MOSSDEEP, TRAINER_TABITHA_MOSSDEEP (teams: K-space_center)
  - Partner: Steven, Metang Lv42, Skarmory Lv43, Aggron Lv44
  - HMs usable: cut, flash, rock-smash, strength, surf, fly; key items: old-rod, good-rod, super-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: none
  - Notes: Two-on-two with Steven as partner; the map script sets it up and both trainer structs say single. Before it: four Magma Grunts on 1F, then three on 2F fought one after another with no break.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_14#VS_Maxie,_Tabitha`
- **P-24** Seafloor Cavern: Aqua Admin Shelly (`shelly_seafloor_cavern`, at `seafloor-cavern`): badges before: 7, single, required.
  - Trainers: TRAINER_SHELLY_SEAFLOOR_CAVERN (teams: K-shelly_seafloor_cavern)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly, dive; key items: old-rod, good-rod, super-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: hoenn-route-124/underwater, hoenn-route-126/main, hoenn-route-126/underwater, hoenn-route-127, hoenn-route-128, seafloor-cavern
  - Notes: Steven gives HM08 Dive after the Space Center. Underwater seaweed holds Chinchou, Clamperl and Relicanth.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_15#Room_7`
- **P-25** Seafloor Cavern: Aqua Leader Archie (`archie_seafloor_cavern`, at `seafloor-cavern`): badges before: 7, single, required.
  - Trainers: TRAINER_ARCHIE (teams: K-archie_seafloor_cavern)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly, dive; key items: old-rod, good-rod, super-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: none
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_15#VS_Archie`
- **P-26** Sootopolis Gym: Juan (`gym8_juan`, at `sootopolis-city`): badges before: 7, single, required.
  - Trainers: TRAINER_JUAN_1 (teams: K-gym8_juan)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly, dive; key items: old-rod, good-rod, super-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: sootopolis-city, cave-of-origin/entrance, cave-of-origin/1f, cave-of-origin/b1f, hoenn-route-129, hoenn-route-130, mirage-island, hoenn-route-131, pacifidlog-town, hoenn-route-132, hoenn-route-133, hoenn-route-134, sky-pillar/1f, sky-pillar/3f, sky-pillar/5f, sky-pillar/apex, desert-ruins, island-cave, ancient-tomb
  - Notes: Juan is the 8th leader in Emerald (Wallace is Champion). Regirock/Regice/Registeel need the Sealed Chamber puzzle on Route 134 (Dig, then Wailord first and Relicanth last in the party). Mirage Island only appears some days. Rayquaza (Lv70) is back at Sky Pillar's apex once it calms Groudon and Kyogre, before this gym (VAR_SKY_PILLAR_STATE >= 2; the door stays open). The cracked upper floors need the Mach Bike. Wallace hands over HM07 Waterfall before the gym, but climbing a waterfall needs this badge (field_control_avatar.c checks FLAG_BADGE08_GET), so Meteor Falls' back rooms (Bagon) open at the next battle.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_17#Sootopolis_Gym`
- **P-27** Victory Road: Wally (`wally_victory_road`, at `hoenn-victory-road`): badges before: 8, single, required.
  - Trainers: TRAINER_WALLY_VR_1 (teams: K-wally_victory_road)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly, dive, waterfall; key items: old-rod, good-rod, super-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: ever-grande-city, hoenn-victory-road, meteor-falls/b1f, meteor-falls/back, meteor-falls/backsmall-room
  - Notes: Bagon is only in Meteor Falls' back small room (B1F 2R). Every Meteor Falls room past 1F 1R needs Waterfall: Bulbapedia marks all B1F items and trainers 'requires Surf and Waterfall'. PokeAPI areas: main = 1F 1R, back / b1f = 1F 2R / B1F 1R (identical tables), backsmall-room = B1F 2R.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_18#VS_Wally`
- **P-28** Elite Four: Sidney (`e4_sidney`, at `ever-grande-city`): badges before: 8, single, required.
  - Trainers: TRAINER_SIDNEY (teams: K-e4_sidney)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly, dive, waterfall; key items: old-rod, good-rod, super-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: none
  - Notes: The Elite Four and Champion are a gauntlet: no Pokémon Center and no catching between these five fights. Bag items still work.
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_19#Battle_1:_Sidney`
- **P-29** Elite Four: Phoebe (`e4_phoebe`, at `ever-grande-city`): badges before: 8, single, required.
  - Trainers: TRAINER_PHOEBE (teams: K-e4_phoebe)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly, dive, waterfall; key items: old-rod, good-rod, super-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: none
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_19#Battle_2:_Phoebe`
- **P-30** Elite Four: Glacia (`e4_glacia`, at `ever-grande-city`): badges before: 8, single, required.
  - Trainers: TRAINER_GLACIA (teams: K-e4_glacia)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly, dive, waterfall; key items: old-rod, good-rod, super-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: none
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_19#Battle_3:_Glacia`
- **P-31** Elite Four: Drake (`e4_drake`, at `ever-grande-city`): badges before: 8, single, required.
  - Trainers: TRAINER_DRAKE (teams: K-e4_drake)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly, dive, waterfall; key items: old-rod, good-rod, super-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: none
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_19#Battle_4:_Drake`
- **P-32** Champion: Wallace (`champion_wallace`, at `ever-grande-city`): badges before: 8, single, required.
  - Trainers: TRAINER_WALLACE (teams: K-champion_wallace)
  - HMs usable: cut, flash, rock-smash, strength, surf, fly, dive, waterfall; key items: old-rod, good-rod, super-rod, go-goggles, devon-scope
  - Areas newly reachable before this battle: none
  - Notes: Emerald's Champion is Wallace (Steven is Champion in Ruby/Sapphire).
  - Source: `guide:Walkthrough:Pokemon_Emerald/Part_19#Champion`

### Never reachable before the Champion (N)

- **N-01** `littleroot-town`: Johto starters from Birch after completing the Hoenn Pokédex (postgame)
- **N-02** `mossdeep-city/stevens-house`: Beldum in Steven's house after the Hall of Fame
- **N-03** `hoenn-safari-zone/expansion-north`: Safari Zone expansion opens after the Hall of Fame
- **N-04** `hoenn-safari-zone/expansion-south`: Safari Zone expansion opens after the Hall of Fame
- **N-05** `cave-of-origin/b2f`: unused Ruby/Sapphire map in Emerald (PokeAPI still lists encounters)
- **N-06** `cave-of-origin/b3f`: unused Ruby/Sapphire map in Emerald (PokeAPI still lists encounters)
- **N-07** `hoenn-altering-cave`: opens after the Hall of Fame
- **N-08** `desert-underpass`: opens after the Hall of Fame
- **N-09** `marine-cave`: postgame (Kyogre)
- **N-10** `terra-cave`: postgame (Groudon)
- **N-11** `roaming-hoenn`: Latios/Latias start roaming after the Hall of Fame
- **N-12** `artisan-cave`: Battle Frontier (postgame)
- **N-13** `hoenn-battle-frontier`: Battle Frontier (postgame)
- **N-14** `southern-island`: Eon Ticket event
- **N-15** `faraway-island`: Old Sea Map event
- **N-16** `birth-island`: Aurora Ticket event
- **N-17** `navel-rock`: Mystic Ticket event
- **N-18** `hoenn-pokecenter`: Colosseum bonus disc (Japan) gift

## 5. Locations and encounter mapping

- **L-01** `[decomp]` The decomp's region-map sections (MAPSEC) bridge maps to PokeAPI: a section's
  index equals PokeAPI's Gen 3 `location_game_indices`. Randomizer logs name wild sets by MAPSEC name.
- **L-02** Underwater maps (Routes 124 and 126) are PokeAPI areas `hoenn-route-124/underwater` and
  `hoenn-route-126/underwater`; their encounters use the `seaweed` method and need Dive.
- **L-03** `[decomp]` Emerald's Aqua Hideout section has no PokeAPI Gen 3 index (the old index points
  at Ruby's Magma Hideout); the build maps it to `team-aqua-hideout` by hand.
- **L-04** `[decomp]` Altering Cave (Route 103) opens only after the Hall of Fame: `Route103_OnLoad`
  sets the cave-entrance tiles only when `FLAG_SYS_GAME_CLEAR` is set. Of its wild sets, only the
  first (Zubat) is active without Mystery Gift events, so only that set counts.
- **L-05** Mirage Island lives inside the Route 130 map and only appears on some days; its table is
  all Wynaut.
- **L-06** PokeAPI lists Emerald encounters for Cave of Origin B2F and B3F, which are unused
  Ruby/Sapphire maps in Emerald. They are marked never reachable.
- **L-07** Meteor Falls' PokeAPI areas map to ROM rooms by wild table: `main` = 1F 1R; `back` and
  `b1f` = 1F 2R and B1F 1R (identical tables, so which is which can't be told from data);
  `backsmall-room` = B1F 2R (the only Bagon room).
- **L-08** `[decomp]` Wild tables: 216 of 219 PokeAPI location/method pairs match the decomp outright;
  the other three are explained by the `seaweed` method and Mirage Island being in the Route 130 map.
- **L-09** Encounter conditions the data uses (generated below) gate fossils, in-game trades, the
  TV choice that sets the roaming Latios/Latias, and Hall of Fame progress.


**L-09 encounter conditions**: `item-claw-fossil`, `item-root-fossil`, `story-progress-hall-of-fame`, `trade-bagon`, `trade-ralts`, `trade-skitty`, `trade-volbeat`, `tv-option-blue`, `tv-option-red`

### Special encounters (SE): statics, gifts, trades, roamers and other non-wild methods

| ID | Location/area | Method | Species | Level | Conditions |
|---|---|---|---|---|---|
| SE-01 | hoenn-pokecenter | colosseum-bonus-disc-jpn | Pikachu | 10 | — |
| SE-02 | hoenn-pokecenter | colosseum-bonus-disc-jpn | Celebi | 10 | — |
| SE-03 | hoenn-route-119 | devon-scope | Kecleon | 30 | — |
| SE-04 | hoenn-route-119 | devon-scope | Kecleon | 30 | — |
| SE-05 | hoenn-route-120 | devon-scope | Kecleon | 30 | — |
| SE-06 | hoenn-route-120 | devon-scope | Kecleon | 30 | — |
| SE-07 | hoenn-route-120 | devon-scope | Kecleon | 30 | — |
| SE-08 | hoenn-route-120 | devon-scope | Kecleon | 30 | — |
| SE-09 | hoenn-route-120 | devon-scope | Kecleon | 30 | — |
| SE-10 | hoenn-route-120 | devon-scope | Kecleon | 30 | — |
| SE-11 | hoenn-route-119 | feebas-tile-fishing | Feebas | 20-25 | — |
| SE-12 | hoenn-route-101 | gift | Treecko | 5 | — |
| SE-13 | hoenn-route-101 | gift | Torchic | 5 | — |
| SE-14 | hoenn-route-101 | gift | Mudkip | 5 | — |
| SE-15 | hoenn-route-119/weather-institute | gift | Castform | 25 | — |
| SE-16 | littleroot-town | gift | Chikorita | 5 | — |
| SE-17 | littleroot-town | gift | Cyndaquil | 5 | — |
| SE-18 | littleroot-town | gift | Totodile | 5 | — |
| SE-19 | mossdeep-city/stevens-house | gift | Beldum | 5 | — |
| SE-20 | rustboro-city | gift | Lileep | 20 | item-root-fossil |
| SE-21 | rustboro-city | gift | Anorith | 20 | item-claw-fossil |
| SE-22 | lavaridge-town | gift-egg | Wynaut | 5 | — |
| SE-23 | fortree-city | npc-trade | Plusle | 5-100 | trade-volbeat |
| SE-24 | hoenn-battle-frontier/area | npc-trade | Meowth | 5-100 | trade-skitty |
| SE-25 | pacifidlog-town | npc-trade | Horsea | 5-100 | trade-bagon |
| SE-26 | rustboro-city | npc-trade | Seedot | 4-100 | trade-ralts |
| SE-27 | roaming-hoenn/area | roaming-grass | Latias | 40 | story-progress-hall-of-fame, tv-option-red |
| SE-28 | roaming-hoenn/area | roaming-grass | Latios | 40 | story-progress-hall-of-fame, tv-option-blue |
| SE-29 | roaming-hoenn/area | roaming-water | Latias | 40 | — |
| SE-30 | roaming-hoenn/area | roaming-water | Latios | 40 | — |
| SE-31 | ancient-tomb/area | static | Registeel | 40 | — |
| SE-32 | birth-island/area | static | Deoxys | 30 | — |
| SE-33 | desert-ruins/area | static | Regirock | 40 | — |
| SE-34 | faraway-island/area | static | Mew | 30 | — |
| SE-35 | island-cave/area | static | Regice | 40 | — |
| SE-36 | marine-cave/area | static | Kyogre | 70 | — |
| SE-37 | navel-rock/area | static | Lugia | 70 | — |
| SE-38 | navel-rock/area | static | Ho-Oh | 70 | — |
| SE-39 | new-mauville | static | Voltorb | 25 | — |
| SE-40 | sky-pillar/apex | static | Rayquaza | 70 | — |
| SE-41 | southern-island | static | Latias | 50 | — |
| SE-42 | southern-island | static | Latios | 50 | — |
| SE-43 | team-aqua-hideout | static | Electrode | 30 | — |
| SE-44 | terra-cave/area | static | Groudon | 70 | — |
| SE-45 | hoenn-battle-frontier/area | wailmer-pail | Sudowoodo | 40 | — |

## 6. Trainer teams for the story battles (K)

`[decomp]` From `trainer_parties.h` and `trainers.h`. Moves marked *default* were computed with M-08; *custom* are written in the party data. IVs are on the 0–31 scale (M-09).

### K-rival1_route103: Route 103: Rival (first battle)

- treecko player, rival may: **Pokémon Trainer May** `TRAINER_MAY_ROUTE_103_TREECKO`; bag: none
  - Lv5 Torchic, IVs 0: Scratch / Growl (default)
- treecko player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_ROUTE_103_TREECKO`; bag: none
  - Lv5 Torchic, IVs 0: Scratch / Growl (default)
- torchic player, rival may: **Pokémon Trainer May** `TRAINER_MAY_ROUTE_103_TORCHIC`; bag: none
  - Lv5 Mudkip, IVs 0: Tackle / Growl (default)
- torchic player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_ROUTE_103_TORCHIC`; bag: none
  - Lv5 Mudkip, IVs 0: Tackle / Growl (default)
- mudkip player, rival may: **Pokémon Trainer May** `TRAINER_MAY_ROUTE_103_MUDKIP`; bag: none
  - Lv5 Treecko, IVs 0: Pound / Leer (default)
- mudkip player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_ROUTE_103_MUDKIP`; bag: none
  - Lv5 Treecko, IVs 0: Pound / Leer (default)

### K-grunt_petalburg_woods: Petalburg Woods: Team Aqua Grunt

- **Team Aqua Grunt** `TRAINER_GRUNT_PETALBURG_WOODS`; bag: none
  - Lv9 Poochyena, IVs 0: Tackle / Howl / Sand Attack (default)

### K-gym1_roxanne: Rustboro Gym: Roxanne

- **Leader Roxanne** `TRAINER_ROXANNE_1`; bag: Potion, Potion
  - Lv12 Geodude, IVs 12: Tackle / Defense Curl / Rock Throw / Rock Tomb (custom)
  - Lv12 Geodude, IVs 12: Tackle / Defense Curl / Rock Throw / Rock Tomb (custom)
  - Lv15 Nosepass @ Oran Berry, IVs 24: Block / Harden / Tackle / Rock Tomb (custom)

### K-grunt_rusturf_tunnel: Rusturf Tunnel: Team Aqua Grunt (Devon Goods)

- **Team Aqua Grunt** `TRAINER_GRUNT_RUSTURF_TUNNEL`; bag: none
  - Lv11 Poochyena, IVs 0: Tackle / Howl / Sand Attack (default)

### K-rival2_rustboro: Rustboro City: Rival (optional)

- treecko player, rival may: **Pokémon Trainer May** `TRAINER_MAY_RUSTBORO_TREECKO`; bag: none
  - Lv13 Lotad, IVs 3: Astonish / Growl / Absorb / Nature Power (default)
  - Lv15 Torchic, IVs 6: Scratch / Growl / Focus Energy / Ember (default)
- treecko player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_RUSTBORO_TREECKO`; bag: none
  - Lv13 Lotad, IVs 3: Astonish / Growl / Absorb / Nature Power (default)
  - Lv15 Torchic, IVs 6: Scratch / Growl / Focus Energy / Ember (default)
- torchic player, rival may: **Pokémon Trainer May** `TRAINER_MAY_RUSTBORO_TORCHIC`; bag: none
  - Lv13 Torkoal, IVs 3: Ember / Smog / Curse (default)
  - Lv15 Mudkip, IVs 6: Growl / Mud-Slap / Water Gun / Bide (default)
- torchic player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_RUSTBORO_TORCHIC`; bag: none
  - Lv13 Slugma, IVs 3: Yawn / Smog / Ember (default)
  - Lv15 Mudkip, IVs 6: Growl / Mud-Slap / Water Gun / Bide (default)
- mudkip player, rival may: **Pokémon Trainer May** `TRAINER_MAY_RUSTBORO_MUDKIP`; bag: none
  - Lv13 Wingull, IVs 3: Growl / Water Gun / Supersonic / Wing Attack (default)
  - Lv15 Treecko, IVs 6: Pound / Leer / Absorb / Quick Attack (default)
- mudkip player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_RUSTBORO_MUDKIP`; bag: none
  - Lv13 Wingull, IVs 3: Growl / Water Gun / Supersonic / Wing Attack (default)
  - Lv15 Treecko, IVs 6: Pound / Leer / Absorb / Quick Attack (default)

### K-gym2_brawly: Dewford Gym: Brawly

- **Leader Brawly** `TRAINER_BRAWLY_1`; bag: Super Potion, Super Potion
  - Lv16 Machop, IVs 12: Karate Chop / Low Kick / Seismic Toss / Bulk Up (custom)
  - Lv16 Meditite, IVs 12: Focus Punch / Light Screen / Reflect / Bulk Up (custom)
  - Lv19 Makuhita @ Sitrus Berry, IVs 24: Arm Thrust / Vital Throw / Reversal / Bulk Up (custom)

### K-grunts_oceanic_museum: Oceanic Museum: Team Aqua Grunts

- **Team Aqua Grunt** `TRAINER_GRUNT_MUSEUM_1`; bag: none
  - Lv15 Carvanha, IVs 0: Leer / Bite / Rage / Focus Energy (default)
- **Team Aqua Grunt** `TRAINER_GRUNT_MUSEUM_2`; bag: none
  - Lv14 Zubat, IVs 0: Leech Life / Supersonic / Astonish (default)
  - Lv14 Carvanha, IVs 0: Leer / Bite / Rage / Focus Energy (default)

### K-rival3_route110: Route 110: Rival

- treecko player, rival may: **Pokémon Trainer May** `TRAINER_MAY_ROUTE_110_TREECKO`; bag: none
  - Lv18 Wingull, IVs 6: Growl / Water Gun / Supersonic / Wing Attack (default)
  - Lv18 Lombre, IVs 6: Astonish / Growl / Absorb / Nature Power (default)
  - Lv20 Combusken, IVs 12: Focus Energy / Ember / Double Kick / Peck (default)
- treecko player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_ROUTE_110_TREECKO`; bag: none
  - Lv18 Wingull, IVs 6: Growl / Water Gun / Supersonic / Wing Attack (default)
  - Lv18 Lombre, IVs 6: Astonish / Growl / Absorb / Nature Power (default)
  - Lv20 Combusken, IVs 12: Focus Energy / Ember / Double Kick / Peck (default)
- torchic player, rival may: **Pokémon Trainer May** `TRAINER_MAY_ROUTE_110_TORCHIC`; bag: none
  - Lv18 Lombre, IVs 6: Astonish / Growl / Absorb / Nature Power (default)
  - Lv18 Slugma, IVs 6: Yawn / Smog / Ember / Rock Throw (default)
  - Lv20 Marshtomp, IVs 12: Water Gun / Bide / Mud Shot / Foresight (default)
- torchic player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_ROUTE_110_TORCHIC`; bag: none
  - Lv18 Lombre, IVs 6: Astonish / Growl / Absorb / Nature Power (default)
  - Lv18 Slugma, IVs 6: Yawn / Smog / Ember / Rock Throw (default)
  - Lv20 Marshtomp, IVs 12: Water Gun / Bide / Mud Shot / Foresight (default)
- mudkip player, rival may: **Pokémon Trainer May** `TRAINER_MAY_ROUTE_110_MUDKIP`; bag: none
  - Lv18 Wingull, IVs 6: Growl / Water Gun / Supersonic / Wing Attack (default)
  - Lv18 Slugma, IVs 6: Yawn / Smog / Ember / Rock Throw (default)
  - Lv20 Grovyle, IVs 12: Absorb / Quick Attack / Fury Cutter / Pursuit (default)
- mudkip player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_ROUTE_110_MUDKIP`; bag: none
  - Lv18 Slugma, IVs 6: Yawn / Smog / Ember / Rock Throw (default)
  - Lv18 Wingull, IVs 6: Growl / Water Gun / Supersonic / Wing Attack (default)
  - Lv20 Grovyle, IVs 12: Absorb / Quick Attack / Fury Cutter / Pursuit (default)

### K-wally_mauville: Mauville City: Wally

- **Pokémon Trainer Wally** `TRAINER_WALLY_MAUVILLE`; bag: none
  - Lv16 Ralts, IVs 3: Growl / Confusion / Double Team / Teleport (default)

### K-gym3_wattson: Mauville Gym: Wattson

- **Leader Wattson** `TRAINER_WATTSON_1`; bag: Super Potion, Super Potion
  - Lv20 Voltorb, IVs 24: Rollout / Spark / Self-Destruct / Shock Wave (custom)
  - Lv20 Electrike, IVs 24: Shock Wave / Leer / Quick Attack / Howl (custom)
  - Lv22 Magneton, IVs 26: Supersonic / Shock Wave / Thunder Wave / Sonic Boom (custom)
  - Lv24 Manectric @ Sitrus Berry, IVs 30: Quick Attack / Thunder Wave / Shock Wave / Howl (custom)

### K-tabitha_mt_chimney: Mt. Chimney: Magma Admin Tabitha

- **Magma Admin Tabitha** `TRAINER_TABITHA_MT_CHIMNEY`; bag: none
  - Lv18 Numel, IVs 6: Growl / Tackle / Ember (default)
  - Lv20 Poochyena, IVs 6: Howl / Sand Attack / Bite / Odor Sleuth (default)
  - Lv22 Numel, IVs 6: Growl / Tackle / Ember / Magnitude (default)
  - Lv22 Zubat, IVs 6: Supersonic / Astonish / Bite / Wing Attack (default)

### K-maxie_mt_chimney: Mt. Chimney: Magma Leader Maxie

- **Magma Leader Maxie** `TRAINER_MAXIE_MT_CHIMNEY`; bag: Super Potion, Super Potion
  - Lv24 Mightyena, IVs 18: Sand Attack / Bite / Odor Sleuth / Roar (default)
  - Lv24 Zubat, IVs 18: Supersonic / Astonish / Bite / Wing Attack (default)
  - Lv25 Camerupt, IVs 18: Tackle / Ember / Magnitude / Focus Energy (default)

### K-gym4_flannery: Lavaridge Gym: Flannery

- **Leader Flannery** `TRAINER_FLANNERY_1`; bag: Hyper Potion, Hyper Potion
  - Lv24 Numel, IVs 24: Overheat / Take Down / Magnitude / Sunny Day (custom)
  - Lv24 Slugma, IVs 24: Overheat / Smog / Light Screen / Sunny Day (custom)
  - Lv26 Camerupt, IVs 30: Overheat / Tackle / Sunny Day / Attract (custom)
  - Lv29 Torkoal @ White Herb, IVs 30: Overheat / Sunny Day / Body Slam / Attract (custom)

### K-gym5_norman: Petalburg Gym: Norman

- **Leader Norman** `TRAINER_NORMAN_1`; bag: Hyper Potion, Hyper Potion
  - Lv27 Spinda, IVs 24: Teeter Dance / Psybeam / Facade / Encore (custom)
  - Lv27 Vigoroth, IVs 24: Slash / Facade / Encore / Feint Attack (custom)
  - Lv29 Linoone, IVs 24: Slash / Belly Drum / Facade / Headbutt (custom)
  - Lv31 Slaking @ Sitrus Berry, IVs 30: Counter / Yawn / Facade / Feint Attack (custom)

### K-shelly_weather_institute: Weather Institute: Aqua Admin Shelly

- **Aqua Admin Shelly** `TRAINER_SHELLY_WEATHER_INSTITUTE`; bag: none
  - Lv28 Carvanha, IVs 6: Focus Energy / Scary Face / Crunch / Screech (default)
  - Lv28 Mightyena, IVs 6: Bite / Odor Sleuth / Roar / Swagger (default)

### K-rival4_route119: Route 119: Rival

- treecko player, rival may: **Pokémon Trainer May** `TRAINER_MAY_ROUTE_119_TREECKO`; bag: none
  - Lv29 Pelipper, IVs 12: Wing Attack / Supersonic / Mist / Protect (default)
  - Lv29 Lombre, IVs 12: Absorb / Nature Power / Fake Out / Fury Swipes (default)
  - Lv31 Combusken, IVs 18: Double Kick / Peck / Sand Attack / Bulk Up (default)
- treecko player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_ROUTE_119_TREECKO`; bag: none
  - Lv29 Pelipper, IVs 12: Wing Attack / Supersonic / Mist / Protect (default)
  - Lv29 Lombre, IVs 12: Absorb / Nature Power / Fake Out / Fury Swipes (default)
  - Lv31 Combusken, IVs 18: Double Kick / Peck / Sand Attack / Bulk Up (default)
- torchic player, rival may: **Pokémon Trainer May** `TRAINER_MAY_ROUTE_119_TORCHIC`; bag: none
  - Lv29 Lombre, IVs 12: Absorb / Nature Power / Fake Out / Fury Swipes (default)
  - Lv29 Slugma, IVs 12: Ember / Rock Throw / Harden / Amnesia (default)
  - Lv31 Marshtomp, IVs 18: Mud Shot / Foresight / Mud Sport / Take Down (default)
- torchic player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_ROUTE_119_TORCHIC`; bag: none
  - Lv29 Lombre, IVs 12: Absorb / Nature Power / Fake Out / Fury Swipes (default)
  - Lv29 Slugma, IVs 12: Ember / Rock Throw / Harden / Amnesia (default)
  - Lv31 Marshtomp, IVs 18: Mud Shot / Foresight / Mud Sport / Take Down (default)
- mudkip player, rival may: **Pokémon Trainer May** `TRAINER_MAY_ROUTE_119_MUDKIP`; bag: none
  - Lv29 Slugma, IVs 12: Ember / Rock Throw / Harden / Amnesia (default)
  - Lv29 Lombre, IVs 12: Absorb / Nature Power / Fake Out / Fury Swipes (default)
  - Lv31 Grovyle, IVs 18: Fury Cutter / Pursuit / Screech / Leaf Blade (default)
- mudkip player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_ROUTE_119_MUDKIP`; bag: none
  - Lv29 Slugma, IVs 12: Ember / Rock Throw / Harden / Amnesia (default)
  - Lv29 Pelipper, IVs 12: Wing Attack / Supersonic / Mist / Protect (default)
  - Lv31 Grovyle, IVs 18: Fury Cutter / Pursuit / Screech / Leaf Blade (default)

### K-gym6_winona: Fortree Gym: Winona

- **Leader Winona** `TRAINER_WINONA_1`; bag: Hyper Potion, Hyper Potion
  - Lv29 Swablu, IVs 25: Perish Song / Mirror Move / Safeguard / Aerial Ace (custom)
  - Lv29 Tropius, IVs 25: Sunny Day / Aerial Ace / Solar Beam / Synthesis (custom)
  - Lv30 Pelipper, IVs 25: Water Gun / Supersonic / Protect / Aerial Ace (custom)
  - Lv31 Skarmory, IVs 26: Sand Attack / Fury Attack / Steel Wing / Aerial Ace (custom)
  - Lv33 Altaria @ Oran Berry, IVs 31: Earthquake / Dragon Breath / Dragon Dance / Aerial Ace (custom)

### K-rival5_lilycove: Lilycove City: Rival (optional)

- treecko player, rival may: **Pokémon Trainer May** `TRAINER_MAY_LILYCOVE_TREECKO`; bag: none
  - Lv31 Tropius, IVs 18: Stomp / Sweet Scent / Whirlwind / Magical Leaf (default)
  - Lv32 Pelipper, IVs 18: Wing Attack / Supersonic / Mist / Protect (default)
  - Lv32 Ludicolo, IVs 18: Astonish / Growl / Absorb / Nature Power (default)
  - Lv34 Combusken, IVs 24: Peck / Sand Attack / Bulk Up / Quick Attack (default)
- treecko player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_LILYCOVE_TREECKO`; bag: none
  - Lv31 Tropius, IVs 18: Stomp / Sweet Scent / Whirlwind / Magical Leaf (default)
  - Lv32 Pelipper, IVs 18: Wing Attack / Supersonic / Mist / Protect (default)
  - Lv32 Ludicolo, IVs 18: Astonish / Growl / Absorb / Nature Power (default)
  - Lv34 Combusken, IVs 24: Peck / Sand Attack / Bulk Up / Quick Attack (default)
- torchic player, rival may: **Pokémon Trainer May** `TRAINER_MAY_LILYCOVE_TORCHIC`; bag: none
  - Lv31 Tropius, IVs 18: Stomp / Sweet Scent / Whirlwind / Magical Leaf (default)
  - Lv32 Ludicolo, IVs 18: Astonish / Growl / Absorb / Nature Power (default)
  - Lv32 Slugma, IVs 18: Ember / Rock Throw / Harden / Amnesia (default)
  - Lv34 Marshtomp, IVs 24: Mud Shot / Foresight / Mud Sport / Take Down (default)
- torchic player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_LILYCOVE_TORCHIC`; bag: none
  - Lv31 Tropius, IVs 18: Stomp / Sweet Scent / Whirlwind / Magical Leaf (default)
  - Lv32 Ludicolo, IVs 18: Astonish / Growl / Absorb / Nature Power (default)
  - Lv32 Slugma, IVs 18: Ember / Rock Throw / Harden / Amnesia (default)
  - Lv34 Marshtomp, IVs 24: Mud Shot / Foresight / Mud Sport / Take Down (default)
- mudkip player, rival may: **Pokémon Trainer May** `TRAINER_MAY_LILYCOVE_MUDKIP`; bag: none
  - Lv31 Tropius, IVs 18: Stomp / Sweet Scent / Whirlwind / Magical Leaf (default)
  - Lv32 Slugma, IVs 18: Ember / Rock Throw / Harden / Amnesia (default)
  - Lv32 Pelipper, IVs 18: Wing Attack / Supersonic / Mist / Protect (default)
  - Lv34 Grovyle, IVs 24: Fury Cutter / Pursuit / Screech / Leaf Blade (default)
- mudkip player, rival brendan: **Pokémon Trainer Brendan** `TRAINER_BRENDAN_LILYCOVE_MUDKIP`; bag: none
  - Lv31 Tropius, IVs 18: Stomp / Sweet Scent / Whirlwind / Magical Leaf (default)
  - Lv32 Slugma, IVs 18: Ember / Rock Throw / Harden / Amnesia (default)
  - Lv32 Pelipper, IVs 18: Wing Attack / Supersonic / Mist / Protect (default)
  - Lv34 Grovyle, IVs 24: Fury Cutter / Pursuit / Screech / Leaf Blade (default)

### K-tabitha_magma_hideout: Magma Hideout: Magma Admin Tabitha

- **Magma Admin Tabitha** `TRAINER_TABITHA_MAGMA_HIDEOUT`; bag: none
  - Lv26 Numel, IVs 9: Tackle / Ember / Magnitude / Focus Energy (default)
  - Lv28 Mightyena, IVs 9: Bite / Odor Sleuth / Roar / Swagger (default)
  - Lv30 Zubat, IVs 9: Astonish / Bite / Wing Attack / Confuse Ray (default)
  - Lv33 Camerupt, IVs 9: Focus Energy / Take Down / Amnesia / Rock Slide (default)

### K-maxie_magma_hideout: Magma Hideout: Magma Leader Maxie

- **Magma Leader Maxie** `TRAINER_MAXIE_MAGMA_HIDEOUT`; bag: Super Potion, Super Potion
  - Lv37 Mightyena, IVs 18: Roar / Swagger / Scary Face / Take Down (default)
  - Lv38 Crobat, IVs 18: Bite / Wing Attack / Confuse Ray / Air Cutter (default)
  - Lv39 Camerupt, IVs 18: Take Down / Amnesia / Rock Slide / Earthquake (default)

### K-matt_aqua_hideout: Aqua Hideout: Aqua Admin Matt

- **Aqua Admin Matt** `TRAINER_MATT`; bag: Super Potion
  - Lv34 Mightyena, IVs 6: Odor Sleuth / Roar / Swagger / Scary Face (default)
  - Lv34 Golbat, IVs 6: Astonish / Bite / Wing Attack / Confuse Ray (default)

### K-gym7_tate_liza: Mossdeep Gym: Tate & Liza

- **Leader Tate&Liza (double)** `TRAINER_TATE_AND_LIZA_1`; bag: Hyper Potion, Hyper Potion, Hyper Potion, Hyper Potion
  - Lv41 Claydol, IVs 30: Earthquake / Ancient Power / Psychic / Light Screen (custom)
  - Lv41 Xatu, IVs 30: Psychic / Sunny Day / Confuse Ray / Calm Mind (custom)
  - Lv42 Lunatone @ Sitrus Berry, IVs 30: Light Screen / Psychic / Hypnosis / Calm Mind (custom)
  - Lv42 Solrock @ Sitrus Berry, IVs 30: Sunny Day / Solar Beam / Psychic / Flamethrower (custom)

### K-space_center: Mossdeep Space Center: Maxie & Tabitha (multi battle with Steven)

- **Magma Leader Maxie** `TRAINER_MAXIE_MOSSDEEP`; bag: none
  - Lv42 Mightyena, IVs 18: Swagger / Scary Face / Take Down / Taunt (default)
  - Lv43 Crobat, IVs 18: Wing Attack / Confuse Ray / Air Cutter / Mean Look (default)
  - Lv44 Camerupt, IVs 18: Take Down / Amnesia / Rock Slide / Earthquake (default)
- **Magma Admin Tabitha** `TRAINER_TABITHA_MOSSDEEP`; bag: none
  - Lv36 Camerupt, IVs 12: Focus Energy / Take Down / Amnesia / Rock Slide (default)
  - Lv38 Mightyena, IVs 12: Roar / Swagger / Scary Face / Take Down (default)
  - Lv40 Golbat, IVs 12: Bite / Wing Attack / Confuse Ray / Air Cutter (default)

### K-shelly_seafloor_cavern: Seafloor Cavern: Aqua Admin Shelly

- **Aqua Admin Shelly** `TRAINER_SHELLY_SEAFLOOR_CAVERN`; bag: none
  - Lv37 Sharpedo, IVs 12: Scary Face / Crunch / Screech / Slash (default)
  - Lv37 Mightyena, IVs 12: Roar / Swagger / Scary Face / Take Down (default)

### K-archie_seafloor_cavern: Seafloor Cavern: Aqua Leader Archie

- **Aqua Leader Archie** `TRAINER_ARCHIE`; bag: Super Potion, Super Potion
  - Lv41 Mightyena, IVs 18: Roar / Swagger / Scary Face / Take Down (default)
  - Lv41 Crobat, IVs 18: Bite / Wing Attack / Confuse Ray / Air Cutter (default)
  - Lv43 Sharpedo, IVs 18: Screech / Slash / Taunt / Swagger (default)

### K-gym8_juan: Sootopolis Gym: Juan

- **Leader Juan** `TRAINER_JUAN_1`; bag: Hyper Potion, Hyper Potion
  - Lv41 Luvdisc, IVs 24: Water Pulse / Attract / Sweet Kiss / Flail (custom)
  - Lv41 Whiscash, IVs 24: Rain Dance / Water Pulse / Amnesia / Earthquake (custom)
  - Lv43 Sealeo, IVs 24: Encore / Body Slam / Aurora Beam / Water Pulse (custom)
  - Lv43 Crawdaunt, IVs 24: Water Pulse / Crabhammer / Taunt / Leer (custom)
  - Lv46 Kingdra @ Chesto Berry, IVs 30: Water Pulse / Double Team / Ice Beam / Rest (custom)

### K-wally_victory_road: Victory Road: Wally

- **Pokémon Trainer Wally** `TRAINER_WALLY_VR_1`; bag: Full Restore, Full Restore
  - Lv44 Altaria, IVs 18: Aerial Ace / Safeguard / Dragon Breath / Dragon Dance (custom)
  - Lv43 Delcatty, IVs 18: Sing / Assist / Charm / Feint Attack (custom)
  - Lv44 Roselia, IVs 18: Magical Leaf / Leech Seed / Giga Drain / Toxic (custom)
  - Lv41 Magneton, IVs 18: Supersonic / Thunderbolt / Tri Attack / Screech (custom)
  - Lv45 Gardevoir, IVs 30: Double Team / Calm Mind / Psychic / Future Sight (custom)

### K-e4_sidney: Elite Four: Sidney

- **Elite Four Sidney** `TRAINER_SIDNEY`; bag: Full Restore, Full Restore
  - Lv46 Mightyena, IVs 30: Roar / Double-Edge / Sand Attack / Crunch (custom)
  - Lv48 Shiftry, IVs 30: Torment / Double Team / Swagger / Extrasensory (custom)
  - Lv46 Cacturne, IVs 30: Leech Seed / Feint Attack / Needle Arm / Cotton Spore (custom)
  - Lv48 Crawdaunt, IVs 30: Surf / Swords Dance / Strength / Facade (custom)
  - Lv49 Absol @ Sitrus Berry, IVs 31: Aerial Ace / Rock Slide / Swords Dance / Slash (custom)

### K-e4_phoebe: Elite Four: Phoebe

- **Elite Four Phoebe** `TRAINER_PHOEBE`; bag: Full Restore, Full Restore
  - Lv48 Dusclops, IVs 30: Shadow Punch / Confuse Ray / Curse / Protect (custom)
  - Lv49 Banette, IVs 30: Shadow Ball / Grudge / Will-O-Wisp / Feint Attack (custom)
  - Lv50 Sableye, IVs 30: Shadow Ball / Double Team / Night Shade / Feint Attack (custom)
  - Lv49 Banette, IVs 30: Shadow Ball / Psychic / Thunderbolt / Facade (custom)
  - Lv51 Dusclops @ Sitrus Berry, IVs 31: Shadow Ball / Ice Beam / Rock Slide / Earthquake (custom)

### K-e4_glacia: Elite Four: Glacia

- **Elite Four Glacia** `TRAINER_GLACIA`; bag: Full Restore, Full Restore
  - Lv50 Sealeo, IVs 30: Encore / Body Slam / Hail / Ice Ball (custom)
  - Lv50 Glalie, IVs 30: Light Screen / Crunch / Icy Wind / Ice Beam (custom)
  - Lv52 Sealeo, IVs 30: Attract / Double-Edge / Hail / Blizzard (custom)
  - Lv52 Glalie, IVs 30: Shadow Ball / Explosion / Hail / Ice Beam (custom)
  - Lv53 Walrein @ Sitrus Berry, IVs 31: Surf / Body Slam / Ice Beam / Sheer Cold (custom)

### K-e4_drake: Elite Four: Drake

- **Elite Four Drake** `TRAINER_DRAKE`; bag: Full Restore, Full Restore
  - Lv52 Shelgon, IVs 30: Rock Tomb / Dragon Claw / Protect / Double-Edge (custom)
  - Lv54 Altaria, IVs 30: Double-Edge / Dragon Breath / Dragon Dance / Aerial Ace (custom)
  - Lv53 Kingdra, IVs 30: Smokescreen / Dragon Dance / Surf / Body Slam (custom)
  - Lv53 Flygon, IVs 30: Flamethrower / Crunch / Dragon Breath / Earthquake (custom)
  - Lv55 Salamence @ Sitrus Berry, IVs 31: Flamethrower / Dragon Claw / Rock Slide / Crunch (custom)

### K-champion_wallace: Champion: Wallace

- **Champion Wallace** `TRAINER_WALLACE`; bag: Full Restore, Full Restore, Full Restore, Full Restore
  - Lv57 Wailord, IVs 31: Rain Dance / Water Spout / Double-Edge / Blizzard (custom)
  - Lv55 Tentacruel, IVs 31: Toxic / Hydro Pump / Sludge Bomb / Ice Beam (custom)
  - Lv56 Ludicolo, IVs 31: Giga Drain / Surf / Leech Seed / Double Team (custom)
  - Lv56 Whiscash, IVs 31: Earthquake / Surf / Amnesia / Hyper Beam (custom)
  - Lv56 Gyarados, IVs 31: Dragon Dance / Earthquake / Hyper Beam / Surf (custom)
  - Lv58 Milotic @ Sitrus Berry, IVs 31: Recover / Surf / Ice Beam / Toxic (custom)

## 7. TM/HM sources and move tutors

`[decomp]` From map data: item balls, hidden items, NPC gifts, marts and Game Corner prizes. One row per source; a TM can have several. Gym TMs name the leader that triggers the gift. HM field use needs a badge (M-12).

| ID | Move | Method | Location | Map | Detail |
|---|---|---|---|---|---|
| TM-TM01 | Focus Punch | item-ball | hoenn-route-115 | Route115 | — |
| TM-TM02 | Dragon Claw | item-ball | meteor-falls | MeteorFalls_B1F_2R | — |
| TM-TM03 | Water Pulse | gift | sootopolis-city | SootopolisCity_Gym_1F | after defeating TRAINER_JUAN_1 |
| TM-TM04 | Calm Mind | gift | mossdeep-city | MossdeepCity_Gym | after defeating TRAINER_TATE_AND_LIZA_1 |
| TM-TM05 | Roar | gift | hoenn-route-114 | Route114 | — |
| TM-TM06 | Toxic | item-ball | fiery-path | FieryPath | — |
| TM-TM07 | Hail | item-ball | shoal-cave | ShoalCave_LowTideIceRoom | — |
| TM-TM08 | Bulk Up | gift | dewford-town | DewfordTown_Gym | after defeating TRAINER_BRAWLY_1 |
| TM-TM09 | Bullet Seed | gift | hoenn-route-104 | Route104 | — |
| TM-TM10 | Hidden Power | gift | fortree-city | FortreeCity_House2 | — |
| TM-TM10 | Hidden Power | mart | slateport-city | SlateportCity | SlateportCity_Pokemart_PowerTMs |
| TM-TM11 | Sunny Day | item-ball | scorched-slab | ScorchedSlab | — |
| TM-TM12 | Taunt | gift | hoenn-route-110 | Route110_TrickHouseEnd | — |
| TM-TM12 | Taunt | gift | hoenn-route-110 | Route110_TrickHouseEntrance | — |
| TM-TM13 | Ice Beam | game-corner | mauville-city | MauvilleCity_GameCorner | — |
| TM-TM13 | Ice Beam | item-ball | abandoned-ship | AbandonedShip_Room_B1F | — |
| TM-TM14 | Blizzard | mart | lilycove-city | LilycoveCity_DepartmentStore_4F | LilycoveCity_DepartmentStore_4F_Pokemart_AttackTMs |
| TM-TM15 | Hyper Beam | mart | lilycove-city | LilycoveCity_DepartmentStore_4F | LilycoveCity_DepartmentStore_4F_Pokemart_AttackTMs |
| TM-TM16 | Light Screen | mart | lilycove-city | LilycoveCity_DepartmentStore_4F | LilycoveCity_DepartmentStore_4F_Pokemart_DefenseTMs |
| TM-TM17 | Protect | mart | lilycove-city | LilycoveCity_DepartmentStore_4F | LilycoveCity_DepartmentStore_4F_Pokemart_DefenseTMs |
| TM-TM18 | Rain Dance | item-ball | abandoned-ship | AbandonedShip_HiddenFloorRooms | — |
| TM-TM19 | Giga Drain | gift | hoenn-route-123 | Route123 | — |
| TM-TM20 | Safeguard | mart | lilycove-city | LilycoveCity_DepartmentStore_4F | LilycoveCity_DepartmentStore_4F_Pokemart_DefenseTMs |
| TM-TM21 | Frustration | gift | pacifidlog-town | PacifidlogTown_House2 | — |
| TM-TM22 | Solar Beam | item-ball | hoenn-safari-zone | SafariZone_Northwest | — |
| TM-TM23 | Iron Tail | item-ball | meteor-falls | MeteorFalls_1F_1R | — |
| TM-TM24 | Thunderbolt | game-corner | mauville-city | MauvilleCity_GameCorner | — |
| TM-TM24 | Thunderbolt | gift | mauville-city | MauvilleCity | — |
| TM-TM25 | Thunder | mart | lilycove-city | LilycoveCity_DepartmentStore_4F | LilycoveCity_DepartmentStore_4F_Pokemart_AttackTMs |
| TM-TM26 | Earthquake | item-ball | seafloor-cavern | SeafloorCavern_Room9 | — |
| TM-TM27 | Return | gift | fallarbor-town | FallarborTown_CozmosHouse | — |
| TM-TM27 | Return | gift | pacifidlog-town | PacifidlogTown_House2 | — |
| TM-TM28 | Dig | gift | hoenn-route-114 | Route114_FossilManiacsHouse | — |
| TM-TM29 | Psychic | game-corner | mauville-city | MauvilleCity_GameCorner | — |
| TM-TM29 | Psychic | item-ball | hoenn-victory-road | VictoryRoad_B1F | — |
| TM-TM30 | Shadow Ball | item-ball | mt-pyre | MtPyre_6F | — |
| TM-TM31 | Brick Break | gift | sootopolis-city | SootopolisCity_House1 | — |
| TM-TM32 | Double Team | game-corner | mauville-city | MauvilleCity_GameCorner | — |
| TM-TM32 | Double Team | hidden-item | hoenn-route-113 | Route113 | — |
| TM-TM33 | Reflect | mart | lilycove-city | LilycoveCity_DepartmentStore_4F | LilycoveCity_DepartmentStore_4F_Pokemart_DefenseTMs |
| TM-TM34 | Shock Wave | gift | mauville-city | MauvilleCity_Gym | after defeating TRAINER_WATTSON_1 |
| TM-TM35 | Flamethrower | game-corner | mauville-city | MauvilleCity_GameCorner | — |
| TM-TM36 | Sludge Bomb | gift | dewford-town | DewfordTown_Hall | — |
| TM-TM37 | Sandstorm | item-ball | hoenn-route-111 | Route111 | — |
| TM-TM38 | Fire Blast | mart | lilycove-city | LilycoveCity_DepartmentStore_4F | LilycoveCity_DepartmentStore_4F_Pokemart_AttackTMs |
| TM-TM39 | Rock Tomb | gift | rustboro-city | RustboroCity_Gym | after defeating TRAINER_ROXANNE_1 |
| TM-TM40 | Aerial Ace | gift | fortree-city | FortreeCity_Gym | after defeating TRAINER_WINONA_1 |
| TM-TM41 | Torment | gift | slateport-city | SlateportCity_BattleTentLobby | — |
| TM-TM42 | Facade | gift | petalburg-city | PetalburgCity_Gym | after defeating TRAINER_NORMAN_1 |
| TM-TM43 | Secret Power | mart | slateport-city | SlateportCity | SlateportCity_Pokemart_PowerTMs |
| TM-TM44 | Rest | gift | lilycove-city | LilycoveCity_House2 | — |
| TM-TM45 | Attract | gift | verdanturf-town | VerdanturfTown_BattleTentLobby | — |
| TM-TM46 | Thief | gift | slateport-city | SlateportCity_OceanicMuseum_1F | — |
| TM-TM47 | Steel Wing | gift | granite-cave | GraniteCave_StevensRoom | — |
| TM-TM48 | Skill Swap | item-ball | mt-pyre | MtPyre_Exterior | — |
| TM-TM49 | Snatch | gift | ss-tidal | SSTidalRooms | — |
| TM-TM50 | Overheat | gift | lavaridge-town | LavaridgeTown_Gym_1F | after defeating TRAINER_FLANNERY_1 |
| TM-HM01 | Cut | gift | rustboro-city | RustboroCity_CuttersHouse | — |
| TM-HM02 | Fly | gift | hoenn-route-119 | Route119 | — |
| TM-HM03 | Surf | gift | petalburg-city | PetalburgCity_WallysHouse | — |
| TM-HM04 | Strength | gift | rusturf-tunnel | RusturfTunnel | — |
| TM-HM05 | Flash | gift | granite-cave | GraniteCave_1F | — |
| TM-HM06 | Rock Smash | gift | mauville-city | MauvilleCity_House1 | — |
| TM-HM07 | Waterfall | gift | sootopolis-city | SootopolisCity | — |
| TM-HM08 | Dive | gift | mossdeep-city | MossdeepCity_StevensHouse | — |

**Known conditions the table can't show** (from docs/decisions.md D1): TM02 Dragon Claw needs Waterfall (Meteor Falls back room); TM26 Earthquake is in Seafloor Cavern; TM07 Hail is in Shoal Cave's ice room; TM11 Sunny Day is in Scorched Slab (Surf); TM18 Rain Dance is on the Abandoned Ship's hidden floor (Dive); TM21/TM27 in Pacifidlog depend on friendship; TM19 Giga Drain needs a Grass Pokémon; TM12 Taunt is a Trick House reward; TM49 Snatch is on the S.S. Tidal (postgame).

### Move tutors (TU)

Each Hoenn tutor teaches once in Emerald; the other tutors are at the postgame Battle Frontier.

| ID | Move | Location | Map | One time |
|---|---|---|---|---|
| TU-01 | Double-Edge | sootopolis-city | SootopolisCity_PokemonCenter_1F | True |
| TU-02 | Dynamic Punch | mossdeep-city | MossdeepCity | True |
| TU-03 | Explosion | pacifidlog-town | PacifidlogTown_PokemonCenter_1F | True |
| TU-04 | Fury Cutter | verdanturf-town | VerdanturfTown_PokemonCenter_1F | True |
| TU-05 | Metronome | fallarbor-town | FallarborTown_Mart | True |
| TU-06 | Mimic | lavaridge-town | LavaridgeTown_House | True |
| TU-07 | Rollout | mauville-city | MauvilleCity | True |
| TU-08 | Sleep Talk | fortree-city | FortreeCity_House2 | True |
| TU-09 | Substitute | lilycove-city | LilycoveCity_DepartmentStoreRooftop | True |
| TU-10 | Swagger | slateport-city | SlateportCity_PokemonFanClub | True |

## 8. Randomizer log format (Universal Pokémon Randomizer ZX)

The parser was written from a format description, **without a real log**, so these are the claims
most likely to be wrong in detail.

- **R-01** Sections are headed `--Name--`: `--Wild Pokemon--`, `--Trainers Pokemon--`, `--TM Moves--`,
  `--Pokemon Base Stats & Types--`, `--Randomized Evolutions--`, a starters section, `--Static Pokemon--`,
  and `--Move Tutors--`. A section appears only for what was randomized; anything missing falls back
  to vanilla. Unknown sections are recorded, not parsed.
- **R-02** Wild sets look like `Set #N - ROUTE 104 Grass/Cave (rate=20)` (methods: Grass/Cave, Surfing,
  Rock Smash, Fishing), followed by one line per slot: `Species Lv4-5` or `Lv4`, optionally followed
  by `HP .. ATK .. DEF .. SPATK .. SPDEF .. SPEED ..`.
- **R-03** Set numbers follow the ROM's wild-header order (209 sets in Emerald), so set N maps to an
  exact map even when several sets share a name (every Granite Cave floor is `GRANITE CAVE`).
- **R-04** Fishing is one 10-slot set split Old 0–1, Good 2–4, Super 5–9 (M-11).
- **R-05** Trainers: `#265 (ROXANNE) - Geodude Lv12, ...` (compact), or with moveset logging one line
  per Pokémon (`Geodude Lv12 @ Item - MOVE, MOVE, ...`). `#N` is the decomp trainer id
  (`TRAINER_ROXANNE_1 = 265` in `opponents.h`).
- **R-06** `--TM Moves--` lines are `TM01 THUNDERBOLT`, using the ROM's move names (e.g. `FAINT ATTACK`
  for Feint Attack).
- **R-07** Evolutions: `RALTS -> KIRLIA`, branching as `WURMPLE -> SILCOON and CASCOON`.
  Starters: `Set starter 1 to BAGON`.
- **R-08** A log that randomizes learnsets (`--Pokemon Movesets--`) isn't parsed; the agent says it can't
  answer movesets for that run.

## 9. Open questions

- **Q-01** The walkthrough's order understated reachability five times (Route 116, Rusturf Tunnel,
  Slateport, Lilycove, Rayquaza). Which other areas in section 4 are reachable *earlier* than listed,
  under rule P-R2?
- **Q-02** P-06 relies on reaching Steven in Granite Cave (to deliver the letter) before Brawly. Is that
  possible without Flash, which needs Brawly's badge?
- **Q-03** P-R4: is there any gate besides Norman's that forces Brawly, or Winona, earlier?
- **Q-04** Route 115 (P-11): is any of its fishing water reachable from the Rustboro beach before the
  Meteor Falls exit, and with which rods at that point?
- **Q-05** Rayquaza (P-26): besides the Mach Bike for Sky Pillar's cracked floors, does anything else gate
  catching it before Juan?
- **Q-06** Lilycove before Winona (P-17): does the Devon Scope alone get you past Route 120's Kecleon to
  Route 121, or does something else block the way?
- **Q-07** Are the field-move badges in M-12 right for Emerald?
- **Q-08** Is any battle missing that a Nuzlocke player would treat as a major fight (e.g. Mt. Pyre
  summit, Weather Institute or Mt. Chimney grunts)?
- **Q-09** Trainer Pokémon abilities aren't in the data. Which ability slot do Emerald trainer Pokémon
  get, and is it predictable from the party data?
- **Q-10** Do the randomizer format claims R-01 to R-08 match real UPR ZX logs for Emerald?
- **Q-11** Do the encounter rates in M-10 and the rod split in M-11 match Emerald?
