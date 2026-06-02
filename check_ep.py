#!/usr/bin/env python3
"""Check entry points for symphony.trackers group."""
from importlib.metadata import entry_points
import sys

if sys.version_info >= (3, 12):
    eps = entry_points(group="symphony.trackers")
else:
    eps = entry_points().get("symphony.trackers", [])

print("Entry points in symphony.trackers:")
for ep in eps:
    print(f"  {ep.name}: {ep.value}")