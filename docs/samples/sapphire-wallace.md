# Agent: sapphire-wallace

**Question:** What should I catch to beat Wallace?

127.5 s · 19 model calls · 87,429 tokens · about $0.209 · researchers: battle_researcher, catch_researcher, moves_researcher, story_researcher · 21 trace steps (full trace in `sapphire-wallace.json`)

## Answer

Chinchou and Magnemite are excellent additions to handle Wallace's Ice coverage and Whiscash's Ground typing, perfectly complementing your Grass/Electric core [1][2][3][4].

### Top picks

#### Chinchou (core)
* **Where:** Route 124 or Route 126: Dive (seaweed) (Lv20-30, 30% encounter rate) [5][6].
* **When:** Available right now using Dive [5].
* **Why it helps now:** With Volt Absorb, it resists or absorbs Water, resists Ice attacks from Wallace's Sealeo and Milotic, and hits his Water-types super-effectively with Electric STAB moves like Spark [1][7][8][4].
* **Long run:** Evolves into Lanturn at Level 27 [9]. Its massive base 125 HP makes it a resilient tank against Glacia's Ice-types and Steven's Water/Steel types in the Elite Four [1][10].
* **Backup:** None [10].

#### Magnemite (core)
* **Where:** New Mauville (Lv22-26, 49-50% encounter rate walking) [11][12].
* **When:** Available now using the Basement Key from Wattson [11].
* **Why it helps now:** Its Electric/Steel typing resists Ice Beam and Aurora Beam, allowing it to safely switch in on Milotic and Sealeo and retaliate with powerful Electric attacks like Thunderbolt [2][13][8][4].
* **Long run:** Evolves into Magneton at Level 30 [14]. Its defensive typing and 120 base Special Attack make it a fantastic pivot against Glacia and Steven, though it must avoid Earthquake [2][10].
* **Backup:** Spheal (found in Shoal Cave at Lv26-32, 50% encounter rate walking) [15][16]. Its Thick Fat ability and Water/Ice typing neutralize the Ice-type coverage moves that threaten Sceptile and Breloom [15]. It evolves into Sealeo at 32 and Walrein at 44, which excels against Drake's Dragon-types [17][18].

---

### Key Battle Notes

* **Gym Leader Wallace:** Whiscash knows Earthquake, which is immune to Electric and deals 2x damage to Electric-types, making it a severe threat to Manectric [3][19]. Use Sceptile's Leaf Blade (4x effective) to defeat it quickly [3][19]. Beware of Sealeo's Aurora Beam and Milotic's Ice Beam, which deal 2x damage to Sceptile and Breloom [19][8][4]. Pivot to an Ice-resisting partner like Lanturn or Magneton to handle them safely [1][2][8][4].

---

### Assumptions
* You have access to New Mauville via Wattson's Basement Key [11].
* Your Sceptile has learned Leaf Blade (learned at Level 29) [10].

### To sharpen this
* Do you plan to catch and use Kyogre, or would you prefer a regular encounter like Chinchou or Magnemite to fill out your team?
* Do you already have the Thunderbolt TM from Wattson, or do you have Game Corner coins to purchase it for Magneton?

## Sources

1. PokeAPI: Lanturn (species data) (`pokeapi:pokemon_species#171`)
2. PokeAPI: Magneton (species data) (`pokeapi:pokemon_species#82`)
3. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/2) (`decomp:trainer_parties.h#gTrainerParty_Wallace/2`)
4. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/5) (`decomp:trainer_parties.h#gTrainerParty_Wallace/5`)
5. PokeAPI: Chinchou at Route 124 (seaweed) (`pokeapi:encounters#29283`)
6. PokeAPI: Chinchou at Route 126 (seaweed) (`pokeapi:encounters#29318`)
7. PokeAPI: Lanturn learns Spark (level-up) (`pokeapi:pokemon_moves#171/209/level-up/25`)
8. pokeruby src/data/trainer_parties.h (gTrainerParty_Wallace/3) (`decomp:trainer_parties.h#gTrainerParty_Wallace/3`)
9. PokeAPI: Chinchou evolves into Lanturn (`pokeapi:pokemon_evolution#95`)
10. LockeSmith's Sapphire rules (agent/brief.py, checked in docs/audit/engine.txt) (`rules:game`)
11. PokeAPI: Magnemite at New Mauville (walk) (`pokeapi:encounters#28694`)
12. PokeAPI: Magnemite at New Mauville (walk) (`pokeapi:encounters#28706`)
13. pokeruby data/maps/MauvilleCity (TM24) (`decomp:data/maps/MauvilleCity#TM24`)
14. PokeAPI: Magnemite evolves into Magneton (`pokeapi:pokemon_evolution#51`)
15. PokeAPI: Spheal at Shoal Cave (walk) (`pokeapi:encounters#28670`)
16. PokeAPI: Spheal at Shoal Cave (walk) (`pokeapi:encounters#70724`)
17. PokeAPI: Spheal evolves into Sealeo (`pokeapi:pokemon_evolution#184`)
18. PokeAPI: Sealeo evolves into Walrein (`pokeapi:pokemon_evolution#185`)
19. Gen 3 type chart (pokeruby data/type_effectiveness.inc) (`rules:gen3_type_chart`)
