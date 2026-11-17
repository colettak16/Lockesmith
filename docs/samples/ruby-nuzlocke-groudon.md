# Agent: ruby-nuzlocke-groudon

**Question:** Ruby Nuzlocke with level caps. Should I catch Groudon in the Cave of Origin, and what else do I need for Wallace?

71.3 s · 16 model calls · 67,101 tokens · about $0.194 · researchers: battle_researcher, catch_researcher, moves_researcher, story_researcher · 16 trace steps (full trace in `ruby-nuzlocke-groudon.json`)

## Answer

You can catch Groudon to use later, but its Level 45 encounter violates Wallace's Level 43 cap, so you must box it for the Gym and rely on your party and new encounters [1][2].

### Top picks

#### Magneton (from Magnemite) — *core* [3][4]
* **Where:** New Mauville (walk, Lv22-26, 49-50% encounter rate) [5].
* **When:** Available immediately (requires Surf to access New Mauville) [3].
* **Why it helps now:** Evolves into Magneton at level 30 [3][4]. Its massive Special Attack and Electric typing allow it to sweep through most of Wallace's Water-types [3][4]. Its Steel typing grants invaluable defensive resistances against Ice-type moves like Milotic's Ice Beam [3][4].
* **Key Moves:** Thunderbolt [3].
* **Long run:** Outstanding against Glacia (resists Ice) and useful against Steven's Skarmory, Cradily, and Armaldo, though it must avoid Ground-type attacks due to a 4x weakness [3][4].
* **Backup:** **Lanturn** (from Chinchou, Route 124 or 126 Underwater in seaweed, Lv20-30, 30%) [6]. Its Volt Absorb ability and Water/Electric typing make it a perfect defensive wall against other Water-types, taking minimal damage while striking back with super-effective Electric moves [7][8]. It has an incredible matchup against Glacia's Water-types and Steven's Skarmory, though lower offensive stats mean it relies on matching up defensively [7][8].

#### Vileplume (from Oddish) — *core* [9][10]
* **Where:** Safari Zone SE/SW (walk, Lv25-27, 40%) or Route 119 (walk, Lv24-27, 30%) [11].
* **When:** Available immediately [9].
* **Why it helps now:** Wallace's Whiscash is immune to Electric attacks and can threaten your Electric-types with Ground moves [9][2]. A Grass-type like Vileplume or Bellossom will hit Whiscash for 4x super-effective damage [9][10][12]. *Note: Vileplume needs a Leaf Stone; ensure you can acquire one before the battle.*
* **Key Moves:** Giga Drain, Sleep Powder [9].
* **Long run:** Extremely useful for countering heavy Ground- and Rock-types in Steven's champion team [9].
* **Backup:** None.

---

### Key Battles

#### Groudon (Cave of Origin)
The Cave of Origin encounter with Groudon is a mandatory story event [1]. You do not have to catch it; defeating it or fleeing will also clear the event and unlock Sootopolis Gym [1][2]. If you do catch it, it is encountered at Level 45, which exceeds Wallace's Level 43 cap, meaning you must keep it in the PC for the Gym battle [1][2].

#### Gym 8 Leader: Wallace
Wallace leads with Luvdisc (Lv40) and has Whiscash (Lv42), Sealeo (Lv40), Seaking (Lv42), and Milotic (Lv43) [13][14][15][16][17]. 
* **Whiscash** is immune to Electric and carries Ground moves [14][18]. Your Breloom provides a great answer, learning Sky Uppercut at Level 36 [19], while a Grass-type like Vileplume can hit its 4x Grass weakness [9][18].
* **Sealeo** (Aurora Beam) and **Milotic** (Ice Beam) can hit your Grass and Flying types (Breloom, Swellow) for super-effective damage [15][17][18].
* **Manectric** is perfectly positioned to sweep much of Wallace's team, learning Bite at Level 39 [20]. It learns Thunder at Level 45, but this will be unavailable due to the Level 43 cap [21][2].

---

### Assumptions
* You are allowing the use of legendary Pokémon as long as they adhere to your level caps [22].
* You have not already exhausted your encounters in New Mauville or the Safari Zone [22].

### To sharpen this
* What are the current movesets of your Swampert, Breloom, Swellow, and Manectric?
* Do you already have a Leaf Stone or Sun Stone to evolve a Gloom?

### Not covered
* Whether your specific Nuzlocke ruleset bans legendary Pokémon altogether, regardless of level caps [22].

### Rules I followed
- Nuzlocke: first encounter per named location only; gifts, statics and trades are free (checked by the Verifier)
- level caps: stay at or below the next boss's highest level (checked by the Verifier)

## Sources

1. Story progression (data/progression_rs.yaml): Cave of Origin: Groudon (Lv45) (`progression:legendary_cave_of_origin`)
2. Story progression (data/progression_rs.yaml): Sootopolis Gym: Wallace (`progression:gym8_wallace`)
3. PokeAPI: Magnemite (species data) (`pokeapi:pokemon_species#81`)
4. PokeAPI: Magneton (species data) (`pokeapi:pokemon_species#82`)
5. PokeAPI: Magnemite at New Mauville (walk) (`pokeapi:encounters#27243`)
6. PokeAPI: Chinchou at Route 124 (seaweed) (`pokeapi:encounters#27832`)
7. PokeAPI: Chinchou (species data) (`pokeapi:pokemon_species#170`)
8. PokeAPI: Lanturn (species data) (`pokeapi:pokemon_species#171`)
9. PokeAPI: Oddish (species data) (`pokeapi:pokemon_species#43`)
10. PokeAPI: Vileplume (species data) (`pokeapi:pokemon_species#45`)
11. PokeAPI: Oddish at Safari Zone (walk) (`pokeapi:encounters#28074`)
12. PokeAPI: Bellossom (species data) (`pokeapi:pokemon_species#182`)
13. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/1) (`decomp:trainer_parties.h#gTrainerParty_Wallace/1`)
14. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/2) (`decomp:trainer_parties.h#gTrainerParty_Wallace/2`)
15. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/3) (`decomp:trainer_parties.h#gTrainerParty_Wallace/3`)
16. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/4) (`decomp:trainer_parties.h#gTrainerParty_Wallace/4`)
17. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/5) (`decomp:trainer_parties.h#gTrainerParty_Wallace/5`)
18. Gen 3 type chart (pokeruby data/type_effectiveness.inc) (`rules:gen3_type_chart`)
19. PokeAPI: Breloom learns Sky Uppercut (level-up) (`pokeapi:pokemon_moves#286/327/level-up/36`)
20. PokeAPI: Manectric learns Bite (level-up) (`pokeapi:pokemon_moves#310/44/level-up/39`)
21. PokeAPI: Manectric learns Thunder (level-up) (`pokeapi:pokemon_moves#310/87/level-up/45`)
22. LockeSmith's Ruby rules (agent/brief.py, checked in docs/audit/engine.txt) (`rules:game`)
