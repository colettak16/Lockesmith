# Codex review of docs/review_packet_frlg_round2.md (2026-11-03)

Model: gpt-6.1-sol via the Codex CLI, reasoning effort high, packet on stdin from an empty folder. Points applied were checked at the pinned commit first (docs/decisions.md D16).

The revised battle order is playable, and **none of the listed HMs is too early**. The remaining problems are a few encounter-location entries, omitted wild-battle gates, and the exact S.S. Anne closure timing.

I used your pinned excerpts as supplied. Supplementary links below point to current repository files; I could not independently fetch the rest of `ce6406d8`.

**Change-by-change verdicts**

| Change | Verdict | Explanation |
|---|---|---|
| R-01 | **CONFIRMED** | Storage is restored upon entering Three Isle Port, before the Biker fights—not upon rescuing Lostelle. |
| R-02 | **CONFIRMED** | Hall of Fame, 60 species owned, and One Island visited. Completing Lostelle’s errand is not itself a National Dex requirement. |
| R-03 | **CONFIRMED** | Miguel gates passage through Mt. Moon. The western Route 4 Pokémon Center and Mt. Moon encounters precede him. |
| R-04 | **CONFIRMED** | The listed southern destinations can precede Misty after Bill. For these encounter identifiers, Route 2’s northern entry represents the **Mr. Mime trade**, correctly reached through Diglett’s Cave. |
| R-05 | **CONFIRMED** | Those destinations and northern Route 12 fishing are available before Surge. Fly can be obtained there, but becomes usable after Surge. |
| R-06 | **CONFIRMED** | The three Rockets and Fuji rescue belong here. However, the preceding **ghost Marowak gate is still missing**. |
| R-07 | **CONFIRMED** | Route 19 beach fishing precedes Koga; Surf use follows him. |
| R-08 | **CONFIRMED**, with a timing clarification | Everything listed is obtainable before step 14. **Card Key is already obtainable before step 13**, because Silph opens after Fuji; it has no Surf requirement. |
| R-09 | **CONFIRMED** | Four consecutive battles: three Biker Goons and Paxton. The listed One/Two Island destinations can precede them. |
| R-10 | **CONFIRMED** | The **Dunsparce grass** is postgame. The accessible port itself must be distinguished from that grass. |
| R-11 | **CONFIRMED** | Celio exchanges the Ruby and Tri-Pass for the Rainbow Pass after the National Dex unlocks the Ruby quest. |
| R-12 | **CONFIRMED** | Tri-Pass starts after Blaine and persists through this pre-Champion itinerary. |
| R-13 | **CONFIRMED** | Copycat’s house opens after Silph Giovanni; Mimic also requires bringing a Poké Doll. |
| R-14 | **CONFIRMED** | Leaving the ship after receiving HM01 triggers departure. **The rival battle itself does not close anything.** A Sevii pass enables ferry travel, without reopening `SSAnne_Exterior`. |

The Route 2 distinction matters: the encounter data assigns FRLG’s Mr. Mime trade to `north-towards-pewter-city`. That entry should stay at step 6, even though the northern outdoor grass is geographically reachable before Brock. [PokeAPI encounter data](https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/encounters.csv)

**Step-by-step review**

Numbers below refer to your existing table.

| Step | Finding |
|---|---|
| **1 — Lab rival** | **Move `pallet-town/main` here from step 2**, assuming it includes the starter encounter. You choose your starter before this battle. |
| **2 — Optional Route 22 rival** | Other listed areas are correctly available. Remove the duplicate “optional” label. |
| **3 — Brock** | Correct for the encounter identifiers being used. |
| **4 — Miguel** | Correct. Also normalize the excluded `kanto-route-3/pokemon-center` alias to the Route 4 Pokémon Center here; see below. |
| **5 — Cerulean rival** | Correct. |
| **6 — Misty** | Correct. Bill’s rescue and receipt of the S.S. Ticket must occur within this preceding interval. Old Rod, Bicycle, Diglett’s Cave and the Mr. Mime trade are obtainable before Misty. |
| **7 — S.S. Anne rival** | Correct. **Do not close the ship/dock at the battle itself.** |
| **8 — Surge** | Listed destinations and Cut/Flash timing are correct. Flash assumes **10 species owned**. Pallet fishing is also available by this step after returning through Diglett’s Cave and using Cut. |
| **9 — Erika** | Correct; Fly is now usable following Surge. |
| **10 — Hideout Giovanni** | Correct. The Lift Key must have been collected before reaching him. |
| **11 — Tower rival** | Valid placement. The battle can be done earlier, on the first Lavender visit, but postponing it causes no problem. |
| **12 — Tower Rockets/Fuji** | **Add ghost Marowak on 6F before these Rockets**, either as its own step or an explicitly named part of this step. If separate, put `pokemon-tower`’s catchable floors before the new Marowak step. |
| **13 — Koga** | Area/HM timing is correct **after clearing a Snorlax roadblock**. Name that event explicitly; details below. Card Key can also already be collected during this interval. |
| **14 — Silph rival** | Correct. Surf permits Cinnabar, fossil revival, the Mansion and Secret Key before this battle. |
| **15 — Silph Giovanni** | Correct for the **Lapras encounter** represented by `saffron-city/silph-co-7f`: the employee becomes reachable after the rival. The physical floor is accessible earlier. |
| **16 — Sabrina** | Correct. Copycat/Mimic is now available too, following step 15. |
| **17 — Blaine** | Correct; no Tri-Pass yet. |
| **18 — Bikers/Paxton** | Correct destinations and HM timing. The initial Lostelle-request scene on Two Island must occur before the gang sequence. Remove the duplicate “optional” label. |
| **19 — Hypno** | Correct. Afterward, hand over the Meteorite and return to Bill/Celio before proceeding back to Kanto. Remove the duplicate “optional” label. |
| **20 — Viridian Giovanni** | Correct on the completed-Sevii branch. Tri-Pass and Rock Smash remain conditional on taking that detour. |
| **21 — Route 22 rival** | Correct. |
| **22 — Lorelei** | Correct under your stated Route 23 convention. |
| **23 — Bruno** | Correct. |
| **24 — Agatha** | Correct. |
| **25 — Lance** | Correct. |
| **26 — Champion** | Correct. |

There are four substantive details behind those flags:

- **Marowak is a required progression battle**, not an ordinary trainer covered by your implicit-trainer convention. It blocks the ascent to 7F and cannot be caught. [6F ghost script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/PokemonTower_6F/scripts.inc)

- **At least one Snorlax must be cleared before reaching Fuchsia/Koga.** Either Route 12 or Route 16 works. You need not defeat it—catching it or fleeing can clear the road. If step 13 lists both southern approaches as explored, clearing both can occur within that interval. An explicit “clear Route 12/16 Snorlax” subevent is sufficient. [Route 12 script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/Route12/scripts.inc), [Route 16 script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/Route16/scripts.inc)

- **The S.S. Anne closure note is too early.** After beating the rival, you can leave without collecting Cut, fish at the dock, and return aboard. Replace “only before the ship’s rival” with **“until leaving the ship after receiving HM01, between steps 7 and 8.”** [Captain’s script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/SSAnne_CaptainsOffice/scripts.inc), [departure script](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/SSAnne_Exterior/scripts.inc)

- **The initial Sevii visit is optional as a whole.** Once you take Bill’s initial trip, steps 18–19 are prerequisites to completing the errand and returning normally to Kanto; they are not independently skippable while continuing directly to step 20. The Meteorite handover advances the return scene, and Vermilion ferry access is gated accordingly. [Meteorite handover](https://raw.githubusercontent.com/pret/pokefirered/master/data/maps/TwoIsland_JoyfulGameCorner/scripts.inc), [ferry menus](https://raw.githubusercontent.com/pret/pokefirered/master/data/scripts/seagallop.inc)

**Corrections to “Never reachable before the Champion”**

- **`pallet-town` is wrong as a geographical or ordinary encounter exclusion.** Its shoreline fishing is available before Surge once you can return with Cut; Surf encounters follow Koga. If the unsuffixed entry duplicates `pallet-town/main`, merge the identifiers instead of declaring one postgame. [Pallet encounter tables](https://raw.githubusercontent.com/pret/pokefirered/master/src/data/wild_encounters.json)
- **`kanto-route-3/pokemon-center` is a location-data alias/error**, not a postgame destination. Its Magikarp purchase should map to `kanto-route-4/pokemon-center` at step 4. The encounter database contains both identifiers for that purchase. [Location-area identifiers](https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/location_areas.csv), [encounter records](https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/encounters.csv)
- **`three-isle-port` is correct only when it means the Dunsparce encounter patch.** Label it that way so it does not contradict the pregame port visit in R-01.
- **`kanto-pokecenter` represents event-distribution encounters**, so it belongs under an event-only exclusion, rather than a normal story unlock.

The remaining postgame exclusions are consistent with this itinerary. If “key items” is meant to be exhaustive, also add the omitted progression items—especially **S.S. Ticket, Lift Key and Meteorite**—at their acquisition points; their omission does not make the currently listed items premature.