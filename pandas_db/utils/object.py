class Object:
    def __init__(self, *args):
        for arg in args:
            if hasattr(arg, "__class__"):
                setattr(self, arg.__class__.__name__, arg)
            elif hasattr(arg, "__name__"):
                setattr(self, arg.__name__, arg)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            return None

