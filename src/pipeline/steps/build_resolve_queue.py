"""
Build resolve queue from unresolved mentions.
"""

def build_resolve_queue(unresolved_mentions: List[dict], source_items: List[dict]) -> List[dict]:
    """
    Aggregate unresolved mentions by surface_norm.
    Impact-weighted for prioritization.
    
    Returns list for resolve queue UI.
    """
    # TODO: Implement
    # - Group unresolved by surface_norm
    # - Compute impact (engagement-weighted count)
    # - Collect top examples with candidates
    # - Sort by impact desc
    # - Write to unresolved_mentions table (or queue table)
    # - Return queue list
    pass
