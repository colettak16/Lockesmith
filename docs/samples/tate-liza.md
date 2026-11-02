# Agent: tate-liza

**Question:** What should I catch to get through Tate & Liza?

79.1 s · 19 model calls · 83,178 tokens · about $0.247 · researchers: battle_researcher, catch_researcher, moves_researcher, story_researcher · 20 trace steps (full trace in `tate-liza.json`)

## Answer

To counter Tate & Liza's double battle strategy, catch a Sharpedo or Shuppet to exploit their Psychic typing with special Dark or physical Ghost attacks [1][2][3][4].

### Top picks

#### Sharpedo (core)
* **Where:** Route 122 (Super Rod, levels 30-35, 40% odds) [5][6].
* **When:** Available on the water route just before Mt. Pyre [5].
* **Why it helps now:** Its Water/Dark typing gives it STAB moves (Surf and Crunch) that deal super-effective special damage to all of Tate & Liza's Pokémon, bypassing their defensive setups [1][7][3][4]. *Note: In Gen III, Surf (Water) and Crunch (Dark) are both special moves, meaning they use Sharpedo's lower Sp. Atk (95) rather than its massive Attack (120).*
* **Long run:** Incredibly strong against Phoebe's Ghost types in the Elite Four, though its paper-thin defenses make it high-risk for taking direct hits [1].
* **Backup:** **Staryu** (Lilycove City, Super Rod, 15% odds) [8]. It can evolve into Starmie with a Water Stone to hit their Rock/Ground types with Surf [9], making it a premier utility sweeper later [9]. *Note: Make sure you can obtain a Water Stone before Mossdeep Gym.*

#### Shuppet (core)
* **Where:** Mt. Pyre 1F-3F (Walking, levels 22-29, 100% odds) [10].
* **When:** Inside Mt. Pyre on Route 122 before reaching Lilycove City [10].
* **Why it helps now:** Since Ghost moves are physical in Gen III, Shuppet's evolution, Banette, uses its massive base 115 Attack to hit Tate & Liza's Psychic types incredibly hard with Shadow Ball [11][2][12][3][4].
* **Long run:** Remains a powerful physical attacker against Phoebe's Ghost-type team in the Elite Four and provides strong neutral physical damage [11][2].
* **Backup:** **Absol** (Route 120, tall grass) [13]. Uses its high Attack stat with physical moves like Slash and TM30 Shadow Ball to hit Psychic types incredibly hard [14][12][4].

---

### Key Battle Notes

#### Mossdeep Gym: Tate & Liza
Tate & Liza use a highly synergistic double battle strategy [15]. 
* Their entire team (Claydol, Xatu, Lunatone, Solrock) is immune to Ground moves [15][16][17][18], allowing Claydol to safely spam Earthquake (dealing 2x damage to your Manectric) [15].
* Solrock sets up Sunny Day to fire off instantaneous Solar Beams (dealing 4x damage to Marshtomp/Swampert) and boosted Flamethrowers (dealing 2x damage to Breloom) [18].
* All four of their Pokémon carry Psychic, which deals 2x damage to Breloom [15][16][17][18].

---

### Assumptions
* You will train Marshtomp to level 36 so it evolves into Swampert before the Gym battle.
* Your party will be leveled up to roughly level 41-42 to match Tate & Liza.

### To sharpen this
* Do you prefer a bulky, defensive Ghost-type option like Dusclops, or a fast, offensive physical sweeper like Banette?
* Have you already used TM30 Shadow Ball from Mt. Pyre, or is it available for Banette or Absol?

### Not covered
* Whether you currently have access to a Water Stone (e.g., from the Abandoned Ship or trading Blue Shards) to evolve Staryu into Starmie.

## Sources

1. PokeAPI: Sharpedo (species data) (`pokeapi:pokemon_species#319`)
2. PokeAPI: Banette (species data) (`pokeapi:pokemon_species#354`)
3. database query df73c3cdc5 (`sql:df73c3cdc5`)
4. database query e8f9d1adfd (`sql:e8f9d1adfd`)
5. PokeAPI: Carvanha at Route 118 (super-rod) (`pokeapi:encounters#29835`)
6. PokeAPI: Sharpedo at Route 122 (super-rod) (`pokeapi:encounters#30596`)
7. PokeAPI: Sharpedo learns Crunch (level-up) (`pokeapi:pokemon_moves#319/242/level-up/22`)
8. PokeAPI: Staryu at Lilycove City (super-rod) (`pokeapi:encounters#30913`)
9. PokeAPI: Staryu evolves into Starmie (`pokeapi:pokemon_evolution#70`)
10. PokeAPI: Shuppet at Mt. Pyre (walk) (`pokeapi:encounters#29953`)
11. PokeAPI: Shuppet evolves into Banette (`pokeapi:pokemon_evolution#180`)
12. database query 6005a6e2e2 (`sql:6005a6e2e2`)
13. PokeAPI: Absol (species data) (`pokeapi:pokemon_species#359`)
14. PokeAPI: Absol learns Slash (level-up) (`pokeapi:pokemon_moves#359/163/level-up/36`)
15. pokeemerald src/data/trainer_parties.h (sParty_TateAndLiza1/1) (`decomp:trainer_parties.h#sParty_TateAndLiza1/1`)
16. pokeemerald src/data/trainer_parties.h (sParty_TateAndLiza1/2) (`decomp:trainer_parties.h#sParty_TateAndLiza1/2`)
17. pokeemerald src/data/trainer_parties.h (sParty_TateAndLiza1/3) (`decomp:trainer_parties.h#sParty_TateAndLiza1/3`)
18. pokeemerald src/data/trainer_parties.h (sParty_TateAndLiza1/4) (`decomp:trainer_parties.h#sParty_TateAndLiza1/4`)
