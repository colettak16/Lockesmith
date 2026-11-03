# Baseline: ruby-nuzlocke-groudon

vertex_ai/gemini-3.1-pro-preview, no tools, no system prompt. 58.3 s, 124 input / 4060 output tokens, about $0.0490.

## Prompt

```text
I'm playing Pokémon Emerald. My starter was Mudkip and my rival is May. I have 7 badges: Stone, Knuckle, Dynamo, Heat, Balance, Feather, Mind. My party: Swampert Lv41, Breloom Lv38, Swellow Lv38, Manectric Lv37. Rules: Nuzlocke (first encounter per area only), level caps at the next gym leader's highest level.

Ruby Nuzlocke with level caps. Should I catch Groudon in the Cave of Origin, and what else do I need for Wallace?
```

## Answer

First things first, let’s clear up a slight version mix-up in your prompt to make sure you don't walk into a trap! 

You mentioned playing **Emerald** at the start, but then asked about a **Ruby Nuzlocke** regarding Groudon and Wallace. 
*   **If you are playing Emerald:** Groudon is not in the Cave of Origin (you go to the Sky Pillar for Rayquaza). The 8th Gym Leader is **Juan**, not Wallace (Wallace is the Champion), and the level cap would be **46** (Juan's Kingdra). 
*   **If you are playing Ruby:** Groudon *is* in the Cave of Origin, and **Wallace** is the 8th Gym Leader. 

Because you specifically mentioned Cave of Origin Groudon and Wallace, **I am going to assume you are playing Pokémon Ruby.**

Here is exactly how you should handle Groudon and prepare for Wallace.

### 1. Should you catch Groudon?
**Catch it, but you CANNOT use it against Wallace.**
In Pokémon Ruby, you encounter Groudon at **Level 45**. Wallace is the 8th Gym Leader, and his highest level Pokémon (Milotic) is **Level 43**. 
Because you are playing with strict level caps, **Groudon exceeds the cap and is illegal for the 8th Gym.** 

Additionally, many Nuzlockers ban box-art legendaries because their massive stats trivialize the game, but that is entirely up to your personal ruleset (Your Run, Your Rules). If you allow legendaries, catch it and box it for the Elite Four (Sidney's level cap is 49). 

*Tip: If you want to catch Groudon as your Cave of Origin encounter, use a Repel. The only other Pokémon in the cave are Zubat/Golbat, Sableye, and Mawile. If your lead Pokémon is Level 45 and you use a Max Repel, you will bypass the wild encounters and legally claim Groudon as your one encounter for the area.*

### 2. Evaluating your current team for Wallace (Level Cap: 43)
Wallace uses Water-types: Luvdisc (40), Sealeo (40), Whiscash (41), Seaking (42), and Milotic (43). 

Your current core is phenomenally good, but requires careful positioning here:
*   **Manectric (Lv 37 -> 43):** Your MVP. With the Thunderbolt TM from Wattson (New Mauville), Manectric sweeps Luvdisc, Seaking, and Sealeo. 
*   **Breloom (Lv 38 -> 43):** Your Whiscash counter. Whiscash is Ground/Water, making it immune to Manectric. Breloom will obliterate it with a Grass move (get the Giga Drain TM from Route 123). *Keep Breloom away from Sealeo and Milotic to avoid 4x weakness to Ice attacks.*
*   **Swampert (Lv 41 -> 43):** A great bulky pivot, but Wallace's Water moves will hit for neutral damage, and Earthquake won't do much to his bulky waters. 
*   **Swellow (Lv 38 -> 43):** Guts + Facade (pre-burn on a wild Vulpix/Slugma) hits insanely hard, but it’s very fragile to Ice moves. Mostly a cleaner.

### 3. What else do you need for Wallace?
You currently have 4 Pokémon. You need to fill your last 2 slots to deal with Wallace's Ace: **Milotic**. 

Milotic is an absolute tank with *Recover, Water Pulse, Twister, and Ice Beam*. If it survives a Thunderbolt from Manectric, Manectric could die to a critical hit or get confused by Water Pulse. You need **safe switch-ins** that resist Water and/or Ice. 

Here are the best additions you can get right now:

*   **Magneton (New Mauville):** The ultimate Milotic counter. Electric/Steel typing means it **resists Ice Beam, Twister, and Water Pulse**. It can safely switch in on Milotic, tank hits effortlessly, and nuke it with Thunderbolt. If you haven't used your New Mauville encounter, go get one.
*   **Tentacruel (Surfing almost anywhere):** A fantastic special wall. Water/Poison resists both Water and Ice, and it has massive Special Defense. It can easily pivot into Milotic or Sealeo to take the heat off Breloom/Manectric. You can teach it Toxic to wear Milotic down if things go wrong.
*   **Gyarados (Magikarp via Old Rod anywhere):** Intimidate is always useful, and it resists Water. 
*   **Walrein / Sealeo (Spheal in Shoal Cave):** Ice/Water perfectly walls most of Wallace’s team. A great bulky addition if you get unlucky with other encounters.

### The Battle Plan
1.  **Level up your team to Level 43.** Do not go over.
2.  **Lead with Manectric.** OHKO the Luvdisc with Thunderbolt.
3.  **Bait the Whiscash.** When Wallace sends out Whiscash, switch immediately to Breloom. Whiscash has Earthquake and Amnesia but no Ice moves in Ruby. Kill it with a Grass move. 
4.  **Bring Manectric back** for Seaking and Sealeo. 
5.  **Tag-team Milotic.** Hit it with Manectric. If Manectric gets low, pivot to your Water/Ice resist (like Tentacruel or Magneton), heal Manectric, or finish it off with your new counter.

Good luck! You've made it through the hardest parts of Hoenn (Norman and Winona). Keep playing around the critical hits and you'll have your 8th badge.
