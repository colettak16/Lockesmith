# Cross-game audit: Ruby/Sapphire vs Emerald

These scripts back section 12 ("Area-unlock verification") and Q-10 of the Ruby/Sapphire review packet, [docs/review_packet_rs.md](../docs/review_packet_rs.md). They compare [pret/pokeruby](https://github.com/pret/pokeruby), which builds both Ruby and Sapphire, with [pret/pokeemerald](https://github.com/pret/pokeemerald). Both are pinned at the commits the build uses, in [data/sources.lock.json](../data/sources.lock.json): pokeruby `5784633ce4ef` and pokeemerald `731ad5bfd6e6`.

```sh
uv run python -m audit                  # everything; writes docs/audit/*.txt (about a minute)
uv run python -m audit.reach MAP_ROUTE110 MAP_JAGGED_PASS   # one check, some maps
uv run python -m audit.chokepoints RUBY                     # version-dependent checks take RUBY or SAPPHIRE
```

The first run downloads both decomps at their pinned commits into `build/.cache/audit/` (`audit/sources.py`, about 75 MB). Only `data/`, `include/` and `src/` are kept. The files are parsed as text, JSON and binary map data; nothing in them is built or run.

The reports are committed in [docs/audit/](../docs/audit/), so you can read the results without running anything. Each report's first line names the two commits it compared.

## What each check does, and the packet claims it backs

| Module | Report | Packet | What it compares |
|---|---|---|---|
| `reach.py` | `reach.txt` | V-01, V-06 | Per-map reachability. For every shared map, every entrance and each set of field moves (the ones with a bike run once with the Mach Bike and once with the Acro Bike), a flood fill under the engine's movement rules: ledges, elevation, Surf start and stop, doors, waterfalls, and each bike's tiles (muddy slopes, cracked floors, bumpy slopes, rails, the Acro side jump). It records the exits, walkable encounter tiles, water and fishing reached. Lists the maps where any entrance differs (the 9 in V-06), then where the two bikes reach different things in each game. |
| `layouts.py` | `layouts.txt` | V-06 | Which shared maps have any different blocks (127 of 348), before reachability decides whether a difference matters. |
| `chokepoints.py` | `chokepoints_{ruby,sapphire}.txt` | V-02, V-07 | Walls off each object visible at a new game, one hide flag at a time. It reports the ones whose removal costs some entrance an exit, encounters or water, and which scripts remove them in each game. Result: 14 groups in Ruby/Sapphire, 20 in Emerald. |
| `story_gates.py` | `story_gates_{ruby,sapphire}.txt` | V-02 (the rest), V-03, V-08 | Blockers hidden by `setflag` that stand on the same tile in both games, and whether their removing scripts live in the same place: 540, of which 517 do, and the other 23 are Mt. Chimney's scene and Cozmo. Also lists step triggers on a story variable that only one game has. |
| `map_changes.py` | `map_changes_{ruby,sapphire}.txt` | V-04, V-09 | Every conditional branch in a map's scripts, and what its target changes: tiles, layout, an NPC's permanent position, or warps. It reads both branch syntaxes (pokeruby's `compare` plus a one-argument `goto_if_eq`). |
| `engine.py` | `engine.txt` | V-10, V-11 | Metatile behavior numbering and tile bits, the `MetatileBehavior_Is*` predicates, map headers, bike/Escape Rope/running permissions, heal locations, abilities that act outside battle (with Pickup's item table and whether it depends on level), and wild-encounter functions that only one game has. |
| `encounter_scripts.py` | `encounter_scripts_{ruby,sapphire}.txt` | Q-10, SE-10, E-10 | Every `setwildbattle`, `givemon` and `giveegg`, and the specials that create a Pokémon or start an encounter from a script (the roamer, in-game trades, the daycare egg, Rock Smash). Each comes with the checks on the way to it and the object's hide flag, side by side per species. This one is for reading: flag names differ between the decomps. Encounters that start in C with no script (the wild tables, fishing, Feebas) are left to `engine.py`. |
| `core_data.py` | `core_data.txt` | section 2 (C) | Species data, moves, learnsets, TM/HM compatibility, egg moves, evolutions, the type chart and the encounter slot rates. Most of the differences it prints are renamed constants. |

`python -m audit` also checks V-13: the four version-dependent reports are identical for Ruby and Sapphire.

## What isn't scripted

- **The movement rules in `reach.py`** were read from the C source: `field_player_avatar.c`, `field_control_avatar.c`, `event_object_movement.c` and `item_use.c`. The comments in `reach.run` name the functions. To check them, read those files in both decomps.
- **Some V-11 facts were read by hand:** the tide table (`time_events.c`), Fly destinations, the League guards' badge check, and the Sootopolis encounter block (`AreLegendariesInSootopolisPreventingEncounters`, which `engine.txt` lists as Emerald-only).
- **V-12's spot checks** were read by hand. **V-14**, the Lilycove store, is pinned by a test (`tests/test_rs_facts.py`).
- **Limits (V-15):**
  - NPCs that wander aren't modeled.
  - Arrow warps count in any direction.
  - Rotating gates and script-changed tiles are covered by `map_changes.py` and the engine reading, not by the flood fill.
  - `map_changes.py` follows each branch one label deep.
  - Each map is checked on its own: an edge entrance starts from every open tile on that edge, so a gate in the neighbouring map shows up on that map, not this one.
  - Falling through cracked floors and holes isn't counted as an exit.
  - Nothing was run in an emulator.
