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

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class ComponentType(Enum):
    ActionRow = 1  # A container for other components
    Button = 2  # A clickable button


class ButtonStyle(Enum):
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5


@dataclass()
class Component:
    """ Interactive component on a message object. """

    type: ComponentType

    # valid for action rows
    components: Optional[List["Component"]] = None

    # valid for buttons
    style: Optional[ButtonStyle] = None
    label: Optional[str] = None
    emoji: Optional[dict] = None
    custom_id: Optional[str] = None
    url: Optional[str] = None
    disabled: Optional[bool] = None

    def to_dict(self):
        data = {"type": self.type.value}

        if self.components is not None:
            data["components"] = [c.to_dict() for c in self.components]
        else:
            data["style"] = self.style.value
            data["label"] = self.label

            if self.url:
                data["url"] = self.url
            else:
                data["custom_id"] = self.custom_id

        if self.emoji:
            data["emoji"] = self.emoji
        if self.disabled is not None:
            data["disabled"] = self.disabled

        return data


class ActionRow(Component):
    """ A non-interactive container component for other types of components. """

    def __init__(self, components: List[Component]):
        super().__init__(type=ComponentType.ActionRow, components=components)


class Button(Component):
    """ A non-link button component. """

    def __init__(
        self,
        custom_id: str,
        style: ButtonStyle,
        label: str = "",
        emoji: Optional[dict] = None,
        disabled: bool = False,
    ):
        super().__init__(
            type=ComponentType.Button,
            custom_id=custom_id,
            style=style,
            label=label or None,
            emoji=emoji,
            disabled=disabled,
        )


class LinkButton(Component):
    """ A link button component. """

    def __init__(
        self,
        url: str,
        style: ButtonStyle,
        label: str = "",
        emoji: Optional[dict] = None,
        disabled: bool = False,
    ):
        super().__init__(
            type=ComponentType.Button,
            url=url,
            style=style,
            label=label or None,
            emoji=emoji,
            disabled=disabled,
        )
