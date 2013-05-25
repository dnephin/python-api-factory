

try:
    import colander.drop as drop
except ImportError:
    class _drop(object): pass
    drop = _drop()