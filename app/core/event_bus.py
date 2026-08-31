import threading
from typing import Callable, Dict, List, Any

class EventBus:
    """Thread-safe lightweight event bus for cross-module communication."""
    _listeners: Dict[str, List[Callable]] = {}
    _lock = threading.Lock()

    @classmethod
    def subscribe(cls, event_type: str, handler: Callable[[Any], None]):
        with cls._lock:
            if event_type not in cls._listeners:
                cls._listeners[event_type] = []
            if handler not in cls._listeners[event_type]:
                cls._listeners[event_type].append(handler)

    @classmethod
    def unsubscribe(cls, event_type: str, handler: Callable[[Any], None]):
        with cls._lock:
            if event_type in cls._listeners and handler in cls._listeners[event_type]:
                cls._listeners[event_type].remove(handler)

    @classmethod
    def emit(cls, event_type: str, data: Any = None):
        handlers = []
        with cls._lock:
            if event_type in cls._listeners:
                handlers = list(cls._listeners[event_type])
        for h in handlers:
            try:
                h(data)
            except Exception as e:
                print(f"[EventBus] Error dispatching event '{event_type}': {e}")
