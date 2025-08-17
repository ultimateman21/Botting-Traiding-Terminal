from PyQt6.QtCore import QObject, pyqtSignal
from typing import Callable


class ExchangeRegistrySignals(QObject):
    providerChanged = pyqtSignal(str)


class ExchangeRegistry:
    _methods = {}
    _active_provider = None
    signals = ExchangeRegistrySignals()

    @classmethod
    def register_provider(cls, provider: str):
        if provider not in cls._methods:
            cls._methods[provider] = {}

    @classmethod
    def register(cls, provider: str, name: str, method: Callable):
        if provider not in cls._methods:
            cls.register_provider(provider)
        cls._methods[provider][name] = method

    @classmethod
    def get(cls, name: str):
        if cls._active_provider is None:
            raise RuntimeError('No active provider selected')
        if cls._active_provider not in cls._methods:
            raise RuntimeError(f'Active provider {cls._active_provider} was deleted')
        if name not in cls._methods[cls._active_provider]:
            raise AttributeError(f'Method {name} not found in {cls._active_provider}')

        return cls._methods[cls._active_provider][name]

    @classmethod
    def pro_get(cls, provider: str, name: str):
        if provider not in cls._methods:
            raise ValueError(f'Provider {provider} not registered')
        return cls._methods[provider][name]

    @classmethod
    def switch_provider(cls, provider: str):
        if provider not in cls._methods:
            raise ValueError(f'Provider {provider} not registered')
        cls._active_provider = provider
        cls.signals.providerChanged.emit(provider)

    @classmethod
    def deregister_provider(cls, provider: str):
        if provider == cls._active_provider:
            cls._active_provider = None
        cls._methods.pop(provider, None)

    @classmethod
    def get_registered_providers(cls):
        return list(cls._methods.keys())

    @classmethod
    def get_active_provider(cls):
        return cls._active_provider
