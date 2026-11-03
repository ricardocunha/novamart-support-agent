"""Single source of "today" so date-based answers are reproducible in demos and evals."""

import os
from datetime import date


def today() -> date:
    pinned = os.getenv("NOVAMART_TODAY")
    return date.fromisoformat(pinned) if pinned else date.today()
