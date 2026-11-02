# Agent: nuzlocke-juan

**Question:** Nuzlocke with the dupes clause and level caps. Juan is next; what should I catch?

75.8 s · 14 model calls · 61,075 tokens · about $0.186 · researchers: battle_researcher, catch_researcher, moves_researcher · 13 trace steps (full trace in `nuzlocke-juan.json`)

## Answer

Target Magneton, Lanturn, or Walrein from unused areas to handle Juan's Water/Ice threats and boost your endgame [1][2][3].

### Top picks

#### Magnemite (core)
* **Where:** New Mauville, Walking, Lv 22-26 (50% encounter rate) [4]
* **When:** Available immediately using Surf to access New Mauville [4].
* **Why:** Evolves into Magneton, which resists Juan's Ice-type attacks and hits his Water-types extremely hard with STAB Electric moves like Thunderbolt [5][6].
* **Long run:** S-Tier utility [5]. Magneton's Steel typing provides numerous resistances, making it exceptionally reliable through Victory Road, Elite Four Glacia, and Champion Wallace [5].
* **Backup:** **Staryu** (Lilycove City, Super Rod, 15% encounter rate, Lv 25-30) [7]. It evolves into Starmie, which resists Ice and can sweep Juan's bulky Water-types with Thunderbolt [8][9][10]. *Note: Starmie requires a Water Stone, so ensure you have one before the Sootopolis Gym.*

#### Chinchou (core)
* **Where:** Route 124 or Route 126 (underwater), Seaweed, Lv 20-30 (30% encounter rate) [11]
* **When:** Available immediately using Dive [11].
* **Why:** Evolves into Lanturn, which resists both Water and Ice-type attacks from Juan's team, while threatening back with STAB Electric moves [12][13][14].
* **Long run:** Outstanding against the final boss (Champion Wallace) and Elite Four Glacia's Water-types due to its unique typing [12].
* **Backup:** None [14].

#### Spheal (core)
* **Where:** Shoal Cave (high-tide or low-tide), Walking, Lv 26-32 (50% encounter rate) [15]
* **When:** Available immediately north of Mossdeep City [15].
* **Why:** Evolves into Walrein before the level cap [16][17]. Its Thick Fat ability halves incoming Ice-type damage, making it a stellar bulky pivot against Juan [18][19].
* **Long run:** An excellent bulky tank that is absolutely crucial for Elite Four Drake (Dragon-type specialist) using STAB Ice moves [18].
* **Backup:** None [19].

---

### Key Battles

#### Gym 8: Juan
* Whiscash carries Earthquake, posing a direct threat to Manectric and Magneton with a super-effective ground move [20].
* Sealeo and Kingdra carry Ice Beam/Aurora Beam, threatening Swellow and Breloom with super-effective damage [21][22].
* Kingdra can fully heal with Rest paired with a Chesto Berry [22].

---

### Assumptions
* You have not used New Mauville, Route 124/126 underwater, or Shoal Cave for Nuzlocke encounters yet.
* You have access to TMs like Thunderbolt (TM24) and Ice Beam (TM13).

### To sharpen this
* Do you have a Grass-type move like Giga Drain available to deal with Juan's Whiscash?
* Do you have setup moves like Bulk Up on Breloom to bypass Kingdra's Double Team evasion?

### Not covered
* The availability of specific TMs (like Thunderbolt and Ice Beam) in your current inventory is unknown.

### Rules I followed
- Nuzlocke: first encounter per named location only, dupes clause; gifts, statics and trades are free (checked by the Verifier)
- encounters already used: Route 101, Route 102, Route 103, Route 104, Petalburg Woods, Route 116, Rusturf Tunnel, Granite Cave, Route 110, Route 117, Route 111, Route 112, Fiery Path, Route 113, Route 114, Meteor Falls, Route 115, Route 118, Route 119, Route 120, Route 121, Safari Zone, Mt. Pyre (checked by the Verifier)
- level caps: stay at or below the next boss's highest level (checked by the Verifier)

## Sources

1. PokeAPI: Magnemite (species data) (`pokeapi:pokemon_species#81`)
2. PokeAPI: Chinchou (species data) (`pokeapi:pokemon_species#170`)
3. PokeAPI: Spheal (species data) (`pokeapi:pokemon_species#363`)
4. PokeAPI: Magnemite at New Mauville (walk) (`pokeapi:encounters#30499`)
5. PokeAPI: Magneton (species data) (`pokeapi:pokemon_species#82`)
6. PokeAPI: Magnemite evolves into Magneton (`pokeapi:pokemon_evolution#51`)
7. PokeAPI: Staryu at Lilycove City (super-rod) (`pokeapi:encounters#30913`)
8. PokeAPI: Staryu (species data) (`pokeapi:pokemon_species#120`)
9. PokeAPI: Starmie (species data) (`pokeapi:pokemon_species#121`)
10. PokeAPI: Staryu evolves into Starmie (`pokeapi:pokemon_evolution#70`)
11. PokeAPI: Chinchou at Route 124 (seaweed) (`pokeapi:encounters#29872`)
12. PokeAPI: Lanturn (species data) (`pokeapi:pokemon_species#171`)
13. PokeAPI: Chinchou evolves into Lanturn (`pokeapi:pokemon_evolution#95`)
14. database query 16d1836167 (`sql:16d1836167`)
15. PokeAPI: Spheal at Shoal Cave (walk) (`pokeapi:encounters#30883`)
16. PokeAPI: Spheal evolves into Sealeo (`pokeapi:pokemon_evolution#184`)
17. PokeAPI: Sealeo evolves into Walrein (`pokeapi:pokemon_evolution#185`)
18. PokeAPI: Walrein (species data) (`pokeapi:pokemon_species#365`)
19. database query 61d6083338 (`sql:61d6083338`)
20. pokeemerald src/data/trainer_parties.h (sParty_Juan1/2) (`decomp:trainer_parties.h#sParty_Juan1/2`)
21. pokeemerald src/data/trainer_parties.h (sParty_Juan1/3) (`decomp:trainer_parties.h#sParty_Juan1/3`)
22. pokeemerald src/data/trainer_parties.h (sParty_Juan1/5) (`decomp:trainer_parties.h#sParty_Juan1/5`)
