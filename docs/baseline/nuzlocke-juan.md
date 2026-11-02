# Baseline: nuzlocke-juan

vertex_ai/gemini-3.1-pro-preview, no tools, no system prompt. 50.8 s, 252 input / 3617 output tokens, about $0.0439.

## Prompt

```text
I'm playing Pokémon Emerald. My starter was Mudkip and my rival is May. I have 7 badges: Stone, Knuckle, Dynamo, Heat, Balance, Feather, Mind. My party: Swampert Lv42, Breloom Lv40, Swellow Lv40, Manectric Lv39. Rules: Nuzlocke (first encounter per area only), dupes clause, level caps at the next gym leader's highest level. Areas whose encounter I've already used: Route 101, Route 102, Route 103, Route 104, Petalburg Woods, Route 116, Rusturf Tunnel, Granite Cave, Route 110, Route 117, Route 111, Route 112, Fiery Path, Route 113, Route 114, Meteor Falls, Route 115, Route 118, Route 119, Route 120, Route 121, Safari Zone, Mt. Pyre.

Nuzlocke with the dupes clause and level caps. Juan is next; what should I catch?
```

## Answer

Your team of Swampert, Breloom, Swellow, and Manectric is incredibly solid, but you have two empty slots in your party. With the level cap sitting at **Lv. 46** (Juan’s Kingdra), you are in a great position to fill out your team. 

Juan is notorious for being a run-killer in Emerald, almost entirely because of his **Kingdra** (Water Pulse, Ice Beam, Rest, Sleep Talk, Double Team). Since Kingdra is Water/Dragon, it is only weak to Dragon, meaning your Manectric and Breloom will only hit it for neutral damage.

Since you have Surf, Dive, and the Super Rod (from Mossdeep City), the entire ocean is open to you. Here are the best encounters you should target right now, taking advantage of the **Dupes Clause**:

### 1. New Mauville (Magneton)
If you haven't been here yet, go immediately. You get the Basement Key from Wattson in Mauville City after getting Surf.
*   **The Catch:** You will encounter either Voltorb or Magnemite. Both are great, but **Magnemite/Magneton** is a top-tier Nuzlocke Pokémon. 
*   **Why for Juan:** Magneton resists both of Kingdra's attacks (Water and Ice). It also has massive Special Attack and Defense. It’s arguably the safest Pokémon to put in front of Kingdra. 

### 2. Shoal Cave (Spheal -> Walrein)
Located north of Mossdeep City. 
*   **The Catch:** Depending on the tide, you can find Spheal, Snorunt, Zubat, or Tentacool. If you already have a Zubat/Golbat and a Tentacool/Tentacruel from earlier routes, your Dupes Clause almost guarantees you a **Spheal (Walrein)** or Snorunt.
*   **Why for Juan:** Walrein is a bulky Water/Ice type with massive HP. Because of its typing, it resists both of Kingdra’s attacking moves. Walrein also gets **Encore** via level up, which can lock Kingdra into Double Team or Rest, completely shutting down its strategy so you can get a free switch to a heavy hitter.

### 3. Lilycove City (Staryu -> Starmie)
You can fish in the water right inside Lilycove City using the **Super Rod**.
*   **The Catch:** The Super Rod yields Wailmer (85%) and Staryu (15%). 
*   **Dupes Clause Trick:** Before fishing in Lilycove, go to Route 124 or 125 and fish for a Wailmer. Once you catch Wailmer, go to Lilycove. Thanks to your Dupes Clause, your first valid encounter in Lilycove will be guaranteed to be **Staryu**. You can evolve it with a Water Stone (found on the Abandoned Ship or traded for a Blue Shard).
*   **Why for Juan:** Starmie is fast, hits incredibly hard, and can learn Thunderbolt, Ice Beam, Psychic, and Surf. It also gets Recover. 

### 4. Abandoned Ship (Tentacruel)
If you didn't catch a Tentacool on your earlier surfing routes, get one now.
*   **The Catch:** Tentacool/Tentacruel are everywhere here. 
*   **Why for Juan:** Tentacruel has incredibly high Special Defense. It resists Water and Ice. Furthermore, it has the **Clear Body** ability (prevents stat drops) and can learn **Toxic**. You can poison Kingdra, and then stall it out with Barrier/Protect.

---

### Strategy for Juan (Level Cap: 46)

Juan’s Team: **Luvdisc (41), Whiscash (41), Sealeo (43), Crawdaunt (43), Kingdra (46)**

*   **Luvdisc:** Lead with Manectric. Easy OHKO with Thunderbolt/Spark.
*   **Whiscash:** It’s Water/Ground, so Manectric can’t hit it. Switch immediately to **Breloom**. Whiscash has a 4x weakness to Grass. Giga Drain or Bullet Seed will obliterate it. *Be careful:* it knows Amnesia and Earthquake.
*   **Sealeo:** Breloom can hit it with Fighting moves, but Sealeo has Aurora Beam (Ice). Manectric is your safest bet here to take it out with Electric moves.
*   **Crawdaunt:** Breloom’s Mach Punch/Sky Uppercut or Manectric's Electric moves will destroy it. 
*   **Kingdra:** **The Boss.** 
    *   **The "Never Miss" Strategy:** Since Kingdra will spam Double Team, accuracy is your worst enemy. Teach **Shock Wave (TM39)** to Manectric or Starmie/Magneton, and/or teach **Aerial Ace (TM40)** to Swellow. These moves bypass accuracy checks and ignore Double Team evasion boosts. 
    *   **The Stall Strategy:** Bring in a bulky Water-type (Tentacruel or Walrein) that resists Ice and Water. Use Toxic on Kingdra (it will cure it with Rest, but you re-apply it when it wakes up) and just out-heal it. 

**Next Steps Checklist:**
1. Go catch Magnemite in New Mauville.
2. Exploit Dupes Clause to get Staryu in Lilycove and Spheal in Shoal Cave.
3. Grind your team to Level 45/46. (The reporters Gabby & Ty on Route 111/118/120 are great for safe EXP).
4. Put the TM for Shock Wave or Aerial Ace on your team to ensure Kingdra's Double Team doesn't end your run!
