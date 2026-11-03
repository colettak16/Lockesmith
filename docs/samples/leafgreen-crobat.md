# Agent: leafgreen-crobat

**Question:** My Golbat is really friendly now. Will it evolve into Crobat before the Elite Four?

14.0 s · 3 model calls · 8,376 tokens · about $0.023 · researchers: none · 3 trace steps (full trace in `leafgreen-crobat.json`)

## Answer

No, Golbat cannot evolve into Crobat before the Elite Four in LeafGreen [1].

### National Dex Restriction
In Pokémon LeafGreen, you cannot obtain Pokémon that are not in the original 151 Kanto Pokédex until you receive the National Dex [1]. Because Crobat is Pokémon #169 (introduced in Generation II), the game will actively prevent Golbat's evolution attempt from completing, even if it has maximum friendship [1].

### When you can get Crobat
You must first defeat the Elite Four and enter the Hall of Fame [1]. After that, once you have caught at least 60 different species of Pokémon and visited One Island, Professor Oak will upgrade your Pokédex to the National Dex [1]. Only then will your high-friendship Golbat be allowed to evolve into Crobat when it levels up [1].

### Assumptions
* Your Golbat already has high enough friendship to trigger the evolution, but the game mechanics will cancel it [1].

## Sources

1. LockeSmith's LeafGreen rules (agent/brief.py) (`rules:game`)
