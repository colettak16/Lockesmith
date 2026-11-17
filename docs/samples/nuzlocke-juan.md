# Agent: nuzlocke-juan

**Question:** Nuzlocke with the dupes clause and level caps. Juan is next; what should I catch?

83.9 s · 27 model calls · 111,663 tokens · about $0.249 · researchers: battle_researcher, catch_researcher, moves_researcher · 28 trace steps (full trace in `nuzlocke-juan.json`)

## Answer

Target Spheal in Shoal Cave and Chinchou on Route 124 underwater to prepare for Juan's Level 46 cap [1].

### Top picks

#### Spheal (Tank / Ice Attacker) — **Core** [2]
* **Where:** Shoal Cave, Walking (Lv26-32, 50% rate, guaranteed if you have Zubat/Golbat) [3][4][5]
* **When:** Available immediately, but evolve before Lv46 [6]
* **Why:** With Thick Fat, Walrein minimizes Ice-type damage and has the bulk to take on Juan's stalling team safely [2][6].
* **Long run:** Essential for defeating Drake of the Elite Four with powerful Ice-type moves [6].
* **Backup:** Staryu (Lilycove City via Super Rod, 15% rate) [7]. Starmie is incredibly fast with deep coverage (Thunderbolt, Ice Beam, Surf) to sweep [8]. *Note: Starmie requires a Water Stone; make sure you can obtain one before facing Juan.*

#### Chinchou (Electric/Water Pivot) — **Core** [9]
* **Where:** Route 124 (underwater), Seaweed (Lv20-30, 30% rate) [10]
* **When:** Available as soon as Dive is usable (after Space Center) [11]
* **Why:** Lanturn's typing resists Water and Ice, and it hits Juan's team super-effectively with STAB Electric moves [9][6].
* **Long run:** Volt Absorb and excellent HP make Lanturn an incredible tank and pivot against Wallace and Glacia [9][12].
* **Backup:** Magnemite (New Mauville, ~49% rate) [13]. Magneton offers high Special Attack to clear Water-types (though it must dodge Whiscash's Earthquake) and key Steel-type resistances for the Elite Four [14][15].

---

### Key Battles

#### Gym 8: Juan
* Juan's team is capped at Level 46 (Kingdra) [16].
* Whiscash knows Earthquake, which threatens Electric-type counters [17].
* Kingdra stalls with Double Team, Ice Beam, Rest, and a Chesto Berry, requiring high bulk or burst damage to overcome safely [16].

---

### Assumptions
* You have not caught Zubat or Golbat yet, but encountering them triggers the dupes clause for a guaranteed Spheal encounter.

### To sharpen this
* Do you already have a Zubat or Golbat registered in your Pokédex?
* Do you have the Storage Key for the Abandoned Ship to access TM13 Ice Beam?

### Not covered
* Other potential encounter areas requiring HMs not yet unlocked.

### Rules I followed
- Nuzlocke: first encounter per named location only, dupes clause; gifts, statics and trades are free (checked by the Verifier)
- encounters already used: Route 101, Route 102, Route 103, Route 104, Petalburg Woods, Route 116, Rusturf Tunnel, Granite Cave, Route 110, Route 117, Route 111, Route 112, Fiery Path, Route 113, Route 114, Meteor Falls, Route 115, Route 118, Route 119, Route 120, Route 121, Safari Zone, Mt. Pyre (checked by the Verifier)
- level caps: stay at or below the next boss's highest level (checked by the Verifier)

## Sources

1. LockeSmith's Emerald rules (agent/brief.py) (`rules:game`)
2. PokeAPI: Spheal (species data) (`pokeapi:pokemon_species#363`)
3. PokeAPI: Spheal at Shoal Cave (walk) (`pokeapi:encounters#30883`)
4. PokeAPI: Spheal at Shoal Cave (walk) (`pokeapi:encounters#70746`)
5. PokeAPI: Zubat at Shoal Cave (walk) (`pokeapi:encounters#70741`)
6. database query a490601260 (`sql:a490601260`)
7. PokeAPI: Staryu at Lilycove City (super-rod) (`pokeapi:encounters#30913`)
8. PokeAPI: Staryu (species data) (`pokeapi:pokemon_species#120`)
9. PokeAPI: Chinchou (species data) (`pokeapi:pokemon_species#170`)
10. PokeAPI: Chinchou at Route 124 (seaweed) (`pokeapi:encounters#29872`)
11. Story progression (data/progression.yaml): Mossdeep Space Center: Maxie & Tabitha (multi battle with Steven) (`progression:space_center`)
12. database query b86cf59b31 (`sql:b86cf59b31`)
13. PokeAPI: Magnemite at New Mauville (walk) (`pokeapi:encounters#30487`)
14. PokeAPI: Magnemite (species data) (`pokeapi:pokemon_species#81`)
15. database query 86f8f978ec (`sql:86f8f978ec`)
16. pokeemerald src/data/trainer_parties.h (sParty_Juan1/5) (`decomp:trainer_parties.h#sParty_Juan1/5`)
17. pokeemerald src/data/trainer_parties.h (sParty_Juan1/2) (`decomp:trainer_parties.h#sParty_Juan1/2`)
