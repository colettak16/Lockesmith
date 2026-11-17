# What's in docs/

Supporting material for the [main README](../README.md): the design record, the evidence behind the data, and saved runs.

## Design and deployment

| | |
|---|---|
| [decisions.md](decisions.md) | Every design decision, D1–D20, with the reason, what it cost and what testing turned up. "Data findings" lists where PokeAPI disagrees with the decomps. Start here for *why* something is built the way it is. |
| [deploy.md](deploy.md) | Cloud Run setup: continuous deploy from GitHub, IAP sign-in, Vertex AI permissions, session affinity, LangFuse keys. |
| [images/](images/) | The LangFuse screenshots in the main README. |

## Saved answers

| | |
|---|---|
| [samples/](samples/) | LockeSmith's full answers to nine of the site's twelve example questions, each as Markdown (`.md`) and the raw `/chat` response with every tool call (`.json`), from [`scripts/run_samples.py`](../scripts/run_samples.py). [expected.md](samples/expected.md) has the expected answers, generated from the databases by [`scripts/expected_answers.py`](../scripts/expected_answers.py). [vague.md](samples/vague.md) and [out-of-scope.md](samples/out-of-scope.md) show the agent asking a clarifying question and declining an off-topic one. |
| [baseline/](baseline/) | The same questions put to Gemini 3.5 Flash with no tools and no system prompt ([`scripts/baseline.py`](../scripts/baseline.py)). |

## Checking the data

Each game's facts and story order were written up as numbered claims and checked against the decompilation before the agents relied on them. Code, tests and docs/decisions.md cite these claims by ID.

| | |
|---|---|
| [review_packet.md](review_packet.md) | Emerald: battle mechanics, species, moves and evolutions as of Gen III, data findings, the story order, encounter mapping and every story trainer's team. Generated from the database by [`build/review_packet.py`](../build/review_packet.py). |
| [review_packet_rs.md](review_packet_rs.md) | Ruby and Sapphire: what differs from Emerald, the story order, the randomizer log format, data findings and the area-unlock check (section 12). |
| [review_packet_frlg.md](review_packet_frlg.md), [review_packet_frlg_round2.md](review_packet_frlg_round2.md) | FireRed and LeafGreen story order and facts: the first draft, then the revised order. |
| [audit/](audit/) | Reports from `uv run python -m audit`: the mechanical Ruby/Sapphire-vs-Emerald comparison behind section 12 of the Ruby/Sapphire packet ([audit/README.md](../audit/README.md)). |

[PLAN.md](../PLAN.md) at the repo root is the original plan from Nov 1, kept as written.
