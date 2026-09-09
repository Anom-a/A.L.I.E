"""Domain ports (interfaces).

Ports are the boundary the domain/application defines and outer layers
implement (dependency inversion). They are declared with ``typing.Protocol`` so
no concrete adapter needs to subclass anything, and they speak only in standard
-library and domain types — never provider SDK types.
"""
