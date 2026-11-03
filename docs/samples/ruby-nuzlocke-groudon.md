# Agent: ruby-nuzlocke-groudon

**Question:** Ruby Nuzlocke with level caps. Should I catch Groudon in the Cave of Origin, and what else do I need for Wallace?

186.1 s · 24 model calls · 110,022 tokens · about $0.291 · researchers: battle_researcher, catch_researcher, moves_researcher, story_researcher · 27 trace steps (full trace in `ruby-nuzlocke-groudon.json`)

## Answer

You can catch Groudon since statics are free, but at Level 45 it breaks Wallace's Level 43 cap and must sit out the gym [1][2].

### Top picks

#### Chinchou (core)
* **Where:** Route 124 or 126 (Underwater), Seaweed, Lv20-30 [3][4].
* **When:** Before Wallace, once Dive is usable.
* **Why:** Its Water/Electric typing allows it to resist Wallace's Water-type moves while firing back with super-effective STAB Electric attacks [5].
* **Long run:** Evolves into Lanturn, a solid tanky pivot with high HP that functions well against Glacia, Wallace, and elements of Steven's team [5].
* **Backup:** Staryu (Lilycove City, Super Rod, Lv25-30) is a fast, powerful special attacker that can sweep Wallace if taught Thunderbolt [6]. It evolves into Starmie (requires a Water Stone, so make sure you can obtain one before the fight) and excels against Maxie, Courtney, and Steven [6].

#### Magnemite (core)
* **Where:** New Mauville, Walk, Lv22-26 [7][8].
* **When:** Before Wallace.
* **Why:** Its massive 120 Special Attack makes it a premier Electric-type sweeper against Wallace's Water-type team, and its Steel typing adds useful defensive resistances [9].
* **Long run:** Evolves into Magneton. It is excellent through the Elite Four (particularly Glacia) and invaluable against Champion Steven's Steel-type team [9].

---

### Plan

1. **Clear Seafloor Cavern:** Defeat Magma Admin Courtney (highest Lv38), then Magma Leader Maxie (highest Lv43) [10][11]. While inside, grab TM26 Earthquake from Room 9 for your Swampert [12][13].
2. **Catch Groudon in Cave of Origin:** After defeating Maxie, proceed to the Cave of Origin [1]. This is a mandatory battle [1]. It is caught at Level 45 with Slash, Bulk Up, Earthquake, and Fire Blast [14][15]. Because your Nuzlocke rules allow static encounters for free, you can catch it without using up a standard route encounter.
3. **Box Groudon for Gym 8:** Wallace’s ace is his Level 43 Milotic [2]. Because Groudon is Level 45, it breaks your level cap and cannot participate in the gym battle [2][16].
4. **Equip Key Moves for Wallace:** Teach Manectric Thunderbolt (TM24 from Mauville) [17]. Ensure Breloom has Sky Uppercut [18] and a Grass-type move like Giga Drain (TM19 from Route 123) [19] or Solar Beam (TM22) [20] to help bypass Water/Ground dual types.

---

### Key Battles

#### Gym Leader Wallace
* **Milotic and Sealeo:** Milotic's Ice Beam deals 4x damage to Breloom and 2x damage to Swellow [21][2]. Sealeo's Aurora Beam also deals 2x damage to both [21][22]. Keep Breloom and Swellow away from these two.
* **Whiscash:** It is immune to Electric attacks and carries Earthquake, which deals 2x damage to Manectric [21][23]. Switch Manectric out immediately when Whiscash enters, preferably to Breloom or a Flying-type.
* **Seaking:** It carries Horn Drill, a 30% accuracy OHKO move [24]. Take it down quickly or swap to a Ghost-type pivot if you have one.

---

### Assumptions
* You have not already used your route encounters for New Mauville or the underwater seaweed [25].
* You intend to enforce the level cap strictly, preventing the use of any Pokémon over level 43 against Wallace [25].

### To sharpen this
* Have you already completed the New Mauville quest or caught a Pokémon there?
* Do you have the Thunderbolt TM (TM24) from Wattson, or will you need to obtain it from the Game Corner?

### Rules I followed
- Nuzlocke: first encounter per named location only; gifts, statics and trades are free (checked by the Verifier)
- level caps: stay at or below the next boss's highest level (checked by the Verifier)

## Sources

1. Story progression (data/progression_rs.yaml): Cave of Origin: Groudon (Lv45) (`progression:legendary_cave_of_origin`)
2. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/5) (`decomp:trainer_parties.h#gTrainerParty_Wallace/5`)
3. PokeAPI: Chinchou at Route 124 (seaweed) (`pokeapi:encounters#27832`)
4. PokeAPI: Chinchou at Route 126 (seaweed) (`pokeapi:encounters#27867`)
5. PokeAPI: Lanturn (species data) (`pokeapi:pokemon_species#171`)
6. PokeAPI: Staryu at Lilycove City (super-rod) (`pokeapi:encounters#26702`)
7. PokeAPI: Magnemite at New Mauville (walk) (`pokeapi:encounters#27243`)
8. PokeAPI: Magnemite at New Mauville (walk) (`pokeapi:encounters#27255`)
9. PokeAPI: Magneton (species data) (`pokeapi:pokemon_species#82`)
10. Story progression (data/progression_rs.yaml): Seafloor Cavern: Magma Admin Courtney (`progression:admin_seafloor_cavern`)
11. Story progression (data/progression_rs.yaml): Seafloor Cavern: Magma Leader Maxie (`progression:leader_seafloor_cavern`)
12. Bulbapedia: Walkthrough:Pokémon Ruby and Sapphire/Part 16 § Route 128 > Seafloor Cavern > Chamber 10 (`guide:Walkthrough:Pokemon_Ruby_and_Sapphire/Part_16#Chamber_10`)
13. pokeruby data/maps/SeafloorCavern_Room9 (TM26) (`decomp:data/maps/SeafloorCavern_Room9#TM26`)
14. PokeAPI: Groudon learns Slash (level-up) (`pokeapi:pokemon_moves#383/163/level-up/20`)
15. PokeAPI: Groudon learns Fire Blast (level-up) (`pokeapi:pokemon_moves#383/126/level-up/45`)
16. Story progression (data/progression_rs.yaml): Sootopolis Gym: Wallace (`progression:gym8_wallace`)
17. pokeruby data/maps/MauvilleCity (TM24) (`decomp:data/maps/MauvilleCity#TM24`)
18. PokeAPI: Breloom learns Sky Uppercut (level-up) (`pokeapi:pokemon_moves#286/327/level-up/36`)
19. pokeruby data/maps/Route123 (TM19) (`decomp:data/maps/Route123#TM19`)
20. pokeruby data/maps/SafariZone_Northwest (TM22) (`decomp:data/maps/SafariZone_Northwest#TM22`)
21. Gen 3 type chart (pokeruby data/type_effectiveness.inc) (`rules:gen3_type_chart`)
22. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/3) (`decomp:trainer_parties.h#gTrainerParty_Wallace/3`)
23. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/2) (`decomp:trainer_parties.h#gTrainerParty_Wallace/2`)
24. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/4) (`decomp:trainer_parties.h#gTrainerParty_Wallace/4`)
25. LockeSmith's Ruby rules (agent/brief.py, checked in docs/audit/engine.txt) (`rules:game`)
