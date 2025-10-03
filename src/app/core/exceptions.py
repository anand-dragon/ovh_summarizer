class DocumentConflictError(Exception):
    """Name or URL already used by another document (but not an exact match)."""
