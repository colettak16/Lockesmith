# Review packet: FireRed/LeafGreen story order and facts (round 1)

LockeSmith answers questions about Pokémon FireRed/LeafGreen runs from data built out of the pret/pokefirered
decompilation (commit ce6406d8) and PokeAPI. This packet is the draft story order (`data/progression_frlg.yaml`) and
the facts behind it. Please review it like a careful FireRed/LeafGreen expert.

**For each claim (C-xx) say CONFIRMED, WRONG (with the correct fact) or UNSURE. For each open question (Q-xx)
give your best answer and how sure you are.** Then list anything missing: story steps, gates, or areas listed too
early or too late. Decomp excerpts are at the end (E-xx); where a claim cites one, the excerpt is the ground truth.

## How the order is meant to work

- Each step is a story battle in a canonical order. `areas_new` lists the places with wild/gift Pokémon that first
  become reachable before that battle, having fought only the battles above it. HMs and key items are cumulative.
- Gym order is flexible in Kanto; the tool also takes the player's actual badges. Optional steps can be skipped.
- Scope is the main story to the Champion. Postgame and event-only places are listed separately as never reachable.

## Draft story order

| # | step | badges before | HMs usable | key items | areas first reachable |
|---|---|---|---|---|---|
| 1 | Oak's Lab: Rival (first battle) | 0 | - | - | - |
| 2 | Route 22: Rival (optional) (optional) | 0 | - | - | pallet-town/main, kanto-route-1, viridian-city, kanto-route-22, kanto-route-2/south-towards-viridian-city, viridian-forest |
| 3 | Pewter Gym: Brock | 0 | - | - | - |
| 4 | Cerulean City: Rival | 1 | - | - | kanto-route-3, kanto-route-4/main, kanto-route-4/pokemon-center, mt-moon, cerulean-city |
| 5 | Cerulean Gym: Misty | 1 | - | old-rod | kanto-route-24, kanto-route-25, kanto-route-5, kanto-underground-path, kanto-route-6, vermilion-city, kanto-route-11, digletts-cave, kanto-route-2/north-towards-pewter-city |
| 6 | S.S. Anne: Rival | 2 | - | old-rod | ss-anne |
| 7 | Vermilion Gym: Lt. Surge | 2 | cut, flash | old-rod | kanto-route-9, kanto-route-10, rock-tunnel, kanto-route-8, kanto-route-7, celadon-city/main, celadon-city/celadon-mansion, celadon-city/prize-corner |
| 8 | Celadon Gym: Erika | 3 | cut, flash, fly | old-rod | - |
| 9 | Rocket Hideout: Giovanni | 4 | cut, flash, fly | old-rod | - |
| 10 | Pokémon Tower: Rival | 4 | cut, flash, fly | old-rod, silph-scope | pokemon-tower |
| 11 | Fuchsia Gym: Koga | 4 | cut, flash, fly, strength | old-rod, silph-scope, poke-flute, good-rod, super-rod | kanto-route-12, kanto-route-13, kanto-route-14, kanto-route-15, kanto-route-16, kanto-route-17, kanto-route-18, fuchsia-city, kanto-safari-zone |
| 12 | Silph Co.: Rival | 5 | cut, flash, fly, strength, surf | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea | saffron-city/fighting-dojo, kanto-sea-route-19, kanto-sea-route-20, kanto-sea-route-21, seafoam-islands, kanto-power-plant, cinnabar-island, pokemon-mansion |
| 13 | Silph Co. 11F: Giovanni | 5 | cut, flash, fly, strength, surf | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea, card-key | saffron-city/silph-co-7f |
| 14 | Saffron Gym: Sabrina | 5 | cut, flash, fly, strength, surf | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea, card-key | - |
| 15 | Cinnabar Gym: Blaine | 6 | cut, flash, fly, strength, surf | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea, card-key, secret-key | cinnabar-island/cinnabar-lab |
| 16 | Sevii Islands: Berry Forest's Hypno (optional errand) (optional) | 7 | cut, flash, fly, strength, surf, rock-smash | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea, card-key, secret-key, tri-pass | one-island, kindle-road, treasure-beach, mt-ember/main, mt-ember/cave, mt-ember/inside, mt-ember/summit, two-island, cape-brink, three-isle-port, bond-bridge, berry-forest |
| 17 | Viridian Gym: Giovanni | 7 | cut, flash, fly, strength, surf, rock-smash | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea, card-key, secret-key | - |
| 18 | Route 22: Rival (before the League) | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea, card-key, secret-key | - |
| 19 | Elite Four: Lorelei | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea, card-key, secret-key | kanto-route-23, kanto-victory-road-2 |
| 20 | Elite Four: Bruno | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea, card-key, secret-key | - |
| 21 | Elite Four: Agatha | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea, card-key, secret-key | - |
| 22 | Elite Four: Lance | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea, card-key, secret-key | - |
| 23 | Champion: Rival | 8 | cut, flash, fly, strength, surf, rock-smash | old-rod, silph-scope, poke-flute, good-rod, super-rod, tea, card-key, secret-key | - |

Never reachable before the Champion: pallet-town (the starter is your choice at Oak's Lab, not a catch); kanto-route-3/pokemon-center (PokeAPI duplicate: the Magikarp salesman is in Route 4's Pokémon Center (Route4_PokemonCenter_1F); Route 3 has none); kanto-pokecenter (the Japanese Colosseum bonus disc, not part of the game); cerulean-cave (postgame: the guard steps aside once Celio's network machine works, after the Sevii Islands' Ruby and Sapphire quests (OneIsland_PokemonCenter_1F)); roaming-kanto (postgame: the roaming beast starts when Celio's network machine works (special InitRoamer)); navel-rock (event-only: needs the MysticTicket); birth-island (event-only: needs the AuroraTicket); kanto-altering-cave (postgame (Six Island), and only one table without a Mystery Gift); water-labyrinth (postgame: Five Island needs the Rainbow Pass); four-island (postgame: Islands 4-7 need the Rainbow Pass, given after the Hall of Fame); icefall-cave (postgame (Four Island)); five-island (postgame (Rainbow Pass)); five-isle-meadow (postgame (Rainbow Pass)); memorial-pillar (postgame (Rainbow Pass)); resort-gorgeous (postgame (Rainbow Pass)); water-path (postgame (Rainbow Pass)); ruin-valley (postgame (Rainbow Pass)); green-path (postgame (Rainbow Pass)); outcast-island (postgame (Rainbow Pass)); pattern-bush (postgame (Rainbow Pass)); lost-cave (postgame (Rainbow Pass)); canyon-entrance (postgame (Rainbow Pass)); sevault-canyon (postgame (Rainbow Pass)); tanoby-ruins (postgame (Rainbow Pass)); monean-chamber (postgame (Tanoby Ruins)); liptoo-chamber (postgame (Tanoby Ruins)); weepth-chamber (postgame (Tanoby Ruins)); dilford-chamber (postgame (Tanoby Ruins)); scufib-chamber (postgame (Tanoby Ruins)); rixy-chamber (postgame (Tanoby Ruins)); viapos-chamber (postgame (Tanoby Ruins)); trainer-tower (postgame (Seven Island)); mt-ember/1f-cave-behind-team-rocket (postgame: the caves open for the Ruby quest (VAR_MAP_SCENE_ONE_ISLAND_POKEMON_CENTER_1F >= 4, MtEmber_Exterior)); mt-ember/b1f (postgame: the Ruby quest's caves); mt-ember/b2f (postgame: the Ruby quest's caves); mt-ember/b3f (postgame: the Ruby quest's caves)

## Claims

- **C-01** Outside battle, each HM needs one badge: Flash Boulder, Cut Cascade, Fly Thunder, Strength Rainbow, Surf Soul, Rock Smash Marsh, Waterfall Volcano (E1).
- **C-02** The Viridian Gym opens once you hold the Cascade through Volcano Badges; the Boulder Badge isn't checked (E2).
- **C-03** Saffron's four gatehouses let you in after you give a guard Tea, from an old woman in the Celadon Condominiums 1F.
- **C-04** A Rocket blocks Sabrina's gym door until Giovanni is beaten at Silph Co. 11F, so both Silph Co. fights come before Sabrina (E3).
- **C-05** The early Route 22 rival is optional (Route 22 is a detour before the League); the late Route 22 rival is required, armed by the Viridian Gym win (E4).
- **C-06** After Blaine, Bill's trip to One Island can be declined and taken later (E5).
- **C-07** Once on One Island, the ferry offers Vermilion only after Bill brings you back to Cinnabar, which happens after Lostelle's rescue (Berry Forest, Three Island) and the Meteorite delivery to her father on Two Island (E6-E9).
- **C-08** The Sevii errand (Islands 1-3) is not required for the Viridian Gym or the League.
- **C-09** PC storage is disabled on the Sevii Islands from the first meeting with Celio until postgame (E9: FLAG_SYS_PC_STORAGE_DISABLED).
- **C-10** Before the National Dex (given after the Hall of Fame), any evolution into a species past #151 is cancelled, including level-up and friendship ones like Golbat -> Crobat; evolution stones into such species can't be used (E10).
- **C-11** Espeon and Umbreon can never be evolved in FireRed/LeafGreen: the day/night friendship evolutions are commented out (no clock).
- **C-12** The rival takes the starter strong against yours: Bulbasaur -> rival Charmander, Charmander -> Squirtle, Squirtle -> Bulbasaur (E11).
- **C-13** Cerulean Cave opens and the roaming beast starts only when Celio's network machine works, after the Sevii 4-7 Ruby/Sapphire quests (E12).
- **C-14** TM10 Hidden Power isn't given by any NPC, mart or item ball; it only comes from Pickup (5% of finds) (E13).
- **C-15** Cape Brink (Two Island) teaches Frenzy Plant / Blast Burn / Hydro Cannon only to a lead Venusaur / Charizard / Blastoise with friendship exactly 255 (E14).
- **C-16** Pokemon Tower's 6F Marowak is a scripted ghost battle that can't be caught (E15).
- **C-17** Ghosts in Pokemon Tower can't be identified or caught without the Silph Scope (from Giovanni at the Rocket Hideout).
- **C-18** Fuchsia City needs the Poke Flute either way: Snorlax blocks Route 12 (from Lavender) and Route 16 (towards Cycling Road).
- **C-19** The Magikarp salesman is in Route 4's Pokemon Center (Mt. Moon); PokeAPI also lists one on Route 3, which is a duplicate.
- **C-20** Cinnabar's gym needs the Secret Key from the Pokemon Mansion's basement.
- **C-21** The Celadon Department Store roof girl trades TM16, TM20 and TM33 for Fresh Water, Soda Pop and Lemonade.

## Open questions

- **Q-01** (Cerulean City: Rival) Mt. Moon's Super Nerd and Rocket fights aren't modelled as steps; check none gates an area.
- **Q-02** (Cerulean Gym: Misty) Route 5 / Underground Path / Vermilion / Diglett's Cave reachable before Misty? (no gate found yet in the scripts).
- **Q-03** (S.S. Anne: Rival) S.S. Anne (and its fishing rows) close after you leave the ship: add a `closes` entry once confirmed in the scripts.
- **Q-04** (Vermilion Gym: Lt. Surge) Flash: HM05 from Oak's aide in Route 2's east building (needs 10 species caught) — confirm its map is reachable here.
- **Q-05** (Celadon Gym: Erika) Route 16's house and grass: reachable without the Poké Flute (Snorlax blocks Route 16's gatehouse)? kanto-route-16 is listed at Koga for now.
- **Q-06** (Fuchsia Gym: Koga) Good Rod (Fuchsia) and Super Rod (Route12_FishingHouse) locations and reachability; Strength listed here since the Rainbow Badge is held.
- **Q-07** (Silph Co.: Rival) Is the Fighting Dojo open while Rockets hold Saffron? Seafoam/Power Plant could be listed earlier by Surf timing only — fine as is.
- **Q-08** (Cinnabar Gym: Blaine) Cinnabar Lab (fossils, trades) is reachable as soon as Cinnabar is; listed here for now.
- **Q-09** (Sevii Islands: Berry Forest's Hypno (optional errand)) Mt. Ember's PokeAPI areas match the decomp's wild tables by species: main = Exterior, cave/inside = Summit Path floors, summit = Summit (Moltres); the Ruby Path (1F cave, B1F-B3F) is postgame. Does the Summit Path need Strength or Rock Smash? Can Fly leave the islands before the errand is done?
- **Q-10** (Viridian Gym: Giovanni) rock-smash is in hm_gates_open only if the Sevii errand was done (HM06 is on Kindle Road).
- **Q-11** Is anything before Brock gated (e.g. Route 3's exit east of Pewter blocked until the Boulder Badge)?
- **Q-12** Is Route 5 / the Underground Path / Vermilion reachable before Misty, or does something block Cerulean's south exit?
- **Q-13** Do Mt. Moon's Rocket or Super Nerd battles block the way through (required steps)?
- **Q-14** Where exactly are the Good Rod and Super Rod given, and what has to be done to reach each?
- **Q-15** Does the S.S. Anne leave for good after the Cut scene, closing its fishing spot?
- **Q-16** Can Fly take you from the Sevii Islands back to Kanto before the errand is done?
- **Q-17** Any FireRed/LeafGreen story gate this draft misses (e.g. the Pokemon Fan Club's Bike Voucher, Mr. Fuji, Seafoam currents needing Strength, the Power Plant needing Surf)?

## Decomp excerpts

```text
### E1 party_menu.c: HMs outside battle
    {
        // All field moves before WATERFALL are HMs.
        if (fieldMove <= FIELD_MOVE_WATERFALL && FlagGet(FLAG_BADGE01_GET + fieldMove) != TRUE)
        {
            DisplayPartyMenuMessage(gText_CantUseUntilNewBadge, TRUE);
#define FIELD_MOVE_FLASH        0
#define FIELD_MOVE_CUT          1
#define FIELD_MOVE_FLY          2
#define FIELD_MOVE_STRENGTH     3
#define FIELD_MOVE_SURF         4
#define FIELD_MOVE_ROCK_SMASH   5
#define FIELD_MOVE_WATERFALL    6
#define FIELD_MOVE_TELEPORT     7
### E2 ViridianCity/scripts.inc: gym door
ViridianCity_EventScript_TryUnlockGym::
	goto_if_unset FLAG_BADGE02_GET, EventScript_Return
	goto_if_unset FLAG_BADGE03_GET, EventScript_Return
	goto_if_unset FLAG_BADGE04_GET, EventScript_Return
	goto_if_unset FLAG_BADGE05_GET, EventScript_Return
	goto_if_unset FLAG_BADGE06_GET, EventScript_Return
	goto_if_unset FLAG_BADGE07_GET, EventScript_Return
	setvar VAR_MAP_SCENE_VIRIDIAN_CITY_GYM_DOOR, 1
	return
### E3 SaffronCity/map.json: gym door warp and the Rocket below it
warp to SaffronCity_Gym at (46,12); object ROCKET at (46,13) flag FLAG_HIDE_SAFFRON_ROCKETS (set in SilphCo_11F after Giovanni)
### E4 Route22: rival triggers (coord_events)
EarlyRivalTrigger* when VAR_MAP_SCENE_ROUTE22 == 1 (set at Oak's Lab after the Parcel); LateRivalTrigger* when == 3 (set in ViridianCity_Gym after Giovanni)
### E5 CinnabarIsland/scripts.inc: Bill's offer can be declined
135:CinnabarIsland_EventScript_DeclineSailToOneIsland::
136-	msgbox CinnabarIsland_Text_IllBeWaitingInPokeCenter
137-	closemessage
138-	call_if_unset FLAG_TEMP_2, CinnabarIsland_EventScript_BillExitToPokeCenter
139-	call_if_set FLAG_TEMP_2, CinnabarIsland_EventScript_BillReturnToPokeCenter
### E6 data/scripts/seagallop.inc: ferry from One Island
EventScript_ChooseDestFromOneIsland::
	goto_if_ge VAR_MAP_SCENE_ONE_ISLAND_POKEMON_CENTER_1F, 5, EventScript_SeviiDestinationsPage1
	goto_if_ge VAR_MAP_SCENE_CINNABAR_ISLAND, 4, EventScript_ChooseDestFromOneIslandVermilionAllowed
	multichoice 19, 6, MULTICHOICE_ISLAND_23, FALSE
	switch VAR_RESULT
	case 0, EventScript_SailToTwoIsland2
	case 1, EventScript_SailToThreeIsland2
	case 2, EventScript_CancelSail
	case SCR_MENU_CANCEL, EventScript_CancelSail
	end
### E7 CinnabarIsland: what allows Vermilion
CinnabarIsland_EventScript_ReturnFromSeviiIslands::
	lockall
	textcolor NPC_TEXT_COLOR_MALE
	msgbox CinnabarIsland_Text_IfYouHaveTriPassYouCanGoAgain
	closemessage
	applymovement LOCALID_CINNABAR_BILL, CinnabarIsland_Movement_BillExit
	waitmovement 0
	removeobject LOCALID_CINNABAR_BILL
	setvar VAR_MAP_SCENE_CINNABAR_ISLAND, 4
	setflag FLAG_HIDE_TWO_ISLAND_GAME_CORNER_LOSTELLE
### E8 TwoIsland_JoyfulGameCorner: the Meteorite needs Lostelle back
TwoIsland_JoyfulGameCorner_EventScript_LostellesDaddy::
	lock
	faceplayer
	goto_if_eq VAR_MAP_SCENE_TWO_ISLAND_JOYFUL_GAME_CORNER, 4, JoyfulGameCorner_EventScript_MinigameAttendant
	goto_if_set FLAG_GOT_MOON_STONE_FROM_JOYFUL_GAME_CORNER, TwoIsland_JoyfulGameCorner_EventScript_GetGameCornerRunning
	goto_if_eq VAR_MAP_SCENE_TWO_ISLAND_JOYFUL_GAME_CORNER, 3, TwoIsland_JoyfulGameCorner_EventScript_GiveDaddyMeteorite
	msgbox TwoIsland_JoyfulGameCorner_Text_PleaseGoToThreeIsland
	release
	end

TwoIsland_JoyfulGameCorner_EventScript_GiveDaddyMeteorite::
	goto_if_set FLAG_NO_ROOM_FOR_JOYFUL_GAME_CORNER_MOON_STONE, TwoIsland_JoyfulGameCorner_EventScript_ReceiveMoonStone
	msgbox TwoIsland_JoyfulGameCorner_Text_ThisIsForMe
	setvar VAR_MAP_SCENE_ONE_ISLAND_POKEMON_CENTER_1F, 2
### E9 OneIsland_PokemonCenter_1F: first meeting
	msgbox OneIsland_PokemonCenter_1F_Text_CanYouDeliverThisMeteoritePlayer
	msgreceiveditem OneIsland_PokemonCenter_1F_Text_AcceptedMeteoriteFromBill, ITEM_METEORITE, 1, MUS_OBTAIN_KEY_ITEM
	additem ITEM_METEORITE
	applymovement LOCALID_CELIO, Common_Movement_WalkInPlaceFasterDown
	waitmovement 0
	msgbox OneIsland_PokemonCenter_1F_Text_CelioPleaseTakeThis
	giveitem_msg OneIsland_PokemonCenter_1F_Text_ObtainedTriPass, ITEM_TRI_PASS, 1, MUS_OBTAIN_KEY_ITEM
	msgbox OneIsland_PokemonCenter_1F_Text_PassLetsYouTravelBetweenIslands
	call_if_ge VAR_MAP_SCENE_PALLET_TOWN_RIVALS_HOUSE, 2, OneIsland_PokemonCenter_1F_EventScript_ReceiveTownMapPage
	call_if_lt VAR_MAP_SCENE_PALLET_TOWN_RIVALS_HOUSE, 2, OneIsland_PokemonCenter_1F_EventScript_ReceiveTownMap
	setflag FLAG_SYS_SEVII_MAP_123
	msgbox OneIsland_PokemonCenter_1F_Text_BillCatchYouLater
	closemessage
	applymovement LOCALID_ONE_ISLAND_POKEMON_CENTER_BILL, Common_Movement_WalkInPlaceFasterUp
	waitmovement 0
	applymovement LOCALID_CELIO, Common_Movement_WalkInPlaceFasterUp
	waitmovement 0
	setflag FLAG_SYS_PC_STORAGE_DISABLED
	setvar VAR_MAP_SCENE_ONE_ISLAND_POKEMON_CENTER_1F, 1
### E10 evolution_scene.c: National Dex gate

    // Automatically cancel if the Pokemon would evolve into a species you have not
    // yet unlocked, such as Crobat.
    if (!IsNationalPokedexEnabled()
        && gTasks[taskId].tState == EVOSTATE_WAIT_CYCLE_MON_SPRITE
        && gTasks[taskId].tPostEvoSpecies > SPECIES_MEW)
    {
        gTasks[taskId].tState = EVOSTATE_CANCEL;
        gTasks[taskId].tEvoWasStopped = TRUE;
        gTasks[sEvoGraphicsTaskId].tEvoStopped = TRUE;
        StopBgAnimation();
        return;
party_menu.c MonCanEvolve:
static bool8 MonCanEvolve(void)
{
    if (!IsNationalPokedexEnabled()
     && GetEvolutionTargetSpecies(&gPlayerParty[gPartyMenu.slotId], EVO_MODE_ITEM_USE, gSpecialVar_ItemId) > KANTO_DEX_COUNT)
        return FALSE;
    else
        return TRUE;
}
### E11 PalletTown_ProfessorOaksLab: rival's starter
	goto_if_eq VAR_STARTER_MON, 0, PalletTown_ProfessorOaksLab_EventScript_RivalApproachForBattleCharmander
	goto_if_eq VAR_STARTER_MON, 1, PalletTown_ProfessorOaksLab_EventScript_RivalApproachForBattleBulbasaur
	goto_if_eq VAR_STARTER_MON, 2, PalletTown_ProfessorOaksLab_EventScript_RivalApproachForBattleSquirtle
(VAR_STARTER_MON 0 Bulbasaur, 1 Squirtle, 2 Charmander; the *Charmander branch fights TRAINER_RIVAL_OAKS_LAB_CHARMANDER)
### E12 OneIsland_PokemonCenter_1F: postgame gates
	special SetPostgameFlags
	setflag FLAG_SYS_CAN_LINK_WITH_RS
	setflag FLAG_HIDE_CERULEAN_CAVE_GUARD
	setflag FLAG_HIDE_LORELEI_IN_HER_HOUSE
	setvar VAR_MAP_SCENE_ONE_ISLAND_POKEMON_CENTER_1F, 6
	special InitRoamer
	release
	end
### E13 battle_script_commands.c: Pickup table (TM10)
static const struct PickupItem sPickupItems[] =
{
    { ITEM_ORAN_BERRY, 15 },
    { ITEM_CHERI_BERRY, 25 },
    { ITEM_CHESTO_BERRY, 35 },
    { ITEM_PECHA_BERRY, 45 },
    { ITEM_RAWST_BERRY, 55 },
    { ITEM_ASPEAR_BERRY, 65 },
    { ITEM_PERSIM_BERRY, 75 },
    { ITEM_TM10, 80 },
    { ITEM_PP_UP, 85 },
    { ITEM_RARE_CANDY, 90 },
    { ITEM_NUGGET, 95 },
    { ITEM_SPELON_BERRY, 96 },
    { ITEM_PAMTRE_BERRY, 97 },
    { ITEM_WATMEL_BERRY, 98 },
    { ITEM_DURIN_BERRY, 99 },
    { ITEM_BELUE_BERRY, 1 },
### E14 field_specials.c: Cape Brink tutor
static const u8 sCapeBrinkCompatibleSpecies[] = {
    SPECIES_VENUSAUR,
    SPECIES_CHARIZARD,
    SPECIES_BLASTOISE
};
2239:    if (i == NELEMS(sCapeBrinkCompatibleSpecies) || GetMonData(&gPlayerParty[leadMonSlot], MON_DATA_FRIENDSHIP) != 255)
### E15 PokemonTower_6F: Marowak ghost
	goto_if_questlog EventScript_ReleaseEnd
	setwildbattle SPECIES_MAROWAK, 30
	special StartMarowakBattle
	waitstate

```
