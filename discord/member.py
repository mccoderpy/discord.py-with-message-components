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

import datetime
import inspect
import itertools
import sys
from operator import attrgetter

from typing import (
    Optional,
    Union,
    List,
    Dict,
    Coroutine,
    Tuple,
    TYPE_CHECKING,
    Any,
    Iterable,
    Callable,
    Type,
    TypeVar,
)

from typing_extensions import Literal

from . import utils, abc
from .asset import Asset
from .user import BaseUser, User, _BaseUser
from .activity import ActivityTypes, create_activity
from .permissions import Permissions
from .voice_client import VoiceProtocol, VoiceClient
from .enums import Status, try_enum
from .flags import GuildMemberFlags, PublicUserFlags
from .colour import Colour
from .object import Object
from .errors import NotInVoiceChannel

if TYPE_CHECKING:
    from .types.user import (
        User as UserData,
        MemberWithUser,
        UserWithMember,
        PartialMember
    )
    from .role import Role
    from .state import ConnectionState
    from .guild import Guild
    from .activity import BaseActivity, Spotify
    from .message import Message
    from .channel import ThreadChannel, VoiceChannel, StageChannel, DMChannel

    VocalGuildChannel = Union[VoiceChannel, StageChannel]


MISSING = utils.MISSING
T = TypeVar('T')
VP = TypeVar('VP', bound=VoiceProtocol)

__all__ = (
    'VoiceState',
    'Member',
)


class VoiceState:
    """Represents a Discord user's voice state.
    
    .. container:: operations

        .. describe:: await voice(...)
            Acts as a shortcut to :meth:`VoiceProtocol.connect`.
            Raises :exc:`NotInVoiceChannel` if :attr:`channel` is ``None``.
    
    Attributes
    ------------
    deaf: :class:`bool`
        Indicates if the user is currently deafened by the guild.
    mute: :class:`bool`
        Indicates if the user is currently muted by the guild.
    self_mute: :class:`bool`
        Indicates if the user is currently muted by their own accord.
    self_deaf: :class:`bool`
        Indicates if the user is currently deafened by their own accord.
    self_stream: :class:`bool`
        Indicates if the user is currently streaming via 'Go Live' feature.

        .. versionadded:: 1.3

    self_video: :class:`bool`
        Indicates if the user is currently broadcasting video.
    suppress: :class:`bool`
        Indicates if the user is suppressed from speaking.

        Only applies to stage channels.

        .. versionadded:: 1.7

    requested_to_speak_at: Optional[:class:`datetime.datetime`]
        A datetime object that specifies the date and time in UTC that the member
        requested to speak. It will be ``None`` if they are not requesting to speak
        anymore or have been accepted to speak.

        Only applicable to stage channels.

        .. versionadded:: 1.7

    afk: :class:`bool`
        Indicates if the user is currently in the AFK channel in the guild.
    channel: Optional[Union[:class:`VoiceChannel`, :class:`StageChannel`]]
        The voice channel that the user is currently connected to. ``None`` if the user
        is not currently in a voice channel.
    """

    __slots__ = ('session_id', 'deaf', 'mute', 'self_mute',
                 'self_stream', 'self_video', 'self_deaf', 'afk', 'channel',
                 'requested_to_speak_at', 'suppress')

    if TYPE_CHECKING:
        session_id: Optional[str]
        self_mute: bool
        self_deaf: bool
        self_stream: bool
        self_video: bool
        afk: bool
        mute: bool
        deaf: bool
        suppress: bool
        requested_to_speak_at: Optional[datetime.datetime]

    def __init__(self, *, data, channel: Optional[VocalGuildChannel] = None) -> None:
        self.session_id = data.get('session_id')
        self._update(data, channel)

    def _update(self, data, channel: Optional[VocalGuildChannel]) -> None:
        self.self_mute = data.get('self_mute', False)
        self.self_deaf = data.get('self_deaf', False)
        self.self_stream = data.get('self_stream', False)
        self.self_video = data.get('self_video', False)
        self.afk = data.get('suppress', False)
        self.mute = data.get('mute', False)
        self.deaf = data.get('deaf', False)
        self.suppress = data.get('suppress', False)
        self.requested_to_speak_at = utils.parse_time(data.get('request_to_speak_timestamp'))
        self.channel = channel

    def __repr__(self):
        attrs = [
            ('self_mute', self.self_mute),
            ('self_deaf', self.self_deaf),
            ('self_stream', self.self_stream),
            ('suppress', self.suppress),
            ('requested_to_speak_at', self.requested_to_speak_at),
            ('channel', self.channel)
        ]
        return f"<{self.__class__.__name__} {' '.join('%s=%r' % t for t in attrs)}>"

    def __call__(
            self,
            *,
            timeout: Optional[float] = 60.0,
            reconnect: bool = True,
            cls: VP = VoiceClient
    ) -> Coroutine[None, None, VP]:
        channel = self.channel
        if not channel:
            raise NotInVoiceChannel()
        return channel.connect(timeout=timeout, reconnect=reconnect, cls=cls)


def flatten_user(*types):
    def decorator(cls):
        for attr, value in itertools.chain(*(t.__dict__.items() for t in types)):
            # ignore private/special methods
            if attr.startswith('_'):
                continue

            # don't override what we already have
            if attr in cls.__dict__:
                continue

            # if it's a slotted attribute or a property, redirect it
            # slotted members are implemented as member_descriptors in Type.__dict__
            if not hasattr(value, '__annotations__'):
                getter = attrgetter(f'_user.{attr}')
                setattr(cls, attr, property(getter, doc=f'Equivalent to :attr:`User.{attr}`'))
            else:
                # Technically, this can also use attrgetter
                # However I'm not sure how I feel about "functions" returning properties
                # It probably breaks something in Sphinx.
                # probably a member function by now
                def generate_function(x):
                    # We want sphinx to properly show coroutine functions as coroutines
                    if inspect.iscoroutinefunction(value):
                        async def general(self, *args, **kwargs):
                            return await getattr(self._user, x)(*args, **kwargs)
                    else:
                        def general(self, *args, **kwargs):
                            return getattr(self._user, x)(*args, **kwargs)

                    general.__name__ = x
                    return general

                func = generate_function(attr)
                func = utils.copy_doc(value)(func)
                setattr(cls, attr, func)

        return cls
    return decorator


@flatten_user(BaseUser, User)
class Member(abc.Messageable, _BaseUser):
    """Represents a Discord member to a :class:`Guild`.

    This implements a lot of the functionality of :class:`User`.

    .. container:: operations

        .. describe:: x == y

            Checks if two members are equal.
            Note that this works with :class:`User` instances too.

        .. describe:: x != y

            Checks if two members are not equal.
            Note that this works with :class:`User` instances too.

        .. describe:: hash(x)

            Returns the member's hash.

        .. describe:: str(x)

            Returns the members :attr:`username` if :attr:`is_migrated` is true, else the member's name with discriminator.

            .. note::

                When the migration is complete, this will always return the :attr:`username`.

    Attributes
    ----------
    joined_at: Optional[:class:`datetime.datetime`]
        A datetime object that specifies the date and time in UTC that the member joined the guild.
        If the member left and rejoined the guild, this will be the latest date. In certain cases, this can be ``None``.
    activities: Tuple[Union[:class:`BaseActivity`, :class:`Spotify`]]
        The activities that the user is currently doing.

        .. note::

            Due to a Discord API limitation, a user's Spotify activity may not appear
            if they are listening to a song with a title longer
            than 128 characters. See :old-issue:`1738` for more information.

    guild: :class:`Guild`
        The guild that the member belongs to.
    nick: Optional[:class:`str`]
        The guild specific nickname of the user.
    pending: :class:`bool`
        Whether the member is pending member verification.

        .. versionadded:: 1.6
    premium_since: Optional[:class:`datetime.datetime`]
        A datetime object that specifies the date and time in UTC when the member used their
        Nitro boost on the guild, if available. This could be ``None``.
    """

    __slots__ = ('_roles', 'joined_at', 'premium_since', '_client_status',
                 'activities', 'guild', '_flags', 'pending', 'nick', 'guild_avatar', 'guild_banner',
                 '_user', '_state', '_communication_disabled_until')

    if TYPE_CHECKING:
        name: str
        username: str
        global_name: str
        id: int
        discriminator: str
        bot: bool
        system: bool
        created_at: datetime.datetime
        default_avatar: str
        avatar: Optional[str]
        dm_channel: Optional[DMChannel]
        create_dm = User.create_dm
        mutual_guilds: List[Guild]
        public_flags: PublicUserFlags
        banner: Optional[str]
        accent_color: Optional[Colour]
        accent_colour: Optional[Colour]
        communication_disabled_until: Optional[datetime.datetime]


    def __init__(self, *, data: MemberWithUser, guild: Guild, state: ConnectionState):
        self._state: ConnectionState = state
        self._user: User = state.store_user(data['user'])
        self.guild: Guild = guild
        self.joined_at: Optional[datetime.datetime] = utils.parse_time(data.get('joined_at'))
        self.premium_since: Optional[datetime.datetime] = utils.parse_time(data.get('premium_since'))
        self._update_roles(data)
        self._client_status: Dict[Optional[str], str] = {None: 'offline'}
        self.activities: Tuple[ActivityTypes, ...] = tuple(map(create_activity, data.get('activities', [])))
        self.nick: Optional[str] = data.get('nick')
        self._flags: int = data.get('flags', 0)
        self.pending: bool = data.get('pending', False)
        self.guild_avatar = data.get('avatar')
        self.guild_banner = data.get('banner')
        self._communication_disabled_until = data.get('communication_disabled_until', None)

    def __str__(self) -> str:
        return str(self._user)

    def __repr__(self) -> str:
        user = self._user
        if not user.is_migrated:
            return f'<Member id={user.id} username={user.username!r} global_name={user.global_name} ' \
                   f'discriminator={user.discriminator!r} bot={user.bot} nick={self.nick!r} guild={self.guild!r}>'
        return f'<Member id={user.id} username={user.username!r} global_name={user.global_name} ' \
               f'bot={user.bot} nick={self.nick!r} guild={self.guild!r}>'

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, _BaseUser) and other.id == self.id

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self._user)

    @property
    def flags(self) -> GuildMemberFlags:
        """:class:`GuildMemberFlags`: Guild specific flags for the member."""
        return GuildMemberFlags._from_value(self._flags)

    @classmethod
    def _from_message(cls, *, message: Message, data: MemberWithUser):
        author = message.author
        data['user'] = author._to_minimal_user_json()
        return cls(data=data, guild=message.guild, state=message._state)

    def _update_from_message(self, data):
        self.joined_at = utils.parse_time(data.get('joined_at'))
        self.premium_since = utils.parse_time(data.get('premium_since'))
        self._update_roles(data)
        self.nick = data.get('nick', None)
        self._flags = data.get('flags', 0)
        self.pending = data.get('pending', False)

    @classmethod
    def _try_upgrade(cls, *,  data: UserWithMember, guild: Guild, state: ConnectionState) -> Union[Member, User]:
        # A User object with a 'member' key
        try:
            member_data: MemberWithUser = data.pop('member')  # type: ignore
        except KeyError:
            return state.store_user(data)
        else:
            member_data['user'] = data
            return cls(data=member_data, guild=guild, state=state)

    @classmethod
    def _from_presence_update(cls, *, data, guild: Guild, state: ConnectionState) -> Tuple[Member, Member]:
        clone = cls(data=data, guild=guild, state=state)
        to_return = cls(data=data, guild=guild, state=state)
        to_return._client_status = {
            sys.intern(key): sys.intern(value)
            for key, value in data.get('client_status', {}).items()
        }
        to_return._client_status[None] = sys.intern(data['status'])
        return to_return, clone

    @classmethod
    def _copy(cls, member: Member) -> Member:
        self = cls.__new__(cls)  # to bypass __init__

        self._roles = utils.SnowflakeList(member._roles, is_sorted=True)
        self.joined_at = member.joined_at
        self.premium_since = member.premium_since
        self._client_status = member._client_status.copy()
        self._communication_disabled_until = member._communication_disabled_until
        self.guild = member.guild
        self.nick = member.nick
        self.guild_avatar = member.guild_avatar
        self.guild_banner = member.guild_banner
        self.pending = member.pending
        self._flags = member._flags
        self.activities = member.activities
        self._state = member._state

        # Reference will not be copied unless necessary by PRESENCE_UPDATE
        # See below
        self._user = member._user
        return self

    async def _get_channel(self) -> DMChannel:
        return await self.create_dm()

    def _update_roles(self, data: PartialMember) -> None:
        self._roles = utils.SnowflakeList(map(int, data.get('roles', [])))

    def _update(self, data: MemberWithUser) -> None:
        # the nickname change is optional,
        # if it isn't in the payload then it didn't change
        try:
            self.nick = data['nick']
        except KeyError:
            pass

        try:
            self.pending = data['pending']
        except KeyError:
            pass
        
        try:
            self._flags = data['flags']
        except KeyError:
            pass
        

        try:
            self._communication_disabled_until = data['communication_disabled_until']
        except KeyError:
            self._communication_disabled_until = None

        self.premium_since = utils.parse_time(data.get('premium_since'))
        self._update_roles(data)

    def _presence_update(self, data, user: Optional[UserData] = None) -> Optional[Tuple[User, User]]:
        self.activities = tuple(map(create_activity, data.get('activities', [])))
        self._client_status = {
            sys.intern(key): sys.intern(value)
            for key, value in data.get('client_status', {}).items()
        }
        self._client_status[None] = sys.intern(data['status'])

        if user:
            return self._update_inner_user(user)

    def _update_inner_user(self, user: UserData) -> Tuple[User, User]:
        u = self._user
        original = (
            u.username,
            u.global_name,
            u.avatar,
            u.avatar_decoration,
            u.discriminator,
            u._public_flags
        )
        if len(user) == 1 and 'id' in user:
            # The user wasn't updated, so we can just ignore this
            return
        # These keys seem to always be available
        modified = (
            user.get('username'),
            user.get('global_name'),
            user.get('avatar'),
            user.get('avatar_decoration'),
            user.get('discriminator', '0'),
            user.get('public_flags', 0)
        )

        if original != modified:
            to_return = User._copy(self._user)
            u.username, u.global_name, u.avatar, u.avatar_decoration, u.discriminator, u._public_flags = modified
            # Signal to dispatch on_user_update
            return to_return, u

    @property
    def status(self) -> Status:
        """:class:`Status`: The member's overall status. If the value is unknown, then it will be a :class:`str` instead."""
        return try_enum(Status, self._client_status[None])

    @property
    def raw_status(self) -> str:
        """:class:`str`: The member's overall status as a string value.

        .. versionadded:: 1.5
        """
        return self._client_status[None]

    @status.setter
    def status(self, value):
        # internal use only
        self._client_status[None] = str(value)

    @property
    def mobile_status(self) ->  Status:
        """:class:`Status`: The member's status on a mobile device, if applicable."""
        return try_enum(Status, self._client_status.get('mobile', 'offline'))

    @property
    def desktop_status(self) -> Status:
        """:class:`Status`: The member's status on the desktop client, if applicable."""
        return try_enum(Status, self._client_status.get('desktop', 'offline'))

    @property
    def web_status(self) -> Status:
        """:class:`Status`: The member's status on the web client, if applicable."""
        return try_enum(Status, self._client_status.get('web', 'offline'))

    def is_on_mobile(self) -> bool:
        """:class:`bool`: A helper function that determines if a member is active on a mobile device."""
        return 'mobile' in self._client_status

    @property
    def colour(self) -> Colour:
        """:class:`Colour`: A property that returns a colour denoting the rendered colour
        for the member. If the default colour is the one rendered then an instance
        of :meth:`Colour.default` is returned.

        There is an alias for this named :attr:`color`.
        """

        roles = self.roles[1:] # remove @everyone

        # highest order of the colour is the one that gets rendered.
        # if the highest is the default colour then the next one with a colour
        # is chosen instead
        for role in reversed(roles):
            if role.colour.value:
                return role.colour
        return Colour.default()

    @property
    def color(self) -> Colour:
        """:class:`Colour`: A property that returns a color denoting the rendered color for
        the member. If the default color is the one rendered then an instance of :meth:`Colour.default`
        is returned.

        There is an alias for this named :attr:`colour`.
        """
        return self.colour

    @property
    def role_ids(self) -> utils.SnowflakeList:
        """:class:`utils.SnowflakeList`: An iterable of :class:`int` contain the ID's of the roles the member has.
        You can use this to check on an efficient way whether a member has a role or not"""
        return self._roles

    @property
    def roles(self) -> List[Role]:
        """List[:class:`Role`]: A :class:`list` of :class:`Role` that the member belongs to. Note
        that the first element of this list is always the default '@everyone'
        role.

        These roles are sorted by their position in the role hierarchy.
        """
        result = []
        g = self.guild
        for role_id in self._roles:
            role = g.get_role(role_id)
            if role:
                result.append(role)
        result.append(g.default_role)
        result.sort()
        return result

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the member."""
        return f'<@!{self.id}>' if self.nick else f'<@{self.id}>'

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name.

        This is either the guild :attr:`nick`, the :attr:`global_name` or the :attr:`username` of the user.
        """
        return self.nick or self.global_name or self.username

    @property
    def guild_avatar_url(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild-specific banner asset for the member if any."""
        return self.guild_avatar_url_as()

    def guild_avatar_url_as(
            self,
            *,
            format: Optional[Literal['jpeg', 'jpg', 'webp', 'png', 'gif']] = None,
            static_format: Literal['jpeg', 'jpg', 'webp', 'png'] = 'webp',
            size: int = 1024
    ) -> Optional[Asset]:
        """Returns an :class:`Asset` for the guild-specific avatar of the member if any, else :obj:`None`.

        The format must be one of 'webp', 'jpeg', or 'png'. The
        size must be a power of 2 between 16 and 4096.

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the avatar to.
        static_format: :class:`str`
            The format to attempt to convert the avatar to if the avatar is animated.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        Optional[:class:`Asset`]
            The resulting CDN asset if any.
        """
        if self.guild_avatar:
            return Asset._from_guild_avatar(self._state, self, static_format=static_format, format=format, size=size)

    def is_guild_avatar_animated(self) -> bool:
        """:class:`bool`: Indicates if the member has an animated guild-avatar."""
        return bool(self.guild_avatar and self.guild_avatar.startswith('a_'))

    @property
    def display_avatar_url(self) -> Asset:
        """:class:`Asset`:
        Returns the displayed avatar of the member.

        This is in the following order:
        - Guild-specific avatar if available
        - User avatar if available
        - Default avatar
         """
        return self.guild_avatar_url or self.avatar_url

    @property
    def display_avatar(self) -> Asset:
        """:class:`Asset`: An alias for :attr:`display_avatar_url`."""
        return self.display_avatar_url

    def display_avatar_url_as(
            self,
            format: Optional[Literal['jpeg', 'jpg', 'webp', 'png', 'gif']] = None,
            static_format: Literal['jpeg', 'jpg', 'webp', 'png'] = 'webp',
            size: int = 1024
    ) -> Asset:
        """:class:`Asset`: Same behaviour as :meth:`User.avatar_url_as` and :meth:`.guild_avatar_url_as` but it prefers the guild-specific avatar"""
        if self.guild_avatar:
            return self.guild_avatar_url_as(format=format, static_format=static_format, size=size)
        return self.avatar_url_as(format=format, static_format=static_format, size=size)

    @property
    def guild_banner_url(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild-specific banner asset for the member if any."""
        return self.guild_banner_url_as()

    def guild_banner_url_as(
            self,
            *,
            format: Optional[Literal['jpeg', 'jpg', 'webp', 'png', 'gif']] = None,
            static_format: Literal['jpeg', 'jpg', 'webp', 'png'] = 'webp',
            size: int = 1024
    ) -> Optional[Asset]:
        """Returns an :class:`Asset` for the guild-specific banner of the member if any, else :obj:`None`.

        The format must be one of 'webp', 'jpeg', 'gif' or 'png'. The
        size must be a power of 2 between 16 and 4096.

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the banner to.
        static_format: :class:`str`
            The format to attempt to convert the banner to if the banner is animated.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        Optional[:class:`Asset`}
            The resulting CDN asset if any.
        """
        return Asset._from_guild_banner(self._state, self, static_format=static_format, format=format, size=size)

    def is_guild_banner_animated(self) -> bool:
        """:class:`bool`: Indicates if the member has an animated guild-banner."""
        return bool(self.guild_banner and self.guild_banner.startswith('a_'))

    @property
    def display_banner_url(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild-specific banner asset for the member if he has one, else the default banner asset if any."""
        return self.guild_banner_url or self.banner_url

    def display_banner_url_as(
            self,
            format: Optional[Literal['jpeg', 'jpg', 'webp', 'png', 'gif']] = None,
            static_format: Literal['jpeg', 'jpg', 'webp', 'png'] = 'webp',
            size: int = 1024
    ) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Same behaviour as :meth:`User.banner_url_as` and :meth:`~Member.guild_banner_url_as` but it prefers the guild-specific banner"""
        if self.guild_banner:
            return self.guild_banner_url_as(format=format, static_format=static_format, size=size)
        return self.banner_url_as(format=format, static_format=static_format, size=size)

    @property
    def activity(self) -> Optional[Union[BaseActivity, Spotify]]:
        """Union[:class:`BaseActivity`, :class:`Spotify`]: Returns the primary
        activity the user is currently doing. Could be ``None`` if no activity is being done.

        .. note::

            Due to a Discord API limitation, this may be ``None`` if
            the user is listening to a song on Spotify with a title longer
            than 128 characters. See :old-issue:`1738` for more information.

        .. note::

            A user may have multiple activities, these can be accessed under :attr:`activities`.
        """
        if self.activities:
            return self.activities[0]

    def mentioned_in(self, message: Message) -> bool:
        """Checks if the member is mentioned in the specified message.

        Parameters
        -----------
        message: :class:`Message`
            The message to check if you're mentioned in.

        Returns
        -------
        :class:`bool`
            Indicates if the member is mentioned in the message.
        """
        if message.guild is None or message.guild.id != self.guild.id:
            return False

        if self._user.mentioned_in(message):
            return True

        return any(self._roles.has(role.id) for role in message.role_mentions)

    def permissions_in(self, channel: Union[abc.GuildChannel, ThreadChannel]) -> Permissions:
        """An alias for :meth:`abc.GuildChannel.permissions_for`.

        Basically equivalent to:

        .. code-block:: python3

            channel.permissions_for(self)

        Parameters
        -----------
        channel: :class:`abc.GuildChannel`
            The channel to check your permissions for.

        Returns
        -------
        :class:`Permissions`
            The resolved permissions for the member.
        """
        return channel.permissions_for(self)

    @property
    def top_role(self) -> Role:
        """:class:`Role`: Returns the member's highest role.

        This is useful for figuring where a member stands in the role
        hierarchy chain.
        """
        guild = self.guild
        if len(self._roles) == 0:
            return guild.default_role

        return max(guild.get_role(rid) or guild.default_role for rid in self._roles)

    @property
    def guild_permissions(self) -> Permissions:
        """:class:`Permissions`: Returns the member's guild permissions.

        This only takes into consideration the guild permissions
        and not most of the implied permissions or any of the
        channel permission overwrites. For 100% accurate permission
        calculation, please use either :meth:`permissions_in` or
        :meth:`abc.GuildChannel.permissions_for`.

        This does take into consideration guild ownership and the
        administrator implication.
        """

        if self.guild.owner_id == self.id:
            return Permissions.all()

        base = Permissions.none()
        for r in self.roles:
            base.value |= r.permissions.value

        if base.administrator:
            return Permissions.all()

        return base

    @property
    def voice(self) -> Optional[VoiceState]:
        """Optional[:class:`VoiceState`]: Returns the member's current voice state."""
        return self.guild._voice_state_for(self._user.id)

    @property
    def communication_disabled_until(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: The time until the member is timeouted, if any"""
        return datetime.datetime.fromisoformat(self._communication_disabled_until) if self._communication_disabled_until else None

    @property
    def timed_out(self) -> bool:
        """:class.`bool`: Returns True when the member is timed out.

        .. versionadded:: 2.0
        """
        return (
            self.communication_disabled_until is not None
            and self.communication_disabled_until
            > utils.utcnow()
        )

    @utils.deprecated('Member.timeout')
    async def mute(self, until: datetime.datetime, *, reason: Optional[str] = None) -> Member:
        return await self.edit(communication_disabled_until=until, reason=reason)

    async def timeout(
            self,
            until: Union[datetime.datetime, datetime.timedelta],
            *,
            reason: Optional[str] = None
    ) -> Member:
        """|coro|

        A shortcut method to timeout a member.
        This just calls :meth:`~Member.edit` with the `communication_disabled_until` field set.

        The :attr:`~Permissions.moderate_members` permission is needed to do this.

        Parameters
        -----------
        until: Union[:class:`~datetime.datetime`, :class:`~datetime.timedelta`]
            Until when the member should be timeouted.
            This can be a timezone aware datetime object or a timedelta that will be added to the current time.
            
            .. note::

                This can be max 28 days from current time!

        reason: Optional[:class:`str`]
            The reason for sending the member to timeout - Shows up in the audit-log
        
        Raises
        -------
        TypeError
            The passed :class:`~datetime.datetime` object is not timezone aware
        Forbidden
            The bot missing access to time out this member
        HTTPException
            Sending the member to timeout failed
        """
        if isinstance(until, datetime.timedelta):
            until = utils.utcnow() + until
        return await self.edit(communication_disabled_until=until, reason=reason)

    async def remove_timeout(self, *, reason: Optional[str] = None) -> Member:
        """|coro|

        A shortcut method to remove a member from timeout.

        The :attr:`~Permissions.moderate_members` permission is needed to do this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for removing the member from timeout - Shows up in the audit-log

        Raises
        -------
        Forbidden
            The bot missing access to remove this member from timeout
        HTTPException
            Removing the member from timeout failed
        """
        return await self.edit(communication_disabled_until=None, reason=reason)

    async def ban(
            self,
            delete_message_days: Optional[int] = None,
            delete_message_seconds: Optional[int] = 0,
            reason: Optional[str] = None
    ):
        """|coro|

        Bans this member. Equivalent to :meth:`Guild.ban`.
        """
        await self.guild.ban(
            self,
            delete_message_days=delete_message_days,
            delete_message_seconds=delete_message_seconds,
            reason=reason
        )

    async def unban(self, *, reason: Optional[str] = None):
        """|coro|

        Unbans this member. Equivalent to :meth:`Guild.unban`.
        """
        await self.guild.unban(self, reason=reason)

    async def kick(self, *, reason: Optional[str] = None):
        """|coro|

        Kicks this member. Equivalent to :meth:`Guild.kick`.
        """
        await self.guild.kick(self, reason=reason)

    async def edit(
            self,
            *,
            nick: Optional[str] = MISSING,
            mute: bool = MISSING,
            deafen: bool = MISSING,
            suppress: bool = MISSING,
            roles: Iterable[abc.Snowflake] = MISSING,
            voice_channel: Optional[VoiceChannel] = MISSING,
            flags: GuildMemberFlags = MISSING,
            communication_disabled_until: Optional[datetime.datetime] = MISSING,
            reason: Optional[str] = None
    ) -> Member:
        """|coro|

        Edits the member's data.

        Depending on the parameter passed, this requires different permissions listed below:

        +------------------------------+--------------------------------------------+
        |          Parameter           |              Permission                    |
        +------------------------------+--------------------------------------------+
        | nick                         | :attr:`Permissions.manage_nicknames`       |
        +------------------------------+--------------------------------------------+
        | mute                         | :attr:`Permissions.mute_members`           |
        +------------------------------+--------------------------------------------+
        | deafen                       | :attr:`Permissions.deafen_members`         |
        +------------------------------+--------------------------------------------+
        | roles                        | :attr:`Permissions.manage_roles`           |
        +------------------------------+--------------------------------------------+
        | voice_channel                | :attr:`Permissions.move_members`           |
        +------------------------------+--------------------------------------------+
        | flags                        | - :attr:`Permissions.manage_guild` OR      |
        |                              | - :attr:`Permissions.manage_roles` OR      |
        |                              | - :attr:`Permissions.moderate_members` AND |
        |                              |   :attr:`Permissions.kick_members` AND     |
        |                              |   :attr:`Permissions.ban_members`          |
        +------------------------------+--------------------------------------------+
        | communication_disabled_until | :attr:`Permissions.moderate_members`       |
        +------------------------------+--------------------------------------------+

        All parameters are optional.

        .. versionchanged:: 1.1
            Can now pass ``None`` to ``voice_channel`` to kick a member from voice.

        Parameters
        -----------
        nick: Optional[:class:`str`]
            The member's new nickname. Use ``None`` to remove the nickname.
        mute: :class:`bool`
            Indicates if the member should be guild muted or un-muted.
        deafen: :class:`bool`
            Indicates if the member should be guild deafened or un-deafened.
        suppress: :class:`bool`
            Indicates if the member should be suppressed in stage channels.

            .. versionadded:: 1.7

        roles: Optional[List[:class:`Role`]]
            The member's new list of roles. This *replaces* the roles.
        voice_channel: Optional[:class:`VoiceChannel`]
            The voice channel to move the member to.
            Pass ``None`` to kick them from voice.
        flags: Optional[:class:`GuildMemberFlags`]
            The new flags for this member.
            Note that you are currently only able to update the
            :attr:`~discord.GuildMemberFlags.bypasses_verification` flag.
        communication_disabled_until: Optional[:class:`datetime.datetime`]
            Temporarily puts the member in timeout until this time.
            If :obj:`None`, then the member  is removed from timeout.

            .. note::

                The :class:`~datetime.datetime` object must be timezone aware.

        reason: Optional[:class:`str`]
            The reason for editing this member. Shows up on the audit log.

        Raises
        -------
        TypeError
            The :class:`~datetime.datetime` object passed to ``communication_disabled_until`` is not timezone aware
        Forbidden
            You do not have the proper permissions to the action requested.
        HTTPException
            The operation failed.
        """
        http = self._state.http
        guild_id = self.guild.id
        me = self._state.self_id == self.id
        payload: Dict[str, Any] = {}

        if nick is not MISSING:
            nick = nick or ''
            if me:
                await http.change_my_nickname(guild_id, nick, reason=reason)
            else:
                payload['nick'] = nick

        if mute is not MISSING:
            payload['mute'] = mute

        if deafen is not MISSING:
            payload['deaf'] = deafen

        if suppress is not MISSING:
            voice_state_payload: Dict[str, Any] = {
                'channel_id': self.voice.channel.id,
                'suppress': suppress,
            }

            if suppress or self.bot:
                voice_state_payload['request_to_speak_timestamp'] = None

            if me:
                await http.edit_my_voice_state(guild_id, voice_state_payload)
            else:
                if not suppress:
                    voice_state_payload[
                        'request_to_speak_timestamp'
                    ] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                await http.edit_voice_state(guild_id, self.id, voice_state_payload)

        if voice_channel is not MISSING:
            payload['channel_id'] = voice_channel and voice_channel.id

        if roles is not MISSING:
            payload['roles'] = tuple(r.id for r in roles)

        if flags is not MISSING:
            payload['flags'] = flags.value

        if communication_disabled_until is not MISSING:
            if communication_disabled_until:
                if not communication_disabled_until.tzinfo:
                    raise TypeError(
                        'communication_disabled_until must be an aware datetime.'
                        'Consider using discord.utils.utcnow() '
                        'or datetime.datetime.now().astimezone() for local time.'
                    )
                payload['communication_disabled_until'] = communication_disabled_until.isoformat()
            else:
                payload['communication_disabled_until'] = None

        if payload:
            data = await http.edit_member(guild_id, self.id, reason=reason, **payload)
            self._update(data)
            return self

        # TODO: wait for WS event for modify-in-place behaviour

    async def request_to_speak(self) -> None:
        """|coro|

        Request to speak in the connected channel.

        Only applies to stage channels.

        .. note::

            Requesting members that are not the client is equivalent
            to :attr:`.edit` providing ``suppress`` as ``False``.

        .. versionadded:: 1.7

        Raises
        -------
        Forbidden
            You do not have the proper permissions to the action requested.
        HTTPException
            The operation failed.
        """
        payload = {
            'channel_id': self.voice.channel.id,
            'request_to_speak_timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        if self._state.self_id != self.id:
            payload['suppress'] = False
            await self._state.http.edit_voice_state(self.guild.id, self.id, payload)
        else:
            await self._state.http.edit_my_voice_state(self.guild.id, payload)

    async def move_to(self, channel: Optional[VocalGuildChannel], *, reason: Optional[str] = None) -> None:
        """|coro|

        Moves a member to a new voice channel (they must be connected first).

        You must have the :attr:`~Permissions.move_members` permission to
        use this.

        This raises the same exceptions as :meth:`edit`.

        .. versionchanged:: 1.1
            Can now pass ``None`` to kick a member from voice.

        Parameters
        -----------
        channel: Optional[Union[:class:`VoiceChannel`, :class:`StageChannel`]
            The new voice channel to move the member to.
            Pass ``None`` to kick them from voice.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.
        """
        await self.edit(voice_channel=channel, reason=reason)

    async def add_roles(self, *roles: abc.Snowflake, reason: Optional[str] = None, atomic: bool = True) -> None:
        r"""|coro|

        Gives the member a number of :class:`Role`\s.

        You must have the :attr:`~Permissions.manage_roles` permission to
        use this, and the added :class:`Role`\s must appear lower in the list
        of roles than the highest role of the member.

        Parameters
        -----------
        \*roles: :class:`abc.Snowflake`
            An argument list of :class:`abc.Snowflake` representing a :class:`Role`
            to give to the member.
        reason: Optional[:class:`str`]
            The reason for adding these roles. Shows up on the audit log.
        atomic: :class:`bool`
            Whether to atomically add roles. This will ensure that multiple
            operations will always be applied regardless of the current
            state of the cache.

        Raises
        -------
        Forbidden
            You do not have permissions to add these roles.
        HTTPException
            Adding roles failed.
        """

        if not atomic:
            new_roles = utils._unique(
                (Object(id=r.id) for s in (self.roles[1:], roles) for r in s),
                tuple
            )
            await self.edit(roles=new_roles, reason=reason) # type: ignore
        else:
            req = self._state.http.add_role
            guild_id = self.guild.id
            user_id = self.id
            for role in roles:
                await req(guild_id, user_id, role.id, reason=reason)

    async def remove_roles(self, *roles: Role, reason: Optional[str] = None, atomic: bool = True):
        r"""|coro|

        Removes :class:`Role`\s from this member.

        You must have the :attr:`~Permissions.manage_roles` permission to
        use this, and the removed :class:`Role`\s must appear lower in the list
        of roles than the highest role of the member.

        Parameters
        -----------
        \*roles: :class:`abc.Snowflake`
            An argument list of :class:`abc.Snowflake` representing a :class:`Role`
            to remove from the member.
        reason: Optional[:class:`str`]
            The reason for removing these roles. Shows up on the audit log.
        atomic: :class:`bool`
            Whether to atomically remove roles. This will ensure that multiple
            operations will always be applied regardless of the current
            state of the cache.

        Raises
        -------
        Forbidden
            You do not have permissions to remove these roles.
        HTTPException
            Removing the roles failed.
        """

        if not atomic:
            new_roles = [Object(id=r.id) for r in self.roles[1:]]  # remove @everyone
            for role in roles:
                try:
                    new_roles.remove(Object(id=role.id))
                except ValueError:
                    pass

            await self.edit(roles=new_roles, reason=reason)
        else:
            req = self._state.http.remove_role
            guild_id = self.guild.id
            user_id = self.id
            for role in roles:
                await req(guild_id, user_id, role.id, reason=reason)
