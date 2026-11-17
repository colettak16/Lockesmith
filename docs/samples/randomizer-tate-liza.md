# Agent: randomizer-tate-liza

**Question:** What should I catch to get through Tate & Liza?

71.4 s · 14 model calls · 55,375 tokens · about $0.146 · researchers: battle_researcher, catch_researcher, moves_researcher · 13 trace steps (full trace in `randomizer-tate-liza.json`)

## Answer

Since this randomized run gave Tate & Liza a pure Fire-type team, your best bet is leveling up Marshtomp and catching another fast Water-type to drown them [1].

### Top picks

#### Staryu (Starmie) — Core [2]
* **Where:** Lilycove City (Super Rod, 15%, levels 25-30) [3]
* **When to catch:** Before Tate & Liza
* **Why it helps now:** With base 115 Speed and 100 Special Attack as Starmie, it can easily outspeed and wash away Tate & Liza's Fire-type team (Camerupt, Torkoal, Magcargo, and Houndoom) using Surf [1]. 
* **Long run:** One of the best Water-types in the game [3]. It gets incredibly diverse TM coverage (Thunderbolt, Ice Beam, Psychic, Surf) making it a top-tier asset for the Elite Four [3].
* **Backup:** Spheal (Shoal Cave, Walk, 50%, levels 26-32) [4]. Its Water/Ice typing and high bulk give you a more durable option to take hits while dealing super-effective Water damage [4]. Walrein's exceptional bulk and Ice typing make it a premier counter to Elite Four Drake's Dragon-types later on [5].
* *Note:* Starmie needs a Water Stone to evolve. Make sure you can obtain one before challenging Tate & Liza.

#### Carvanha (Sharpedo) — For this fight [6]
* **Where:** Route 119 (Super Rod, 100%, levels 20-45) or Route 118 (Super Rod, 60%, levels 20-45) [7]
* **When to catch:** Before Tate & Liza
* **Why it helps now:** Evolves immediately at level 30 into Sharpedo, giving you an aggressive Water-type attacker that can deal massive damage to the Fire-type gym [6][8].
* **Long run:** Outstanding late-game offensive profile, but its low defenses make it a glass cannon that requires careful positioning [8].
* **Backup:** None listed.
* *Note:* In Generation III, Surf (Water) and Crunch (Dark) are both classified as Special attacks. While Sharpedo has a massive Attack stat of 120, its Special Attack is still a decent 95 [9].

---

### Key Battles

#### Gym 7: Mossdeep Gym (Tate & Liza)
* **The Team:** Tate & Liza's randomized team consists entirely of Fire-types: Camerupt, Torkoal, Magcargo, and Houndoom [1].
* **Strategy:** Magcargo is 4x weak to Water and Ground, while the others are 2x weak to both types [10]. Beware of Camerupt's Earthquake and Rock Slide, which threaten Manectric, Swellow, and Breloom [1].
* **Preparation:** Level up your team. Your highest level is 33, while Tate & Liza's Pokémon peak at level 42 [11]. Evolving Marshtomp into Swampert (at level 36) is highly recommended so it can tank hits and use its Ground typing [11].

---

### Assumptions
* You have access to a Super Rod [3].
* You are willing to grind levels to close the 9-level gap before challenging the gym [11].

### To sharpen this
* Do you have a Water Stone available to evolve Staryu [2]?
* Do you need advice on the best grinding spots before taking on the gym [11]?

### Not covered
* Whether you have the TMs for Thunderbolt, Ice Beam, or Psychic available for Starmie [3].

## Sources

1. Your randomizer log: Leader Tate&Liza's team (`log:trainers#271`)
2. PokeAPI: Staryu evolves into Starmie (`pokeapi:pokemon_evolution#70`)
3. PokeAPI: Staryu at Lilycove City (super-rod) (`pokeapi:encounters#30913`)
4. PokeAPI: Spheal at Shoal Cave (walk) (`pokeapi:encounters#70736`)
5. PokeAPI: Sealeo evolves into Walrein (`pokeapi:pokemon_evolution#185`)
6. PokeAPI: Carvanha evolves into Sharpedo (`pokeapi:pokemon_evolution#166`)
7. PokeAPI: Carvanha at Route 119 (super-rod) (`pokeapi:encounters#30515`)
8. database query 1224539e18 (`sql:1224539e18`)
9. PokeAPI: Sharpedo learns Crunch (level-up) (`pokeapi:pokemon_moves#319/242/level-up/22`)
10. Gen 3 type chart (pokeemerald gTypeEffectiveness) (`rules:gen3_type_chart`)
11. Story progression (data/progression.yaml): Mossdeep Gym: Tate & Liza (`progression:gym7_tate_liza`)
