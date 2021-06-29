from __future__ import annotations

import abc
import asyncio
import functools
import typing

import nest_asyncio


# Patch asyncio to allow nested loops
nest_asyncio.apply()


class HybridSync(object, metaclass=abc.ABCMeta):
    def __init__(self, async_enabled: bool = True, async_limit: typing.Optional[int] = None,
                 event_loop: typing.Optional[asyncio.AbstractEventLoop] = None):
        self._async_enabled = async_enabled
        self._async_loop = event_loop or asyncio.get_event_loop()

        self._async_semaphore = asyncio.Semaphore(async_limit) if async_limit else None

    async def _semaphore_wrapper(self, coroutine):
        with self._async_semaphore:
            return await coroutine

    @staticmethod
    def wrapper(coroutine):
        @functools.wraps(coroutine)
        def f(self: HybridSync, *args, async_enabled: typing.Optional[bool] = None, **kwargs):
            if async_enabled is None:
                async_enabled = self._async_enabled

            if async_enabled:
                if self._async_semaphore is None:
                    return coroutine(self, *args, **kwargs)
                else:
                    return self._semaphore_wrapper(coroutine(self, *args, **kwargs))
            else:
                return self._async_loop.run_until_complete(coroutine(self, *args, **kwargs))

        return f
