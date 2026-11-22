"""
Minimal in-process message bus for inter-agent communication.
Agents publish messages; other agents subscribe by topic.
"""

from collections import defaultdict
from typing import Callable, Any


class MessageBus:
    """Simple synchronous publish/subscribe message bus."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._history: list[dict] = []

    def subscribe(self, topic: str, handler: Callable[[dict], Any]) -> None:
        """Register *handler* to be called when a message is published on *topic*."""
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, payload: dict) -> None:
        """Publish a message; all subscribers for *topic* are called immediately."""
        message = {"topic": topic, **payload}
        self._history.append(message)
        for handler in self._subscribers.get(topic, []):
            handler(message)

    def get_history(self, topic: str | None = None) -> list[dict]:
        """Return all messages, optionally filtered by topic."""
        if topic is None:
            return list(self._history)
        return [m for m in self._history if m["topic"] == topic]
