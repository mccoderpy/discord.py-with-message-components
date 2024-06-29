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
    Optional,
    Union
)
from typing_extensions import (
    TypedDict,
    NotRequired,
    Literal
)

from .snowflake import SnowflakeID
from .emoji import PartialEmoji
from .channel import ChannelType, ThreadChannel
from .appinfo import PartialAppInfo
from .user import BaseUser, User, WebhookUser, PartialMember


__all__ = (
    'ActionRow',
    'Button',
    'SelectMenu',
    'SelectOption',
    'DefaultValue',
    'TextInput',
    'MessageComponent',
    'Attachment',
    'PartialEmoji',
    'Reaction',
    'Embed',
    'PartialMessage',
    'RoleSubscriptionData',
    'Message',
    'MessageReference',
    'MessageActivity',
    'MessageInteraction',
    'Modal'
)


ComponentType = Literal[1, 2, 3, 4, 5, 6, 7, 8]
ButtonStyle = Literal[1, 2, 3, 4, 5, 6]
TextInputStyle = Literal[1, 2]
SelectDefaultValueType = Literal['user', 'role', 'channel']
MessageType = Literal[
    0,  # Default
    1,  # Recipient Add
    2,  # Recipient Remove
    3,  # Call
    4,  # Channel Name Change
    5,  # Channel Icon Change
    6,  # Channel Pin
    7,  # Guild Member Join
    8,  # User Premium Guild Subscription
    9,  # User Premium Guild Subscription Tier 1
    10,  # User Premium Guild Subscription Tier 2
    11,  # User Premium Guild Subscription Tier 3
    12,  # Channel Follow Add
    14,  # Guild Discovery Disqualified
    15,  # Guild Discovery Requalified
    16,  # Guild Discovery Grace Period Initial Warning
    17,  # Guild Discovery Grace Period Final Warning
    18,  # Thread Created
    19,  # Reply
    20,  # Chatinput Command
    21,  # Thread Starter Message
    22,  # Guild Invite Reminder
    23,  # Context Menu Command
    24,  # Automod Action
    25,  # Role Subscription Purchase
    26,  # Interaction Premium Upsell
    27,  # Stage start
    28,  # Stage end
    29,  # Stage speaker change
    31,  # Stage topic change
    32  # Guild application premium subscription
]
EmbedType = Literal['rich', 'image', 'video', 'gifv', 'article', 'link']
MessageActivityType = Literal[1, 2, 3, 5]
StickerFormatType = Literal[1, 2, 3, 4]
ReactionType = Literal[1, 2]


class ActionRow(TypedDict):
    type: Literal[1]
    components: List[MessageComponent]


class Button(TypedDict):
    type: Literal[2]
    style: ButtonStyle
    label: str
    emoji: NotRequired[PartialEmoji]
    custom_id: NotRequired[str]
    url: NotRequired[str]
    disabled: NotRequired[bool]
    sku_id: NotRequired[int]


class DefaultValue(TypedDict):
    id: SnowflakeID
    type: SelectDefaultValueType


class SelectMenu(TypedDict):
    type: Literal[3, 5, 6, 7, 8]
    custom_id: str
    options: NotRequired[List[SelectOption]]
    channel_types: NotRequired[List[ChannelType]]
    placeholder: NotRequired[str]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]
    default_values: NotRequired[List[DefaultValue]]


class SelectOption(TypedDict):
    label: str
    value: str
    description: NotRequired[str]
    emoji: NotRequired[PartialEmoji]
    default: NotRequired[Literal[True]]


class TextInput(TypedDict):
    type: Literal[4]
    custom_id: str
    style: TextInputStyle
    label: str
    min_length: NotRequired[int]
    max_length: NotRequired[int]
    required: NotRequired[bool]
    value: NotRequired[str]
    placeholder: NotRequired[str]


MessageComponent = Union[Button, SelectMenu, TextInput]


class Attachment(TypedDict):
    id: SnowflakeID
    filename: str
    description: NotRequired[str]
    content_type: NotRequired[str]
    size: int
    url: str
    proxy_url: str
    height: NotRequired[Optional[int]]
    width: NotRequired[Optional[int]]
    ephemeral: NotRequired[Literal[True]]
    duration_secs: NotRequired[float]
    waveform: NotRequired[str]


class PartialMessage(TypedDict):
    id: SnowflakeID
    channel_id: SnowflakeID
    guild_id: NotRequired[SnowflakeID]


class EmbedFooter(TypedDict):
    text: str
    icon_url: NotRequired[str]
    proxy_icon_url: NotRequired[str]


class EmbedImage(TypedDict):
    url: str
    proxy_url: NotRequired[str]
    height: NotRequired[int]
    width: NotRequired[int]


class EmbedThumbnail(TypedDict):
    url: str
    proxy_url: NotRequired[str]
    height: NotRequired[int]
    width: NotRequired[int]


class EmbedVideo(TypedDict):
    url: NotRequired[str]
    proxy_url: NotRequired[str]
    height: NotRequired[int]
    width: NotRequired[int]


class EmbedProvider(TypedDict):
    name: NotRequired[str]
    url: NotRequired[str]


class EmbedAuthor(TypedDict):
    name: str
    url: NotRequired[str]
    icon_url: NotRequired[str]
    proxy_icon_url: NotRequired[str]


class EmbedField(TypedDict):
    name: str
    value: str
    inline: NotRequired[bool]


class Embed(TypedDict):
    title: NotRequired[str]
    type: EmbedType
    description: NotRequired[str]
    url: NotRequired[str]
    timestamp: NotRequired[str]
    color: NotRequired[int]
    footer: NotRequired[EmbedFooter]
    image: NotRequired[EmbedImage]
    thumbnail: NotRequired[EmbedThumbnail]
    video: NotRequired[EmbedVideo]
    provider: NotRequired[EmbedProvider]
    author: NotRequired[EmbedAuthor]
    fields: NotRequired[List[EmbedField]]


class ReactionCountDetails(TypedDict):
    normal: int
    burst: int


class Reaction(TypedDict):
    count: int
    burst_count: NotRequired[int]
    count_details: NotRequired[ReactionCountDetails]
    me: bool
    emoji: PartialEmoji
    type: Literal[1, 2]
    burst: NotRequired[bool]  # As burst reactions api is still subject to change this might be removed in the future
    message_id: NotRequired[SnowflakeID]
    channel_id: NotRequired[SnowflakeID]
    user_id: NotRequired[SnowflakeID]



class ChannelMention(TypedDict):
    id: SnowflakeID
    guild_id: SnowflakeID
    type: ChannelType
    name: str


class MessageReference(TypedDict):
    message_id: NotRequired[SnowflakeID]
    channel_id: NotRequired[SnowflakeID]
    guild_id: NotRequired[SnowflakeID]
    fail_if_not_exists: NotRequired[bool]


class MessageActivity(TypedDict):
    type: MessageActivityType
    party_id: NotRequired[str]


class MessageInteraction(TypedDict):
    id: SnowflakeID
    type: Literal[1]
    name: str
    user: BaseUser
    member: NotRequired[PartialMember]


class StickerItem(TypedDict):
    id: SnowflakeID
    name: str
    format_type: StickerFormatType


class RoleSubscriptionData(TypedDict):
    role_subscription_listing_id: SnowflakeID
    tier_name: str
    total_months_subscribed: int
    is_renewal: bool


class Message(PartialMessage):
    author: Union[User, WebhookUser]
    content: str
    timestamp: str
    edited_timestamp: Optional[str]
    tts: bool
    mention_everyone: bool
    mentions: List[User]
    mention_roles: List[SnowflakeID]
    mention_channels: NotRequired[List[ChannelMention]]
    attachments: List[Attachment]
    embeds: List[Embed]
    reactions: NotRequired[List[Reaction]]
    nonce: NotRequired[Union[int, str]]
    pinned: bool
    webhook_id: NotRequired[SnowflakeID]
    type: MessageType
    activity: NotRequired[MessageActivity]
    application: NotRequired[PartialAppInfo]
    application_id: NotRequired[SnowflakeID]
    message_reference: NotRequired[MessageReference]
    flags: NotRequired[int]
    referenced_message: NotRequired[Optional[Message]]
    interaction: NotRequired[MessageInteraction]
    thread: NotRequired[ThreadChannel]
    components: NotRequired[List[ActionRow]]
    sticker_items: NotRequired[List[StickerItem]]
    position: NotRequired[int]
    role_subscription_data: NotRequired[RoleSubscriptionData]


class Modal(TypedDict):
    title: str
    custom_id: str
    components: List[ActionRow]
