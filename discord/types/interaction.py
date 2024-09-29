# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2021-present mccoderpy

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations

from typing import (
    Dict,
    List,
    Union
)

from typing_extensions import (
    Literal,
    NotRequired,
    TypedDict
)

from .channel import PartialChannel
from .guild import Role
from .message import (
    ActionRow,
    Attachment,
    ComponentType,
    Message,
    PartialMessage
)
from .snowflake import SnowflakeID
from .user import BaseUser, MemberWithUser, PartialMember

__all__ = (
    'AuthorizingIntegrationOwners',
    'PingInteraction',
    'ApplicationCommandInteraction',
    'ComponentInteraction',
    'ModalSubmitInteraction',
    'ApplicationCommandData',
    'ApplicationCommandInteractionDataOption',
    'MessageComponentData',
    'ModalSubmitData',
    'ResolvedData',
    'Interaction',
    'InteractionData',
)


InteractionType = Literal[1, 2, 3, 4, 5]
ApplicationCommandType = Literal[1, 2, 3]
ContextType = Literal[1, 2, 3]
AppIntegrationType = Literal[1, 2]


class PartialInteractionGuild(TypedDict):
    locale: str
    id: SnowflakeID
    features: List[str]


class ResolvedData(TypedDict):
    users: NotRequired[Dict[SnowflakeID, BaseUser]]
    members: NotRequired[Dict[SnowflakeID, PartialMember]]
    roles: NotRequired[Dict[SnowflakeID, Role]]
    channels: NotRequired[Dict[SnowflakeID, PartialChannel]]
    messages: NotRequired[Dict[SnowflakeID, PartialMessage]]
    attachments: NotRequired[Dict[SnowflakeID, Attachment]]


class ApplicationCommandInteractionDataOption(TypedDict):
    name: str
    type: ApplicationCommandType
    value: NotRequired[Union[str, int, float, bool]]
    options: NotRequired[List[ApplicationCommandInteractionDataOption]]
    focused: NotRequired[Literal[True]]


class ApplicationCommandData(TypedDict):
    id: SnowflakeID
    name: str
    type: ApplicationCommandType
    resolved: NotRequired[ResolvedData]
    options: NotRequired[List[ApplicationCommandInteractionDataOption]]
    guild_id: NotRequired[SnowflakeID]
    target_id: NotRequired[SnowflakeID]


class MessageComponentData(TypedDict):
    custom_id: str
    component_type: ComponentType
    values: NotRequired[List[str]]


class ModalSubmitData(TypedDict):
    custom_id: str
    values: List[ActionRow]


class PingInteraction(TypedDict):
    type: Literal[1]
    id: SnowflakeID
    application_id: SnowflakeID


class AuthorizingIntegrationOwners(TypedDict):
    Literal['0']: NotRequired[SnowflakeID]  # Guild ID or 0 in a DM with the Bot
    Literal['1']: NotRequired[SnowflakeID]  # User ID


class BaseInteraction(TypedDict):
    id: SnowflakeID
    application_id: SnowflakeID
    token: str
    version: int
    locale: str
    authorizing_integration_owners: AppIntegrationType
    context: NotRequired[ContextType]
    guild_id: NotRequired[SnowflakeID]
    channel_id: NotRequired[SnowflakeID]
    channel: NotRequired[PartialChannel]
    guild: NotRequired[PartialInteractionGuild]
    user: NotRequired[BaseUser]
    member: NotRequired[MemberWithUser]
    app_permissions: NotRequired[str]
    guild_locale: NotRequired[str]


class ApplicationCommandInteraction(BaseInteraction, final=False):
    type: Literal[1, 3]
    data: ApplicationCommandData

    
class ComponentInteraction(BaseInteraction, final=False):
    type: Literal[2]
    data: MessageComponentData
    message: Message


class ModalSubmitInteraction(BaseInteraction, final=False):
    type: Literal[4]
    data: ModalSubmitData


Interaction = Union[ApplicationCommandInteraction, ComponentInteraction, ModalSubmitInteraction]
InteractionData = Union[ApplicationCommandData, MessageComponentData, ModalSubmitData]
