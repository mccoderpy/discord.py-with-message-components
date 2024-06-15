# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz & (c) 2021-present mccoderpy

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

from .enums import UserFlags

from typing import (
    Union,
    Dict,
    Tuple,
    Iterator,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from typing import Self

__all__ = (
    'SystemChannelFlags',
    'ChannelFlags',
    'MessageFlags',
    'PublicUserFlags',
    'GuildMemberFlags',
    'Intents',
    'MemberCacheFlags',
    'ApplicationFlags',
    'SKUFlags',
)


class flag_value:
    def __init__(self, func):
        self.name: str = func.__name__
        self.flag: int = func(None)
        self.__doc__: str = func.__doc__

    def __get__(self, instance: BaseFlags, owner) -> Union[Self, bool]:
        if instance is None:
            return self
        return instance._has_flag(self.flag)

    def __set__(self, instance: BaseFlags, value: bool) -> None:
        instance._set_flag(self.flag, value)

    def __repr__(self) -> str:
        return '<flag_value flag={.flag!r}>'.format(self)

    def __str__(self) -> str:
        return self.name


class alias_flag_value(flag_value):
    pass


def fill_with_flags(*, inverted=False):
    def decorator(cls):
        cls.VALID_FLAGS = {
            name: value.flag
            for name, value in cls.__dict__.items()
            if isinstance(value, flag_value)
        }

        if inverted:
            max_bits = max(cls.VALID_FLAGS.values()).bit_length()
            cls.DEFAULT_VALUE = -1 + (2 ** max_bits)
        else:
            cls.DEFAULT_VALUE = 0

        return cls
    return decorator


# n.b. flags must inherit from this and use the decorator above
class BaseFlags:
    DEFAULT_VALUE: int
    VALID_FLAGS: Dict[str, int]
    __slots__ = ('value',)

    def __init__(self, **kwargs):
        self.value = self.DEFAULT_VALUE
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError('%r is not a valid flag name.' % key)
            setattr(self, key, value)

    @classmethod
    def _from_value(cls, value) -> Self:
        self = cls.__new__(cls)
        self.value = value
        return self

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return '<%s value=%s>' % (self.__class__.__name__, self.value)

    def __iter__(self) -> Iterator[Tuple[str, bool]]:
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, alias_flag_value):
                continue

            if isinstance(value, flag_value):
                yield name, self._has_flag(value.flag)

    def _has_flag(self, o) -> bool:
        return (self.value & o) == o

    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value |= o
        elif toggle is False:
            self.value &= ~o
        else:
            raise TypeError('Value to set for %s must be a bool.' % self.__class__.__name__)


@fill_with_flags(inverted=True)
class SystemChannelFlags(BaseFlags):
    r"""Wraps up a Discord system channel flag value.

    Similar to :class:`Permissions`\, the properties provided are two way.
    You can set and retrieve individual bits using the properties as if they
    were regular bools. This allows you to edit the system flags easily.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.
        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

    Attributes
    -----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """
    __slots__ = ()

    # For some reason the flags for system channels are "inverted"
    # ergo, if they're set then it means "suppress" (off in the GUI toggle)
    # Since this is counter-intuitive from an API perspective and annoying
    # these will be inverted automatically

    def _has_flag(self, o: int) -> bool:
        return (self.value & o) != o

    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value &= ~o
        elif toggle is False:
            self.value |= o
        else:
            raise TypeError('Value to set for SystemChannelFlags must be a bool.')

    @flag_value
    def join_notifications(self):
        """:class:`bool`: Returns ``True`` if the system channel is used for member join notifications."""
        return 1

    @flag_value
    def premium_subscriptions(self):
        """:class:`bool`: Returns ``True`` if the system channel is used for Nitro boosting notifications."""
        return 2

    @flag_value
    def guild_reminder_notifications(self):
        """:class:`bool`: Returns ``True`` if the system channel is used for server setup tips."""
        return 4

    @flag_value
    def join_notification_replies(self):
        """:class:`bool`: Returns ``True`` if sticker reply buttons should show under member join messages."""
        return 8

    @flag_value
    def role_subscription_purchase_notifications(self):
        """:class:`bool`: Returns ``True`` if the system channel is used for role subscription purchase and
        renewal notifications."""
        return 16

    @flag_value
    def role_subscription_purchase_notification_replies(self):
        """:class:`bool`: Returns ``True`` if sticker reply buttons should show under role subscription purchase and
        renewal messages."""
        return 32


@fill_with_flags()
class ChannelFlags(BaseFlags):
    r"""Wraps up a Discord Channel flag value"""
    __slots__ = ()

    @flag_value
    def removed_from_guild_feed(self):
        """:class:`bool`: Returns ``True`` if the channel is removed from the guild's home feed/from highlights."""
        return 1 << 0

    @alias_flag_value
    def removed_from_home(self):
        """:class:`bool`: An alias to :attr:`removed_from_guild_feed`."""
        return 1 << 0

    @flag_value
    def pinned(self):
        """:class:`bool`: Returns ``True`` if the channel is a :class:`ForumPost` pinned at the top of the parent forum."""
        return 1 << 1

    @flag_value
    def removed_from_active_now(self):
        """:class:`bool`: Returns ``True`` if the channel is removed from the active now section in the guild's feed."""
        return 1 << 2

    @flag_value
    def require_tags(self):
        """
        :class:`bool`:
        Returns ``True`` if this channel is a :class:`ForumChannel` that requires at least one tag when creating a post.
        """
        return 1 << 4

    @flag_value
    def is_spam(self):
        """:class:`bool`: Returns ``True`` if the channel is marked as spam."""
        return 1 << 5

    @flag_value
    def is_resource_channel(self):
        """:class:`bool`: Returns ``True`` if the channel is a resource channel."""
        return 1 << 7

    @flag_value
    def clyde_ai(self):
        """:class:`bool`: Returns ``True`` if clyde has access to this thread.

            .. experiment:: Clyde, Discord's AI Chatbot
                :article: 13066317497239-Clyde-Discord-s-AI-Chatbot
        """
        return 1 << 8

    # TODO: add IS_SCHEDULED_FOR_DELETION (1 << 9) flag when we get more info on it

    @flag_value
    def is_media_channel(self):
        """:class:`bool`: Returns ``True`` if the channel is a media channel."""
        return 1 << 10

    @flag_value
    def summaries_disabled(self):
        """:class:`bool`: Returns ``True`` if AI summaries are disabled for this channel.

            .. experiment:: AI powered summaries
                :article: 12926016807575-Summaries-AI
        """
        return 1 << 11

    # TODO: add APPLICATION_SHELF_CONSENT (1 << 12) flag when we get more info on it

    @flag_value
    def is_role_subscription_template_preview_channel(self):
        """:class:`bool`: Returns ``True`` if the channel is part of a role subscription template preview.

            .. experiment:: Role Subscription Template
        """
        return 1 << 13

    # TODO: add IS_BROADCASTING (1 << 14) flag when we get more info on it

    @flag_value
    def hide_media_download_options(self):
        """:class:`bool`: Returns ``True`` embedding media download options is disabled.

        .. note::
            Available only for media channels.
    """
        return 1 << 15


@fill_with_flags()
class MessageFlags(BaseFlags):
    r"""Wraps up a Discord Message flag value.

    See :class:`SystemChannelFlags`.

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.
        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

    .. versionadded:: 1.3

    Attributes
    -----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """
    __slots__ = ()

    @flag_value
    def crossposted(self):
        """:class:`bool`: Returns ``True`` if the message is the original crossposted message."""
        return 1

    @flag_value
    def is_crossposted(self):
        """:class:`bool`: Returns ``True`` if the message was crossposted from another channel."""
        return 2

    @flag_value
    def suppress_embeds(self):
        """:class:`bool`: Returns ``True`` if the message's embeds have been suppressed."""
        return 4

    @flag_value
    def source_message_deleted(self):
        """:class:`bool`: Returns ``True`` if the source message for this crosspost has been deleted."""
        return 8

    @flag_value
    def urgent(self):
        """:class:`bool`: Returns ``True`` if the source message is an urgent message.

        An urgent message is one sent by Discord Trust and Safety.
        """
        return 16

    @flag_value
    def has_thread(self):
        """:class:`bool`: Returns ``True`` if the source message is associated with a thread.

        This message has an associated thread, with the same id as the message.
        """
        return 32

    @flag_value
    def ephemeral(self):
        """:class:`bool`: Returns ``True`` if the message ist ephemeral (hidden).

        This message is only visible to the user who invoked the Interaction.
        """
        return 64

    @flag_value
    def loading(self):
        """:class:`bool`: Returns ``True`` if the message is an interaction response and the bot is "thinking".

        This message is an interaction response and the bot is "thinking"
        """
        return 128

    @flag_value
    def failed_to_mention_some_roles_in_thread(self):
        """:class:`bool`: Returns ``True`` if the message failed to mention some roles and add their members to the thread."""
        return 256
    
    @flag_value
    def show_link_not_discord_warning(self):
        """:class:`bool`: Returns ``True`` if the message should show a warning that the link may not be safe.
        
        .. note::
            Although this gets set by Discord for some embeds, and we receive a :func:`~discord.on_message_edit` event, it is not officially documented by Discord.
            It's in the client but not used anywhere.
        """
        
        return 1024
    
    @flag_value
    def suppress_notifications(self):
        """:class:`bool`: Returns ``True`` if the message is "silent".
        
        The user(s) will still see a mention in the channel, but no push or desktop notification will be sent.
        """
        return 4096
    
    @flag_value
    def is_voice_message(self):
        """:class:`bool`: Returns ``True`` if the message is a voice message."""
        return 8192


@fill_with_flags()
class PublicUserFlags(BaseFlags):
    r"""Wraps up the Discord User Public flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two PublicUserFlags are equal.
        .. describe:: x != y

            Checks if two PublicUserFlags are not equal.
        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

    .. versionadded:: 1.4

    Attributes
    -----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    __slots__ = ()

    @flag_value
    def staff(self):
        """:class:`bool`: Returns ``True`` if the user is a Discord Employee."""
        return UserFlags.staff.value

    @flag_value
    def partner(self):
        """:class:`bool`: Returns ``True`` if the user is a Discord Partner."""
        return UserFlags.partner.value

    @flag_value
    def hypesquad(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Events member."""
        return UserFlags.hypesquad.value

    @flag_value
    def bug_hunter(self):
        """:class:`bool`: Returns ``True`` if the user is a Bug Hunter"""
        return UserFlags.bug_hunter.value

    @flag_value
    def hypesquad_bravery(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Bravery member."""
        return UserFlags.hypesquad_bravery.value

    @flag_value
    def hypesquad_brilliance(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Brilliance member."""
        return UserFlags.hypesquad_brilliance.value

    @flag_value
    def hypesquad_balance(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Balance member."""
        return UserFlags.hypesquad_balance.value

    @flag_value
    def early_supporter(self):
        """:class:`bool`: Returns ``True`` if the user is an Early Supporter."""
        return UserFlags.early_supporter.value

    @flag_value
    def team_user(self):
        """:class:`bool`: Returns ``True`` if the user is a Team User."""
        return UserFlags.team_user.value

    @flag_value
    def system(self):
        """:class:`bool`: Returns ``True`` if the user is a system user (i.e. represents Discord officially)."""
        return UserFlags.system.value

    @flag_value
    def bug_hunter_level_2(self):
        """:class:`bool`: Returns ``True`` if the user is a Bug Hunter Level 2"""
        return UserFlags.bug_hunter_level_2.value

    @flag_value
    def verified_bot(self):
        """:class:`bool`: Returns ``True`` if the user is a Verified Bot."""
        return UserFlags.verified_bot.value

    @flag_value
    def verified_bot_developer(self):
        """:class:`bool`: Returns ``True`` if the user is an Early Verified Bot Developer."""
        return UserFlags.verified_bot_developer.value

    @alias_flag_value
    def early_verified_bot_developer(self):
        """:class:`bool`: An alias for :attr:`verified_bot_developer`.

        .. versionadded:: 1.5
        """
        return UserFlags.verified_bot_developer.value

    @flag_value
    def certified_moderator(self):
        """:class:`bool`: Returns ``True`` if the user is an Discord Certified Moderator."""
        return UserFlags.certified_moderator.value

    @flag_value
    def bot_http_interactions(self):
        """:class:`bool`: Returns ``True`` if a bot-user uses only HTTP interactions and is shown in the online member list"""
        return UserFlags.bot_http_interactions.value

    @flag_value
    def spammer(self):
        """:class:`bool`: Returns ``True`` if the user is flagged as a spammer by discord."""
        return UserFlags.spammer.value

    @flag_value
    def active_developer(self):
        """:class:`bool`: Returns ``True`` if the user is a developer of an active discord application."""
        return UserFlags.active_developer.value

    def all(self):
        """List[:class:`UserFlags`]: Returns all public flags the user has."""
        return [public_flag for public_flag in UserFlags if self._has_flag(public_flag.value)]


@fill_with_flags()
class GuildMemberFlags(BaseFlags):
    r"""Wraps up the Discord Guild Member flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two GuildMemberFlags are equal.
        .. describe:: x != y

            Checks if two GuildMemberFlags are not equal.
        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

    Attributes
    -----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """
    
    __slots__ = ()
    
    @flag_value
    def rejoined(self):
        """:class:`bool`: Returns :obj:`True` if the member has left and rejoined the guild"""
        return 1 << 0
    
    @flag_value
    def completed_onboarding(self):
        """:class:`bool`: Returns :obj:`True` if the member has completed onboarding"""
        return 1 << 1
    
    @flag_value
    def bypasses_verification(self):
        """:class:`bool`: Returns :obj:`True` if the member is exempt from guild verification requirements
        
        .. note::
            This flag is editable and allows a member who does not meet verification requirements to participate in a
            server.

            This requires either:

             - :attr:`~discord.Permissions.manage_guild` OR
             - :attr:`~discord.Permissions.manage_roles` OR
             - :attr:`~discord.Permissions.moderate_members` AND :attr:`~discord.Permissions.kick_members` AND
                :attr:`~discord.Permissions.ban_members` permissions.
        """
        return 1 << 2
    
    @flag_value
    def started_onboarding(self):
        """:class:`bool`: Returns :obj:`True` if the member has started onboarding"""
        return 1 << 3


@fill_with_flags()
class Intents(BaseFlags):
    r"""Wraps up a Discord gateway intent flag.

    Similar to :class:`Permissions`\, the properties provided are two way.
    You can set and retrieve individual bits using the properties as if they
    were regular bools.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    This is used to disable certain gateway features that are unnecessary to
    run your bot. To make use of this, it is passed to the ``intents`` keyword
    argument of :class:`Client`.

    .. versionadded:: 1.5

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.
        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

    Attributes
    -----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    __slots__ = ()

    def __init__(self, **kwargs):
        self.value = self.DEFAULT_VALUE
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError('%r is not a valid flag name.' % key)
            setattr(self, key, value)

    @classmethod
    def all(cls) -> Intents:
        """A factory method that creates a :class:`Intents` with everything enabled."""
        bits = max(cls.VALID_FLAGS.values()).bit_length()
        value = ((1 << bits) - 1) & ~(1 << 17 | 1 << 18 | 1 << 19)
        self = cls.__new__(cls)
        self.value = value
        return self

    @classmethod
    def none(cls) -> Intents:
        """A factory method that creates a :class:`Intents` with everything disabled."""
        self = cls.__new__(cls)
        self.value = self.DEFAULT_VALUE
        return self

    @classmethod
    def default(cls) -> Intents:
        """A factory method that creates a :class:`Intents` with everything enabled
        except :attr:`presences`, :attr:`members` and :attr:`message_content` (privileged intents).
        """
        self = cls.all()
        self.presences = False
        self.members = False
        self.message_content = False
        return self

    @flag_value
    def guilds(self):
        """:class:`bool`: Whether guild related events are enabled.

        This corresponds to the following events:

        - :func:`on_guild_join`
        - :func:`on_guild_remove`
        - :func:`on_guild_available`
        - :func:`on_guild_unavailable`
        - :func:`on_guild_channel_update`
        - :func:`on_guild_channel_create`
        - :func:`on_guild_channel_delete`
        - :func:`on_guild_channel_pins_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Client.guilds`
        - :class:`Guild` and all its attributes.
        - :meth:`Client.get_channel`
        - :meth:`Client.get_all_channels`

        It is highly advisable to leave this intent enabled for your bot to function.
        """
        return 1 << 0

    @flag_value
    def members(self):
        """:class:`bool`: Whether guild member related events are enabled.

        This corresponds to the following events:

        - :func:`on_member_join`
        - :func:`on_member_remove`
        - :func:`on_member_update` (nickname, roles)
        - :func:`on_user_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :meth:`Client.get_all_members`
        - :meth:`Guild.chunk`
        - :meth:`Guild.fetch_members`
        - :meth:`Guild.get_member`
        - :attr:`Guild.members`
        - :attr:`Member.roles`
        - :attr:`Member.nick`
        - :attr:`Member.premium_since`
        - :attr:`User.name`
        - :attr:`User.avatar` (:attr:`User.avatar_url` and :meth:`User.avatar_url_as`)
        - :attr:`User.discriminator`

        For more information go to the :ref:`member intent documentation <need_members_intent>`.

        .. note::

            Currently, this requires opting in explicitly via the developer portal as well.
            Bots in over 100 guilds will need to apply to Discord for verification.
        """
        return 1 << 1

    @flag_value
    def bans(self):
        """:class:`bool`: Whether guild ban related events are enabled.

        This corresponds to the following events:

        - :func:`on_member_ban`
        - :func:`on_member_unban`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 2

    @flag_value
    def emojis(self):
        """:class:`bool`: Whether guild emoji related events are enabled.

        This corresponds to the following events:

        - :func:`on_guild_emojis_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Emoji`
        - :meth:`Client.get_emoji`
        - :meth:`Client.emojis`
        - :attr:`Guild.emojis`
        """
        return 1 << 3

    @flag_value
    def integrations(self):
        """:class:`bool`: Whether guild integration related events are enabled.

        This corresponds to the following events:

        - :func:`on_guild_integrations_update`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 4

    @flag_value
    def webhooks(self):
        """:class:`bool`: Whether guild webhook related events are enabled.

        This corresponds to the following events:

        - :func:`on_webhooks_update`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 5

    @flag_value
    def invites(self):
        """:class:`bool`: Whether guild invite related events are enabled.

        This corresponds to the following events:

        - :func:`on_invite_create`
        - :func:`on_invite_delete`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 6

    @flag_value
    def voice_states(self):
        """:class:`bool`: Whether guild voice state related events are enabled.

        This corresponds to the following events:

        - :func:`on_voice_state_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`VoiceChannel.members`
        - :attr:`VoiceChannel.voice_states`
        - :attr:`Member.voice`
        """
        return 1 << 7

    @flag_value
    def presences(self):
        """:class:`bool`: Whether guild presence related events are enabled.

        This corresponds to the following events:

        - :func:`on_member_update` (activities, status)

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Member.activities`
        - :attr:`Member.status`
        - :attr:`Member.raw_status`

        For more information go to the :ref:`presence intent documentation <need_presence_intent>`.

        .. note::

            Currently, this requires opting in explicitly via the developer portal as well.
            Bots in over 100 guilds will need to apply to Discord for verification.
        """
        return 1 << 8

    @alias_flag_value
    def messages(self):
        """:class:`bool`: Whether guild and direct message related events are enabled.

        This is a shortcut to set or get both :attr:`guild_messages` and :attr:`dm_messages`.

        This corresponds to the following events:

        - :func:`on_message` (both guilds and DMs)
        - :func:`on_message_edit` (both guilds and DMs)
        - :func:`on_message_delete` (both guilds and DMs)
        - :func:`on_raw_message_delete` (both guilds and DMs)
        - :func:`on_raw_message_edit` (both guilds and DMs)
        - :func:`on_private_channel_create`

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Message`
        - :attr:`Client.cached_messages`

        Note that due to an implicit relationship this also corresponds to the following events:

        - :func:`on_reaction_add` (both guilds and DMs)
        - :func:`on_reaction_remove` (both guilds and DMs)
        - :func:`on_reaction_clear` (both guilds and DMs)
        """
        return (1 << 9) | (1 << 12)

    @flag_value
    def guild_messages(self):
        """:class:`bool`: Whether guild message related events are enabled.

        See also :attr:`dm_messages` for DMs or :attr:`messages` for both.

        This corresponds to the following events:

        - :func:`on_message` (only for guilds)
        - :func:`on_message_edit` (only for guilds)
        - :func:`on_message_delete` (only for guilds)
        - :func:`on_raw_message_delete` (only for guilds)
        - :func:`on_raw_message_edit` (only for guilds)

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Message`
        - :attr:`Client.cached_messages` (only for guilds)

        Note that due to an implicit relationship this also corresponds to the following events:

        - :func:`on_reaction_add` (only for guilds)
        - :func:`on_reaction_remove` (only for guilds)
        - :func:`on_reaction_clear` (only for guilds)
        """
        return 1 << 9

    @flag_value
    def dm_messages(self):
        """:class:`bool`: Whether direct message related events are enabled.

        See also :attr:`guild_messages` for guilds or :attr:`messages` for both.

        This corresponds to the following events:

        - :func:`on_message` (only for DMs)
        - :func:`on_message_edit` (only for DMs)
        - :func:`on_message_delete` (only for DMs)
        - :func:`on_raw_message_delete` (only for DMs)
        - :func:`on_raw_message_edit` (only for DMs)
        - :func:`on_private_channel_create`

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Message`
        - :attr:`Client.cached_messages` (only for DMs)

        Note that due to an implicit relationship this also corresponds to the following events:

        - :func:`on_reaction_add` (only for DMs)
        - :func:`on_reaction_remove` (only for DMs)
        - :func:`on_reaction_clear` (only for DMs)
        """
        return 1 << 12

    @alias_flag_value
    def reactions(self):
        """:class:`bool`: Whether guild and direct message reaction related events are enabled.

        This is a shortcut to set or get both :attr:`guild_reactions` and :attr:`dm_reactions`.

        This corresponds to the following events:

        - :func:`on_reaction_add` (both guilds and DMs)
        - :func:`on_reaction_remove` (both guilds and DMs)
        - :func:`on_reaction_clear` (both guilds and DMs)
        - :func:`on_raw_reaction_add` (both guilds and DMs)
        - :func:`on_raw_reaction_remove` (both guilds and DMs)
        - :func:`on_raw_reaction_clear` (both guilds and DMs)

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Message.reactions` (both guild and DM messages)
        """
        return (1 << 10) | (1 << 13)

    @flag_value
    def guild_reactions(self):
        """:class:`bool`: Whether guild message reaction related events are enabled.

        See also :attr:`dm_reactions` for DMs or :attr:`reactions` for both.

        This corresponds to the following events:

        - :func:`on_reaction_add` (only for guilds)
        - :func:`on_reaction_remove` (only for guilds)
        - :func:`on_reaction_clear` (only for guilds)
        - :func:`on_raw_reaction_add` (only for guilds)
        - :func:`on_raw_reaction_remove` (only for guilds)
        - :func:`on_raw_reaction_clear` (only for guilds)

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Message.reactions` (only for guild messages)
        """
        return 1 << 10

    @flag_value
    def dm_reactions(self):
        """:class:`bool`: Whether direct message reaction related events are enabled.

        See also :attr:`guild_reactions` for guilds or :attr:`reactions` for both.

        This corresponds to the following events:

        - :func:`on_reaction_add` (only for DMs)
        - :func:`on_reaction_remove` (only for DMs)
        - :func:`on_reaction_clear` (only for DMs)
        - :func:`on_raw_reaction_add` (only for DMs)
        - :func:`on_raw_reaction_remove` (only for DMs)
        - :func:`on_raw_reaction_clear` (only for DMs)

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Message.reactions` (only for DM messages)
        """
        return 1 << 13

    @alias_flag_value
    def typing(self):
        """:class:`bool`: Whether guild and direct message typing related events are enabled.

        This is a shortcut to set or get both :attr:`guild_typing` and :attr:`dm_typing`.

        This corresponds to the following events:

        - :func:`on_typing` (both guilds and DMs)

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return (1 << 11) | (1 << 14)

    @flag_value
    def guild_typing(self):
        """:class:`bool`: Whether guild and direct message typing related events are enabled.

        See also :attr:`dm_typing` for DMs or :attr:`typing` for both.

        This corresponds to the following events:

        - :func:`on_typing` (only for guilds)

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 11

    @flag_value
    def dm_typing(self):
        """:class:`bool`: Whether guild and direct message typing related events are enabled.

        See also :attr:`guild_typing` for guilds or :attr:`typing` for both.

        This corresponds to the following events:

        - :func:`on_typing` (only for DMs)

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 14

    @flag_value
    def message_content(self):
        """:class:`bool`: Whether to receive the content, embeds, attachments and components of a message.

        .. note::

            The bot will still receive these fields when the message is in a privat chat with the bot,
            or the bot is mentioned in the message.

        This corresponds to the following events:

        - :func:`on_message` (content, embeds, attachments, components)
        - :func:`on_message_edit` (content, embeds, attachments, components)
        - :func:`on_raw_message_edit` (cached_message)
        - :func:`on_message_delete` (content, embeds, attachments, components)
        - :func:`on_raw_message_delete` (cached_message)
        - :func:`on_bulk_message_delete` (content, embeds, attachments, components)
        - :func:`on_raw_bulk_message_delete` (cached_messages)
        - :func:`on_auto_moderation_action` (content, matched_content)

        This also corresponds to the following attributes and classes:

        - :attr:`Message.content`
        - :attr:`Message.embeds`
        - :attr:`Message.attachments`
        - :attr:`Message.components`

        For more information go to the `message-content intent documentation <https://support-dev.discord.com/hc/en-us/articles/4404772028055>`_ .

        .. note::

            Currently, this requires opting in explicitly via the developer portal as well.
            Bots in over 100 guilds will need to apply to Discord for verification.
        """
        return  1 << 15

    @flag_value
    def scheduled_events(self):
        """:class:`bool`: Whether to receive events related to creating, updating and deleting scheduled events.
        Also, whether to receive events when a user is added or removed (interested).

        This corresponds to the following events:

        - :func:`on_scheduled_event_create`
        - :func:`on_scheduled_event_update`
        - :func:`on_scheduled_event_delete`
        - :func:`on_scheduled_event_user_add`
        - :func:`on_scheduled_event_user_remove`
        """
        return 1 << 16

    @flag_value
    def auto_moderation_configurations(self):
        """:class:`bool`: Whether to receive events related to creating, updating and deleting auto moderation rules.

        This corresponds to the following events:

        - :func:`on_auto_moderation_rule_create`
        - :func:`on_auto_moderation_rule_update`
        - :func:`on_auto_moderation_rule_delete`
        """
        return 1 << 20

    @flag_value
    def auto_moderation_actions(self):
        """:class:`bool`: Whether to receive events when auto moderation actions are taken.

        This corresponds to the following event:

        - :func:`on_auto_moderation_action`
        """
        return 1 << 21


@fill_with_flags()
class MemberCacheFlags(BaseFlags):
    """Controls the library's cache policy when it comes to members.

    This allows for finer grained control over what members are cached.
    Note that the bot's own member is always cached. This class is passed
    to the ``member_cache_flags`` parameter in :class:`Client`.

    Due to a quirk in how Discord works, in order to ensure proper cleanup
    of cache resources it is recommended to have :attr:`Intents.members`
    enabled. Otherwise the library cannot know when a member leaves a guild and
    is thus unable to cleanup after itself.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    The default value is all flags enabled.

    .. versionadded:: 1.5

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.
        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

    Attributes
    -----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    __slots__ = ()

    def __init__(self, **kwargs):
        bits = max(self.VALID_FLAGS.values()).bit_length()
        self.value = (1 << bits) - 1
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError('%r is not a valid flag name.' % key)
            setattr(self, key, value)

    @classmethod
    def all(cls) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` with everything enabled."""
        bits = max(cls.VALID_FLAGS.values()).bit_length()
        value = (1 << bits) - 1
        self = cls.__new__(cls)
        self.value = value
        return self

    @classmethod
    def none(cls) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` with everything disabled."""
        self = cls.__new__(cls)
        self.value = self.DEFAULT_VALUE
        return self

    @property
    def _empty(self):
        return self.value == self.DEFAULT_VALUE

    @flag_value
    def online(self):
        """:class:`bool`: Whether to cache members with a status.

        For example, members that are part of the initial ``GUILD_CREATE``
        or become online at a later point. This requires :attr:`Intents.presences`.

        Members that go offline are no longer cached.
        """
        return 1

    @flag_value
    def voice(self):
        """:class:`bool`: Whether to cache members that are in voice.

        This requires :attr:`Intents.voice_states`.

        Members that leave voice are no longer cached.
        """
        return 2

    @flag_value
    def joined(self):
        """:class:`bool`: Whether to cache members that joined the guild
        or are chunked as part of the initial log in flow.

        This requires :attr:`Intents.members`.

        Members that leave the guild are no longer cached.
        """
        return 4

    @classmethod
    def from_intents(cls, intents):
        """A factory method that creates a :class:`MemberCacheFlags` based on
        the currently selected :class:`Intents`.

        Parameters
        ------------
        intents: :class:`Intents`
            The intents to select from.

        Returns
        ---------
        :class:`MemberCacheFlags`
            The resulting member cache flags.
        """

        self = cls.none()
        if intents.members:
            self.joined = True
        if intents.presences:
            self.online = True
        if intents.voice_states:
            self.voice = True

        if not self.joined and self.online and self.voice:
            self.voice = False

        return self

    def _verify_intents(self, intents):
        if self.online and not intents.presences:
            raise ValueError('MemberCacheFlags.online requires Intents.presences enabled')

        if self.voice and not intents.voice_states:
            raise ValueError('MemberCacheFlags.voice requires Intents.voice_states')

        if self.joined and not intents.members:
            raise ValueError('MemberCacheFlags.joined requires Intents.members')

        if not self.joined and self.voice and self.online:
            msg = 'Setting both MemberCacheFlags.voice and MemberCacheFlags.online requires MemberCacheFlags.joined ' \
                  'to properly evict members from the cache.'
            raise ValueError(msg)

    @property
    def _voice_only(self):
        return self.value == 2

    @property
    def _online_only(self):
        return self.value == 1


@fill_with_flags()
class ApplicationFlags(BaseFlags):
    r"""Wraps up the flags of an application.

        .. container:: operations

            .. describe:: x == y

                Checks if two ApplicationFlags are equal.
            .. describe:: x != y

                Checks if two ApplicationFlags are not equal.
            .. describe:: hash(x)

                Return the flag's hash.
            .. describe:: iter(x)

                Returns an iterator of ``(name, value)`` pairs. This allows it
                to be, for example, constructed as a dict or a list of pairs.
                Note that aliases are not shown.


        Attributes
        -----------
        value: :class:`int`
            The raw value. This value is a bit array field of a 53-bit integer
            representing the currently available flags. You should query
            flags via the properties rather than using this raw value.
    """
    @flag_value
    def managed_emoji(self):
        """:class:`bool`: Returns ``True`` if the application is a managed emoji.
        
        .. versionadded:: 2.0
        """
        return 1 << 2

    @flag_value
    def group_dm_create(self):
        """:class:`bool`: Returns ``True`` if the application can create group DMs.
        
        .. versionadded:: 2.0
        """
        return 1 << 5

    @flag_value
    def application_auto_moderation_rule_create_badge(self):
        """:class:`bool`: Returns ``True`` if the application uses the Auto Moderation API.

        .. versionadded:: 2.0
        """
        return 1 << 6

    @flag_value
    def rpc_has_connected(self):
        """:class:`bool`: Returns ``True`` if the application has connected to RPC.
        
        .. versionadded:: 2.0
        """
        return 1 << 11
    
    @flag_value
    def gateway_presence(self):
        """:class:`bool`: Returns ``True`` if the application is approved for the privileged gateway presence-intent."""
        return 1 << 12

    @flag_value
    def gateway_presence_limited(self):
        """:class:`bool`: Returns ``True`` if the privileged gateway presence-intent
        is enabled in the application in the developer-portal.
        """
        return 1 << 13

    @flag_value
    def gateway_guild_members(self):
        """:class:`bool`: Returns ``True`` if the application is approved
        for the privileged gateway guild-members-intent.
        """
        return 1 << 14

    @flag_value
    def gateway_guild_members_limited(self):
        """:class:`bool`: Returns ``True`` if the privileged gateway guild-members-intent
        is enabled in the application in the developer-portal.
        """
        return 1 << 15

    @flag_value
    def verification_pending_guild_limit(self):
        """:class:`bool: Returns ``True`` if this application has reached the required number of guilds
        to apply for verification. (76+ Guilds)
        """
        return 1 << 16

    @flag_value
    def embedded(self):
        """:class:`bool`: Returns ``True`` if this application could have embedded invites.(usually  voice-activity's)
        """
        return 1 << 17

    @flag_value
    def gateway_message_content(self):
        """:class:`bool`: Returns ``True`` if the application is approved
        for the privileged gateway message-content-intent.
        """
        return 1 << 18

    @flag_value
    def gateway_message_content_limited(self):
        """:class:`bool`: Returns ``True`` if the privileged gateway message-content-intent
        is enabled in the application in the developer-portal.
        """
        return 1 << 19

    @flag_value
    def application_commands_badge(self):
        """:class:`bool`: Returns ``True`` if the app has at least one global `application-command <application_commands>`_ registered."""
        return 1 << 23

    @flag_value
    def active_application(self):
        """:class:`bool`: Returns ``True`` is an active application (e.g. has at leas one app command executed in the last 30 days)."""
        return 1 << 24


@fill_with_flags()
class SKUFlags(BaseFlags):
    """Wraps up the flags of a :class:`SKU`.

    .. container:: operations

        .. describe:: x == y

            Checks if two SKUFlags are equal.
        .. describe:: x != y

            Checks if two SKUFlags are not equal.
        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

    Attributes
    -----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    @flag_value
    def premium_purchase(self):
        """:class:`bool`: A premium purchase SKU"""
        return 1 << 0

    @flag_value
    def has_free_premium_content(self):
        """:class:`bool`: An SKU containing free premium content"""
        return 1 << 1

    @flag_value
    def available(self):
        """:class:`bool`: Whether the SKU is currently available for purchase"""
        return 1 << 2

    # @flag_value
    # def premium_and_distribution(self):
    #     """:class:`bool`: Undocumented"""
    #     return 1 << 3

    # @flag_value
    # def sticker(self):
    #     """":class:`bool`: Undocumented"""
    #     return 1 << 4

    @flag_value
    def guild_role(self):
        """:class:`bool`: A role that can be purchased for a guild"""
        return 1 << 5

    @flag_value
    def available_for_subscription_gifting(self):
        """:class:`bool`: An SKU that can be purchased as a gift for others."""
        return 1 << 6

    @flag_value
    def app_guild_subscription(self):
        """:class:`bool`: A recurring SKU that can be purchased by a user and applied to a single server.
        Grants access to every user in that server."""
        return 1 << 7

    @flag_value
    def app_user_subscription(self):
        """:class:`bool`: Recurring SKU purchased by a user for themselves.
        Grants access to the purchasing user in every server."""
        return 1 << 8

    # @flag_value
    # def creator_monetization(self):
    #     """:class:`bool`: Undocumented"""
    #     return 1 << 9

    @flag_value
    def guild_product(self):
        """:class:`bool`: A product in the guild store"""
        return 1 << 10

    # @flag_value
    # def user_update_mask(self):
    #     """:class:`bool`: Undocumented"""
    #     return 0 << 0
    #
    # @flag_value
    # def staff_create_subscription_group_listing_mask(self):
    #     """:class:`bool`: Undocumented"""
    #     return 384
