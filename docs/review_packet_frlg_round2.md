# Review packet: FireRed/LeafGreen story order, round 2

Round 1 (your review) led to the changes listed below; each was checked in pret/pokefirered at commit ce6406d8
before it was applied. Please review the revised order as a careful FireRed/LeafGreen expert:

1. For each change (R-xx), say CONFIRMED or WRONG (with the fix).
2. Then go through the table step by step and flag anything still wrong: a step missing or out of order, an area
   listed too early or too late, an HM or key item listed before it can be had. Say which step and why.
3. Keep in mind the conventions: an area appears at the first step it can be reached before; HMs/key items are
   cumulative; ordinary trainers between milestones are implicitly fought; optional steps (marked) can be skipped,
   and the Sevii steps assume the player took Bill's trip. Route 23's partial mid-game access is knowingly not
   modelled (the whole route opens with the League).

## Changes since round 1

- **R-01** PC storage is off from the first One Island meeting until Three Isle Port (ThreeIsland_Port clears FLAG_SYS_PC_STORAGE_DISABLED on transition) (E1).
- **R-02** The National Dex needs the Hall of Fame, 60 species caught and One Island visited (E2).
- **R-03** New required step: Mt. Moon's Super Nerd Miguel (B2F), after Brock (E3). Route 3, Route 4's Pokemon Center and Mt. Moon open before him; Route 4's main area and Cerulean after.
- **R-04** Cerulean's south/east exits stay blocked until the S.S. Ticket (E4), so Route 5, the Underground Path, Route 6, Vermilion, the S.S. Anne's dock, Route 11, Diglett's Cave and Route 2's north part come before Misty, after the Cerulean rival and Bill.
- **R-05** With Cut (after the S.S. Anne): Route 16's north branch (Snorlax still gates its 'pokeflute' encounter and Cycling Road), Tea from the Celadon Condominiums, Saffron's Fighting Dojo (open during the takeover), and Route 12's north-end fishing come before Surge.
- **R-06** New required step: Pokemon Tower 7F's three Rockets after the 2F rival; rescuing Mr. Fuji gives the Poke Flute and opens Silph Co. (E5). The Tower's catchable floors are listed at this step (Silph Scope in hand).
- **R-07** Route 19's shore fishing comes before Koga (Fuchsia's beach); Surf still needs Koga's Soul Badge.
- **R-08** Cinnabar's lab (fossils, trades), the Card Key and the Secret Key come at the Silph rival's step, with Surf.
- **R-09** New optional step: Three Island's three Biker Goons and Cue Ball Paxton (E6), before Bond Bridge and Berry Forest. One Island, Kindle Road, Treasure Beach, Mt. Ember (exterior, Summit Path, summit) and Cape Brink open before them.
- **R-10** Three Isle Port's grass is postgame: it's past the Dunsparce Tunnel, dug out only with the National Dex (E7).
- **R-11** Islands 4-7: the Rainbow Pass comes from Celio for the Ruby, after the National Dex (E8).
- **R-12** The Tri-Pass stays a key item after the Sevii steps; Blaine's step doesn't have it.
- **R-13** The Mimic tutor (Copycat's house) is blocked by a Rocket at its door until Silph Co. is cleared.
- **R-14** The S.S. Anne's dock closes for good when you step off with HM01 (the ship leaves; the harbor sailor turns you away without a Sevii pass).

## Revised story order

| # | step | badges before | HMs usable | key items | areas first reachable |
|---|---|---|---|---|---|
| 1 | Oak's Lab: Rival (first battle) | 0 | - | - | - |
| 2 | Route 22: Rival (optional) (optional) | 0 | - | - | pallet-town/main, kanto-route-1, viridian-city, kanto-route-22, kanto-route-2/south-towards-viridian-city, viridian-forest |
| 3 | Pewter Gym: Brock | 0 | - | - | - |
| 4 | Mt. Moon: Super Nerd Miguel | 1 | - | - | kanto-route-3, kanto-route-4/pokemon-center, mt-moon |
| 5 | Cerulean City: Rival | 1 | - | - | kanto-route-4/main, cerulean-city |
| 6 | Cerulean Gym: Misty | 1 | - | old-rod, bicycle | kanto-route-24, kanto-route-25, kanto-route-5, kanto-underground-path, kanto-route-6, vermilion-city, ss-anne, kanto-route-11, digletts-cave, kanto-route-2/north-towards-pewter-city |
| 7 | S.S. Anne: Rival | 2 | - | old-rod, bicycle | - |
| 8 | Vermilion Gym: Lt. Surge | 2 | cut, flash | old-rod, bicycle, tea | kanto-route-9, kanto-route-10, rock-tunnel, kanto-route-8, kanto-route-7, celadon-city/main, celadon-city/celadon-mansion, celadon-city/prize-corner, kanto-route-16, saffron-city/fighting-dojo, kanto-route-12 (old-rod/good-rod/super-rod) |
| 9 | Celadon Gym: Erika | 3 | cut, flash, fly | old-rod, bicycle, tea | - |
| 10 | Rocket Hideout: Giovanni | 4 | cut, flash, fly | old-rod, bicycle, tea | - |
| 11 | Pokémon Tower: Rival | 4 | cut, flash, fly | old-rod, bicycle, tea, silph-scope | - |
| 12 | Pokémon Tower 7F: Team Rocket (Mr. Fuji) | 4 | cut, flash, fly | old-rod, bicycle, tea, silph-scope | pokemon-tower |
| 13 | Fuchsia Gym: Koga | 4 | cut, flash, fly, strength | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod | kanto-route-12, kanto-route-13, kanto-route-14, kanto-route-15, kanto-route-17, kanto-route-18, fuchsia-city, kanto-safari-zone, kanto-sea-route-19 |
| 14 | Silph Co.: Rival | 5 | cut, flash, fly, strength, surf | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key | kanto-sea-route-20, kanto-sea-route-21, seafoam-islands, kanto-power-plant, cinnabar-island, cinnabar-island/cinnabar-lab, pokemon-mansion |
| 15 | Silph Co. 11F: Giovanni | 5 | cut, flash, fly, strength, surf | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key | saffron-city/silph-co-7f |
| 16 | Saffron Gym: Sabrina | 5 | cut, flash, fly, strength, surf | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key | - |
| 17 | Cinnabar Gym: Blaine | 6 | cut, flash, fly, strength, surf | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key | - |
| 18 | Three Island: Biker gang and Cue Ball Paxton (optional Sevii errand) (optional) | 7 | cut, flash, fly, strength, surf, rock-smash | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key, tri-pass | one-island, kindle-road, treasure-beach, mt-ember/main, mt-ember/cave, mt-ember/inside, mt-ember/summit, two-island, cape-brink |
| 19 | Sevii Islands: Berry Forest's Hypno (optional errand) (optional) | 7 | cut, flash, fly, strength, surf, rock-smash | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key, tri-pass | bond-bridge, berry-forest |
| 20 | Viridian Gym: Giovanni | 7 | cut, flash, fly, strength, surf, rock-smash | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key, tri-pass | - |
| 21 | Route 22: Rival (before the League) | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key, tri-pass | - |
| 22 | Elite Four: Lorelei | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key, tri-pass | kanto-route-23, kanto-victory-road-2 |
| 23 | Elite Four: Bruno | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key, tri-pass | - |
| 24 | Elite Four: Agatha | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key, tri-pass | - |
| 25 | Elite Four: Lance | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key, tri-pass | - |
| 26 | Champion: Rival | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, bicycle, tea, silph-scope, poke-flute, good-rod, super-rod, card-key, secret-key, tri-pass | - |

Closes for good: ss-anne after step 'rival4_ss_anne' (the S.S. Anne leaves when you step off with HM01 (VAR_MAP_SCENE_VERMILION_CITY = 3); after that Vermilion's harbor sailor turns you away unless you have a Sevii pass, so the dock's fishing (SSAnne_Exterior) is only before the ship's rival)

Never reachable before the Champion: pallet-town; three-isle-port; kanto-route-3/pokemon-center; kanto-pokecenter; cerulean-cave; roaming-kanto; navel-rock; birth-island; kanto-altering-cave; water-labyrinth; four-island; icefall-cave; five-island; five-isle-meadow; memorial-pillar; resort-gorgeous; water-path; ruin-valley; green-path; outcast-island; pattern-bush; lost-cave; canyon-entrance; sevault-canyon; tanoby-ruins; monean-chamber; liptoo-chamber; weepth-chamber; dilford-chamber; scufib-chamber; rixy-chamber; viapos-chamber; trainer-tower; mt-ember/1f-cave-behind-team-rocket; mt-ember/b1f; mt-ember/b2f; mt-ember/b3f

## Decomp excerpts (pinned commit)

### E1 ThreeIsland_Port/scripts.inc
```text
ThreeIsland_Port_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, ThreeIsland_Port_OnTransition
	.byte 0

ThreeIsland_Port_OnTransition::
	clearflag FLAG_SYS_PC_STORAGE_DISABLED
	setflag FLAG_SEVII_DETOUR_FINISHED
	end
```
### E2 PalletTown_ProfessorOaksLab/scripts.inc
```text
PalletTown_ProfessorOaksLab_EventScript_TryStartNationalDexScene::
	call PokedexRating_EventScript_RateInPerson
	closemessage
	goto_if_lt VAR_0x8009, 60, PalletTown_ProfessorOaksLab_EventScript_DontStartNationalDexScene
	goto_if_unset FLAG_WORLD_MAP_ONE_ISLAND, PalletTown_ProfessorOaksLab_EventScript_DontStartNationalDexScene
	delay 30
```
### E3 MtMoon_B2F/scripts.inc (battles)
```text
38:	trainerbattle_no_intro TRAINER_SUPER_NERD_MIGUEL, MtMoon_B2F_Text_MiguelDefeat
119:	trainerbattle_single TRAINER_TEAM_ROCKET_GRUNT, MtMoon_B2F_Text_Grunt1Intro, MtMoon_B2F_Text_Grunt1Defeat
124:	trainerbattle_single TRAINER_TEAM_ROCKET_GRUNT_2, MtMoon_B2F_Text_Grunt2Intro, MtMoon_B2F_Text_Grunt2Defeat
129:	trainerbattle_single TRAINER_TEAM_ROCKET_GRUNT_3, MtMoon_B2F_Text_Grunt3Intro, MtMoon_B2F_Text_Grunt3Defeat
134:	trainerbattle_single TRAINER_TEAM_ROCKET_GRUNT_4, MtMoon_B2F_Text_Grunt4Intro, MtMoon_B2F_Text_Grunt4Defeat
```
### E4 CeruleanCity/scripts.inc
```text
CeruleanCity_OnTransition::
	setworldmapflag FLAG_WORLD_MAP_CERULEAN_CITY
	call_if_unset FLAG_GOT_SS_TICKET, CeruleanCity_EventScript_BlockExits
	end

CeruleanCity_EventScript_BlockExits::
	setobjectxyperm LOCALID_CERULEAN_POLICEMAN, 30, 12
	setobjectxyperm LOCALID_CERULEAN_SLOWBRO, 26, 31
	setobjectxyperm LOCALID_CERULEAN_LASS, 27, 31
	return
```
### E5 SaffronCity/scripts.inc and PokemonTower_7F
```text
7:	call_if_unset FLAG_RESCUED_MR_FUJI, SaffronCity_EventScript_MoveDoorGuardGrunt
44:	goto_if_set FLAG_RESCUED_MR_FUJI, SaffronCity_EventScript_DoorGuardAsleep
10:	setflag FLAG_RESCUED_MR_FUJI
19:	trainerbattle_single TRAINER_TEAM_ROCKET_GRUNT_19, PokemonTower_7F_Text_Grunt1Intro, PokemonTower_7F_Text_Grunt1Defeat, PokemonTower_7F_EventScript_DefeatedGrunt1
103:	trainerbattle_single TRAINER_TEAM_ROCKET_GRUNT_20, PokemonTower_7F_Text_Grunt2Intro, PokemonTower_7F_Text_Grunt2Defeat, PokemonTower_7F_EventScript_DefeatedGrunt2
167:	trainerbattle_single TRAINER_TEAM_ROCKET_GRUNT_21, PokemonTower_7F_Text_Grunt3Intro, PokemonTower_7F_Text_Grunt3Defeat, PokemonTower_7F_EventScript_DefeatedGrunt3
```
### E6 ThreeIsland/scripts.inc (battles)
```text
211:	trainerbattle_no_intro TRAINER_BIKER_GOON, ThreeIsland_Text_Biker1Defeat
221:	trainerbattle_no_intro TRAINER_BIKER_GOON_2, ThreeIsland_Text_Biker2Defeat
231:	trainerbattle_no_intro TRAINER_BIKER_GOON_3, ThreeIsland_Text_Biker3Defeat
248:	trainerbattle_no_intro TRAINER_CUE_BALL_PAXTON, ThreeIsland_Text_PaxtonDefeat
```
### E7 ThreeIsland_DunsparceTunnel/scripts.inc
```text
ThreeIsland_DunsparceTunnel_OnTransition::
	setworldmapflag FLAG_WORLD_MAP_THREE_ISLAND_DUNSPARCE_TUNNEL
	specialvar VAR_RESULT, IsNationalPokedexEnabled
	copyvar VAR_0x8008, VAR_RESULT
	call_if_eq VAR_0x8008, TRUE, ThreeIsland_DunsparceTunnel_EventScript_SetLayoutDugOut
	call_if_eq VAR_0x8008, FALSE, ThreeIsland_DunsparceTunnel_EventScript_MoveProspectorToWall
	end
```
### E8 OneIsland_PokemonCenter_1F/scripts.inc
```text
OneIsland_PokemonCenter_1F_EventScript_GiveRainbowPass::
	msgbox OneIsland_PokemonCenter_1F_Text_AnotherGemstoneInSeviiIslands
	removeitem ITEM_RUBY
	removeitem ITEM_TRI_PASS
	setvar VAR_MAP_SCENE_ONE_ISLAND_POKEMON_CENTER_1F, 5
	additem ITEM_RAINBOW_PASS
	setflag FLAG_SYS_SEVII_MAP_4567
```
