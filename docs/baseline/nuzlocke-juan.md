# Baseline: nuzlocke-juan

vertex_ai/gemini-3.1-pro-preview, no tools, no system prompt. 53.6 s, 252 input / 5283 output tokens, about $0.0639.

## Prompt

```text
I'm playing Pokémon Emerald. My starter was Mudkip and my rival is May. I have 7 badges: Stone, Knuckle, Dynamo, Heat, Balance, Feather, Mind. My party: Swampert Lv42, Breloom Lv40, Swellow Lv40, Manectric Lv39. Rules: Nuzlocke (first encounter per area only), dupes clause, level caps at the next gym leader's highest level. Areas whose encounter I've already used: Route 101, Route 102, Route 103, Route 104, Petalburg Woods, Route 116, Rusturf Tunnel, Granite Cave, Route 110, Route 117, Route 111, Route 112, Fiery Path, Route 113, Route 114, Meteor Falls, Route 115, Route 118, Route 119, Route 120, Route 121, Safari Zone, Mt. Pyre.

Nuzlocke with the dupes clause and level caps. Juan is next; what should I catch?
```

## Answer

With 7 badges down, your level cap for Juan is **Level 46** (his ace is Kingdra). 

Looking at your current team, **Manectric** and **Breloom** match up incredibly well against 4 of Juan's 5 Pokémon. Breloom will absolutely destroy Whiscash (which has a 4x weakness to Grass and no Ice moves), and Manectric can sweep Luvdisc, Sealeo, and Crawdaunt with Thunderbolt.

However, Juan’s ace—**Kingdra**—is a notorious run-killer. It has Water Pulse, Ice Beam, Rest (with a Chesto Berry), and Double Team. Because it is his final Pokémon, you cannot use Roar or Whirlwind to phase away its Double Team boosts. 

Looking at your list of used areas, you have left some of the best locations in the game untouched. Here is exactly what you should go catch to counter Kingdra and build your team for the Elite Four:

### 1. The Ultimate Kingdra Counter: Magneton
**Location:** New Mauville (Surf from Route 110)
**Encounter:** Magnemite / Voltorb (If you get Voltorb, Electrode is still great, but Magneton is the prize).
*   **Why it's perfect:** Magneton is Electric/Steel. Steel resists Kingdra’s Ice Beam, and Electric takes neutral damage from Water Pulse. More importantly, Magneton learns **Lock-On** (Lv 33) and **Swift** (Lv 44) natively. 
*   **The Strategy:** You can either use Lock-On followed by Thunderbolt to guarantee a hit through 6 Double Teams, or teach it **Shock Wave** (TM34 from Wattson), which is a "never-miss" Electric move. Magneton completely walls Kingdra and slowly whittles it down without missing. 

### 2. The Unkillable Tank: Spheal (Walrein)
**Location:** Shoal Cave (Route 125, north of Mossdeep)
**Encounter:** Spheal / Sealeo (or Snorunt, but Spheal is most common)
*   **Why it's perfect:** If you evolve Spheal into Walrein (Lv 44), you get a massive Water/Ice tank with the ability Thick Fat. It resists Water Pulse and takes 1/4 damage from Ice Beam. 
*   **The Strategy:** Walrein is your ultimate safe switch. It can soak up Kingdra's hits indefinitely, heal up, and use Body Slam to fish for Paralysis, effectively neutralizing Kingdra's speed and Double Team evasion advantage. (Walrein is also basically mandatory to easily beat Drake in the Elite Four).

### 3. The Perfect Pivot: Chinchou (Lanturn)
**Location:** Underwater (Dive on Route 124 or 126)
**Encounter:** Chinchou / Clamperl / Relicanth
*   **Why it's perfect:** Lanturn (evolves at Lv 27) is Water/Electric. It resists both of Kingdra's attacking moves (Water and Ice).
*   **The Strategy:** Like Magneton, you can teach it Shock Wave (TM34) to bypass Double Team. It has a massive HP pool and can comfortably sit in front of Kingdra all day while hitting it with STAB Electric moves.

### 4. The Fast Sweeper: Staryu (Starmie)
**Location:** Lilycove City (Fish with the Super Rod)
**Encounter:** Staryu (15% chance, repels + level manipulation can help depending on dupes)
*   **Why it's perfect:** Starmie is blazing fast and has fantastic Special Attack. It resists Water and Ice.
*   **The Strategy:** You can teach it Thunderbolt (Game Corner TM), Ice Beam (Abandoned Ship TM), Recover, and either Swift or Shock Wave. It can outspeed and out-damage almost anything Juan throws at you.

---

### How to route the Gym Fight:
1. **Lead with Manectric:** OHKO his **Luvdisc** with Thunderbolt. 
2. **Switch to Breloom on Whiscash:** Whiscash will likely try to set up Rain Dance or Amnesia. Breloom is faster and will OHKO it with Giga Drain (TM19 from Route 123) or chunk it massively with Sky Uppercut/Mach Punch.
3. **Bring Manectric back out:** Thunderbolt will OHKO or 2HKO **Sealeo** and **Crawdaunt**. (If Manectric gets low, Swampert and Breloom can help clean these two up). 
4. **The Kingdra Finale:** Switch into your new **Magneton** or **Lanturn**. Spam **Shock Wave** (TM34). Because Shock Wave never misses, Double Team is completely useless. Let Kingdra use Rest to consume its Chesto Berry, then keep spamming Shock Wave until it goes down. 

**Pro Nuzlocke Tip:** Give your Kingdra counter a **Cheri Berry** to hold. Kingdra's Water Pulse has a 20% chance to confuse, which is the only way it can reliably break your strategy if it gets lucky. Removing that RNG makes this fight a guaranteed win.
