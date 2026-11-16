# Agent: randomizer-tate-liza

**Question:** What should I catch to get through Tate & Liza?

81.9 s · 14 model calls · 65,260 tokens · about $0.204 · researchers: battle_researcher, catch_researcher, moves_researcher · 14 trace steps (full trace in `randomizer-tate-liza.json`)

## Answer

Tate & Liza's randomized team is entirely Fire-type, making bulky Water-types like Spheal and Sharpedo ideal catches to pair with your Marshtomp's evolutions [1].

### Top picks

#### Spheal (core)
* **Where to catch:** Shoal Cave (B1F, B2F, or high-tide) via walking (50% encounter rate, Levels 26-32) [2].
* **When to catch:** Immediately available after acquiring Surf to reach Shoal Cave north of Mossdeep [3].
* **Why it helps now:** Tate & Liza's randomized team consists of Camerupt, Torkoal, Magcargo, and Houndoom [1]. Spheal's Water typing allows it to exploit their heavy Fire-type composition, especially using Surf which hits both opponents in a Double Battle [4][1][3].
* **Long run:** Outstanding long-term value [4]. It evolves into Sealeo (and eventually Walrein), has massive bulk, and hits 26 remaining opponents super-effectively, making it incredibly strong against Elite Four Drake's Dragon types [4][5].
* **Backup:** Aron (found in Granite Cave B1F or B2F via walking, 40% encounter rate, Levels 9-12) [6][7]. It acts as a premier physical wall against Normal and Flying moves and evolves into Lairon and then Aggron, yielding a monumental 180 Base Defense [7][8].

#### Sharpedo (core)
* **Where to catch:** Route 103 or Route 118 by fishing with the Super Rod (Lv30-35, 40% encounter rate) [9][10].
* **When to catch:** Immediately available once you have the Super Rod [9][10].
* **Why it helps now:** Its strong offensive stats allow it to quickly sweep Tate & Liza's Fire-type team before they can retaliate [11][1]. *(Note: Surf is a Special move in Gen III, so it won't use Sharpedo's massive 120 Physical Attack, but its 95 Special Attack is still very serviceable)*.
* **Long run:** Hits 15 remaining opponents super-effectively and is excellent against Elite Four Phoebe, but its low defensive stats make it a glass cannon [11].
* **Backup:** Shuppet (found on Mt. Pyre 1F-3F, 100% encounter rate, Levels 22-29) [12][13]. It evolves into Banette, deals immense physical Ghost-type STAB damage, and is extremely useful for defeating Elite Four Phoebe [13][14].

---

### Key Battles

#### Gym Leader: Tate & Liza
Tate & Liza have a randomized, Fire-heavy team of Camerupt (Lv41), Torkoal (Lv41), Magcargo (Lv42), and Houndoom (Lv42) [1]. Camerupt carries Earthquake and Rock Slide, which threaten Manectric and Swellow [1]. Use Water-type moves like Surf to deal heavy damage to both opponents simultaneously [15][3].

---

### Next Steps

1. **Level up your party:** Your party is currently heavily underleveled [1]. Marshtomp is Level 33, while Tate & Liza's team is Level 41-42; you will need to level up significantly to survive [1].
2. **Evolve Marshtomp and upgrade moves:** Marshtomp evolves into Swampert at level 36 [16]. Teach it Surf (HM03) and Muddy Water (learned at level 37) to exploit the Fire-type weaknesses of the Gym Leaders' Pokémon [17][3].

---

### Assumptions
* Your randomized seed left wild encounters and TM availability normal [18].
* You are willing to spend time grinding levels to bridge the 9-level gap before fighting Tate & Liza [1].

### To sharpen this
* Are you willing to replace Marshtomp/Swampert or run multiple Water-types, as Spheal/Sharpedo would add type overlap to your party [4][11]?
* Do you prefer a highly defensive pivot or a fast, offensive threat for your tactical playstyle [4][11]?

### Not covered
* We don't know the exact movesets of your party, so we can't suggest exactly which moves to replace.

## Sources

1. Your randomizer log: Leader Tate&Liza's team (`log:trainers#271`)
2. PokeAPI: Spheal at Shoal Cave (walk) (`pokeapi:encounters#70736`)
3. pokeemerald data/maps/PetalburgCity_WallysHouse (HM03) (`decomp:data/maps/PetalburgCity_WallysHouse#HM03`)
4. PokeAPI: Spheal (species data) (`pokeapi:pokemon_species#363`)
5. PokeAPI: Walrein (species data) (`pokeapi:pokemon_species#365`)
6. PokeAPI: Aron at Granite Cave (walk) (`pokeapi:encounters#29913`)
7. PokeAPI: Aron (species data) (`pokeapi:pokemon_species#304`)
8. PokeAPI: Aggron (species data) (`pokeapi:pokemon_species#306`)
9. PokeAPI: Sharpedo at Route 103 (super-rod) (`pokeapi:encounters#29611`)
10. PokeAPI: Sharpedo at Route 118 (super-rod) (`pokeapi:encounters#29834`)
11. PokeAPI: Sharpedo (species data) (`pokeapi:pokemon_species#319`)
12. PokeAPI: Shuppet at Mt. Pyre (walk) (`pokeapi:encounters#29953`)
13. PokeAPI: Shuppet (species data) (`pokeapi:pokemon_species#353`)
14. PokeAPI: Banette (species data) (`pokeapi:pokemon_species#354`)
15. Gen 3 type chart (pokeemerald gTypeEffectiveness) (`rules:gen3_type_chart`)
16. PokeAPI: Marshtomp evolves into Swampert (`pokeapi:pokemon_evolution#135`)
17. PokeAPI: Marshtomp learns Muddy Water (level-up) (`pokeapi:pokemon_moves#259/330/level-up/37`)
18. LockeSmith's Emerald rules (agent/brief.py) (`rules:game`)
