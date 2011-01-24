from threading import local

__all__ = ['activate', 'deactivate', 'get_collector', 'add_module']

_active = local()

def activate():
    """
    Activates a global accessible object, where we can save information about
    required dojo modules.
    """
    class Collector:
        used_dojo_modules = []

        def add(self, module):
            # just add a module once!
            if not module in self.used_dojo_modules:
                self.used_dojo_modules.append(module)

    _active.value = Collector()

def deactivate():
    """
    Resets the currently active global object
    """
    if hasattr(_active, "value"):
        del _active.value

def get_collector():
    """Returns the currently active collector object."""
    t = getattr(_active, "value", None)
    if t is not None:
        try:
            return t
        except AttributeError:
            return None
    return None

def get_modules():
    collector = get_collector()
    if collector is not None:
        return collector.used_dojo_modules
    return []

def add_module(module):
    collector = get_collector()
    if collector is not None:
        collector.add(module)
    # otherwise do nothing
    pass

