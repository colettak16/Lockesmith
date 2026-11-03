# Codex review of docs/review_packet_frlg.md, round 1 (2026-11-03)

Model: gpt-6.1-sol via the Codex CLI (the user's ChatGPT account), reasoning effort high, run from an empty folder with the packet on stdin. Its links point to pret/pokefirered master; every claim applied was checked at the pinned commit first (docs/decisions.md D16).

The main battle sequence is workable. **C-09 is wrong**, and several areas and items are placed later than their actual first availability. The biggest missing milestones are Mt. Moon clearance, Mr. Fuji’s rescue, and Three Island’s biker battles.

I treated E1–E15 as authoritative. Supplemental decomp links below point to `master`; I could not retrieve the pinned revision directly.

| Claim | Verdict | Review |
|---|---|---|
| C-01 | **CONFIRMED** | All seven badge/HM pairings match E1. Possessing the HM and having a compatible Pokémon are additional requirements. |
| C-02 | **CONFIRMED** | E2 checks badges 2–7 and omits Boulder. Boulder is nevertheless required earlier in ordinary progression. |
| C-03 | **CONFIRMED** | Tea comes from the old woman in Celadon Condominiums 1F. Giving it to one guard opens all four approaches. [Tea script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/CeladonCity_Condominiums_1F/scripts.inc). |
| C-04 | **CONFIRMED** | Sabrina’s entrance remains blocked until Silph Giovanni is defeated. E3 supports this ordering. |
| C-05 | **CONFIRMED** | Early Route 22 rival is optional; the post-Giovanni rival is required on the normal League approach. E4. |
| C-06 | **CONFIRMED** | Bill waits in Cinnabar’s Pokémon Center if declined. E5. |
| C-07 | **CONFIRMED** | For the initial visit, complete Lostelle’s rescue, deliver the Meteorite, then return to One Island for Bill’s return sequence. That enables subsequent ferry travel to Vermilion. E6–E9. |
| C-08 | **CONFIRMED** | You can decline Bill and complete Viridian Gym and the League. |
| C-09 | **WRONG** | **Entering Three Isle Port clears `FLAG_SYS_PC_STORAGE_DISABLED` immediately.** Neither Lostelle’s rescue nor the postgame is required. [Port transition script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/ThreeIsland_Port/scripts.inc). |
| C-10 | **CONFIRMED** | E10 supports the evolution restriction. Qualify the parenthetical: the National Dex requires the Hall of Fame, **60 species registered as caught**, and having visited One Island; it is not automatic upon becoming Champion. [Oak’s script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/PalletTown_ProfessorOaksLab/scripts.inc). |
| C-11 | **CONFIRMED** | The evolution table retains the entries, but their day/night evaluation code is commented out. Neither evolution can occur within FRLG, even after the National Dex. [Evolution code](https://raw.githubusercontent.com/pret/pokefirered/master/src/pokemon.c). |
| C-12 | **CONFIRMED** | All three starter mappings match E11. |
| C-13 | **CONFIRMED** | Both unlock at completion of Celio’s Ruby/Sapphire network quest, not merely after the Hall of Fame. E12. |
| C-14 | **CONFIRMED** | Pickup is the native FRLG source. TM10 occupies 5% of the Pickup item distribution; that is **5% of successful finds**, not 5% of battles. E13. |
| C-15 | **CONFIRMED** | E14 requires the corresponding fully evolved Kanto starter as the lead Pokémon and friendship exactly 255. It need not be the starter originally chosen by that save. |
| C-16 | **CONFIRMED** | The level-30 ghost Marowak is a special, uncatchable battle. E15. Ordinary wild Cubone remain catchable. |
| C-17 | **CONFIRMED** | Without the Scope, Tower wild encounters remain unidentified ghosts and cannot be caught. The Scope does not make the scripted Marowak catchable. |
| C-18 | **CONFIRMED** | For ordinary first access to Fuchsia, either land route requires clearing a Snorlax with the Poké Flute. Cycling Road additionally requires a Bicycle. |
| C-19 | **CONFIRMED** | The salesman is in `Route4_PokemonCenter_1F`. Treat the Route 3 record as the same acquisition, not another salesman. |
| C-20 | **CONFIRMED** | The Secret Key is in Pokémon Mansion B1F and unlocks Cinnabar Gym. |
| C-21 | **CONFIRMED** | Fresh Water → TM16 Light Screen; Soda Pop → TM20 Safeguard; Lemonade → TM33 Reflect. Each reward is once per save. [Roof script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/CeladonCity_DepartmentStore_Roof/scripts.inc). |

For the open questions, “high” means I would use the answer in the progression data; qualifications identify anything still worth checking against the pinned maps.

| Question | Best answer | Confidence |
|---|---|---|
| Q-01 | **Mt. Moon does gate onward progression.** Super Nerd Miguel must be defeated and a fossil selected to clear the exit path. A fixed Rocket on the main B2F route also forces a battle; other Rockets are optional. Mt. Moon itself is available before these fights, but eastern Route 4/Cerulean are beyond them. [Scripts](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/MtMoon_B2F/scripts.inc), [events](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/MtMoon_B2F/map.json). | High on Miguel; medium-high on the precise mandatory Rocket set. |
| Q-02 | **Yes, before Misty.** Help Bill and obtain the S.S. Ticket. This moves the policeman and removes Cerulean’s exit obstruction. Misty is needed later to use Cut. [Cerulean script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/CeruleanCity/scripts.inc). | High |
| Q-03 | Add closure **when exiting after receiving HM01**, not on any ordinary exit and not immediately upon defeating the rival. [Captain](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/SSAnne_CaptainsOffice/scripts.inc), [departure](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/SSAnne_Exterior/scripts.inc). | High |
| Q-04 | **Yes.** With Cut, reach `Route2_EastBuilding` through the eastern Route 2 corridor. The aide requires **10 caught species**, not merely seen species. Flash is optional for traversing Rock Tunnel. [Aide script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/Route2_EastBuilding/scripts.inc). | High |
| Q-05 | **Yes.** Cut opens the northern branch containing the grass and Fly house. Snorlax blocks the southern Cycling Road approach. Move Route 16’s initial availability to **#7**, before Surge. [Route 16 events](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/Route16/map.json). | High |
| Q-06 | Good Rod: `FuchsiaCity_House2`, east of the Warden’s house. Super Rod: `Route12_FishingHouse`, south of Snorlax. Both are obtainable before Koga; neither requires Surf. Strength comes from returning the Gold Teeth to the Warden. [Good Rod](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/FuchsiaCity_House2/scripts.inc), [Super Rod](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/Route12_FishingHouse/scripts.inc). | High |
| Q-07 | **The Fighting Dojo is open during the Rocket occupation.** It is available upon first entering Saffron with Tea. Its gift requires defeating the Karate Master. The listed Surf destinations fit after Koga in this canonical order. [Dojo script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/SaffronCity_Dojo/scripts.inc). | High |
| Q-08 | **Yes. Move Cinnabar Lab to #12**, alongside Cinnabar and the Mansion. Fossil revival and trades do not require Blaine, Sabrina, or Silph completion. | High |
| Q-09 | The Exterior/summit identification and Ruby-versus-summit story distinction are sound. **Strength is required on the direct Moltres route; Rock Smash is optional for that route**, but required for Rock Smash encounters. Fly cannot return you to Kanto. I would retain **UNSURE** on the exact `cave`/`inside` aliases until comparing encounter methods, levels and slots—not species alone. [Official guide’s summit route](https://www.scribd.com/document/735465149/Poke-mon-FireRed-Version-and-LeafGreen-Version-Prima-Official-Game-Guide-2004-text). | High on story access and Strength; medium on Rock Smash independence and aliases. |
| Q-10 | Gate actual Rock Smash use on **HM06 obtained AND Marsh Badge**. Completing the errand does not guarantee collecting HM06; it can also be collected before rescuing Lostelle. | High |
| Q-11 | **Yes.** Pewter’s east exit is blocked until Brock is defeated. Also model Oak’s Parcel/Pokédex sequence before proceeding north through Viridian. | High |
| Q-12 | Same as Q-02: **Bill/S.S. Ticket opens the southward route; Misty is unnecessary.** | High |
| Q-13 | Same as Q-01: **Miguel and the main-path Rocket matter** if the table promises that only listed battles have been fought. | High on Miguel; medium-high on Rocket enumeration. |
| Q-14 | Same as Q-06. The Route 12 fisherman does not require possessing the Good Rod first. | High |
| Q-15 | **Yes**, after receiving Cut and triggering departure by exiting normally. The fishing location then closes permanently during ordinary play. | High |
| Q-16 | **No.** Fly cannot switch from the Sevii region to Kanto. It cannot bypass the initial ferry restriction. [Fly-map permissions](https://raw.githubusercontent.com/pret/pokefirered/master/src/region_map.c). | High |
| Q-17 | Yes: Mr. Fuji’s rescue, Bicycle possession, separate HM acquisition, Seafoam’s Strength puzzles, Silph’s entrance condition, and the Three Island bikers are material missing gates. Details follow. | High |

The following changes are needed in the order and gate model:

1. **Add explicit Tower completion after the Tower rival.** The ghost Marowak, the three upstairs Rockets, rescuing Mr. Fuji, and receiving his Poké Flute are separate events. Rescuing Fuji also opens Silph Co.; the Tower rival victory alone does not. [Saffron entrance script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/SaffronCity/scripts.inc).

2. **Separate Tower entry from catch availability.** Its lower floors can be entered upon reaching Lavender, before obtaining the Scope. Under your “before this battle” convention, the catchable upper-floor encounters belong after the 2F rival, with the Scope held—not before that rival in #10.

3. **Move these first-availability entries earlier:**

   | Entry | Correction |
   |---|---|
   | `ss-anne` | **#5**, because the Ticket and ship are available before Misty. Cut remains behind the ship rival. |
   | `kanto-route-16` grass/Fly-house branch | **#7**, with Cut. Keep the Snorlax/Cycling Road branch separately gated. |
   | Tea | **#7**, upon reaching Celadon. |
   | Fighting Dojo | **#7**, via Tea and Saffron. Gate the actual Hitmon gift on its battles. |
   | Route 12’s northern fishing section | **#7 at latest**, from Lavender; southern access still needs Snorlax cleared. |
   | Route 19 shore fishing | **#11**, before Koga. Surfing remains unavailable until Koga. |
   | Cinnabar Lab | **#12**, alongside Cinnabar. |
   | Card Key | **#12**, before the Silph rival: it is needed to reach that encounter normally. |
   | Secret Key | Obtainable during **#12**, since the Mansion is already reachable. |

4. **Route 23 needs sectional gates.** It is not wholly locked until eight badges. The first fishing shore is reachable after the Rainbow checkpoint; Surf opens further access after Koga, and grass becomes accessible after the Marsh checkpoint. Victory Road still requires passing all eight checks. Thus `kanto-route-23` is too late at #19 if an area means *any* available encounter method. [Route description](https://bulbapedia.bulbagarden.net/wiki/Kanto_Route_23), [badge scripts](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/Route23/scripts.inc).

5. **Move Three Isle Port’s Dunsparce encounters to postgame.** The port itself is visited during the errand, but its encounter grass is beyond the tunnel whose completed layout requires the **National Dex**. This is independent of the port restoring PCs. [Tunnel script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/ThreeIsland_DunsparceTunnel/scripts.inc).

6. **Add the Three Island biker sequence before Bond Bridge/Berry Forest access.** It comprises three Biker Goon fights followed by Cue Ball Paxton. These are missing predecessors to Hypno under the stated battle rule. [Biker scripts](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/ThreeIsland/scripts.inc).

7. **Add the Bicycle acquisition chain.** Fan Club chairman → Bike Voucher → Cerulean Bike Shop → Bicycle. Cycling Road checks Bicycle possession. The eastern route to Fuchsia remains an alternative. [Cycling Road gate](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/Route16_NorthEntrance_1F/scripts.inc).

8. **Track HM possession separately from badge permission.** Surf is obtained in the Safari Zone before Koga; Strength requires the Gold Teeth exchange; Flash requires the aide’s caught-species threshold. A badge alone does not guarantee any of these acquisitions.

9. **Keep Seafoam’s internal gates separate from entering the area.** Surf permits entry and some encounters; Strength’s boulder/current puzzles gate traversal and Articuno. Cinnabar remains reachable independently by surfing south from Pallet.

10. **Preserve optional-branch state.** After completing #16, the Tri-Pass should remain in subsequent rows—it currently disappears at #17. If #16 is skipped, its areas and HM06 must not become available automatically. During the initial island visit, Kanto is temporarily inaccessible until the return sequence.

11. **Clarify the ordinary-trainer abstraction.** “Having fought only the battles above” is literally incompatible with several routes, Nugget Bridge, the Rocket Hideout, and the Dojo gift. Either include required ordinary battles or explicitly say they are implicitly permitted between major milestones.

The remaining postgame exclusions are broadly correct. Tighten the Rainbow Pass explanation to **Hall of Fame → National Dex → deliver Ruby to Celio → Rainbow Pass**. Also, label starter-only `pallet-town` as **excluded acquisition data**, rather than geographically “never reachable”: its exclusion is intentional, but the place and starter are plainly reachable before the first rival battle.