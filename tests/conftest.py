"""Tests never send traces: blank the LangFuse keys before anything loads .env (which doesn't
override variables that are already set), so agent/observability.py stays off."""

import os

for key in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"):
    os.environ[key] = ""
