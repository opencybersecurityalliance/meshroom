def exclude_nones(data: dict):
    """Exclude None values from a dict"""
    return {k: v for k, v in data.items() if v is not None}
