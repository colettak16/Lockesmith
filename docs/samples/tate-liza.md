# Agent: tate-liza

**Question:** What should I catch to get through Tate & Liza?

77.1 s · 14 model calls · 55,062 tokens · about $0.173 · researchers: battle_researcher, catch_researcher, moves_researcher · 13 trace steps (full trace in `tate-liza.json`)

## Answer

Catch a Sharpedo or Shuppet to exploit Tate & Liza's type weaknesses, and level up Marshtomp to evolve into Swampert [1].

### Top picks

#### Sharpedo (core)
* **Where:** Route 103, 118, or 122 [2][3]
* **When:** Right now, using the Super Rod [2][3] (at Lv30-35) [2][3].
* **Why it helps now:** Its Dark/Water typing grants it complete immunity to Tate & Liza's Psychic attacks [4]. With STAB Surf and Crunch, it can hit their entire team for super-effective damage [5]. *Note: In Gen III, Water and Dark are both special types, whereas Sharpedo has a massive 120 Attack and a lower 95 Sp. Atk.*
* **Long run:** A potent glass cannon [4]. Its high offenses are very useful against Elite Four Phoebe's Ghost types [4].
* **Backup:** **Spheal** (found walking in Shoal Cave B1F/B2F at Lv26-32 [6]). It evolves into Sealeo at Level 32 [7]. It has great bulk to survive hits, and Surf deals super-effective damage to Claydol, Solrock, and Lunatone [8]. In the long term, it evolves into Walrein at 44, offering S-tier value and acting as the ultimate counter to Elite Four Drake [8].

#### Shuppet (for this fight)
* **Where:** Mt. Pyre 1F-3F [9] (walking at Lv22-29) [9].
* **When:** Right now, at Mt. Pyre [9].
* **Why it helps now:** It evolves into Banette at Level 37 [10]. Ghost-type moves are physical in Gen III, so Banette's massive 115 Attack allows physical Shadow Ball to completely shred the relatively fragile physical defenses of Tate & Liza's team [11].
* **Long run:** Great offensive asset against Elite Four Phoebe, but its low Speed and defensive stats make it risky in later boss fights [11].
* **Backup:** **Absol** (found walking on Route 120 at Lv25-27 [12]). It boasts a colossal 130 base Attack [13]. By teaching it Shadow Ball (TM30), it can bypass its Special Dark typing and crush the Mossdeep Gym leaders with physical Ghost damage [13]. It is a strong physical attacker, but relies on TM support since Dark-type moves run off its lower 75 Sp. Attack [13].

---

### Key Battles

#### Gym 7: Tate & Liza
Tate & Liza use Claydol, Xatu, Lunatone, and Solrock (up to Level 42) [14][15]. Claydol, Lunatone, and Solrock all have the Levitate ability, making them completely immune to Ground-type attacks [16]. Every Pokémon on their team knows Psychic, which hits Breloom for 2x super-effective damage [14][15]. Solrock also carries Sunny Day and Solar Beam, threatening Marshtomp/Swampert with a 4x super-effective Grass-type attack [15]. 

Your Marshtomp is currently Level 33, while Tate & Liza's team reaches Level 42 [15]. Marshtomp evolves into Swampert at Level 36 [1], gaining crucial stats to survive, so make sure to level it up before tackling this gym.

---

### Assumptions
* You have access to the Super Rod.
* You still have the TM for Shadow Ball (TM30) if you choose to use Shuppet/Banette or Absol.

### To sharpen this
* Have you already used TM30 (Shadow Ball)?
* Are you planning to complete the optional Lilycove City rival battle to unlock the Department Store TMs?

### Not covered
* Any specific items or party composition beyond the recommended captures.

## Sources

1. PokeAPI: Marshtomp evolves into Swampert (`pokeapi:pokemon_evolution#135`)
2. PokeAPI: Sharpedo at Route 103 (super-rod) (`pokeapi:encounters#29611`)
3. PokeAPI: Carvanha at Route 118 (super-rod) (`pokeapi:encounters#29835`)
4. PokeAPI: Sharpedo (species data) (`pokeapi:pokemon_species#319`)
5. PokeAPI: Sharpedo learns Crunch (level-up) (`pokeapi:pokemon_moves#319/242/level-up/22`)
6. PokeAPI: Spheal at Shoal Cave (walk) (`pokeapi:encounters#70736`)
7. PokeAPI: Sealeo evolves into Walrein (`pokeapi:pokemon_evolution#185`)
8. PokeAPI: Walrein (species data) (`pokeapi:pokemon_species#365`)
9. PokeAPI: Shuppet at Mt. Pyre (walk) (`pokeapi:encounters#29953`)
10. PokeAPI: Shuppet evolves into Banette (`pokeapi:pokemon_evolution#180`)
11. PokeAPI: Banette (species data) (`pokeapi:pokemon_species#354`)
12. PokeAPI: Absol at Route 120 (walk) (`pokeapi:encounters#30560`)
13. PokeAPI: Absol (species data) (`pokeapi:pokemon_species#359`)
14. pokeemerald src/data/trainer_parties.h (sParty_TateAndLiza1/1) (`decomp:trainer_parties.h#sParty_TateAndLiza1/1`)
15. pokeemerald src/data/trainer_parties.h (sParty_TateAndLiza1/4) (`decomp:trainer_parties.h#sParty_TateAndLiza1/4`)
16. database query a5bbcba1f9 (`sql:a5bbcba1f9`)
