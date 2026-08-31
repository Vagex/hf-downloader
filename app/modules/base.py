import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Type, Any

class BaseAppModule:
    """Standard abstract base class for all pluggable feature modules."""
    module_id: str = "base"
    name: str = "基础模块"
    icon_name: str = "tool"
    category: str = "通用"
    description: str = ""
    order: int = 100

    def __init__(self):
        self.context: Optional[Any] = None
        self.view_container: Optional[tk.Widget] = None

    def initialize(self, app_context: Any):
        """Called once when the application starts."""
        self.context = app_context

    def create_view(self, parent: tk.Widget) -> tk.Widget:
        """Create and return the module's main UI widget."""
        raise NotImplementedError("Each module must implement create_view(parent)")

    def on_activate(self):
        """Called when user switches to this module."""
        pass

    def on_deactivate(self):
        """Called when user switches away from this module."""
        pass

    def on_shutdown(self):
        """Called when application is closing."""
        pass


class ModuleManager:
    """Central registry and lifecycle manager for all modules."""
    _modules: Dict[str, BaseAppModule] = {}
    _module_order: List[str] = []

    @classmethod
    def register(cls, module_class: Type[BaseAppModule]):
        instance = module_class()
        cls._modules[instance.module_id] = instance
        if instance.module_id not in cls._module_order:
            cls._module_order.append(instance.module_id)
        # Sort by module.order
        cls._module_order.sort(key=lambda mid: cls._modules[mid].order)

    @classmethod
    def get_module(cls, module_id: str) -> Optional[BaseAppModule]:
        return cls._modules.get(module_id)

    @classmethod
    def get_all_modules(cls) -> List[BaseAppModule]:
        return [cls._modules[mid] for mid in cls._module_order]
