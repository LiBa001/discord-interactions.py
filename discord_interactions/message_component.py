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

from dataclasses import dataclass
from enum import Enum

from .models import PartialEmoji


class ComponentType(Enum):
    ActionRow = 1  # A container for other components
    Button = 2  # A clickable button
    SelectMenu = 3  # A select menu for picking from choices
    TextInput = 4  # A text input object


class ButtonStyle(Enum):
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5


class TextInputStyle(Enum):
    Short = 1
    Paragraph = 2


@dataclass()
class SelectOption:
    label: str
    value: str
    description: str = None
    emoji: PartialEmoji = None
    default: bool = None

    def to_dict(self):
        data = {"label": self.label, "value": self.value}

        if self.description:
            data["description"] = self.description
        if self.emoji:
            data["emoji"] = PartialEmoji.from_any(self.emoji).to_dict()
        if self.default is not None:
            data["default"] = self.default


@dataclass()
class Component:
    """Interactive component on a message object."""

    type: ComponentType

    # valid for action rows only
    components: list[Component] = None

    # valid for any component but action rows
    custom_id: str = None

    # valid for buttons and select menus
    disabled: bool = None

    # valid for buttons and text input
    style: ButtonStyle | TextInputStyle = None
    label: str = None

    # valid for buttons only
    emoji: PartialEmoji | str = None
    url: str = None

    # valid for select menus and text input
    placeholder: str = None

    # valid for select menus only
    options: list[SelectOption] = None
    min_values: int = None
    max_values: int = None

    # valid for text input only
    min_length: int = None
    max_length: int = None
    required: bool = True
    value: str = None

    def to_dict(self):
        data = {"type": self.type.value}

        match self.type:
            case ComponentType.ActionRow:
                data["components"] = [c.to_dict() for c in self.components]
            case ComponentType.Button:
                data["style"] = self.style.value
                data["label"] = self.label

                if self.url:
                    data["url"] = self.url
                else:
                    data["custom_id"] = self.custom_id
            case ComponentType.SelectMenu:
                data["custom_id"] = self.custom_id
                data["options"] = [o.to_dict() for o in self.options]
                if self.placeholder is not None:
                    data["placeholder"] = self.placeholder
                if self.min_values is not None:
                    data["min_values"] = self.min_values
                if self.max_values is not None:
                    data["max_values"] = self.min_values
            case ComponentType.TextInput:
                data |= {
                    "custom_id": self.custom_id,
                    "style": self.style.value,
                    "label": self.label,
                    "required": self.required,
                }
                if self.min_length is not None:
                    data["min_length"] = self.min_length
                if self.max_length is not None:
                    data["max_length"] = self.max_length
                if self.value is not None:
                    data["value"] = self.value
                if self.placeholder is not None:
                    data["placeholder"] = self.placeholder

        if self.emoji:
            data["emoji"] = PartialEmoji.from_any(self.emoji).to_dict()
        if self.disabled is not None:
            data["disabled"] = self.disabled

        return data


class ActionRow(Component):
    """A non-interactive container component for other types of components."""

    def __init__(self, *components: Component):
        super().__init__(type=ComponentType.ActionRow, components=list(components))


class Button(Component):
    """A non-link button component."""

    def __init__(
        self,
        custom_id: str,
        style: ButtonStyle = ButtonStyle.PRIMARY,
        label: str = "",
        emoji: PartialEmoji | str = None,
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
    """A link button component."""

    def __init__(
        self,
        url: str,
        style: ButtonStyle,
        label: str = "",
        emoji: PartialEmoji | str = None,
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


class SelectMenu(Component):
    """A select menu component."""

    def __init__(
        self,
        custom_id: str,
        options: list[SelectOption],
        placeholder: str = None,
        min_values: int = 0,
        max_values: int = 25,
        disabled: bool = False,
    ):
        super().__init__(
            type=ComponentType.SelectMenu,
            custom_id=custom_id,
            options=options,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
        )

    def add_option(
        self,
        label: str,
        value: str,
        description: str = "",
        emoji: PartialEmoji = None,
        default: bool = False,
    ):
        self.options.append(SelectOption(label, value, description, emoji, default))
        return self


class TextInput(Component):
    """A text input component."""

    def __init__(
        self,
        custom_id: str,
        style: TextInputStyle,
        label: str,
        min_length: int = None,
        max_length: int = None,
        required: bool = True,
        value: str = None,
        placeholder: str = None,
    ):
        super().__init__(
            type=ComponentType.TextInput,
            custom_id=custom_id,
            style=style,
            label=label,
            min_length=min_length,
            max_length=max_length,
            required=required,
            value=value,
            placeholder=placeholder,
        )
