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
    Any,
    List,
    Dict,
    Union,
    Optional,
    TYPE_CHECKING,
    Iterator
)

import datetime
from re import Pattern, compile as _re_compile

from . import utils
from .role import Role
from .object import Object
from .abc import GuildChannel
from .utils import SnowflakeList, MISSING
from .errors import ClientException
from .enums import AutoModEventType, AutoModKeywordPresetType, AutoModActionType, AutoModTriggerType, try_enum


if TYPE_CHECKING:
    from typing_extensions import Self
    from .state import ConnectionState
    from .guild import Guild
    from .user import User
    from .member import Member
    from .types.snowflake import SnowflakeObject


__all__ = (
    'AutoModAction',
    'AutoModTriggerMetadata',
    'AutoModRule',
    'AutoModActionPayload'
)


class AutoModAction:
    """
    Represents an action which will execute whenever a rule is triggered.

    Attributes
    -----------
    type: :class:`AutoModActionType`
        The type of action
    channel_id: :class:`int`
        The channel to which target user content should be logged.

        .. note::
            This field is only present if :attr:`~AutoModAction.type` is :attr:`~AutoModActionType.send_alert_message`
        
    timeout_duration: Union[:class:`int`, :class:`~datetime.timedelta`]
        Duration in seconds (:class:`int`) or a timerange (:class:`~datetime.timedelta`)
        for which the target user should be timeouted.

        **The maximum value is** ``2419200`` **seconds (4 weeks)**

        .. note::
           This field is only present if :attr:`~AutoModAction.type` is :attr:`~AutoModActionType.timeout_user`
    
    custom_message: Optional[:class:`str`]
        Additional explanation that will be shown to target users whenever their message is blocked.
        **Max 150 characters**
        
        .. note::
            This field might only be present if :attr:`~AutoModAction.type` is :attr:`~AutoModActionType.block_message`
    """
    def __init__(self, type: AutoModActionType, **metadata):
        """
        
        Parameters
        -----------
        type: :class:`AutoModActionType`
            The type of action
        
        channel_id: :class:`int`
            The channel to which target user content should be logged.
    
            .. note::
                This field is only required if :attr:`~AutoModAction.type` is
                :attr:`~AutoModActionType.send_alert_message`
            
        timeout_duration: Union[:class:`int`, :class:`datetime.timedelta`]
            Duration in seconds (:class:`int`) or a timerange (:class:`~datetime.timedelta`)
            for which the user should be timeouted.
    
            **The maximum value is** ``2419200`` **seconds (4 weeks)**
    
            .. note::
               This field is only required if :attr:`~AutoModAction.type` is :attr:`~AutoModActionType.timeout_user`
        
        custom_message: Optional[:class:`str`]
            Additional explanation that will be shown to target users whenever their message is blocked.
            **Max 150 characters**
            
            .. note::
                This field is only allowed if :attr:`~AutoModAction.type` is :attr:`~AutoModActionType.block_message`
        
        Raises
        -------
        TypeError
            If the type is :attr:`~AutoModActionType.send_alert_message` and no ``channel_id`` is provided,
            or if the type is :attr:`~AutoModActionType.timeout_user` and no ``timeout_duration`` is provided.
        ValueError
            If the ``custom_message`` is longer than 150 characters,
            or if the ``timeout_duration`` is longer than 4 weeks.
        """
        self.type: AutoModActionType = try_enum(AutoModActionType, type)
        self.metadata = metadata  # maybe we need this later... idk
        
        action_type = self.type  # speedup attribute access
        
        if action_type == AutoModActionType.block_message:
            try:
                custom_message: Optional[str] = metadata['custom_message']
            except KeyError:
                pass
            else:
                if custom_message and len(custom_message) > 150:
                    raise ValueError('The maximum length of the custom message is 150 characters.')
                self.custom_message: Optional[str] = custom_message
            
        elif action_type == AutoModActionType.send_alert_message:
            try:
                self.channel_id: Optional[int] = metadata['channel_id']
            except KeyError:
                raise TypeError('If the type is send_alert_message you must specify a channel_id')
        
        elif action_type == AutoModActionType.timeout_user:
            try:
                timeout_duration: Optional[Union[int, datetime.timedelta]] = metadata['timeout_duration']
            except KeyError:
                raise TypeError('If the type is timeout_user you must specify a timeout_duration')
            else:
                if isinstance(timeout_duration, int):
                    timeout_duration = datetime.timedelta(seconds=timeout_duration)
                if timeout_duration.total_seconds() > 2419200:
                    raise ValueError('The maximum timeout duration is 2419200 seconds (4 weeks).')
                self.timeout_duration: Optional[datetime.timedelta] = timeout_duration

    def to_dict(self) -> Dict[str, Any]:
        base = {
            'type': int(self.type)
        }
        metadata = {}
        if self.type == AutoModActionType.block_message:
            custom_message = getattr(self, 'custom_message', None)
            if custom_message:
                metadata['custom_message'] = self.custom_message
        elif self.type == AutoModActionType.send_alert_message:
            metadata['channel_id'] = self.channel_id
        elif self.type == AutoModActionType.timeout_user:
            metadata['duration_seconds'] = self.timeout_duration
        base['metadata'] = metadata
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        action_type = try_enum(AutoModActionType, data['type'])
        metadata = data['metadata']
        if action_type == AutoModActionType.block_message:
            metadata['custom_message'] = metadata.pop('custom_message', None)
        elif action_type == AutoModActionType.timeout_user:
            metadata['timeout_duration'] = metadata.pop('duration_seconds')
        elif action_type == AutoModActionType.send_alert_message:
            metadata['channel_id'] = int(metadata['channel_id'])
        return cls(action_type, **metadata)


class AutoModTriggerMetadata:
    """Additional data used to determine whether a rule should be triggered.
    Different fields are relevant based on the value of :attr:`AutoModRule.trigger_type`

    Parameters
    -----------
    keyword_filter: Optional[List[:class:`str`]]
        Substrings which will be searched for in content

        .. note::
            This field is only present if :attr:`~AutoModRule.trigger_type` is :attr:`AutoModTriggerType.keyword`

    presets: Optional[List[:class:`AutoModKeywordPresetType`]]
        The internally pre-defined word sets which will be searched for in content

        .. note::
            This field is only present if :attr:`~AutoModRule.trigger_type` is :attr:`AutoModTriggerType.keyword_preset`

    exempt_words: Optional[List[:class:`str`]]
        Substrings which should be excluded from the blacklist.

        .. note::
            This field is only present if :attr:`~AutoModRule.trigger_type` is :attr:`AutoModTriggerType.keyword_preset`

    total_mentions_limit: Optional[:class:`int`]
        Total number of unique role and user mentions allowed per message (Maximum of 50)

        .. note::
            This field is only present if :attr:`~AutoModRule.trigger_type` is :attr:`AutoModTriggerType.mention_spam`

    mention_raid_protection_enabled: Optional[:class:`bool`]
        Whether to automatically detect mention raids

        .. note::
            This field is only present if :attr:`~AutoModRule.trigger_type` is :attr:`AutoModTriggerType.mention_spam`
    """
    def __init__(
            self,
            keyword_filter: Optional[List[str]] = None,
            regex_patterns: Optional[List[Union[str, Pattern]]] = None,
            presets: Optional[List[AutoModKeywordPresetType]] = None,
            exempt_words: Optional[List[str]] = None,
            total_mentions_limit: Optional[int] = None,
            mention_raid_protection_enabled: Optional[bool] = None
    ) -> None:
        """Additional data used to determine whether a rule should be triggered.
        Different fields are relevant based on the value of :attr:`AutoModRule.trigger_type`

        Parameters
        -----------
        keyword_filter: Optional[List[:class:`str`]]
            Substrings which will be searched for in content

            .. note::
                This field is only allowed if :attr:`~AutoModRule.trigger_type` is :attr:`~AutoModTriggerType.keyword`

        regex_patterns: Optional[List[Union[:class:`str`, :class`~re.Pattern`]]]
            Regular expression patterns which will be matched against content
            (Maximum of 10, each max. 260 characters long)

            .. warning::
                Only <Rust `https://docs.rs/regex/latest/regex/`>_ flowered RegEx patterns are currently supported
                by Discord. So things like lookarounds are not allowed as they are not supported in Rust.

            .. note::
                This field is only allowed if :attr:`~AutoModRule.trigger_type` is :attr:`~AutoModTriggerType.keyword`

        presets: Optional[List[:class:`AutoModKeywordPresetType`]]
            The internally pre-defined word sets which will be searched for in content

            .. note::
                This field is only required if :attr:`~AutoModRule.trigger_type` is
                :attr:`~AutoModTriggerType.keyword_preset`

        exempt_words: Optional[List[:class:`str`]]
            Substrings which should be excluded from the blacklist.

            .. note::
                This field is only allowed if :attr:`~AutoModRule.trigger_type` is
                :attr:`~AutoModTriggerType.keyword_preset` :attr:`~AutoModTriggerType.keyword`

        total_mentions_limit: Optional[:class:`int`]
            Total number of unique role and user mentions allowed per message (Maximum of 50)

            .. note::
                This field is only allowed if :attr:`~AutoModRule.trigger_type`
                is :attr:`AutoModTriggerType.mention_spam`

        mention_raid_protection_enabled: Optional[:class:`bool`]
            Whether to automatically detect mention raids

            .. note::
                This field is only allowed if :attr:`~AutoModRule.trigger_type`
                is :attr:`AutoModTriggerType.mention_spam`

        Raises
        -------
        :exc:`TypeError`
            Both of keyword_filter and presets was passed
        """
        if keyword_filter and presets:
            raise TypeError('Only one of keyword_filter or presets are accepted.')
        self.keyword_filter: Optional[List[str]] = keyword_filter or []
        if regex_patterns and presets:
            raise TypeError('regex_patterns can only be used with AutoModRule\'s of type keyword')
        self._regex_patterns: List[Union[str, Pattern]] = regex_patterns or []
        self.presets: List[AutoModKeywordPresetType] = presets or []
        if exempt_words and not (presets or keyword_filter):
            raise TypeError('exempt_words can only be used with keyword_filter or preset')
        self.exempt_words: Optional[List[str]] = exempt_words
        self.total_mentions_limit: Optional[int] = total_mentions_limit
        self.mention_raid_protection_enabled: Optional[bool] = mention_raid_protection_enabled

    @utils.cached_slot_property('_cs_regex_patterns')
    def regex_patterns(self) -> List[Pattern]:
        """List[:class:`~re.Pattern`]: The compiled regex patterns for this rule, if any."""
        return [
            _re_compile(pattern) for pattern in getattr(self, '_regex_patterns', []) if not isinstance(pattern, Pattern)
        ]

    @property
    def prefix_keywords(self) -> Iterator[str]:
        """
        Returns all keywords for words that must start with the keyword.

        .. note::
            This is equal to

            .. code-block:: python3

                for keyword in self.keyword_filter:
                    if keyword[0] != '*' and keyword[-1] == '*':
                        yield keyword
                        
        Yields
        -------
        :class:`str`
            A keyword
        """
        for keyword in self.keyword_filter:
            if keyword[0] != '*' and keyword[-1] == '*':
                yield keyword

    @property
    def suffix_keywords(self) -> Iterator[str]:
        """
        Returns all keywords for words that must end with the keyword.

        .. note::
            This is equal to

            .. code-block:: python3

                for keyword in self.keyword_filter:
                    if keyword[0] == '*' and keyword[-1] != '*':
                        yield keyword

        Yields
        -------
        :class:`str`
            A keyword
        """
        for keyword in self.keyword_filter:
            if keyword[0] != '*' and keyword[-1] == '*':
                yield keyword

    @property
    def anywhere_keywords(self) -> Iterator[str]:
        """
        Returns all keywords which can appear anywhere in a word

        .. note::
            This is equal to

            .. code-block:: python3

                for keyword in self.keyword_filter:
                    if keyword[0] == '*' and keyword[-1] == '*':
                        yield keyword

        Yields
        -------
        :class:`str`
            A keyword
        """
        for keyword in self.keyword_filter:
            if keyword[0] == '*' and keyword[-1] == '*':
                yield keyword

    @property
    def whole_word_keywords(self) -> Iterator[str]:
        """
        Returns all keywords that must occur as a whole in a word or phrase and must be surrounded by spaces.

        .. note::
            This is equal to

            .. code-block:: python3

                for keyword in self.keyword_filter:
                    if keyword[0] != '*' and keyword[-1] != '*':
                        yield keyword

        Yields
        -------
        :class:`str`
            A keyword
        """
        for keyword in self.keyword_filter:
            if keyword[0] != '*' and keyword[-1] != '*':
                yield keyword

    def to_dict(self) -> Dict[str, Any]:
        if self.keyword_filter or self._regex_patterns:
            base = {
                'keyword_filter': self.keyword_filter,
                'regex_patterns': [
                    pattern.pattern if isinstance(pattern, Pattern) else pattern for pattern in self._regex_patterns
                ]
            }
            if self.exempt_words is not None:
                base['allow_list'] = self.exempt_words
            return base
        else:
            if self.presets:
                base = {
                    'presets': [int(p) for p in self.presets]
                }
                if self.exempt_words is not None:
                    base['allow_list'] = self.exempt_words
                return base
            elif self.total_mentions_limit:
                return {
                    'mention_total_limit': self.total_mentions_limit,
                    'mention_raid_protection_enabled': self.mention_raid_protection_enabled
                }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        self = cls.__new__(cls)
        self.presets = presets = data.get('presets')
        if presets:
            self.exempt_words = data.get('allow_list', [])
        else:
            self.keyword_filter = data.get('keyword_filter')
            self._regex_patterns = data.get('regex_patterns')
            self.exempt_words = data.get('allow_list')
        self.total_mentions_limit = data.get('mention_total_limit')
        self.mention_raid_protection_enabled = data.get('mention_raid_protection_enabled')
        return self


class AutoModRule:
    """
    Represents a rule for auto moderation

    .. warning::
        Do not initialize this class directly. Use :meth:`~discord.Guild.create_automod_rule` instead.

    Attributes
    -----------
    id: :class:`int`
        The id of this rule
    guild: :class:`~discord.Guild`
        The guild  this rule belongs to
    name: :class:`str`
        The name of the rule
    creator_id: :class:`int`
        The id of the user which created this rule
    event_type: :class:`AutoModEventType`
        The event which will trigger this rule
    trigger_type: :class:`AutoModEventType`
        The type of content which will trigger the rule
    trigger_metadata: :class:`AutoModTriggerMetadata`
        Additional data used to determine whether a rule should be triggered.
        Different fields are relevant based on the value of :attr:`.trigger_type`.
    actions: List[:class:`AutoModAction`]
        The actions which will execute when the rule is triggered
    enabled: :class:`bool`
        Whether the rule is enabled
    """
    def __init__(
            self,
            state: ConnectionState,
            guild: Guild,
            **data
    ) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self.id: int = int(data['id'])
        self._update(data)

    def _update(self: Self, data) -> Self:
        self.name: str = data['name']
        self.creator_id: int = int(data['creator_id'])
        self.event_type: AutoModEventType = try_enum(AutoModEventType, data['event_type'])
        self.trigger_type: AutoModTriggerType = try_enum(AutoModTriggerType, data['trigger_type'])
        self.trigger_metadata: AutoModTriggerMetadata = AutoModTriggerMetadata.from_dict(data['trigger_metadata'])
        self.actions: List[AutoModAction] = [AutoModAction.from_dict(action) for action in data['actions']]
        self.enabled: bool = data['enabled']
        self._exempt_roles: SnowflakeList = SnowflakeList(map(int, data['exempt_roles']))
        self._exempt_channels: SnowflakeList = SnowflakeList(map(int, data['exempt_channels']))
        return self

    def __repr__(self) -> str:
        return f'<AutoModRule "{self.name}" guild_id={self.guild.id} creator_id={self.creator_id}>'

    @property
    def exempt_roles(self) -> Iterator[Union[Role, Object]]:
        """
        Yields the roles that should not be affected by the rule (Maximum of 20)

        .. note::
            This is equal to

            .. code-block:: python3

                for role_id in self._exempt_roles:
                    role = self.guild.get_role(int(role_id))
                    yield role or Object(int(role_id))

        Yields
        -------
        Union[:class:`~discord.Role`, :class:`~discord.Object`]
            An excluded role or an object with the id if the role is not found
        """
        for role_id in self._exempt_roles:
            role = self.guild.get_role(int(role_id))
            yield role or Object(role_id, type=Role, state=self._state)

    @property
    def exempt_channels(self) -> Iterator[Union[GuildChannel, Object]]:
        """
        Yields the channels that should not be affected by the rule (Maximum of 20)

        .. note::
            This is equal to

            .. code-block:: python3

                for channel_id in self._exempt_channels:
                    channel = self.guild.get_role(int(channel_id))
                    yield channel or Object(channel_id, type=GuildChannel, state=self._state)

        Yields
        -------
        Union[:class:`~discord.Role`, :class:`~discord.Object`]
            An excluded channel or an :class:`~discord.object` with the id if the channel is not found
        """
        for channel_id in self._exempt_channels:
            channel = self.guild.get_role(int(channel_id))
            yield channel or Object(channel_id, type=GuildChannel, state=self._state)
        
    @property
    def creator(self) -> Optional[Member]:
        """
        Returns the creator of the rule

        .. note::
            The :attr:`Intents.members` must be enabled, otherwise this may return `` None``
        
        Raises
        -------
        ClientException:
            If the member is not found and :attr:`~Intents.members` intent is not enabled.
        
        Returns
        --------
        Optional[Member]
            The member, that created the rule.
        """
        creator = self.guild.get_member(self.creator_id)
        # If the member is not found and the members intent is disabled, then raise
        if not creator and not self._state.intents.members:
            raise ClientException('Intents.members must be enabled to use this')
        return creator

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: When the rule was created in UTC"""
        return utils.snowflake_time(self.id)

    async def delete(self, *, reason: Optional[str]) -> None:
        """|coro|

        Deletes the automod rule, this requires the :attr:`~Permissions.manage_server` permission.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting this rule. Shows up in the audit log.

        Raises
        ------
        :exc:`discord.Forbidden`
            The bot is missing permissions to delete the rule
        :exc:`~discord.HTTPException`
            Deleting the rule failed
        """
        await self._state.http.delete_automod_rule(self.guild.id, self.id, reason=reason)

    async def edit(
            self,
            *,
            name: str = MISSING,
            event_type: AutoModEventType = MISSING,
            trigger_type: AutoModTriggerType = MISSING,
            trigger_metadata: AutoModTriggerMetadata = MISSING,
            actions: List[AutoModAction] = MISSING,
            enabled: bool = MISSING,
            exempt_roles: List[SnowflakeObject] = MISSING,
            exempt_channels: List[SnowflakeObject] = MISSING,
            reason: Optional[str] = None,
    ) -> AutoModRule:
        """|coro|

        Edits the automod rule, this requires the :attr:`~Permissions.manage_server` permission.
        
        You only need to provide the parameters you want to edit the.
        
        Parameters
        ----------
        name: :class:`str`
            The name, the rule should have. Only valid if it's not a preset rule.
        event_type: :class:`~discord.AutoModEventType`
            Indicates in what event context a rule should be checked.
        trigger_type: :class:`~discord.AutoModTriggerType`
            Characterizes the type of content which can trigger the rule
        trigger_metadata: :class:`~discord.AutoModTriggerMetadata`
            Additional data used to determine whether a rule should be triggered.
            Different fields are relevant based on the value of :attr:`~AutoModRule.trigger_type`.
        actions: List[:class:`~discord.AutoModAction`]
            The actions which will execute when the rule is triggered.
        enabled: :class:`bool`
            Whether the rule is enabled.
        exempt_roles: List[:class:`.Snowflake`]
            Up to 20 :class:`~discord.Role`'s, that should not be affected by the rule.
        exempt_channels: List[:class:`.Snowflake`]
            Up to 50 :class:`~discord.TextChannel`/:class:`~discord.VoiceChannel`/:class:`~discord.StageChannel`'s,
            that should not be affected by the rule.
        reason: Optional[:class:`str`]
            The reason for editing the rule. Shows up in the audit log.

        Raises
        -------
        :exc:`discord.Forbidden`
            The bot is missing permissions to edit the rule
        :exc:`~discord.HTTPException`
            Editing the rule failed

        Returns
        -------
        :class:`AutoModRule`
            The updated rule on success.
        """
        payload = {}

        if name is not MISSING:
            payload['name'] = name

        if event_type is not MISSING:
            payload['event_type'] = event_type.value

        if trigger_type is not MISSING:
            payload['trigger_type'] = trigger_type.value
        
        if trigger_metadata is not MISSING:
            payload['trigger_metadata'] = trigger_metadata.to_dict()

        if actions is not MISSING:
            payload['actions'] = [action.to_dict() for action in actions]
        else:
            actions = self.actions if exempt_channels is not MISSING else MISSING
            
        if enabled is not MISSING:
            payload['enabled'] = enabled
        
        if exempt_roles is not MISSING:
            payload['exempt_roles'] = [str(r.id) for r in exempt_roles]
        
        if exempt_channels is not MISSING:
            payload['exempt_channels'] = _exempt_channels = [str(c.id) for c in exempt_channels]
        else:
            _exempt_channels = self._exempt_channels
            
        if actions is not MISSING:
            for action in actions:  # Add the channels where messages should be logged to, to the exempted channels
                if action.type.send_alert_message:
                    channel_id = str(action.channel_id)
                    if channel_id not in _exempt_channels:
                        _exempt_channels.append(channel_id)
        
        data = await self._state.http.edit_automod_rule(self.guild.id, self.id, fields=payload, reason=reason)
        return self._update(data)


class AutoModActionPayload:
    """Represents the payload for an :func:`on_automod_action` event

    Attributes
    -----------
    guild_id: :class:`int`
        The id of the guild in which action was executed
    action: :class:`AutoModAction`
        The action which was executed
    rule_id: :class:`int`
        The id of the rule which action belongs to
    rule_trigger_type: :class:`~discord.AutoModTriggerType`
        The trigger type of rule which was triggered
    user_id: :class:`int`
        The id of the user which generated the content which triggered the rule
    channel_id: Optional[:class:`int`]
        The id of the channel in which user content was posted
    message_id: Optional[:class:`int`]
        The id of any user message which content belongs to

        .. note::
            This wil not exists if message was blocked by automod or content was not part of any message

    alert_system_message_id: Optional[:class:`int`]
        The id of any system auto moderation messages posted as the result of this action

        .. note::
            This will only exist if the :attr:`~AutoModAction.type` of the :attr:`~AutoModActionPayload.action` is ``send_alert_message``

    content: :class:`str`
        The user generated text content

        .. important::
            The :attr:`Intents.message_content` intent is required to get a non-empty value for this field

    matched_keyword: :class:`str`
        The word ot phrase configured in the rule that triggered the rule
    matched_content: :class:`str`
        The substring in :attr:`~AutoModActionPayload.content` that triggered the rule

         .. important::
            The :attr:`~Intents.message_content` intent is required to get a non-empty value for this field

    """
    __slots__ = (
        '_state', 'guild_id', 'action', 'rule_id', 'rule_trigger_type', 'user_id', 'channel_id', 'message_id',
        'alert_system_message_id', 'content', 'matched_keyword', 'matched_content'
    )

    def __init__(self, state: ConnectionState, data: Dict[str, Any]) -> None:
        self._state = state
        self.guild_id: int = int(data['guild_id'])
        self.action: AutoModAction = AutoModAction.from_dict(data['action'])
        self.rule_id: int = int(data['rule_id'])
        self.rule_trigger_type: AutoModTriggerType = try_enum(AutoModTriggerType, data['rule_trigger_type'])
        self.user_id: int = int(data['user_id'])
        self.channel_id: Optional[int] = int(data.get('channel_id', 0))
        self.message_id: Optional[int] = int(data.get('message_id', 0))
        self.alert_system_message_id: Optional[int] = int(data.get('alert_system_message_id', 0))
        self.content: str = data['content']
        self.matched_keyword: Optional[str] = data.get('matched_keyword', None)
        self.matched_content: Optional[str] = data.get('matched_content', None)

    @property
    def guild(self) -> Guild:
        """
        The guild in which action was executed

        Returns
        --------
        :class:`Guild`
            The guild object
        """
        return self._state._get_guild(self.guild_id)

    @property
    def channel(self) -> Optional[GuildChannel]:
        """
        The channel in which user content was posted, if any.

        Returns
        --------
        Optional[:class:`abc.GuildChannel`]
            The :class:`TextChannel`, :class:`VoiceChannel` or :class:`ThreadChannel` the user content was posted in.
        """
        return self.guild.get_channel(self.channel_id)

    @property
    def user(self) -> Optional[User]:
        """
        The user which content triggered the rule

        .. note::
            This can return ``None`` if the user is not in the cache

        Returns
        --------
        :class:`.User`
            The user that triggered the rule
        """
        return self._state.get_user(self.user_id)

    @property
    def member(self) -> Optional[Member]:
        """
        The corresponding :class:`Member` of the :attr:`~AutoModActionPayload.user` in the :attr:`~AutoModActionPayload.guild`.

        .. note::
            :attr:`Intents.members` must be enabled in order to use this

        Raises
        -------
        ClientException:
            If the member is not found and :attr:`~Intents.members` intent is not enabled.

        Returns
        --------
        Optional[Member]:
            The guild member
        """
        member = self.guild.get_member(self.user_id)
        # If the member is not found and the members intent is disabled, then raise
        if not member and not self._state.intents.members:
            raise ClientException('Intents.members must be enabled to use this')
        return member
