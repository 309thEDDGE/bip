import importlib.metadata
__version__ = importlib.metadata.version("saber-bip")


def metadata():
    return dict(importlib.metadata.metadata("saber-bip"))
