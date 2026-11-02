"""One-click example questions (PLAN.md §10, §11): the front end's example buttons, the README's
sample queries and scripts/run_samples.py all use this list. Each fills the question and the
run state it depends on; `sample_log` is uploaded first, from static/samples/."""

MID_GAME_PARTY = [
    {"species": "Marshtomp", "level": 33}, {"species": "Breloom", "level": 30},
    {"species": "Swellow", "level": 31}, {"species": "Manectric", "level": 30},
]
SIX = ["stone", "knuckle", "dynamo", "heat", "balance", "feather"]
SEVEN = SIX + ["mind"]
USED_ROUTES = [
    "Route 101", "Route 102", "Route 103", "Route 104", "Petalburg Woods", "Route 116", "Rusturf Tunnel",
    "Granite Cave", "Route 110", "Route 117", "Route 111", "Route 112", "Fiery Path", "Route 113", "Route 114",
    "Meteor Falls", "Route 115", "Route 118", "Route 119", "Route 120", "Route 121", "Safari Zone", "Mt. Pyre",
]

EXAMPLES = [
    {
        "id": "tate-liza", "title": "Mid-game catch plan", "tag": "vanilla", "readme": True,
        "blurb": "Six badges, heading into Emerald's double-battle Mossdeep Gym.",
        "message": "What should I catch to get through Tate & Liza?",
        "run_state": {"starter": "mudkip", "rival": "may", "badges": SIX, "party": MID_GAME_PARTY},
    },
    {
        "id": "nuzlocke-juan", "title": "Nuzlocke into Juan", "tag": "nuzlocke", "readme": True,
        "blurb": "Dupes clause, level caps and 23 used areas: what's still catchable?",
        "message": "Nuzlocke with the dupes clause and level caps. Juan is next; what should I catch?",
        "run_state": {
            "starter": "mudkip", "rival": "may", "badges": SEVEN,
            "party": [{"species": "Swampert", "level": 42}, {"species": "Breloom", "level": 40},
                      {"species": "Swellow", "level": 40}, {"species": "Manectric", "level": 39}],
            "ruleset": {"nuzlocke": True, "dupes_clause": True, "level_caps": True, "used_routes": USED_ROUTES},
        },
    },
    {
        "id": "randomizer-tate-liza", "title": "Randomized gym", "tag": "randomizer", "readme": True,
        "blurb": "Loads a sample randomizer log where Tate & Liza use Fire types.",
        "message": "What should I catch to get through Tate & Liza?",
        "run_state": {"starter": "mudkip", "rival": "may", "badges": SIX, "party": MID_GAME_PARTY},
        "sample_log": "fire-tate-liza.log",
    },
    {
        "id": "monotype", "title": "Custom rules in chat", "tag": "rules",
        "blurb": "Rules typed in plain words become checked constraints.",
        "message": "I'm doing a Water monotype run with no legendaries. What should I catch before Juan?",
        "run_state": {"starter": "mudkip", "rival": "may", "badges": SEVEN,
                      "party": [{"species": "Swampert", "level": 42}, {"species": "Pelipper", "level": 38}]},
    },
    {
        "id": "next-steps", "title": "What do I do next?", "tag": "story",
        "blurb": "Early game: the next story steps and what opens on the way.",
        "message": "I just beat Roxanne. What should I do next?",
        "run_state": {"starter": "treecko", "badges": ["stone"]},
    },
    {
        "id": "plan", "title": "Road to the Champion", "tag": "plan",
        "blurb": "A longer plan: phases by battle, with catches along the way.",
        "message": "Give me a plan from here to the Champion.",
        "run_state": {"starter": "torchic", "rival": "brendan", "badges": ["stone", "knuckle", "dynamo", "heat"],
                      "party": [{"species": "Combusken", "level": 28}, {"species": "Marill", "level": 25},
                                {"species": "Taillow", "level": 24}]},
    },
    {
        "id": "vague", "title": "A vague question", "tag": "clarify",
        "blurb": "With no run state, it asks before researching.",
        "message": "what should I catch?",
        "run_state": {},
    },
    {
        "id": "out-of-scope", "title": "Out of scope", "tag": "decline",
        "blurb": "Another game: it says what it covers instead of guessing.",
        "message": "What's the best EV spread for Garchomp in Pokémon Sword?",
        "run_state": {},
    },
]
