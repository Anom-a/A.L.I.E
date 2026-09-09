"""Application layer: use cases that orchestrate the domain.

This layer depends on the domain (entities, value objects, ports) and on
nothing outside it — no OpenAI, no Tavily, no FastAPI, no LangGraph, no HTTP
client, and no configuration or environment access. Concrete adapters are
injected from the composition root, so a use case only ever talks to a *port*
and never learns which provider is on the other side of it.
"""
