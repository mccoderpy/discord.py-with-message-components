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

import abc
import asyncio
import copy
from typing import (
    Any,
    List,
    Dict,
    Union,
    Mapping,
    overload,
    Optional,
    Callable,
    Coroutine,
    TypeVar,
    TYPE_CHECKING
)

from typing_extensions import (
    Literal,
    Protocol,
    runtime_checkable
)



from . import utils
from .context_managers import Typing
from .enums import ChannelType, InviteTargetType, try_enum
from .errors import ClientException, InvalidArgument
from .file import File
from .flags import ChannelFlags
from .http import handle_message_parameters
from .invite import Invite
from .iterators import HistoryIterator
from .mentions import AllowedMentions
from .permissions import PermissionOverwrite, Permissions
from .role import Role
from .voice_client import VoiceClient, VoiceProtocol

T = TypeVar('T')
VP = TypeVar('VP', bound=VoiceProtocol)

if TYPE_CHECKING:
    from datetime import datetime

    from .types.channel import (
        GuildChannel as GuildChannelData,
        Overwrite as PermissionOverwriteData,
        OverwriteType
    )
    from .client import Client
    from .state import ConnectionState
    from .embeds import Embed
    from .sticker import GuildSticker
    from .components import ActionRow, Button, BaseSelect
    from .scheduled_event import GuildScheduledEvent
    from .member import Member
    from .message import Message, MessageReference
    from .channel import CategoryChannel
    from .guild import Guild
    from .user import ClientUser

    SnowflakeTime = Union["Snowflake", datetime]

MISSING = utils.MISSING
MSNG = utils._MISSING

__all__ = (
    'Snowflake',
    'User',
    'PrivateChannel',
    'GuildChannel',
    'Messageable',
    'Connectable',
    'Mentionable'
)

@runtime_checkable
class Snowflake(Protocol):
    """An ABC that details the common operations on a Discord model.

    Almost all :ref:`Discord models <discord_api_models>` meet this
    abstract base class.

    If you want to create a snowflake on your own, consider using
    :class:`.Object`.

    Attributes
    -----------
    id: :class:`int`
        The model's unique ID.
    """
    
    __slots__ = ()
    id: int


@runtime_checkable
class User(Snowflake, Protocol):
    """An ABC that details the common operations on a Discord user.

    The following implement this ABC:

    - :class:`~discord.User`
    - :class:`~discord.ClientUser`
    - :class:`~discord.Member`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    -----------
    username: :class:`str`
        The user's username.
    global_name: Optional[:class:`str`]
        The users display name, if set.
    discriminator: :class:`str`
        The user's discriminator.
    avatar: Optional[:class:`str`]
        The avatar hash the user has.
    bot: :class:`bool`
        If the user is a bot account.
    """
    
    __slots__ = ()
    username: str
    global_name: Optional[str]
    discriminator: str
    avatar: Optional[str]
    bot: bool
    
    @property
    def name(self):
        """:class:`str`: An alias for :attr:`name`."""
        raise NotImplementedError
    
    @property
    def display_name(self):
        """:class:`str`: Returns the user's display name."""
        raise NotImplementedError

    @property
    def display_avatar(self):
        """:class:`Asset`: Returns the user's display avatar.
        For regular users this is just their default or uploaded avatar.
        """
        raise NotImplementedError

    @property
    def mention(self):
        """:class:`str`: Returns a string that allows you to mention the given user."""
        raise NotImplementedError


@runtime_checkable
class PrivateChannel(Snowflake, Protocol):
    """An ABC that details the common operations on a private Discord channel.

    The following implement this ABC:

    - :class:`~discord.DMChannel`
    - :class:`~discord.GroupChannel`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    -----------
    me: :class:`~discord.ClientUser`
        The user presenting yourself.
    """
    __slots__ = ()

    me: ClientUser


class _Overwrites:
    __slots__ = ('id', 'allow', 'deny', 'type')

    ROLE = 0
    MEMBER = 1

    def __init__(self, data: PermissionOverwriteData) -> None:
        self.id: int = int(data['id'])
        self.allow: int = int(data.get('allow', 0))
        self.deny: int = int(data.get('deny', 0))
        self.type: OverwriteType = data['type']

    def _asdict(self) -> PermissionOverwriteData:
        return {
            'id': self.id,
            'allow': str(self.allow),
            'deny': str(self.deny),
            'type': self.type,
        }

    def is_role(self) -> bool:
        return self.type == self.ROLE

    def is_member(self) -> bool:
        return self.type == self.MEMBER


class GuildChannel:
    """An ABC that details the common operations on a Discord guild channel.

    The following implement this ABC:

    - :class:`~discord.TextChannel`
    - :class:`~discord.VoiceChannel`
    - :class:`~discord.CategoryChannel`
    - :class:`~discord.StageChannel`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`~discord.Guild`
        The guild the channel belongs to.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0.
        e.g. the top channel is position 0.
    """
    __slots__ = ()

    id: int
    name: str
    guild: Guild
    type: ChannelType
    position: int
    category_id: Optional[int]
    flags: ChannelFlags
    _state: ConnectionState
    _overwrites: List[_Overwrites]

    def __str__(self) -> str:
        return self.name

    @property
    def _sorting_bucket(self) -> int:
        raise NotImplementedError

    def _update(self, guild: Guild, data: dict[str, Any]) -> None:
        raise NotImplementedError

    async def _move(
            self,
            position: int,
            parent_id: Optional[int] = None,
            lock_permissions=False,
            *,
            reason: Optional[str]
    ) -> None:
        if position < 0:
            raise InvalidArgument('Channel position cannot be less than 0.')

        http = self._state.http
        bucket = self._sorting_bucket
        channels: List[GuildChannel] = [c for c in self.guild.channels if c._sorting_bucket == bucket]

        channels.sort(key=lambda c: c.position)

        try:
            # remove ourselves from the channel list
            channels.remove(self)
        except ValueError:
            # not there somehow lol
            return
        else:
            index = next((i for i, c in enumerate(channels) if c.position >= position), len(channels))
            # add ourselves at our designated position
            channels.insert(index, self)

        payload = []
        for index, c in enumerate(channels):
            d: Dict[str, Any] = {'id': c.id, 'position': index}
            if parent_id is not MISSING and c.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=lock_permissions)
            payload.append(d)

        await http.bulk_channel_update(self.guild.id, payload, reason=reason)

        self.position = position
        if parent_id is not MISSING:
            self.category_id = int(parent_id) if parent_id else None

    async def _edit(self, options: Dict[str, Any], reason: Optional[str]) -> None:
        try:
            parent = options.pop('category')
        except KeyError:
            parent_id = MISSING
        else:
            parent_id = parent and parent.id

        try:
            options['rate_limit_per_user'] = options.pop('slowmode_delay')
        except KeyError:
            pass

        try:
            rtc_region = options.pop('rtc_region')
        except KeyError:
            pass
        else:
            options['rtc_region'] = None if rtc_region is None else str(rtc_region)

        lock_permissions = options.pop('sync_permissions', False)

        try:
            position = options.pop('position')
        except KeyError:
            if parent_id is not MISSING:
                if lock_permissions:
                    category = self.guild.get_channel(parent_id)
                    options['permission_overwrites'] = [c._asdict() for c in category._overwrites]
                options['parent_id'] = parent_id
            elif lock_permissions and self.category_id is not None:
                # if we're syncing permissions on a pre-existing channel category without changing it
                # we need to update the permissions to point to the pre-existing category
                category = self.guild.get_channel(self.category_id)
                if category:
                    options['permission_overwrites'] = [c._asdict() for c in category._overwrites]
        else:
            await self._move(position, parent_id=parent_id, lock_permissions=lock_permissions, reason=reason)

        overwrites = options.get('overwrites', None)
        if overwrites is not None:
            perms = []
            for target, perm in overwrites.items():
                if not isinstance(perm, PermissionOverwrite):
                    raise InvalidArgument('Expected PermissionOverwrite received {0.__name__}'.format(type(perm)))

                allow, deny = perm.pair()
                perms.append(
                    {
                        'allow': allow.value,
                        'deny': deny.value,
                        'id': target.id,
                        'type': _Overwrites.ROLE if isinstance(target, Role) else _Overwrites.MEMBER,
                    }
                )

            options['permission_overwrites'] = perms

        try:
            ch_type = options['type']
        except KeyError:
            pass
        else:
            if not isinstance(ch_type, ChannelType):
                raise InvalidArgument('type field must be of type ChannelType')
            options['type'] = ch_type.value

        try:
            icon_emoji = options['icon_emoji']
        except KeyError:
            pass
        else:
            if icon_emoji is None:
                options['icon_emoji'] = None
            else:
                options['icon_emoji'] = icon_emoji.to_dict()

        if options:
            data = await self._state.http.edit_channel(self.id, reason=reason, **options)
            return self._update(self.guild, data)

    def _fill_overwrites(self, data: GuildChannelData) -> None:
        self._overwrites = _overwrites = []
        everyone_index = 0
        everyone_id = self.guild.id

        for index, overridden in enumerate(data.get('permission_overwrites', [])):
            overwrite = _Overwrites(overridden)
            _overwrites.append(overwrite)

            if overridden['type'] == _Overwrites.MEMBER:
                continue

            if overwrite.id == everyone_id:
                # the @everyone role is not guaranteed to be the first one
                # in the list of permission overwrites, however the permission
                # resolution code kind of requires that it is the first one in
                # the list since it is special. So we need the index so we can
                # swap it to be the first one.
                everyone_index = index

        # do the swap
        tmp = self._overwrites
        if tmp:
            tmp[everyone_index], tmp[0] = tmp[0], tmp[everyone_index]

    @property
    def changed_roles(self):
        """List[:class:`~discord.Role`]: Returns a list of roles that have been overridden from
        their default values in the :attr:`~discord.Guild.roles` attribute."""
        ret = []
        g = self.guild
        for overwrite in filter(lambda o: o.is_role(), self._overwrites):
            role = g.get_role(overwrite.id)
            if role is None:
                continue

            role = copy.copy(role)
            role.permissions.handle_overwrite(overwrite.allow, overwrite.deny)
            ret.append(role)
        return ret

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the channel."""
        return f'<#{self.id}>'

    @property
    def jump_url(self):
        """:class:`str`: Returns a URL that allows the client to jump to the referenced channel.

        .. versionadded:: 2.0
        """
        return f'https://discord.com/channels/{self.guild.id}/{self.id}'  # type: ignore

    @property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def overwrites_for(self, obj: Union[Role, User]) -> PermissionOverwrite:
        """Returns the channel-specific overwrites for a member or a role.

        Parameters
        -----------
        obj: Union[:class:`~discord.Role`, :class:`~discord.abc.User`]
            The role or user denoting
            whose overwrite to get.

        Returns
        ---------
        :class:`~discord.PermissionOverwrite`
            The permission overwrites for this object.
        """

        if isinstance(obj, User):
            predicate = lambda p: p.is_member()
        elif isinstance(obj, Role):
            predicate = lambda p: p.is_role()
        else:
            predicate = lambda p: True

        for overwrite in filter(predicate, self._overwrites):
            if overwrite.id == obj.id:
                allow = Permissions(overwrite.allow)
                deny = Permissions(overwrite.deny)
                return PermissionOverwrite.from_pair(allow, deny)

        return PermissionOverwrite()

    @property
    def overwrites(self) -> Dict[Union[Role, Member], PermissionOverwrite]:
        """Returns all of the channel's overwrites.

        This is returned as a dictionary where the key contains the target which
        can be either a :class:`~discord.Role` or a :class:`~discord.Member` and the value is the
        overwrite as a :class:`~discord.PermissionOverwrite`.

        Returns
        --------
        Mapping[Union[:class:`~discord.Role`, :class:`~discord.Member`], :class:`~discord.PermissionOverwrite`]
            The channel's permission overwrites.
        """
        ret = {}
        for ow in self._overwrites:
            allow = Permissions(ow.allow)
            deny = Permissions(ow.deny)
            overwrite = PermissionOverwrite.from_pair(allow, deny)
            target = None

            if ow.is_role():
                target = self.guild.get_role(ow.id)
            elif ow.is_member():
                target = self.guild.get_member(ow.id)

            # TODO: There is potential data loss here in the non-chunked
            # case, i.e. target is None because get_member returned nothing.
            # This can be fixed with a slight breaking change to the return type,
            # i.e. adding discord.Object to the list of it
            # However, for now this is an acceptable compromise.
            if target is not None:
                ret[target] = overwrite
        return ret

    @property
    def category(self) -> Optional[CategoryChannel]:
        """Optional[:class:`~discord.CategoryChannel`]: The category this channel belongs to.

        If there is no category then this is ``None``.
        """
        return self.guild.get_channel(self.category_id)

    @property
    def permissions_synced(self) -> bool:
        """:class:`bool`: Whether or not the permissions for this channel are synced with the
        category it belongs to.

        If there is no category then this is ``False``.

        .. versionadded:: 1.3
        """
        category = self.guild.get_channel(self.category_id)
        return bool(category and category.overwrites == self.overwrites)

    def permissions_for(self, member: Member, /) -> Permissions:
        """Handles permission resolution for the current :class:`~discord.Member`.

        This function takes into consideration the following cases:

        - Guild owner
        - Guild roles
        - Channel overrides
        - Member overrides

        Parameters
        ----------
        member: :class:`~discord.Member`
            The member to resolve permissions for.

        Returns
        -------
        :class:`~discord.Permissions`
            The resolved permissions for the member.
        """

        # The current cases can be explained as:
        # Guild owner get all permissions -- no questions asked. Otherwise...
        # The @everyone role gets the first application.
        # After that, the applied roles that the user has in the channel
        # (or otherwise) are then OR'd together.
        # After the role permissions are resolved, the member permissions
        # have to take into effect.
        # After all that is done.. you have to do the following:

        # If manage permissions is True, then all permissions are set to True.

        # The operation first takes into consideration the denied
        # and then the allowed.

        if self.guild.owner_id == member.id:
            return Permissions.all()

        default = self.guild.default_role
        base = Permissions(default.permissions.value)
        roles = member._roles
        get_role = self.guild.get_role

        # Apply guild roles that the member has.
        for role_id in roles:
            role = get_role(role_id)
            if role is not None:
                base.value |= role._permissions

        # Guild-wide Administrator -> True for everything
        # Bypass all channel-specific overrides
        if base.administrator:
            return Permissions.all()

        # Apply @everyone allow/deny first since it's special
        try:
            maybe_everyone = self._overwrites[0]
            if maybe_everyone.id == self.guild.id:
                base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
                remaining_overwrites = self._overwrites[1:]
            else:
                remaining_overwrites = self._overwrites
        except IndexError:
            remaining_overwrites = self._overwrites

        denies = 0
        allows = 0

        # Apply channel specific role permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.is_role() and roles.has(overwrite.id):
                denies |= overwrite.deny
                allows |= overwrite.allow

        base.handle_overwrite(allow=allows, deny=denies)

        # Apply member specific permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.is_member() and overwrite.id == member.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
                break

        # if you can't send a message in a channel then you can't have certain
        # permissions as well
        if not base.send_messages:
            base.send_tts_messages = False
            base.send_voice_messages = False
            base.mention_everyone = False
            base.embed_links = False
            base.attach_files = False
            base.create_public_threads = False
            base.create_private_threads = False
            base.use_application_commands = False

        # if you can't read a channel then you have no permissions there
        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value
        return base

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the channel.

        You must have :attr:`~Permissions.manage_channels` permission to use this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting this channel.
            Shows up on the audit log.

        Raises
        -------
        ~discord.Forbidden
            You do not have proper permissions to delete the channel.
        ~discord.NotFound
            The channel was not found or was already deleted.
        ~discord.HTTPException
            Deleting the channel failed.
        """
        await self._state.http.delete_channel(self.id, reason=reason)

    async def set_permissions(
            self,
            target: Union[Role, User],
            *,
            overwrite: Optional[PermissionOverwrite] = MISSING,
            reason: Optional[str] = None,
            **permissions):
        r"""|coro|

        Sets the channel specific permission overwrites for a target in the
        channel.

        The ``target`` parameter should either be a :class:`~discord.Member` or a
        :class:`~discord.Role` that belongs to guild.

        The ``overwrite`` parameter, if given, must either be ``None`` or
        :class:`~discord.PermissionOverwrite`. For convenience, you can pass in
        keyword arguments denoting :class:`~discord.Permissions` attributes. If this is
        done, then you cannot mix the keyword arguments with the ``overwrite``
        parameter.

        If the ``overwrite`` parameter is ``None``, then the permission
        overwrites are deleted.

        You must have the :attr:`~Permissions.manage_roles` permission to use this.

        Examples
        ----------

        Setting allow and deny: ::

            await message.channel.set_permissions(message.author, read_messages=True,
                                                                  send_messages=False)

        Deleting overwrites ::

            await channel.set_permissions(member, overwrite=None)

        Using :class:`~discord.PermissionOverwrite` ::

            overwrite = discord.PermissionOverwrite()
            overwrite.send_messages = False
            overwrite.read_messages = True
            await channel.set_permissions(member, overwrite=overwrite)

        Parameters
        -----------
        target: Union[:class:`~discord.Member`, :class:`~discord.Role`]
            The member or role to overwrite permissions for.
        overwrite: Optional[:class:`~discord.PermissionOverwrite`]
            The permissions to allow and deny to the target, or ``None`` to
            delete the overwrite.
        \*\*permissions
            A keyword argument list of permissions to set for ease of use.
            Cannot be mixed with ``overwrite``.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.

        Raises
        -------
        ~discord.Forbidden
            You do not have permissions to edit channel specific permissions.
        ~discord.HTTPException
            Editing channel specific permissions failed.
        ~discord.NotFound
            The role or member being edited is not part of the guild.
        ~discord.InvalidArgument
            The overwrite parameter invalid or the target type was not
            :class:`~discord.Role` or :class:`~discord.Member`.
        """

        http = self._state.http

        if isinstance(target, User):
            perm_type = 'member'
        elif isinstance(target, Role):
            perm_type = 'role'
        else:
            raise InvalidArgument(f'target parameter must be either Member or Role, not {target.__class__.__name__}')

        if overwrite is MISSING:
            if not permissions:
                raise InvalidArgument('No overwrite provided.')
            try:
                overwrite = PermissionOverwrite(**permissions)
            except (ValueError, TypeError):
                raise InvalidArgument('Invalid permissions given to keyword arguments.')
        elif permissions:
            raise InvalidArgument('Cannot mix overwrite and keyword arguments.')

        # TODO: wait for event

        if overwrite is None:
            await http.delete_channel_permissions(self.id, target.id, reason=reason)
        elif isinstance(overwrite, PermissionOverwrite):
            (allow, deny) = overwrite.pair()
            await http.edit_channel_permissions(self.id, target.id, allow.value, deny.value, perm_type, reason=reason)
        else:
            raise InvalidArgument('Invalid overwrite type provided.')

    async def _clone_impl(self, base_attrs, *, name: Optional[str] = None, reason: Optional[str] = None):
        base_attrs['permission_overwrites'] = [
            x._asdict() for x in self._overwrites
        ]
        base_attrs['parent_id'] = self.category_id
        base_attrs['name'] = name or self.name
        base_attrs['flags'] = getattr(self, 'flags', ChannelFlags()).value
        guild_id = self.guild.id
        cls = self.__class__
        data = await self._state.http.create_channel(guild_id, self.type.value, reason=reason, **base_attrs)
        obj = cls(state=self._state, guild=self.guild, data=data)

        # temporarily add it to the cache
        self.guild._channels[obj.id] = obj
        return obj

    async def clone(self: T, *, name: Optional[str] = None, reason: Optional[str] = None) -> T:
        """|coro|

        Clones this channel. This creates a channel with the same properties
        as this channel.

        You must have the :attr:`~discord.Permissions.manage_channels` permission to
        do this.

        .. versionadded:: 1.1

        Parameters
        ------------
        name: Optional[:class:`str`]
            The name of the new channel. If not provided, defaults to this
            channel name.
        reason: Optional[:class:`str`]
            The reason for cloning this channel. Shows up on the audit log.

        Raises
        -------
        ~discord.Forbidden
            You do not have the proper permissions to create this channel.
        ~discord.HTTPException
            Creating the channel failed.

        Returns
        --------
        :class:`.abc.GuildChannel`
            The channel that was created.
        """
        raise NotImplementedError

    @overload
    async def move(
            self,
            *,
            beginning: Literal[True] = ...,
            end: Literal[False] = ...,
            before: MSNG = ...,
            after: MSNG = ...,
            offset: int = 0,
            category: Optional[Snowflake] = MISSING,
            sync_permissions: bool = False,
            reason: Optional[str] = None
    ) -> None: ...

    @overload
    async def move(
            self,
            *,
            beginning: Literal[False] = ...,
            end: Literal[True] = ...,
            before: MSNG = ...,
            after: MSNG = ...,
            offset: int = 0,
            category: Optional[Snowflake] = MISSING,
            sync_permissions: bool = False,
            reason: Optional[str] = None
    ) -> None:
        ...

    @overload
    async def move(
            self,
            *,
            beginning: Literal[False] = ...,
            end: Literal[False] = ...,
            before: Snowflake = ...,
            after: MSNG = ...,
            offset: int = 0,
            category: Optional[Snowflake] = MISSING,
            sync_permissions: bool = False,
            reason: Optional[str] = None
    ) -> None:
        ...

    @overload
    async def move(
            self,
            *,
            beginning: Literal[False] = ...,
            end: Literal[False] = ...,
            before: MSNG = ...,
            after: Snowflake = ...,
            offset: int = 0,
            category: Optional[Snowflake] = MISSING,
            sync_permissions: bool = False,
            reason: Optional[str] = None
    ) -> None:
        ...

    async def move(
            self,
            *,
            beginning: bool = False,
            end: bool = False,
            before: Optional[Snowflake] = MISSING,
            after: Optional[Snowflake] = MISSING,
            offset: int = 0,
            category: Optional[Snowflake] = MISSING,
            sync_permissions: bool = False,
            reason: Optional[str] = None
    ):
        """|coro|

        A rich interface to help move a channel relative to other channels.

        If exact position movement is required, :meth:`edit` should be used instead.

        You must have the :attr:`~discord.Permissions.manage_channels` permission to
        do this.

        .. note::

            Voice channels will always be sorted below text channels.
            This is a Discord limitation.

        .. versionadded:: 1.7

        Parameters
        ------------
        beginning: :class:`bool`
            Whether to move the channel to the beginning of the
            channel list (or category if given).
            This is mutually exclusive with ``end``, ``before``, and ``after``.
        end: :class:`bool`
            Whether to move the channel to the end of the
            channel list (or category if given).
            This is mutually exclusive with ``beginning``, ``before``, and ``after``.
        before: :class:`~discord.abc.Snowflake`
            The channel that should be before our current channel.
            This is mutually exclusive with ``beginning``, ``end``, and ``after``.
        after: :class:`~discord.abc.Snowflake`
            The channel that should be after our current channel.
            This is mutually exclusive with ``beginning``, ``end``, and ``before``.
        offset: :class:`int`
            The number of channels to offset the move by. For example,
            an offset of ``2`` with ``beginning=True`` would move
            it 2 after the beginning. A positive number moves it below
            while a negative number moves it above. Note that this
            number is relative and computed after the ``beginning``,
            ``end``, ``before``, and ``after`` parameters.
        category: Optional[:class:`~discord.abc.Snowflake`]
            The category to move this channel under.
            If ``None`` is given then it moves it out of the category.
            This parameter is ignored if moving a category channel.
        sync_permissions: :class:`bool`
            Whether to sync the permissions with the category (if given).
        reason: :class:`str`
            The reason for the move.

        Raises
        -------
        InvalidArgument
            An invalid position was given or a bad mix of arguments were passed.
        Forbidden
            You do not have permissions to move the channel.
        HTTPException
            Moving the channel failed.
        """
        if sum(bool(a) for a in (beginning, end, before, after)) > 1:
            raise InvalidArgument('Only one of [before, after, end, beginning] can be used.')

        parent_id = ... if category is MISSING else category.id

        bucket = self._sorting_bucket
        if parent_id not in (..., None):
            parent_id = category.id
            channels = [
                ch
                for ch in self.guild.channels
                if ch._sorting_bucket == bucket
                and ch.category_id == parent_id
            ]
        else:
            channels = [
                ch
                for ch in self.guild.channels
                if ch._sorting_bucket == bucket
                and ch.category_id == self.category_id
            ]

        channels.sort(key=lambda c: (c.position, c.id))

        try:
            # Try to remove ourselves from the channel list
            channels.remove(self)
        except ValueError:
            # If we're not there then it's probably due to not being in the category
            pass

        index = None
        if beginning is not MISSING:
            index = 0
        elif end is not MISSING:
            index = len(channels)
        elif before is not MISSING:
            index = next((i for i, c in enumerate(channels) if c.id == before.id), None)
        elif after is not MISSING:
            index = next((i + 1 for i, c in enumerate(channels) if c.id == after.id), None)

        if index is None:
            raise InvalidArgument('Could not resolve appropriate move position')

        channels.insert(max((index + offset), 0), self)
        payload = []
        for index, channel in enumerate(channels):
            d = {'id': channel.id, 'position': index}
            if parent_id is not ... and channel.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=sync_permissions)
            payload.append(d)

        await self._state.http.bulk_channel_update(self.guild.id, payload, reason=reason)

    async def create_invite(
            self,
            *,
            max_age: int = 0,
            max_uses: int = 0,
            temporary: bool = False,
            unique: bool = True,
            target_event: Optional[GuildScheduledEvent] = None,
            target_type: Optional[InviteTargetType] = None,
            target_user: Optional[User] = None,
            target_application_id: Optional[int] = None,
            reason: Optional[str] = None,
    ) -> Invite:
        """|coro|

        Creates an instant invite from a text or voice channel.

        You must have the :attr:`~Permissions.create_instant_invite` permission to
        do this.

        Parameters
        ------------
        max_age: Optional[:class:`int`]
            How long the invite should last in seconds. If it's 0 then the invite
            doesn't expire. Defaults to ``0``.
        max_uses: Optional[:class:`int`]
            How many uses the invite could be used for. If it's 0 then there
            are unlimited uses. Defaults to ``0``.
        temporary: Optional[:class:`bool`]
            Denotes that the invite grants temporary membership
            (i.e. they get kicked after they disconnect). Defaults to ``False``.
        unique: Optional[:class:`bool`]
            Indicates if a unique invite URL should be created. Defaults to True.
            If this is set to ``False`` then it will return a previously created
            invite.
        target_type: Optional[:class:`InviteTargetType`]
            The type of target for this voice channel invite, if any.

            .. versionadded:: 2.0

        target_user: Optional[:class:`int`]
        	The user whose stream to display for this invite, required if `target_type` is :attr:`TargetType.stream`.
            The user must be streaming in the channel.

            .. versionadded:: 2.0

        target_application_id: Optional[:class:`int`]
            The id of the embedded application to open for this invite,
            required if `target_type` is :attr:`InviteTargetType.embeded_application`,
            the application must have the EMBEDDED flag.

            .. versionadded:: 2.0

        target_event: Optional[:class:`GuildScheduledEvent`]
            The scheduled event object to link to the event.
            Shortcut to :meth:`.Invite.set_scheduled_event`

            See :meth:`.Invite.set_scheduled_event` for more
            info on event invite linking.

            .. versionadded:: 2.0

        reason: Optional[:class:`str`]
            The reason for creating this invite. Shows up on the audit log.

        Raises
        -------
        ~discord.HTTPException
            Invite creation failed.

        ~discord.NotFound
            The channel that was passed is a category or an invalid channel.

        Returns
        --------
        :class:`~discord.Invite`
            The invite that was created.
        """

        data = await self._state.http.create_invite(
            self.id,
            reason=reason,
            max_age=max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
            target_type=int(target_type) if target_type else None,
            target_user_id=target_user.id if target_user else None,
            target_application_id=target_application_id,
        )
        invite = Invite.from_incomplete(data=data, state=self._state)
        if target_event:
            invite.set_scheduled_event(target_event)
        return invite

    async def invites(self) -> List[Invite]:
        """|coro|

        Returns a list of all active instant invites from this channel.

        You must have :attr:`~Permissions.manage_channels` to get this information.

        Raises
        -------
        ~discord.Forbidden
            You do not have proper permissions to get the information.
        ~discord.HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        List[:class:`~discord.Invite`]
            The list of invites that are currently active.
        """

        state = self._state
        data = await state.http.invites_from_channel(self.id)
        result = []

        for invite in data:
            invite['channel'] = self
            invite['guild'] = self.guild
            result.append(Invite(state=state, data=invite))

        return result


class Messageable:
    """An ABC that details the common operations on a model that can send messages.

    The following implement this ABC:

    - :class:`~discord.TextChannel`
    - :class:`~discord.VoiceChannel`
    - :class:`~discord.DMChannel`
    - :class:`~discord.GroupChannel`
    - :class:`~discord.User`
    - :class:`~discord.Member`
    - :class:`~discord.ext.sub_commands.Context`
    """
    if TYPE_CHECKING:
        _state: ConnectionState
        id: int
    
    __slots__ = ()

    @property
    def is_partial(self) -> bool:
        """:class:`bool`: Whether this channel is considered as a partial one.
        Default to ``False`` for all subclasses of :class:`~discord.abc.Messageable` except :class:`~discord.PartialMessageable`.
        """
        return False

    @abc.abstractmethod
    async def _get_channel(self):
        raise NotImplementedError

    async def send(
            self,
            content: Optional[utils.SupportsStr] = None,
            *,
            tts: bool = False,
            embed: Optional[Embed] = None,
            embeds: Optional[List[Embed]] = None,
            components: Optional[List[Union[ActionRow, List[Union[Button, BaseSelect]]]]] = None,
            file: Optional[File] = None,
            files: Optional[List[File]] = None,
            stickers: Optional[List[GuildSticker]] = None,
            delete_after: Optional[float] = None,
            nonce: Optional[int] = None,
            allowed_mentions: Optional[AllowedMentions] = None,
            reference: Optional[Union[Message, MessageReference]] = None,
            mention_author: Optional[bool] = None,
            suppress_embeds: bool = False,
            suppress_notifications: bool = False
    ) -> Message:  # sourcery skip: raise-from-previous-error
        """|coro|

        Sends a message to the destination with the content given.

        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` parameter must
        be provided.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`~discord.File` object. To upload multiple files, the ``files``
        parameter should be used with a :class:`list` of :class:`~discord.File` objects.

        If the ``embed`` parameter is provided, it must be of type :class:`~discord.Embed` and
        it must be a rich embed type.

        Parameters
        ------------
        content: :class:`str`
            The content of the message to send.
        tts: :class:`bool`
            Indicates if the message should be sent using text-to-speech.
        embed: :class:`~discord.Embed`
            The rich embed for the content.
        embeds: List[:class:`~discord.Embed`]
            A list containing up to ten embeds
        components: List[Union[:class:`~discord.ActionRow`, List[Union[:class:`~discord.Button`, :ref:`Select <select-like-objects>`]]]]
            A list of up to five :class:`~discord.ActionRow`s or :class:`list`,
            each containing up to five :class:`~discord.Button` or one :ref:`Select <select-like-objects>` like object.
        file: :class:`~discord.File`
            The file to upload.
        files: List[:class:`~discord.File`]
            A :class:`list` of files to upload. Must be a maximum of 10.
        stickers: List[:class:`~discord.GuildSticker`]
            A list of up to 3 :class:`discord.GuildSticker` that should be sent with the message.
        nonce: :class:`int`
            The nonce to use for sending this message. If the message was successfully sent,
            then the message will have a nonce with this value.
        delete_after: :class:`float`
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: :class:`~discord.AllowedMentions`
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.

            .. versionadded:: 1.4

        reference: Union[:class:`~discord.Message`, :class:`~discord.MessageReference`]
            A reference to the :class:`~discord.Message` to which you are replying, this can be created using
            :meth:`~discord.Message.to_reference` or passed directly as a :class:`~discord.Message`. You can control
            whether this mentions the author of the referenced message using the :attr:`~discord.AllowedMentions.replied_user`
            attribute of ``allowed_mentions`` or by setting ``mention_author``.

            .. versionadded:: 1.6

        mention_author: Optional[:class:`bool`]
            If set, overrides the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions``.

            .. versionadded:: 1.6

        suppress_embeds: :class:`bool`
            Whether to supress embeds send with the message, default to :obj:`False`
        
        suppress_notifications: :class:`bool`
            Whether to suppress desktop- & push-notifications for this message, default to :obj:`False`
            
            Users will still see a ping-symbol when they are mentioned in the message, or the message is in a dm channel.
            
            .. versionadded:: 2.0
            
        Raises
        --------
        ~discord.HTTPException
            Sending the message failed.
        ~discord.Forbidden
            You do not have the proper permissions to send the message.
        ~discord.InvalidArgument
            The ``files`` list is not of the appropriate size,
            you specified both ``file`` and ``files``,
            or the ``reference`` object is not a :class:`~discord.Message`
            or :class:`~discord.MessageReference`.

        Returns
        ---------
        :class:`~discord.Message`
            The message that was sent.
        """

        channel = await self._get_channel()
        state = self._state
        content = str(content) if content is not None else None
        previous_allowed_mentions = state.allowed_mentions

        if stickers is not None:
            sticker_ids = [str(sticker.id) for sticker in stickers]
        else:
            sticker_ids = MISSING

        if reference is not None:
            try:
                reference = reference.to_message_reference_dict()
            except AttributeError:
                raise InvalidArgument('reference parameter must be Message, PartialMessage or MessageReference')
        else:
            reference = MISSING

        if suppress_embeds or suppress_notifications:
            from .flags import MessageFlags
            flags = MessageFlags._from_value(0)
            flags.suppress_embeds = suppress_embeds
            flags.suppress_notifications = suppress_notifications
        else:
            flags = MISSING

        with handle_message_parameters(
            content=content,
            tts=tts,
            nonce=nonce,
            flags=flags,
            file=file if file is not None else MISSING,
            files=files if files is not None else MISSING,
            embed=embed if embed is not None else MISSING,
            embeds=embeds if embeds is not None else MISSING,
            components=components,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_allowed_mentions,
            message_reference=reference,
            stickers=sticker_ids,
            mention_author=mention_author
        ) as params:
            data = await state.http.send_message(channel.id, params=params)
        ret = state.create_message(channel=channel, data=data)
        if delete_after is not None:
            await ret.delete(delay=delete_after)
        return ret

    async def trigger_typing(self) -> None:
        """|coro|

        Triggers a *typing* indicator to the destination.

        *Typing* indicator will go away after 10 seconds, or after a message is sent.
        """

        channel = await self._get_channel()
        await self._state.http.send_typing(channel.id)

    def typing(self) -> Typing:
        """Returns a context manager that allows you to type for an indefinite period of time.

        This is useful for denoting long computations in your bot.

        .. note::

            This is both a regular context manager and an async context manager.
            This means that both ``with`` and ``async with`` work with this.

        Example Usage: ::

            async with channel.typing():
                # do expensive stuff here
                await asyncio.sleep(15)

            await channel.send('done!')

        """
        return Typing(self)

    async def fetch_message(self, id: int, /) -> Message:
        """|coro|

        Retrieves a single :class:`~discord.Message` from the destination.

        This can only be used by bot accounts.

        Parameters
        ------------
        id: :class:`int`
            The message ID to look for.

        Raises
        --------
        ~discord.NotFound
            The specified message was not found.
        ~discord.Forbidden
            You do not have the permissions required to get a message.
        ~discord.HTTPException
            Retrieving the message failed.

        Returns
        --------
        :class:`~discord.Message`
            The message asked for.
        """

        channel = await self._get_channel()
        data = await self._state.http.get_message(channel.id, id)
        return self._state.create_message(channel=channel, data=data)

    async def pins(self) -> List[Message]:
        """|coro|

        Retrieves all messages that are currently pinned in the channel.

        .. note::

            Due to a limitation with the Discord API, the :class:`.Message`
            objects returned by this method do not contain complete
            :attr:`.Message.reactions` data.

        Raises
        -------
        ~discord.HTTPException
            Retrieving the pinned messages failed.

        Returns
        --------
        List[:class:`~discord.Message`]
            The messages that are currently pinned.
        """

        channel = await self._get_channel()
        state = self._state
        data = await state.http.pins_from(channel.id)
        return [state.create_message(channel=channel, data=m) for m in data]

    def history(
            self,
            *,
            limit: Optional[int] = 100,
            before: Optional[SnowflakeTime] = None,
            after: Optional[SnowflakeTime] = None,
            around: Optional[SnowflakeTime] = None,
            oldest_first: Optional[bool] = None
    ) -> HistoryIterator:
        """Returns an :class:`~discord.AsyncIterator` that enables receiving the destination's message history.

        You must have :attr:`~Permissions.read_message_history` permissions to use this.

        Examples
        ---------

        Usage ::

            counter = 0
            async for message in channel.history(limit=200):
                if message.author == client.user:
                    counter += 1

        Flattening into a list: ::

            messages = await channel.history(limit=123).flatten()
            # messages is now a list of Message...

        All parameters are optional.

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of messages to retrieve.
            If ``None``, retrieves every message in the channel. Note, however,
            that this would make it a slow operation.
        before: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages before this date or message.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        after: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages after this date or message.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        around: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages around this date or message.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
            When using this argument, the maximum limit is 101. Note that if the limit is an
            even number, then this will return at most limit + 1 messages.
        oldest_first: Optional[:class:`bool`]
            If set to ``True``, return messages in oldest->newest order. Defaults to ``True`` if
            ``after`` is specified, otherwise ``False``.

        Raises
        ------
        ~discord.Forbidden
            You do not have permissions to get channel message history.
        ~discord.HTTPException
            The request to get message history failed.

        Yields
        -------
        :class:`~discord.Message`
            The message with the message data parsed.
        """
        return HistoryIterator(self, limit=limit, before=before, after=after, around=around, oldest_first=oldest_first)


class Connectable(Protocol):
    """An ABC that details the common operations on a channel that can
    connect to a voice server.

    The following implement this ABC:

    - :class:`~discord.VoiceChannel`
    - :class:`~discord.StageChannel`

    Note
    ----
    This ABC is not decorated with :func:`typing.runtime_checkable`, so will fail :func:`isinstance`/:func:`issubclass`
    checks.
    """
    __slots__ = ()
    _state: ConnectionState

    def _get_voice_client_key(self):
        raise NotImplementedError

    def _get_voice_state_pair(self):
        raise NotImplementedError

    def __call__(
            self,
            *,
            timeout: float = 60.0,
            reconnect: bool = True,
            cls: VP = VoiceClient
    ) -> Coroutine[None, None, VP]:
        return self.connect(timeout=timeout, reconnect=reconnect, cls=cls)

    async def connect(
            self,
            *,
            timeout: float = 60.0,
            reconnect: bool = True,
            cls: VP = VoiceClient
    ) -> VP:
        """|coro|

        Connects to voice and creates a :class:`VoiceClient` to establish
        your connection to the voice server.

        Parameters
        -----------
        timeout: :class:`float`
            The timeout in seconds to wait for the voice endpoint.
        reconnect: :class:`bool`
            Whether the bot should automatically attempt
            a reconnect if a part of the handshake fails
            or the gateway goes down.
        cls: Type[:class:`VoiceProtocol`]
            A type that subclasses :class:`~discord.VoiceProtocol` to connect with.
            Defaults to :class:`~discord.VoiceClient`.

        Raises
        -------
        asyncio.TimeoutError
            Could not connect to the voice channel in time.
        ~discord.ClientException
            You are already connected to a voice channel.
        ~discord.opus.OpusNotLoaded
            The opus library has not been loaded.

        Returns
        --------
        :class:`~discord.VoiceProtocol`
            A voice client that is fully connected to the voice server.
        """

        key_id, _ = self._get_voice_client_key()
        state = self._state

        if state._get_voice_client(key_id):
            raise ClientException('Already connected to a voice channel.')

        client = state._get_client()
        voice = cls(client, self)

        if not isinstance(voice, VoiceProtocol):
            raise TypeError('Type must meet VoiceProtocol abstract base class.')

        state._add_voice_client(key_id, voice)

        try:
            await voice.connect(timeout=timeout, reconnect=reconnect)
        except asyncio.TimeoutError:
            try:
                await voice.disconnect(force=True)
            except Exception:
                # we don't care if disconnect failed because connection failed
                pass
            raise # re-raise

        return voice


class Mentionable:
    """This class can be used as an annotation for a slash-command option to allow both :class:`Member` and :class:`Role`"""
    pass

if TYPE_CHECKING:
    class Mentionable(User, Member, Role):
        """This class can be used as an annotation for an slash-command option to allow both :class:`Member` and :class:`Role`"""
        pass
