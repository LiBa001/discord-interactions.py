#!/usr/bin/env python

"""
MIT License

Copyright (c) 2020-2022 Linus Bartsch

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

from __future__ import annotations

from typing import Callable, Union, TypeAlias, Generic, TypeVar, Literal, Any
from enum import Enum

from .. import InteractionResponse, InteractionType
from .context import ComponentContext, AfterComponentContext
from .command import _CommandCallbackReturnType

_ElementCallbackReturnType: TypeAlias = Union[InteractionResponse, str, None]
_ElementCallback: TypeAlias = Union[
    Callable[[], _ElementCallbackReturnType],
    Callable[[ComponentContext], _ElementCallbackReturnType],
    Callable[[ComponentContext, Any], _ElementCallbackReturnType]
]
_AfterElementCallback: TypeAlias = Callable[[AfterComponentContext], None]


class ElementType(Enum):
    MESSAGE_COMPONENT = InteractionType.MESSAGE_COMPONENT
    MODAL = InteractionType.MODAL_SUBMIT


T = TypeVar("T", Literal[ElementType.MESSAGE_COMPONENT], Literal[ElementType.MODAL])


class ElementData(Generic[T]):
    """
    Stores and handles registering callbacks for a UI element like a message component.

    :type _type: ElementType
    :param _type: The type of the element (e.g. message component or modal).

    :type custom_id: str
    :param custom_id: Custom id to identify the element.

    :param cb:
        The function to be called when the element is invoked
        (e.g. button clicked).
    """

    def __init__(self, _type: T, custom_id: str, cb: _ElementCallback):
        self.element_type = _type
        self.custom_id = custom_id
        self.callback = cb
        self.after_callback = None
        self.error_callback = None

    @classmethod
    def create_from(cls, _type: T, custom_id: str, callback: Callable) -> ElementData[T]:
        """
        Create an instance of :class:`ElementData`.

        :param _type: The type of element that data is created for
        :param custom_id: The custom id specified when creating the element
        :param callback: The function that is called when the element is triggered
        :return: An object containing all the element data (e.g. custom_id, callbacks)
        """

        return cls(_type, custom_id, callback)

    def after_element(self, f: _AfterElementCallback):
        """
        A decorator to register a function that gets called after an element invocation
        has returned.
        The internal callback function invocation should always fulfill the contract of
        only being called after the initial interaction response has been submitted.
        """

        self.after_callback = f

    def on_error(self, f: Callable[[Exception], _CommandCallbackReturnType]):
        """
        A decorator to set the element error callback function.
        The provided function will be called when an exception is raised in any other
        callback of this element.

        :param f: The error callback function.
        """

        self.error_callback = f


def element(custom_id: str, _type: T = ElementType.MESSAGE_COMPONENT) -> Callable[[_ElementCallback], ElementData[T]]:
    """
    A decorator to register a callback on a UI element.

    :param custom_id: The custom id specified when creating the component.
    :param _type: The type of element.
    """

    def decorator(f: _ElementCallback) -> ElementData[_type]:
        return ElementData.create_from(_type, custom_id, f)

    return decorator
