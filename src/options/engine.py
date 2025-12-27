from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Deque

from .events import Event, EventType

Handler = Callable[[Event], None]


@dataclass
class EventBus:
    """Simple in-memory event bus for deterministic orchestration."""

    _subscribers: dict[EventType, list[Handler]] = field(default_factory=lambda: defaultdict(list))
    _queue: Deque[Event] = field(default_factory=deque)

    def subscribe(self, event_type: EventType, handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        self._queue.append(event)

    def drain(self, max_events: int | None = None) -> None:
        count = 0
        while self._queue:
            event = self._queue.popleft()
            for handler in self._subscribers.get(event.event_type, []):
                handler(event)
            count += 1
            if max_events is not None and count >= max_events:
                break
