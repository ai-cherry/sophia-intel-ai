"""Legacy Artemis agent factory import path (proxy)

This module has moved to `app.artemis.factories.agent_factory`.
It remains as a thin proxy to maintain backward compatibility.
"""

from warnings import warn

warn(
    "app.artemis.agent_factory is deprecated; use app.artemis.factories.agent_factory",
    DeprecationWarning,
    stacklevel=2,
)

from app.artemis.factories.agent_factory import *  # noqa: F401,F403
