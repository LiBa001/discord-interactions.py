#!/usr/bin/env python

"""
MIT License

Copyright (c) 2020-2021 Linus Bartsch

This file contains (partly modified) contents of https://github.com/Rapptz/discord.py.
Respective Copyright (c) 2015-2020 Rapptz

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

from ..errors import DiscordException


class ExtensionError(DiscordException):
    """Base exception for extension related errors.
    This inherits from :exc:`~discord.DiscordException`.

    Attributes
    ------------
    name: :class:`str`
        The extension that had an error.
    """

    def __init__(self, message=None, *args, name):
        self.name = name
        message = message or "Extension {!r} had an error.".format(name)
        # clean-up @everyone and @here mentions
        m = message.replace("@everyone", "@\u200beveryone").replace(
            "@here", "@\u200bhere"
        )
        super().__init__(m, *args)


class ExtensionAlreadyLoaded(ExtensionError):
    """
    An exception raised when an extension has already been loaded.
    This inherits from :exc:`ExtensionError`
    """

    def __init__(self, name):
        super().__init__("Extension {!r} is already loaded.".format(name), name=name)


class ExtensionNotLoaded(ExtensionError):
    """
    An exception raised when an extension was not loaded.
    This inherits from :exc:`ExtensionError`
    """

    def __init__(self, name):
        super().__init__("Extension {!r} has not been loaded.".format(name), name=name)


class NoEntryPointError(ExtensionError):
    """
    An exception raised when an extension does not have a ``setup``
    entry point function.
    This inherits from :exc:`ExtensionError`
    """

    def __init__(self, name):
        super().__init__(
            "Extension {!r} has no 'setup' function.".format(name), name=name
        )


class ExtensionFailed(ExtensionError):
    """
    An exception raised when an extension failed to load during execution of the module
    or ``setup`` entry point.
    This inherits from :exc:`ExtensionError`

    Attributes
    -----------
    name: :class:`str`
        The extension that had the error.
    original: :exc:`Exception`
        The original exception that was raised. You can also get this via
        the ``__cause__`` attribute.
    """

    def __init__(self, name, original):
        self.original = original
        fmt = "Extension {0!r} raised an error: {1.__class__.__name__}: {1}"
        super().__init__(fmt.format(name, original), name=name)


class ExtensionNotFound(ExtensionError):
    """
    An exception raised when an extension is not found.
    This inherits from :exc:`ExtensionError`

    Attributes
    -----------
    name: :class:`str`
        The extension that had the error.
    original: :class:`NoneType`
        Always ``None`` for backwards compatibility.
    """

    def __init__(self, name, original=None):
        self.original = None
        fmt = "Extension {0!r} could not be loaded."
        super().__init__(fmt.format(name), name=name)
