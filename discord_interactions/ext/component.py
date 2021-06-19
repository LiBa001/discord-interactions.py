#!/usr/bin/env python

"""
MIT License

Copyright (c) 2020-2021 Linus Bartsch

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Callable, Union

from .. import InteractionResponse
from .context import ComponentContext, AfterComponentContext
from .command import _CommandCallbackReturnType

_ComponentCallbackReturnType = Union[InteractionResponse, str, None]
_ComponentCallback = Union[
    Callable[[], _ComponentCallbackReturnType],
    Callable[[ComponentContext], _ComponentCallbackReturnType],
]
_AfterComponentCallback = Callable[[AfterComponentContext], None]


class ComponentData:
    """
    Stores and handles registering callbacks for a registered message component.

    :type custom_id: str
    :param custom_id: Custom id to identify the component.

    :param cb:
        The function to be called when the component is invoked
        (e.g. button clicked).
    """

    def __init__(self, custom_id: str, cb: _ComponentCallback):
        self.custom_id = custom_id
        self.callback = cb
        self.after_callback = None
        self.error_callback = None

    @classmethod
    def create_from(cls, component_id: str, callback: Callable) -> "ComponentData":
        """
        Create an instance of :class:`ComponentData`.

        :param component_id: The ``custom_id`` specified when creating the component
        :param callback: The function that is called when the component is triggered
        :return: An object containing all the component data (e.g. custom_id, callbacks)
        """

        return cls(component_id, callback)

    def after_component(self, f: _AfterComponentCallback):
        """
        A decorator to register a function that gets called after a component invocation
        has returned.
        The function will be internally called from within Flask's `after_request`
        function.
        """

        self.after_callback = f

    def on_error(self, f: Callable[[Exception], _CommandCallbackReturnType]):
        """
        A decorator to set the component error callback function.
        The provided function will be called when an exception is raised in any other
        callback of this component.

        :param f: The error callback function.
        """

        self.error_callback = f


def component(component_id: str) -> Callable[[_ComponentCallback], ComponentData]:
    """
    A decorator to register a callback on a message component.

    :param component_id: The custom id specified when creating the component.
    """

    def decorator(f: _ComponentCallback) -> ComponentData:
        return ComponentData.create_from(component_id, f)

    return decorator
