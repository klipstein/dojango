from django.utils.thread_support import currentThread

__all__ = ['activate', 'deactivate', 'get_collector', 'add_module']

_active = {}

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

    _active[currentThread()] = Collector()

def deactivate():
    """
    Resets the currently active global object
    """
    global _active
    if currentThread() in _active:
        del _active[currentThread()]

def get_collector():
    """Returns the currently active collector object."""
    t = _active.get(currentThread(), None)
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