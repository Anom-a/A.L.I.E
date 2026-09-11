"""Shared exceptions for adapter layers."""

class SearchGatewayError(Exception):
    """Raised when an external search gateway cannot retrieve usable results.
    
    This is the standard adapter-level exception for search provider failures.
    Any underlying HTTP or SDK errors are caught and re-raised as this exception,
    ensuring that the application layer never deals with provider-specific exceptions.
    """
