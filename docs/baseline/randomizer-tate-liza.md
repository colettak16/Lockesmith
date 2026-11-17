# Baseline: randomizer-tate-liza

vertex_ai/gemini-3.1-pro-preview, no tools, no system prompt. 52.4 s, 286 input / 4323 output tokens, about $0.0524.

## Prompt

```text
I'm playing Pokémon Emerald. My starter was Mudkip and my rival is May. I have 6 badges: Stone, Knuckle, Dynamo, Heat, Balance, Feather. My party: Marshtomp Lv33, Breloom Lv30, Swellow Lv31, Manectric Lv30. It's a randomized run (Universal Pokémon Randomizer ZX). Here's my spoiler log:

Randomizer Version: 4.6.1
Random Seed: 4570
Settings String: synthetic-acceptance
Note: a hand-made sample in UPR ZX's log format, not a log from a real ROM. Only Tate & Liza are randomized (to Fire types); everything else is vanilla.

--Trainers Pokemon--
#271 (TATE&LIZA)@31F2E8 - Camerupt Lv41, Torkoal Lv41, Magcargo@Sitrus Berry Lv42, Houndoom@Sitrus Berry Lv42

------------------------------------------------------------------
Randomization of Emerald (U) completed.
Time elapsed: 1210ms
RNG Calls: 4570
------------------------------------------------------------------

--ROM Diagnostics--
File name: none (hand-made sample, no ROM)


What should I catch to get through Tate & Liza?
```

## Answer

This is a huge stroke of luck for you! By randomizing Tate and Liza to Fire-types, you've completely bypassed the notorious difficulty of their vanilla Psychic-type gym. Since the rest of your game's wild encounters are vanilla, you have access to some incredibly powerful tools to sweep them.

However, you have one major problem to address first: **Your levels.** Tate and Liza's team is Level 41–42, and your highest is 33. You will need to grind a bit, but with the right catches, you won't need to match their levels perfectly. 

Here is exactly what you should catch and the strategy you should use to wash them away.

### The Strategy: "Gen 3 Surf Mechanics"
In Generation 3 (Ruby/Sapphire/Emerald), the move **Surf** in a Double Battle is incredibly broken because **it hits both opponents, but DOES NOT hit your ally.** (This was changed in Gen 4). 

Because Tate and Liza are using a full Fire-type team in a Double Battle format, **Double-Surf spam** is all you need. Furthermore, Camerupt and Magcargo are **4x weak to Water**, meaning they will be instantly deleted by almost any Surf attack.

### Priority #1: Evolve Marshtomp
Before doing anything else, get your Marshtomp to **Level 36** so it evolves into **Swampert**. Swampert’s Water/Ground typing is virtually invincible in this gym. Give it **Surf** (HM03) and **Earthquake** (TM26, found deep in the Seafloor Cavern, or just use Mud Shot/Dig). 

### Priority #2: Catch a Surf Partner
You want a second Water-type to put right next to Swampert. Since everything else in your ROM is vanilla, you can easily grab one of these around Lilycove City or Mossdeep City:

**1. Staryu / Starmie (The Best Option)**
*   **Why:** Starmie is blazing fast and hits like a truck. Houndoom is their fastest Pokémon, and Starmie will naturally outspeed it and hit it with a super-effective Surf. 
*   **Where to get it:** Use the Super Rod in the water at Lilycove City. 
*   **How to evolve:** Use a Water Stone (trade a Blue Shard to the Treasure Hunter on Route 124). Give it Surf and Mystic Water.

**2. Tentacruel (The Tanky Option)**
*   **Why:** Tentacruel has massive Special Defense and naturally resists Fire-type moves. It's also quite fast. It can comfortably sit next to Swampert and spam Surf all day without taking much damage from Flamethrowers.
*   **Where to get it:** You can encounter wild Tentacruel (around Level 25-30) while surfing on almost any ocean route (Route 124, 125, etc.), or just catch a Tentacool and evolve it at Level 30.

**3. Magikarp / Gyarados OR Wingull / Pelipper (The Earthquake Option)**
*   **Why:** While Gen 3 Surf doesn't hit your ally, **Earthquake DOES hit your ally.** If you want Swampert to be able to spam Earthquake freely to deal with Torkoal and Houndoom, its partner needs to be a Flying-type or have the Levitate ability. Gyarados and Pelipper are both Water/Flying. Gyarados also provides Intimidate, which lowers Camerupt's Earthquake and Torkoal's Body Slam damage. 
*   **Where to get them:** Literally everywhere there is water. 

### How the Battle Will Go
1.  **Bench Breloom:** Breloom is Grass/Fighting and will get instantly KO'd by anything on their team. Leave it in the back.
2.  **Lead Swampert + Your New Water Catch (Starmie/Tentacruel/Gyarados).**
3.  **Turn 1:** Have both of your Pokémon use **Surf**. 
4.  Because Tate and Liza will lead with Camerupt and Torkoal (or Magcargo), the double-Surf will hit both of them. Camerupt will instantly faint to the 4x weakness. Torkoal will take massive damage from two consecutive Surfs. 
5.  **Turn 2+:** Just keep pressing Surf. Magcargo will instantly die upon switching in (4x weakness), and Houndoom's Special Defense isn't high enough to survive Double-Surfs. 

Even if you go into this fight slightly underleveled (around Level 38), the type matchups and the double-target mechanics of Surf will make this the easiest badge of your run!
