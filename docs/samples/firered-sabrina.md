# Agent: firered-sabrina

**Question:** What should I catch to beat Sabrina?

53.8 s · 20 model calls · 88,327 tokens · about $0.214 · researchers: battle_researcher, catch_researcher, moves_researcher, story_researcher · 22 trace steps (full trace in `firered-sabrina.json`)

## Answer

Snorlax is the perfect counter to Sabrina's Psychic-types, combining massive Special Defense to absorb her attacks with high physical Attack to exploit her team's weak physical bulk [1].

### Top picks

#### Snorlax (core)
* **Where:** Route 12 or Route 16 by using the Poké Flute (Lv30) [2][3].
* **When:** Available immediately, before entering Saffron Gym [2].
* **Why it helps now:** It has an enormous HP stat (160) and excellent Special Defense (110) to sponge Sabrina's Special-based Psychic attacks [1]. Since Ghost is a physical type in Gen III, Snorlax is one of the best users of TM30 Shadow Ball (bought at the Celadon Game Corner), dealing heavy physical damage to Sabrina's physically frail Psychic-types [1][4][5].
* **Key moves:** Body Slam, Shadow Ball (TM30 from Celadon Game Corner) [6][4][5].
* **Long run:** Outstanding [1]. It remains one of the strongest overall Pokémon through the Elite Four and Champion due to its sheer bulk, Thick Fat/Immunity ability, and wide TM learnset [1].
* **Backup:** Scyther (core; Celadon Prize Corner for 5,500 coins or Safari Zone, Lv23-28) [7]. It has high physical Attack (110) and Speed (105) to strike hard with physical Bug-type moves against Sabrina's fragile Psychic-types [8]. While it cannot evolve into Scizor until the postgame National Dex, it still functions well as a fast physical attacker [9][8].

---

### Key Battles

#### Gym 6: Sabrina
Sabrina uses Kadabra (Lv38), Mr. Mime (Lv37), Venomoth (Lv38), and Alakazam (Lv43) [10][11][12][13]. Kadabra, Mr. Mime, and Alakazam all use Calm Mind to raise their Special Attack and Special Defense [10][11][13]. Target their weak physical Defense with strong physical attackers [10]. Be cautious of Mr. Mime, which can set up physical defense with Barrier and use Baton Pass to give its stat boosts to Alakazam [11].

---

### Next steps

1. **Navigate Silph Co.:** Retrieve the Card Key on 5F to unlock the electronic doors [14].
2. **Defeat the Rival:** Use the warp panel on 3F to reach the northwest room on 7F, where you will battle your Rival [15][16][17].
3. **Clear out Team Rocket:** Continue to 11F and defeat Giovanni [18]. This clears the Team Rocket Grunts blocking Saffron Gym, allowing you to challenge Sabrina [19].

---

### Assumptions
* You have enough money or Game Corner coins to obtain TM30 Shadow Ball from Celadon City, which is highly recommended for Snorlax [5].

### To sharpen this
* Do you have access to physical TM moves like Return to exploit the low physical Defense of Sabrina's Psychic-types?

## Sources

1. PokeAPI: Snorlax (species data) (`pokeapi:pokemon_species#143`)
2. PokeAPI: Snorlax at Route 12 (pokeflute) (`pokeapi:encounters#58090`)
3. PokeAPI: Snorlax at Route 16 (pokeflute) (`pokeapi:encounters#58091`)
4. PokeAPI: Snorlax learns Shadow Ball (machine) (`pokeapi:pokemon_moves#143/247/machine`)
5. pokefirered data/maps/CeladonCity_GameCorner_PrizeRoom (TM30) (`decomp:data/maps/CeladonCity_GameCorner_PrizeRoom#TM30`)
6. PokeAPI: Snorlax learns Body Slam (level-up) (`pokeapi:pokemon_moves#143/34/level-up/33`)
7. PokeAPI: Scyther at Celadon City (gift) (`pokeapi:encounters#71147`)
8. PokeAPI: Scyther (species data) (`pokeapi:pokemon_species#123`)
9. LockeSmith's FireRed rules (agent/brief.py) (`rules:game`)
10. pokefirered src/data/trainer_parties.h (sParty_LeaderSabrina/1) (`decomp:trainer_parties.h#sParty_LeaderSabrina/1`)
11. pokefirered src/data/trainer_parties.h (sParty_LeaderSabrina/2) (`decomp:trainer_parties.h#sParty_LeaderSabrina/2`)
12. pokefirered src/data/trainer_parties.h (sParty_LeaderSabrina/3) (`decomp:trainer_parties.h#sParty_LeaderSabrina/3`)
13. pokefirered src/data/trainer_parties.h (sParty_LeaderSabrina/4) (`decomp:trainer_parties.h#sParty_LeaderSabrina/4`)
14. Bulbapedia: Walkthrough:Pokémon FireRed and LeafGreen/Part 11 § Saffron City > Silph Co. > 5F (`guide:Walkthrough:Pokemon_FireRed_and_LeafGreen/Part_11#5F`)
15. Story progression (data/progression_frlg.yaml): Silph Co.: Rival (`progression:rival6_silph`)
16. Bulbapedia: Walkthrough:Pokémon FireRed and LeafGreen/Part 11 § Saffron City > Silph Co. > 7F (Northwest) (`guide:Walkthrough:Pokemon_FireRed_and_LeafGreen/Part_11#7F_(Northwest)`)
17. Bulbapedia: Walkthrough:Pokémon FireRed and LeafGreen/Part 11 § Saffron City > Silph Co. > 3F (`guide:Walkthrough:Pokemon_FireRed_and_LeafGreen/Part_11#3F_2`)
18. Story progression (data/progression_frlg.yaml): Silph Co. 11F: Giovanni (`progression:boss2_silph_co`)
19. Story progression (data/progression_frlg.yaml): Saffron Gym: Sabrina (`progression:gym6_sabrina`)
