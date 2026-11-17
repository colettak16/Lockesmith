# Agent: nuzlocke-juan

**Question:** Nuzlocke with the dupes clause and level caps. Juan is next; what should I catch?

71.3 s · 16 model calls · 72,902 tokens · about $0.189 · researchers: battle_researcher, catch_researcher, moves_researcher · 16 trace steps (full trace in `nuzlocke-juan.json`)

## Answer

Spheal and Staryu are excellent additions to handle Juan and the Elite Four, rounding out your team's coverage [1][2].

### Top picks

#### Spheal (Walrein) — Core [1][3]
* **Where:** Shoal Cave (B1F, B2F, or High-Tide), walking, Levels 26-32 (50% encounter rate) [1][4].
* **When:** Available right now, before facing the Mossdeep Space Center or Juan [1].
* **Why it helps now:** Juan's Kingdra is a notorious run-killer with Double Team, Rest, and Ice Beam [5]. Walrein's massive bulk and Thick Fat ability let it easily tank Ice Beam and Water Pulse, allowing it to sit in against Kingdra and hit back with Ice-type attacks [5].
* **Long run:** Walrein is one of the best Elite Four Pokémon in Hoenn [3]. Its Ice-type STAB is critical for defeating Drake's Dragon-types, and its durability makes it excellent against Wallace [3].
* **Backup:** Chinchou (Lanturn) [6][7] (Route 124 or 126 Underwater, seaweed, 30% encounter rate [8]).

#### Staryu (Starmie) — Core [2][9]
* **Where:** Lilycove City, Super Rod, Levels 25-30 (15% encounter rate) [2].
* **When:** Available right now in Lilycove City [2].
* **Why it helps now:** Starmie is a premier fast attacker [9]. With access to Thunderbolt and Ice Beam via TMs, it can effortlessly sweep the rest of Juan's team (Luvdisc, Sealeo, Crawdaunt) before you have to face Kingdra [5][10].
* **Long run:** Starmie's unmatched coverage (Surf, Thunderbolt, Ice Beam, Psychic) and high Speed make it a top-tier sweeper for the entire Elite Four [9].
* **Backup:** Chinchou (Lanturn) [6][7] (Route 124 or 126 Underwater, seaweed, 30% encounter rate [8]).

*Note: Starmie requires a Water Stone to evolve [9]. Make sure you have one available before challenging Juan.*

---

### Key Battles

#### Gym 8: Juan
* **Watch out for:** Juan's Kingdra (Lv46) has Double Team, Rest (holding a Chesto Berry), Water Pulse, and Ice Beam [5]. It threatens Breloom and Swellow with super-effective Ice-type damage [11][5]. 
* **Ground Caution:** Be careful with Manectric, as Juan's Whiscash knows Earthquake [12].

---

### Key Steps
1. **Check your Level Cap:** Juan's highest-level Pokémon is his Kingdra at Level 46 [5]. Ensure your team stays at or below this level limit [13].
2. **Equip Key TMs:** Purchase TM13 Ice Beam and TM24 Thunderbolt from the Mauville Game Corner for your new catches, or pick up TM25 Thunder and TM14 Blizzard from the Lilycove Department Store [14][15][10][16].

---

### Assumptions
* You have the Super Rod needed to fish for Staryu.
* You have access to a Water Stone to evolve Staryu.

### To sharpen this
* Do you already have a Water Stone for Staryu, or need to know where to find one?

### Rules I followed
- Nuzlocke: first encounter per named location only, dupes clause; gifts, statics and trades are free (checked by the Verifier)
- encounters already used: Route 101, Route 102, Route 103, Route 104, Petalburg Woods, Route 116, Rusturf Tunnel, Granite Cave, Route 110, Route 117, Route 111, Route 112, Fiery Path, Route 113, Route 114, Meteor Falls, Route 115, Route 118, Route 119, Route 120, Route 121, Safari Zone, Mt. Pyre (checked by the Verifier)
- level caps: stay at or below the next boss's highest level (checked by the Verifier)

## Sources

1. PokeAPI: Spheal at Shoal Cave (walk) (`pokeapi:encounters#70736`)
2. PokeAPI: Staryu at Lilycove City (super-rod) (`pokeapi:encounters#30913`)
3. PokeAPI: Sealeo evolves into Walrein (`pokeapi:pokemon_evolution#185`)
4. PokeAPI: Spheal at Shoal Cave (walk) (`pokeapi:encounters#70808`)
5. pokeemerald src/data/trainer_parties.h (sParty_Juan1/5) (`decomp:trainer_parties.h#sParty_Juan1/5`)
6. PokeAPI: Chinchou evolves into Lanturn (`pokeapi:pokemon_evolution#95`)
7. PokeAPI: Lanturn (species data) (`pokeapi:pokemon_species#171`)
8. PokeAPI: Chinchou at Route 124 (seaweed) (`pokeapi:encounters#29872`)
9. PokeAPI: Staryu evolves into Starmie (`pokeapi:pokemon_evolution#70`)
10. pokeemerald data/maps/MauvilleCity_GameCorner (TM13) (`decomp:data/maps/MauvilleCity_GameCorner#TM13`)
11. Gen 3 type chart (pokeemerald gTypeEffectiveness) (`rules:gen3_type_chart`)
12. pokeemerald src/data/trainer_parties.h (sParty_Juan1/2) (`decomp:trainer_parties.h#sParty_Juan1/2`)
13. database query ef2ed14180 (`sql:ef2ed14180`)
14. pokeemerald data/maps/LilycoveCity_DepartmentStore_4F (TM25) (`decomp:data/maps/LilycoveCity_DepartmentStore_4F#TM25`)
15. pokeemerald data/maps/LilycoveCity_DepartmentStore_4F (TM14) (`decomp:data/maps/LilycoveCity_DepartmentStore_4F#TM14`)
16. pokeemerald data/maps/MauvilleCity_GameCorner (TM24) (`decomp:data/maps/MauvilleCity_GameCorner#TM24`)
