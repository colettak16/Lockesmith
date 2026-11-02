"""Register Lockesmith's model prices in your LangFuse project, so its traces show cost.

    uv run python scripts/langfuse_prices.py

LangFuse matches a model call to a price by the call's model name. Ours carry LiteLLM's
"vertex_ai/" prefix and are newer than LangFuse's built-in list, so without this the traces
show tokens but no cost. Prices come from agent/pricing.py. Safe to rerun: a model that's
already defined is skipped. Needs LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_BASE_URL
(in .env or the environment).
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

from agent.pricing import PRICES, SOURCE  # noqa: E402

LATER = {"gemini-3.8-flash": (datetime(2027, 1, 1, tzinfo=timezone.utc), (1.50, 7.50))}  # after its introductory price


def main() -> int:
    load_dotenv()
    from langfuse import get_client
    from langfuse.api.commons.types.pricing_tier_input import PricingTierInput

    lf = get_client()
    if not lf.auth_check():
        print("LangFuse rejected the keys: check LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY and LANGFUSE_BASE_URL.")
        return 1
    existing = {(m.model_name, str(m.start_date)[:10] if m.start_date else None) for m in lf.api.models.list(limit=100).data}
    definitions = [(name, None, price) for name, price in PRICES.items()]
    definitions += [(name, start, price) for name, (start, price) in LATER.items()]
    for name, start, (inp, out) in definitions:
        label = f"lockesmith-{name}"
        day = start.date().isoformat() if start else None
        if (label, day) in existing:
            print(f"already defined: {label}" + (f" from {day}" if day else ""))
            continue
        lf.api.models.create(
            model_name=label,
            match_pattern=f"(?i)^(vertex_ai/)?{re.escape(name)}$",
            unit="TOKENS",
            **({"start_date": start} if start else {}),
            pricing_tiers=[PricingTierInput(name="Standard", is_default=True, priority=0, conditions=[],
                                            prices={"input": inp / 1_000_000, "output": out / 1_000_000})],
        )
        print(f"defined {label}: ${inp} / ${out} per 1M input / output tokens" + (f" from {day}" if day else ""))
    print(f"Prices from {SOURCE}. They apply to traces recorded from now on.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
