"""Route mixins for the local HTTP API.

Each mixin owns one concern and exposes a single `_route_<group>` method that
returns `(status, payload)` when it handles the path, or `None` to let the next
group try. `rad.api.Api` assembles them and keeps the (method, path, query,
body) → (status, payload) dispatch contract.
"""
from rad.api_routes.system import SystemMixin
from rad.api_routes.objectives import ObjectivesMixin
from rad.api_routes.memory import MemoryMixin
from rad.api_routes.authority import AuthoritySettingsMixin
from rad.api_routes.chat_usage import ChatUsageMixin
from rad.api_routes.ops import OpsMixin
from rad.api_routes.triage import TriageMixin

__all__ = [
    "SystemMixin",
    "ObjectivesMixin",
    "MemoryMixin",
    "AuthoritySettingsMixin",
    "ChatUsageMixin",
    "OpsMixin",
    "TriageMixin",
]
