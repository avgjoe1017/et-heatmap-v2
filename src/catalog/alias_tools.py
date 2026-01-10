"""
Alias normalization and generation utilities.
"""

import re
from typing import List


def normalize_alias(alias: str) -> str:
    """
    Normalize alias for matching.
    """
    if not alias:
        return ""
    alias = alias.lower()
    alias = re.sub(r"[^\w\s]", "", alias)
    alias = re.sub(r"\s+", " ", alias).strip()
    return alias


def generate_aliases(canonical_name: str) -> List[str]:
    """
    Generate common aliases from canonical name.
    """
    base = normalize_alias(canonical_name)
    if not base:
        return []

    aliases = {base}

    if base.startswith("the "):
        aliases.add(base[4:])

    tokens = base.split()
    if len(tokens) >= 2:
        aliases.add(tokens[-1])
        aliases.add(f"{tokens[0]} {tokens[-1]}")
        initials = "".join(token[0] for token in tokens if token)
        if len(initials) >= 2:
            aliases.add(initials)

    return sorted(aliases)
