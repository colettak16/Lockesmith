# Baseline: randomizer-tate-liza

vertex_ai/gemini-3.1-pro-preview, no tools, no system prompt. 60.5 s, 225 input / 4110 output tokens, about $0.0498.

## Prompt

```text
I'm playing Pokémon Emerald. My starter was Mudkip and my rival is May. I have 6 badges: Stone, Knuckle, Dynamo, Heat, Balance, Feather. My party: Marshtomp Lv33, Breloom Lv30, Swellow Lv31, Manectric Lv30. It's a randomized run (Universal Pokémon Randomizer ZX). Here's my spoiler log:

Randomizer Version: 4.6.1
Random Seed: 4570
Settings String: synthetic-acceptance
Note: a hand-made sample in UPR ZX's log format, not a log from a real ROM. Only Tate & Liza are randomized (to Fire types); everything else is vanilla.

--Trainers Pokemon--
#271 (TATE&LIZA)@31F2E8 - Camerupt Lv41, Torkoal Lv41, Magcargo@Sitrus Berry Lv42, Houndoom@Sitrus Berry Lv42


What should I catch to get through Tate & Liza?
```

## Answer

You’ve hit the jackpot! In a game famous for having "too much water," the randomizer has graciously turned the hardest Gym Leaders in Emerald into a pure Fire-type double battle. 

Two of their Pokémon (Camerupt and Magcargo) have **4x weaknesses to Water**, while the other two (Torkoal and Houndoom) have a 2x weakness. 

Here is exactly what you should do to completely trivialize this fight:

### 1. The Strategy: "Double Surf"
In Generation 3, the move **Surf hits BOTH opponents in a Double Battle**, but *does not* hit your ally. Since Tate & Liza are a Double Battle, having two Pokémon on the field spamming Surf at the same time will hit all four of their weaknesses simultaneously. 

### 2. Evolve Marshtomp! (Priority #1)
Before you catch anything, you **must level up Marshtomp to 36 so it evolves into Swampert**. 
Looking at your party, your team is Lv 30-33, but Tate & Liza are **Lv 41-42**. Even with a massive type advantage, a 10-level gap is dangerous. Getting Swampert gives you a massive stat boost, a Water/Ground typing (resists Fire and Rock, immune to Electric), and a fantastic physical tank. 

### 3. What to Catch (The Surfing Partner)
You want a second Water-type Pokémon to sit next to Swampert and spam Surf. Since you are in Mossdeep City, you have access to some incredible options right now:

*   **Option A: Spheal / Sealeo (Shoal Cave)**
    *   **Location:** Shoal Cave is Route 125, just north of Mossdeep City. You can catch Sealeo natively around Lv 30-32.
    *   **Why it's great:** Try to catch one with the ability **Thick Fat**. Sealeo is Water/Ice, which makes Fire moves hit for neutral damage normally. However, Thick Fat halves Fire damage, effectively giving Sealeo a Fire resistance! It is incredibly bulky and can easily survive anything Tate & Liza throw at it while spamming Surf.
*   **Option B: Tentacruel (Surfing anywhere)**
    *   **Location:** Any ocean route (124, 125, etc.).
    *   **Why it's great:** Tentacruel has massive Special Defense (120 base) and a natural resistance to Fire. It is also very fast. You can catch these at high levels (up to Lv 35) just by surfing around Mossdeep, minimizing the amount of grinding you have to do.
*   **Option C: Staryu / Starmie (Lilycove City)**
    *   **Location:** You can get the **Super Rod** from a fisherman inside a house in Mossdeep City. Fly back to Lilycove City and fish in the water. 
    *   **Why it's great:** Use a Water Stone (found on Route 106 or by trading a Blue Shard) to evolve it into Starmie immediately. Starmie is blazing fast and has fantastic Special Attack. It will outspeed their entire team and nuke them. 
*   **Option D: Pelipper (Surfing anywhere)**
    *   **Location:** Any water route. 
    *   **Why it's great:** Camerupt is part Ground and often carries Magnitude or Earthquake. Pelipper is Water/Flying, meaning it is completely immune to Ground moves while still resisting Fire. 

### 4. Items and Execution
1.  Give **Swampert** the **Mystic Water** (received from the Castform scientists at the Weather Institute).
2.  Give your **New Catch** the **Sea Incense** (found at Mt. Pyre). 
3.  Teach both of them **Surf**. 
4.  Lead the battle with Swampert and your new Water-type. 
5.  Click Surf with both Pokémon on Turn 1 and Turn 2. 

Because of the 4x weaknesses on Camerupt and Magcargo, those two will likely die in a single turn. Houndoom and Torkoal will take double-damage Surfs from two different Pokémon and will faint shortly after. Their Sitrus Berries won't even matter because you will out-damage their healing. You'll win in 2-3 turns without breaking a sweat!
