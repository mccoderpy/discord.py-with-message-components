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
    List,
    Optional
)

from typing_extensions import (
    Literal,
    NotRequired,
    TypedDict
)

from .snowflake import SnowflakeID
from .user import BaseUser
from .emoji import PartialEmoji

__all__ = (
    'ChannelType',
    'OverwriteType',
    'Overwrite',
    'PartialChannel',
    'GuildChannel',
    'VoiceChannel',
    'StageChannel',
    'StageInstance',
    'ForumTag',
    'ForumChannel',
    'DefaultReactionEmoji',
    'ThreadMetadata',
    'DMChannel',
    'GroupChannel'
)

ChannelType = Literal[0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16]
OverwriteType = Literal[0, 1]
StagePrivacyLevel = Literal[1, 2]


class Overwrite(TypedDict):
    id: SnowflakeID
    type: OverwriteType
    allow: str
    deny: str


class GuildChannel(TypedDict):
    id: SnowflakeID
    type: ChannelType
    name: NotRequired[Optional[str]]
    flags: NotRequired[int]
    position: NotRequired[int]
    parent_id: NotRequired[SnowflakeID]
    permission_overwrites: NotRequired[List[Overwrite]]


class ThreadMetadata(TypedDict):
    archived: bool
    auto_archive_duration: int
    archive_timestamp: str
    locked: bool
    invitable: NotRequired[bool]
    create_timestamp: NotRequired[Optional[str]]


class DefaultReactionEmoji(TypedDict):
    emoji_id: NotRequired[SnowflakeID]
    emoji_name: str


class ForumTag(TypedDict):
    id: SnowflakeID
    name: str
    emoji_name: NotRequired[str]
    emoji_id: NotRequired[SnowflakeID]
    moderated: NotRequired[bool]


class PartialChannel(TypedDict):
    id: SnowflakeID
    type: ChannelType
    name: NotRequired[Optional[str]]
    # TODO: What fields are missing here?


class DMChannel(PartialChannel):
    recipients: NotRequired[List[BaseUser]]
    last_message_id: NotRequired[Optional[SnowflakeID]]


class GroupChannel(DMChannel, total=False):
    owner_id: SnowflakeID
    managed: NotRequired[bool]
    icon: Optional[str]


class VoiceChannel(GuildChannel, total=False):
    bitrate: int
    user_limit: int
    video_quality_mode: int
    rate_limit_per_user: int
    nsfw: bool
    icon_emoji: Optional[PartialEmoji]
    rtc_region: Optional[str]
    status: Optional[str]


class StageChannel(VoiceChannel, total=False):
    privacy_level: int
    discoverable_disabled: bool


class StageInstance(TypedDict):
    id: SnowflakeID
    guild_id: SnowflakeID
    channel_id: SnowflakeID
    topic: str
    privacy_level: StagePrivacyLevel
    discoverable_disabled: NotRequired[bool]
    guild_scheduled_event_id: Optional[SnowflakeID]


class ForumChannel(GuildChannel, total=False):
    nsfw: bool
    default_auto_archive_duration: int
    default_rate_limit_per_user: int
    rate_limit_per_user: int
    default_thread_rate_limit_per_user: int
    default_sort_order: int
    default_forum_layout: int
    default_reaction_emoji: DefaultReactionEmoji
    icon_emoji: Optional[PartialEmoji]
    topic: Optional[str]
    template: Optional[bool]
