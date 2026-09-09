"""Interface adapters.

This layer translates between the outside world (SDKs, HTTP APIs, provider
payloads) and the domain. It may import from ``domain`` — never the other way
round — and it must not leak provider types back across the port boundary.
"""
