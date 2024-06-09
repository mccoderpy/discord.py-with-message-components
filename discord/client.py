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

import aiohttp
import asyncio
import copy
import inspect
import logging
import signal
import sys
import re
import traceback
import warnings

from typing import (
    Any,
    Dict,
    List,
    Union,
    Tuple,
    AnyStr,
    TypeVar,
    Iterator,
    Optional,
    Callable,
    Awaitable,
    Coroutine,
    TYPE_CHECKING
)

from typing_extensions import Literal

from .auto_updater import AutoUpdateChecker
from .sticker import StickerPack
from .user import ClientUser, User
from .invite import Invite
from .template import Template
from .widget import Widget
from .guild import Guild
from .channel import _channel_factory, PartialMessageable
from .enums import ChannelType, ApplicationCommandType, Locale
from .mentions import AllowedMentions
from .monetization import Entitlement, SKU
from .errors import *
from .enums import Status, VoiceRegion
from .gateway import *
from .activity import BaseActivity, create_activity
from .voice_client import VoiceRegionInfo, VoiceClient
from .http import HTTPClient
from .state import ConnectionState
from . import utils
from .object import Object
from .backoff import ExponentialBackoff
from .webhook import Webhook
from .iterators import GuildIterator, EntitlementIterator
from .appinfo import AppInfo
from .application_commands import *

if TYPE_CHECKING:
    import datetime
    from re import Pattern

    from .abc import (
        GuildChannel,
        Messageable,
        PrivateChannel,
        VoiceProtocol,
        Snowflake
    )
    from .components import Button, Select
    from .emoji import Emoji
    from .flags import Intents
    from .interactions import ApplicationCommandInteraction, ComponentInteraction, ModalSubmitInteraction
    from .member import Member
    from .message import Message
    from .permissions import Permissions
    from .sticker import Sticker

    _ClickCallback = Callable[[ComponentInteraction, Button], Coroutine[Any, Any, Any]]
    _SelectCallback = Callable[[ComponentInteraction, Select], Coroutine[Any, Any, Any]]
    _SubmitCallback = Callable[[ModalSubmitInteraction], Coroutine[Any, Any, Any]]


T = TypeVar('T')
Coro = TypeVar('Coro', bound=Callable[..., Coroutine[Any, Any, Any]])

log = logging.getLogger(__name__)
MISSING = utils.MISSING

__all__ = (
    'Client',
)


def _cancel_tasks(loop):
    try:
        task_retriever = asyncio.Task.all_tasks
    except AttributeError:
        # future proofing for 3.9 I guess
        task_retriever = asyncio.all_tasks

    tasks = {t for t in task_retriever(loop=loop) if not t.done()}

    if not tasks:
        return

    log.info('Cleaning up after %d tasks.', len(tasks))
    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    log.info('All tasks finished cancelling.')

    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'Unhandled exception during Client.run shutdown.',
                'exception': task.exception(),
                'task': task
            })


def _cleanup_loop(loop):
    try:
        _cancel_tasks(loop)
        if sys.version_info >= (3, 6):
            loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        log.info('Closing the event loop.')
        loop.close()


class _ClientEventTask(asyncio.Task):
    def __init__(self, original_coro, event_name, coro, *, loop):
        super().__init__(coro, loop=loop)
        self.__event_name = event_name
        self.__original_coro = original_coro

    def __repr__(self):
        info = [
            ('state', self._state.lower()),
            ('event', self.__event_name),
            ('coro', repr(self.__original_coro)),
        ]
        if self._exception is not None:
            info.append(('exception', repr(self._exception)))
        return '<ClientEventTask {}>'.format(' '.join('%s=%s' % t for t in info))


class Client:
    r"""Represents a client connection that connects to Discord.
    This class is used to interact with the Discord WebSocket and API.

    A number of options can be passed to the :class:`Client`.

    Parameters
    -----------
    max_messages: Optional[:class:`int`]
        The maximum number of messages to store in the internal message cache.
        This defaults to ``1000``. Passing in ``None`` disables the message cache.

        .. versionchanged:: 1.3
            Allow disabling the message cache and change the default size to ``1000``.
    loop: Optional[:class:`asyncio.AbstractEventLoop`]
        The :class:`asyncio.AbstractEventLoop` to use for asynchronous operations.
        Defaults to ``None``, in which case the default event loop is used via
        :func:`asyncio.get_event_loop()`.
    connector: :class:`aiohttp.BaseConnector`
        The connector to use for connection pooling.
    proxy: Optional[:class:`str`]
        Proxy URL.
    proxy_auth: Optional[:class:`aiohttp.BasicAuth`]
        An object that represents proxy HTTP Basic Authorization.
    shard_id: Optional[:class:`int`]
        Integer starting at ``0`` and less than :attr:`.shard_count`.
    shard_count: Optional[:class:`int`]
        The total number of shards.
    intents: :class:`Intents`
        The intents that you want to enable for the _session. This is a way of
        disabling and enabling certain gateway events from triggering and being sent.
        If not given, defaults to a regularly constructed :class:`Intents` class.
    gateway_version: :class:`int`
        The gateway and api version to use. Defaults to ``v10``.
    api_error_locale: :class:`discord.Locale`
        The locale language to use for api errors. This will be applied to the ``X-Discord-Local`` header in requests.
        Default to :attr:`Locale.en_US`
    member_cache_flags: :class:`MemberCacheFlags`
        Allows for finer control over how the library caches members.
        If not given, defaults to cache as much as possible with the
        currently selected intents.
    fetch_offline_members: :class:`bool`
        A deprecated alias of ``chunk_guilds_at_startup``.
    chunk_guilds_at_startup: :class:`bool`
        Indicates if :func:`.on_ready` should be delayed to chunk all guilds
        at start-up if necessary. This operation is incredibly slow for large
        amounts of guilds. The default is ``True`` if :attr:`Intents.members`
        is ``True``.
    status: Optional[:class:`.Status`]
        A status to start your presence with upon logging on to Discord.
    activity: Optional[:class:`.BaseActivity`]
        An activity to start your presence with upon logging on to Discord.
    allowed_mentions: Optional[:class:`AllowedMentions`]
        Control how the client handles mentions by default on every message sent.
    heartbeat_timeout: :class:`float`
        The maximum numbers of seconds before timing out and restarting the
        WebSocket in the case of not receiving a HEARTBEAT_ACK. Useful if
        processing the initial packets take too long to the point of disconnecting
        you. The default timeout is 60 seconds.
    guild_ready_timeout: :class:`float`
        The maximum number of seconds to wait for the GUILD_CREATE stream to end before
        preparing the member cache and firing READY. The default timeout is 2 seconds.

        .. versionadded:: 1.4
    guild_subscriptions: :class:`bool`
        Whether to dispatch presence or typing events. Defaults to :obj:`True`.

        .. versionadded:: 1.3

        .. warning::

            If this is set to :obj:`False` then the following features will be disabled:

                - No user related updates (:func:`on_user_update` will not dispatch)
                - All member related events will be disabled.
                    - :func:`on_member_update`
                    - :func:`on_member_join`
                    - :func:`on_member_remove`

                - Typing events will be disabled (:func:`on_typing`).
                - If ``fetch_offline_members`` is set to ``False`` then the user cache will not exist.
                  This makes it difficult or impossible to do many things, for example:

                    - Computing permissions
                    - Querying members in a voice channel via :attr:`VoiceChannel.members` will be empty.
                    - Most forms of receiving :class:`Member` will be
                      receiving :class:`User` instead, except for message events.
                    - :attr:`Guild.owner` will usually resolve to ``None``.
                    - :meth:`Guild.get_member` will usually be unavailable.
                    - Anything that involves using :class:`Member`.
                    - :attr:`users` will not be as populated.
                    - etc.

            In short, this makes it so the only member you can reliably query is the
            message author. Useful for bots that do not require any state.
    assume_unsync_clock: :class:`bool`
        Whether to assume the system clock is unsynced. This applies to the ratelimit handling
        code. If this is set to ``True``, the default, then the library uses the time to reset
        a rate limit bucket given by Discord. If this is ``False`` then your system clock is
        used to calculate how long to sleep for. If this is set to ``False`` it is recommended to
        sync your system clock to Google's NTP server.

        .. versionadded:: 1.3

    sync_commands: :class:`bool`
        Whether to sync application-commands on startup, default :obj:`False`.

        This will register global and guild application-commands(slash-, user- and message-commands)
        that are not registered yet, update changes and remove application-commands that could not be found
        in the code anymore if :attr:`delete_not_existing_commands` is set to :obj:`True` what it is by default.

    delete_not_existing_commands: :class:`bool`
        Whether to remove global and guild-only application-commands that are not in the code anymore, default :obj:`True`.

    auto_check_for_updates: :class:`bool`
        Whether to check for available updates automatically, default :obj:`False` for legal reasons.
        For more info see :func:`discord.on_update_available`.

        .. note::

            For now, this may only work on the original repository, **not on forks**.
            This is because it uses an internal API that listens to a private application that is on the original repo.

            In the future this API might be open-sourced, or it will be possible to add your forks URL as a valid source.

    Attributes
    -----------
    ws
        The websocket gateway the client is currently connected to. Could be ``None``.
    loop: :class:`asyncio.AbstractEventLoop`
        The event loop that the client uses for HTTP requests and websocket operations.
    """
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None, **options):
        self.ws: DiscordWebSocket = None
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop() if loop is None else loop
        self._listeners = {}
        self.sync_commands: bool = options.get('sync_commands', False)
        self.delete_not_existing_commands: bool = options.get('delete_not_existing_commands', True)
        self._application_commands_by_type: Dict[str, Dict[str, Union[SlashCommand, UserCommand, MessageCommand]]] = {
            'chat_input': {}, 'message': {}, 'user': {}
        }
        self._guild_specific_application_commands: Dict[
            int, Dict[str, Dict[str, Union[SlashCommand, UserCommand, MessageCommand]]]] = {}
        self._application_commands: Dict[int, ApplicationCommand] = {}
        self.shard_id = options.get('shard_id')
        self.shard_count = options.get('shard_count')

        connector = options.pop('connector', None)
        proxy = options.pop('proxy', None)
        proxy_auth = options.pop('proxy_auth', None)
        unsync_clock = options.pop('assume_unsync_clock', True)
        self.gateway_version: int = options.get('gateway_version', 10)
        self.api_error_locale: Locale = options.pop('api_error_locale', 'en-US')
        self.auto_check_for_updates: bool = options.pop('auto_check_for_updates', False)
        self.http = HTTPClient(
            connector,
            proxy=proxy,
            proxy_auth=proxy_auth,
            unsync_clock=unsync_clock,
            loop=self.loop,
            api_version=self.gateway_version,
            api_error_locale=self.api_error_locale
        )

        self._handlers = {
            'ready': self._handle_ready,
            'connect': lambda: self._ws_connected.set(),
            'resumed': lambda: self._ws_connected.set()
        }

        self._hooks = {
            'before_identify': self._call_before_identify_hook
        }

        self._connection = self._get_state(**options)
        self._connection.shard_count = self.shard_count
        self._closed = False
        self._ready = asyncio.Event()
        self._ws_connected = asyncio.Event()
        self._connection._get_websocket = self._get_websocket
        self._connection._get_client = lambda: self

        if VoiceClient.warn_nacl:
            VoiceClient.warn_nacl = False
            log.warning("PyNaCl is not installed, voice will NOT be supported")
        if self.auto_check_for_updates:
            self._auto_update_checker: Optional[AutoUpdateChecker] = AutoUpdateChecker(client=self)
        else:
            self._auto_update_checker: Optional[AutoUpdateChecker] = None

    # internals
    def _get_websocket(self, guild_id=None, *, shard_id=None):
        return self.ws

    def _get_state(self, **options):
        return ConnectionState(dispatch=self.dispatch, handlers=self._handlers,
                               hooks=self._hooks, syncer=self._syncer, http=self.http, loop=self.loop, **options)

    async def _syncer(self, guilds):
        await self.ws.request_sync(guilds)

    def _handle_ready(self):
        self._ready.set()

    @property
    def latency(self) -> float:
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This could be referred to as the Discord WebSocket protocol latency.
        """
        ws = self.ws
        return float('nan') if not ws else ws.latency

    def is_ws_ratelimited(self) -> bool:
        """:class:`bool`: Whether the websocket is currently rate limited.

        This can be useful to know when deciding whether you should query members
        using HTTP or via the gateway.

        .. versionadded:: 1.6
        """
        if self.ws:
            return self.ws.is_ratelimited()
        return False

    @property
    def user(self) -> ClientUser:
        """Optional[:class:`.ClientUser`]: Represents the connected client. ``None`` if not logged in."""
        return self._connection.user

    @property
    def guilds(self) -> List[Guild]:
        """List[:class:`.Guild`]: The guilds that the connected client is a member of."""
        return self._connection.guilds

    @property
    def emojis(self) -> List[Emoji]:
        """List[:class:`.Emoji`]: The emojis that the connected client has."""
        return self._connection.emojis

    @property
    def stickers(self) -> List[Sticker]:
        """List[:class:`.Sticker`]: The stickers that the connected client has."""
        return self._connection.stickers

    @property
    def cached_messages(self) -> utils.SequenceProxy[Message]:
        """Sequence[:class:`.Message`]: Read-only list of messages the connected client has cached.

        .. versionadded:: 1.1
        """
        return utils.SequenceProxy(self._connection._messages or [])

    @property
    def private_channels(self) -> List[PrivateChannel]:
        """List[:class:`.abc.PrivateChannel`]: The private channels that the connected client is participating on.

        .. note::

            This returns only up to 128 most recent private channels due to an internal working
            on how Discord deals with private channels.
        """
        return self._connection.private_channels

    @property
    def voice_clients(self) -> List[VoiceProtocol]:
        """List[:class:`.VoiceProtocol`]: Represents a list of voice connections.

        These are usually :class:`.VoiceClient` instances.
        """
        return self._connection.voice_clients

    def is_ready(self) -> bool:
        """:class:`bool`: Specifies if the client's internal cache is ready for use."""
        return self._ready.is_set()

    async def _run_event(self, coro: Coro, event_name: str, *args, **kwargs):
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def _schedule_event(self, coro: Coro, event_name: str, *args, **kwargs) -> _ClientEventTask:
        wrapped = self._run_event(coro, event_name, *args, **kwargs)
        # Schedules the task
        return _ClientEventTask(original_coro=coro, event_name=event_name, coro=wrapped, loop=self.loop)

    def dispatch(self, event: str, *args, **kwargs) -> None:
        log.debug('Dispatching event %s', event)
        method = 'on_' + event

        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if isinstance(future, asyncio.Future):
                    if future.cancelled():
                        removed.append(i)
                        continue

                    try:
                        result = condition(*args)
                    except Exception as exc:
                        future.set_exception(exc)
                        removed.append(i)
                    else:
                        if result:
                            if len(args) == 0:
                                future.set_result(None)
                            elif len(args) == 1:
                                future.set_result(args[0])
                            else:
                                future.set_result(args)
                            removed.append(i)

                    if len(removed) == len(listeners):
                        self._listeners.pop(event)
                    else:
                        for idx in reversed(removed):
                            del listeners[idx]
                else:
                    result = condition(*args)
                    if result:
                        self._schedule_event(future, method, *args, **kwargs)

        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        """|coro|

        The default error handler provided by the client.

        By default, this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.
        Check :func:`~discord.on_error` for more details.
        """
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()

    async def on_application_command_error(
            self,
            cmd: ApplicationCommand,
            interaction: ApplicationCommandInteraction,
            exception: BaseException
    ) -> None:
        """|coro|

        The default error handler when an Exception was raised when invoking an application-command.

        By default, this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.
        Check :func:`~discord.on_application_command_error` for more details.
        """
        if hasattr(cmd, 'on_error'):
            return
        if isinstance(cmd, (SlashCommand, SubCommand)):
            name = cmd.qualified_name
        else:
            name = cmd.name
        print('Ignoring exception in {type} command "{name}" ({id})'.format(
            type=str(interaction.command.type).upper(),
            name=name,
            id=interaction.command.id
        ),
            file=sys.stderr
        )
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    async def _request_sync_commands(self, is_cog_reload: bool = False, *, reload_failed: bool = False) -> None:
        """Used to sync commands if the ``GUILD_CREATE`` stream is over or a :class:`~discord.ext.commands.Cog` was reloaded.

        .. warning::
            **DO NOT OVERWRITE THIS METHOD!!!
            IF YOU DO SO, THE APPLICATION-COMMANDS WILL NOT BE SYNCED AND NO COMMAND REGISTERED WILL BE DISPATCHED.**
        """
        if not hasattr(self, 'app'):
            await self.application_info()
        if (is_cog_reload and not reload_failed and getattr(self, 'sync_commands_on_cog_reload', False) is True) or (
                not is_cog_reload and self.sync_commands is True
        ):
            return await self._sync_commands()
        state = self._connection  # Speedup attribute access
        if not is_cog_reload:
            app_id = self.app.id
            log.info('Collecting global application-commands for application %s (%s)', self.app.name, self.app.id)

            self._minimal_registered_global_commands_raw = minimal_registered_global_commands_raw = []
            get_commands = self.http.get_application_commands
            global_registered_raw = await get_commands(app_id)

            for raw_command in global_registered_raw:
                command_type = str(ApplicationCommandType.try_value(raw_command['type']))
                minimal_registered_global_commands_raw.append({'id': int(raw_command['id']), 'type': command_type, 'name': raw_command['name']})
                try:
                    command = self._application_commands_by_type[command_type][raw_command['name']]
                except KeyError:
                    command = ApplicationCommand._from_type(state, data=raw_command)
                    command.func = None
                    self._application_commands[command.id] = self._application_commands_by_type[command_type][command.name] = command
                else:
                    command._fill_data(raw_command)
                    command._state = state
                    self._application_commands[command.id] = command

            log.info(
                'Done! Cached %s global application-commands',
                sum([len(cmds) for cmds in self._application_commands_by_type.values()])
            )
            log.info('Collecting guild-specific application-commands for application %s (%s)', self.app.name, app_id)

            self._minimal_registered_guild_commands_raw = minimal_registered_guild_commands_raw = {}

            for guild in self.guilds:
                try:
                    registered_guild_commands_raw = await get_commands(app_id, guild_id=guild.id)
                except Forbidden:
                    log.info(
                        'Missing access to guild %s (%s) or don\'t have the application.commands scope in there, '
                        'skipping!' % (guild.name, guild.id))
                    continue
                except HTTPException:
                    raise
                if registered_guild_commands_raw:
                    minimal_registered_guild_commands_raw[guild.id] = minimal_registered_guild_commands = []
                    try:
                        guild_commands = self._guild_specific_application_commands[guild.id]
                    except KeyError:
                        self._guild_specific_application_commands[guild.id] = guild_commands = {
                            'chat_input': {}, 'user': {}, 'message': {}
                        }
                    for raw_command in registered_guild_commands_raw:
                        command_type = str(ApplicationCommandType.try_value(raw_command['type']))
                        minimal_registered_guild_commands.append(
                            {'id': int(raw_command['id']), 'type': command_type, 'name': raw_command['name']}
                        )
                        try:
                            command = guild_commands[command_type][raw_command['name']]
                        except KeyError:
                            command = ApplicationCommand._from_type(state, data=raw_command)
                            command.func = None
                            self._application_commands[command.id] = guild._application_commands[command.id] \
                                = guild_commands[command_type][command.name] = command
                        else:
                            command._fill_data(raw_command)
                            command._state = state
                            self._application_commands[command.id] = guild._application_commands[command.id] = command

            log.info(
                'Done! Cached %s commands for %s guilds',
                sum([
                    len(commands) for commands in list(minimal_registered_guild_commands_raw.values())
                ]),
                len(minimal_registered_guild_commands_raw.keys())
            )

        else:
            # re-assign metadata to the commands (for commands added from cogs)
            log.info('Re-assigning metadata to commands')
            # For logging purposes
            no_longer_in_code_global = 0
            no_longer_in_code_guild_specific = 0
            no_longer_in_code_guilds = set()

            for raw_command in self._minimal_registered_global_commands_raw:
                command_type = raw_command['type']
                try:
                    command = self._application_commands_by_type[command_type][raw_command['name']]
                except KeyError:
                    no_longer_in_code_global += 1
                    self._application_commands[raw_command['id']].func = None
                    continue  # Should already be cached in self._application_commands so skip that part here
                else:
                    if command.disabled:
                        no_longer_in_code_global += 1
                    else:
                        command._fill_data(raw_command)
                        command._state = state
                        self._application_commands[command.id] = command
            for guild_id, raw_commands in self._minimal_registered_guild_commands_raw.items():
                try:
                    guild_commands = self._guild_specific_application_commands[guild_id]
                except KeyError:
                    no_longer_in_code_guilds.add(guild_id)
                    no_longer_in_code_guild_specific += len(raw_commands)
                    continue  # Should already be cached in self._application_commands so skip that part here again
                else:
                    guild = self.get_guild(guild_id)
                    for raw_command in raw_commands:
                        command_type = raw_command['type']
                        try:
                            command = guild_commands[command_type][raw_command['name']]
                        except KeyError:
                            if guild_id not in no_longer_in_code_guilds:
                                no_longer_in_code_guilds.add(guild_id)
                            no_longer_in_code_guild_specific += 1
                            self._application_commands[raw_command['id']].func = None
                            pass  # Should already be cached in self._application_commands so skip that part here another once again
                        else:
                            if command.disabled:
                                no_longer_in_code_guild_specific += 1
                            else:
                                command._fill_data(raw_command)
                                command._state = state
                                self._application_commands[command.id] = guild._application_commands[command.id] = command
            log.info('Done!')
            if no_longer_in_code_global:
                log.warning(
                    '%s global application-commands where removed from code but are still registered in discord',
                    no_longer_in_code_global
                )
            if no_longer_in_code_guild_specific:
                log.warning(
                    'In total %s guild-specific application-commands from %s guild(s) where removed from code '
                    'but are still registered in discord', no_longer_in_code_guild_specific,
                    len(no_longer_in_code_guilds)
                )
            if no_longer_in_code_global or no_longer_in_code_guild_specific:
                log.warning(
                    'To prevent the above, set `sync_commands_on_cog_reload` of %s to True',
                    self.__class__.__name__
                )

    @utils.deprecated('Guild.chunk')
    async def request_offline_members(self, *guilds):
        r"""|coro|

        Requests previously offline members from the guild to be filled up
        into the :attr:`.Guild.members` cache. This function is usually not
        called. It should only be used if you have the ``fetch_offline_members``
        parameter set to ``False``.

        When the client logs on and connects to the websocket, Discord does
        not provide the library with offline members if the number of members
        in the guild is larger than 250. You can check if a guild is large
        if :attr:`.Guild.large` is ``True``.

        .. warning::

            This method is deprecated. Use :meth:`Guild.chunk` instead.

        Parameters
        -----------
        \*guilds: :class:`.Guild`
            An argument list of guilds to request offline members for.

        Raises
        -------
        :exc:`.InvalidArgument`
            If any guild is unavailable in the collection.
        """
        if any(g.unavailable for g in guilds):
            raise InvalidArgument('An unavailable guild was passed.')

        for guild in guilds:
            await self._connection.chunk_guild(guild)

    # hooks

    async def _call_before_identify_hook(self, shard_id, *, initial=False):
        # This hook is an internal hook that actually calls the public one.
        # It allows the library to have its own hook without stepping on the
        # toes of those who need to override their own hook.
        await self.before_identify_hook(shard_id, initial=initial)

    async def before_identify_hook(self, shard_id: int, *, initial: bool = False):
        """|coro|

        A hook that is called before IDENTIFYing a _session. This is useful
        if you wish to have more control over the synchronization of multiple
        IDENTIFYing clients.

        The default implementation sleeps for 5 seconds.

        .. versionadded:: 1.4

        Parameters
        ------------
        shard_id: :class:`int`
            The shard ID that requested being IDENTIFY'd
        initial: :class:`bool`
            Whether this IDENTIFY is the first initial IDENTIFY.
        """

        if not initial:
            await asyncio.sleep(5.0)

    # login state management

    async def login(self, token: str) -> None:
        """|coro|

        Logs in the client with the specified credentials.

        This function can be used in two different ways.


        Parameters
        -----------
        token: :class:`str`
            The authentication token. Do not prefix this token with
            anything as the library will do it for you.

        Raises
        ------
        :exc:`.LoginFailure`
            The wrong credentials are passed.
        :exc:`.HTTPException`
            An unknown HTTP related error occurred,
            usually when it isn't 200 or the known incorrect credentials
            passing status code.
        """

        log.info('logging in using static token')
        await self.http.static_login(token.strip())

    @utils.deprecated('Client.close')
    async def logout(self):
        """|coro|

        Logs out of Discord and closes all connections.

        .. deprecated:: 1.7

        .. note::

            This is just an alias to :meth:`close`. If you want
            to do extraneous cleanup when subclassing, it is suggested
            to override :meth:`close` instead.
        """
        await self.close()

    async def connect(self, *, reconnect: bool = True) -> None:
        """|coro|

        Creates a websocket connection and lets the websocket listen
        to messages from Discord. This is a loop that runs the entire
        event system and miscellaneous aspects of the library. Control
        is not resumed until the WebSocket connection is terminated.

        Parameters
        -----------
        reconnect: :class:`bool`
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as
            invalid sharding payloads or bad tokens).

        Raises
        -------
        :exc:`.GatewayNotFound`
            If the gateway to connect to Discord is not found. Usually if this
            is thrown then there is a Discord API outage.
        :exc:`.ConnectionClosed`
            The websocket connection has been terminated.
        """

        backoff = ExponentialBackoff()
        ws_params = {
            'initial': True,
            'shard_id': self.shard_id,
        }
        if self.auto_check_for_updates:
            self._auto_update_checker.start()
        while not self.is_closed():
            try:
                coro = DiscordWebSocket.from_client(self, **ws_params)
                self.ws = await asyncio.wait_for(coro, timeout=60.0)
                ws_params['initial'] = False
                while True:
                    await self.ws.poll_event()
            except ReconnectWebSocket as e:
                log.info('Got a request to %s the websocket.', e.op)
                self._ws_connected.clear()
                self.dispatch('disconnect')
                ws_params.update(
                    sequence=self.ws.sequence,
                    resume=e.resume,
                    session=self.ws.session_id,
                    resume_gateway_url=self.ws.resume_gateway_url if e.resume else None
                )
                continue
            except (OSError,
                    HTTPException,
                    GatewayNotFound,
                    ConnectionClosed,
                    aiohttp.ClientError,
                    asyncio.TimeoutError) as exc:
                self._ws_connected.clear()
                self.dispatch('disconnect')
                if not reconnect:
                    await self.close()
                    if isinstance(exc, ConnectionClosed) and exc.code == 1000:
                        # clean close, don't re-raise this
                        return
                    raise

                if self.is_closed():
                    return

                # If we get connection reset by peer then try to RESUME
                if isinstance(exc, OSError) and exc.errno in (54, 10054):
                    ws_params.update(
                        sequence=self.ws.sequence,
                        initial=False,
                        resume=True,
                        session=self.ws.session_id,
                        resume_gateway_url=self.ws.resume_gateway_url
                    )
                    continue

                # We should only get this when an unhandled close code happens,
                # such as a clean disconnect (1000) or a bad state (bad token, no sharding, etc)
                # sometimes, discord sends us 1000 for unknown reasons, so we should reconnect
                # regardless and rely on is_closed instead
                if isinstance(exc, ConnectionClosed):
                    if exc.code == 4014:
                        if self.shard_count and self.shard_count > 0:
                            raise PrivilegedIntentsRequired(exc.shard_id)
                        else:
                            sys.stderr.write(str(PrivilegedIntentsRequired(exc.shard_id)))
                    if exc.code != 1000:
                        await self.close()
                        if not exc.code == 4014:
                            raise

                retry = backoff.delay()
                log.exception("Attempting a reconnect in %.2fs", retry)
                await asyncio.sleep(retry)
                # Always try to RESUME the connection
                # If the connection is not RESUME-able then the gateway will invalidate the _session.
                # This is apparently what the official Discord client does.
                ws_params.update(
                    sequence=self.ws.sequence,
                    resume=True,
                    session=self.ws.session_id,
                    resume_gateway_url=self.ws.resume_gateway_url
                )

    async def close(self) -> None:
        """|coro|

        Closes the connection to Discord.
        """
        if self._closed:
            return

        for voice in self.voice_clients:
            try:
                await voice.disconnect()  # type: ignore
            except Exception:
                # if an error happens during disconnects, disregard it.
                pass

        await self.http.close()
        if self._auto_update_checker:
            await self._auto_update_checker.close()
        self._closed = True

        if self.ws is not None and self.ws.open:
            await self.ws.close(code=1000)

        self._ws_connected.clear()
        self._ready.clear()

    def clear(self) -> None:
        """Clears the internal state of the bot.

        After this, the bot can be considered "re-opened", i.e. :meth:`is_closed`
        and :meth:`is_ready` both return ``False`` along with the bot's internal
        cache cleared.
        """
        self._closed = False
        self._ready.clear()
        self._ws_connected.clear()
        self._connection.clear()
        self.http.recreate()

    async def start(self, token: str, reconnect: bool = True) -> None:
        """|coro|

        A shorthand coroutine for :meth:`login` + :meth:`connect`.

        Raises
        -------
        TypeError
            An unexpected keyword argument was received.
        """
        await self.login(token)
        await self.connect(reconnect=reconnect)

    def run(
        self,
        token: str,
        reconnect: bool = True,
        *,
        log_handler: Optional[logging.Handler] = MISSING,
        log_formatter: logging.Formatter = MISSING,
        log_level: int = MISSING,
        root_logger: bool = False
    ) -> None:
        """A blocking call that abstracts away the event loop
        initialisation from you.

        If you want more control over the event loop then this
        function should not be used. Use :meth:`start` coroutine
        or :meth:`connect` + :meth:`login`.

        Roughly Equivalent to: ::

            try:
                loop.run_until_complete(start(*args, **kwargs))
            except KeyboardInterrupt:
                loop.run_until_complete(close())
                # cancel all tasks lingering
            finally:
                loop.close()

        This function also sets up the `:mod:`logging` library to make it easier
        for beginners to know what is going on with the library. For more
        advanced users, this can be disabled by passing :obj:`None` to
        the ``log_handler`` parameter.

        .. warning::

            This function must be the last function to call due to the fact that it
            is blocking. That means that registration of events or anything being
            called after this function call will not execute until it returns.

        Parameters
        -----------
        token: :class:`str`
            The authentication token. **Do not prefix this token with anything as the library will do it for you.**
        reconnect: :class:`bool`
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as
            invalid sharding payloads or bad tokens).
        log_handler: Optional[:class:`logging.Handler`]
            The log handler to use for the library's logger. If this is :obj:`None`
            then the library will not set up anything logging related. Logging
            will still work if :obj:`None` is passed, though it is your responsibility
            to set it up.
            The default log handler if not provided is :class:`logging.StreamHandler`.
        log_formatter: :class:`logging.Formatter`
            The formatter to use with the given log handler. If not provided then it
            defaults to a colour based logging formatter (if available).
        log_level: :class:`int`
            The default log level for the library's logger. This is only applied if the
            ``log_handler`` parameter is not :obj:`None`. Defaults to :attr:`logging.INFO`.
        root_logger: :class:`bool`
            Whether to set up the root logger rather than the library logger.
            By default, only the library logger (``'discord'``) is set up. If this
            is set to :obj:`True` then the root logger is set up as well.
            Defaults to :obj:`False`.
        """
        loop = self.loop

        try:
            loop.add_signal_handler(signal.SIGINT, lambda: loop.stop())
            loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())
        except NotImplementedError:
            pass

        async def runner():
            try:
                await self.start(token, reconnect)
            finally:
                if not self.is_closed():
                    await self.close()

        if log_handler is not None:
            utils.setup_logging(
                handler=log_handler,
                formatter=log_formatter,
                level=log_level,
                root=root_logger
            )

        def stop_loop_on_completion(f):
            loop.stop()

        future = asyncio.ensure_future(runner(), loop=loop)
        future.add_done_callback(stop_loop_on_completion)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            log.info('Received signal to terminate bot and event loop.')
        finally:
            future.remove_done_callback(stop_loop_on_completion)
            log.info('Cleaning up tasks.')
            _cleanup_loop(loop)

        if not future.cancelled():
            try:
                return future.result()
            except KeyboardInterrupt:
                # I am unsure why this gets raised here but suppress it anyway
                return None

    # properties

    def is_closed(self) -> bool:
        """:class:`bool`: Indicates if the websocket connection is closed."""
        return self._closed

    @property
    def activity(self) -> Optional[BaseActivity]:
        """Optional[:class:`.BaseActivity`]: The activity being used upon
        logging in.
        """
        return create_activity(self._connection._activity)

    @activity.setter
    def activity(self, value: Optional[BaseActivity]):
        if value is None:
            self._connection._activity = None
        elif isinstance(value, BaseActivity):
            self._connection._activity = value.to_dict()
        else:
            raise TypeError('activity must derive from BaseActivity.')

    @property
    def allowed_mentions(self) -> Optional[AllowedMentions]:
        """Optional[:class:`~discord.AllowedMentions`]: The allowed mention configuration.

        .. versionadded:: 1.4
        """
        return self._connection.allowed_mentions

    @allowed_mentions.setter
    def allowed_mentions(self, value: Optional[AllowedMentions]):
        if value is None or isinstance(value, AllowedMentions):
            self._connection.allowed_mentions = value
        else:
            raise TypeError('allowed_mentions must be AllowedMentions not {0.__class__!r}'.format(value))

    @property
    def intents(self) -> Intents:
        """:class:`~discord.Intents`: The intents configured for this connection.

        .. versionadded:: 1.5
        """
        return self._connection.intents

    # helpers/getters

    @property
    def users(self) -> List[User]:
        """List[:class:`~discord.User`]: Returns a list of all the users the bot can see."""
        return list(self._connection._users.values())

    def get_message(self, id: int) -> Optional[Message]:
        """Returns a :class:`~discord.Message` with the given ID if it exists in the cache, else :obj:`None`"""
        return self._connection._get_message(id)

    def get_channel(self, id: int) -> Optional[Union[Messageable, GuildChannel]]:
        """Returns a channel with the given ID.

        Parameters
        -----------
        id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[Union[:class:`.abc.GuildChannel`, :class:`.abc.PrivateChannel`]]
            The returned channel or ``None`` if not found.
        """
        return self._connection.get_channel(id)

    def get_partial_messageable(
            self,
            id: int,
            *,
            guild_id: Optional[int] = None,
            type: Optional[ChannelType] = None
    ) -> PartialMessageable:
        """Returns a :class:`~discord.PartialMessageable` with the given channel ID.
        This is useful if you have the ID of a channel but don't want to do an API call
        to send messages to it.

        Parameters
        -----------
        id: :class:`int`
            The channel ID to create a :class:`~discord.PartialMessageable` for.
        guild_id: Optional[:class:`int`]
            The optional guild ID to create a :class:`~discord.PartialMessageable` for.
            This is not required to actually send messages, but it does allow the
            :meth:`~discord.PartialMessageable.jump_url` and
            :attr:`~discord.PartialMessageable.guild` properties to function properly.
        type: Optional[:class:`.ChannelType`]
            The underlying channel type for the :class:`~discord.PartialMessageable`.

        Returns
        --------
        :class:`.PartialMessageable`
            The partial messageable created
        """
        return PartialMessageable(state=self._connection, id=id, guild_id=guild_id, type=type)

    def get_guild(self, id: int) -> Optional[Guild]:
        """Returns a guild with the given ID.

        Parameters
        -----------
        id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`.Guild`]
            The guild or ``None`` if not found.
        """
        return self._connection._get_guild(id)

    def get_user(self, id: int) -> Optional[User]:
        """Returns a user with the given ID.

        Parameters
        -----------
        id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`~discord.User`]
            The user or ``None`` if not found.
        """
        return self._connection.get_user(id)

    def get_emoji(self, id: int) -> Optional[Emoji]:
        """Returns an emoji with the given ID.

        Parameters
        -----------
        id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`.Emoji`]
            The custom emoji or ``None`` if not found.
        """
        return self._connection.get_emoji(id)

    def get_all_channels(self) -> Iterator[GuildChannel]:
        """A generator that retrieves every :class:`.abc.GuildChannel` the client can 'access'.

        This is equivalent to: ::

            for guild in client.guilds:
                for channel in guild.channels:
                    yield channel

        .. note::

            Just because you receive a :class:`.abc.GuildChannel` does not mean that
            you can communicate in said channel. :meth:`.abc.GuildChannel.permissions_for` should
            be used for that.

        Yields
        ------
        :class:`.abc.GuildChannel`
            A channel the client can 'access'.
        """

        for guild in self.guilds:
            for channel in guild.channels:
                yield channel

    def get_all_members(self) -> Iterator[Member]:
        """Returns a generator with every :class:`.Member` the client can see.

        This is equivalent to: ::

            for guild in client.guilds:
                for member in guild.members:
                    yield member

        Yields
        ------
        :class:`.Member`
            A member the client can see.
        """
        for guild in self.guilds:
            for member in guild.members:
                yield member

    # listeners/waiters

    async def wait_until_ready(self) -> None:
        """|coro|

        Waits until the client's internal cache is all ready.
        """
        await self._ready.wait()

    def wait_for(
            self,
            event: str,
            *,
            check: Optional[Callable[[Any, ...], bool]] = None,
            timeout: Optional[float] = None
    ) -> Coroutine[Any, Any, Any]:
        """|coro|

        Waits for a WebSocket event to be dispatched.

        This could be used to wait for a user to reply to a message,
        or to react to a message, or to edit a message in a self-contained
        way.

        The ``timeout`` parameter is passed onto :func:`asyncio.wait_for`. By default,
        it does not timeout. Note that this does propagate the
        :exc:`asyncio.TimeoutError` for you in case of timeout and is provided for
        ease of use.

        In case the event returns multiple arguments, a :class:`tuple` containing those
        arguments is returned instead. Please check the
        :ref:`documentation <discord-api-events>` for a list of events and their
        parameters.

        This function returns the **first event that meets the requirements**.

        Examples
        ---------

        Waiting for a user reply: ::

            @client.event
            async def on_message(message):
                if message.content.startswith('$greet'):
                    channel = message.channel
                    await channel.send('Say hello!')

                    def check(m):
                        return m.content == 'hello' and m.channel == channel

                    msg = await client.wait_for('message', check=check)
                    await channel.send('Hello {.author}!'.format(msg))

        Waiting for a thumbs up reaction from the message author: ::

            @client.event
            async def on_message(message):
                if message.content.startswith('$thumb'):
                    channel = message.channel
                    await channel.send('Send me that \N{THUMBS UP SIGN} reaction, mate')

                    def check(reaction, user):
                        return user == message.author and str(reaction.emoji) == '\N{THUMBS UP SIGN}'

                    try:
                        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                    except asyncio.TimeoutError:
                        await channel.send('\N{THUMBS DOWN SIGN}')
                    else:
                        await channel.send('\N{THUMBS UP SIGN}')


        Parameters
        ------------
        event: :class:`str`
            The event name, similar to the :ref:`event reference <discord-api-events>`,
            but without the ``on_`` prefix, to wait for.
        check: Optional[Callable[..., :class:`bool`]]
            A predicate to check what to wait for. The arguments must meet the
            parameters of the event being waited for.
        timeout: Optional[:class:`float`]
            The number of seconds to wait before timing out and raising
            :exc:`asyncio.TimeoutError`.

        Raises
        -------
        asyncio.TimeoutError
            If a timeout is provided, and it was reached.

        Returns
        --------
        Any
            Returns no arguments, a single argument, or a :class:`tuple` of multiple
            arguments that mirrors the parameters passed in the
            :ref:`event reference <discord-api-events>`.
        """

        future = self.loop.create_future()
        if check is None:
            def _check(*args):
                return True
            check = _check
        ev = event.lower()
        try:
            listeners = self._listeners[ev]
        except KeyError:
            listeners = []
            self._listeners[ev] = listeners

        listeners.append((future, check))
        return asyncio.wait_for(future, timeout)

    # event registration

    def event(self, coro: Coro) -> Coro:
        """A decorator that registers an event to listen to.

        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.

        The events must be a :ref:`coroutine <coroutine>`, if not, :exc:`TypeError` is raised.

        Example
        ---------
        .. code-block:: python3

            @client.event
            async def on_ready():
                print('Ready!')

        Raises
        --------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('event registered must be a coroutine function')

        setattr(self, coro.__name__, coro)
        log.debug('%s has successfully been registered as an event', coro.__name__)
        return coro

    def once(
            self, name: str = MISSING, check: Callable[..., bool] | None = None
    ) -> Coro:
        """A decorator that registers an event to listen to only once.
        For example if you want to perform a database connection once the bot is ready.

        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.

        The events must be a :ref:`coroutine <coroutine>`, if not, :exc:`TypeError` is raised.

        Parameters
        ----------
        name: :class:`str`
            The name of the event we want to listen to. This is passed to
            :meth:`~discord.Client.wait_for`. Defaults to ``func.__name__``.
        check: Optional[Callable[..., :class:`bool`]]
            A predicate to check what to wait for. The arguments must meet the
            parameters of the event being waited for.

        Raises
        ------
        TypeError
            The coroutine passed is not actually a coroutine.

        Example
        -------

        .. code-block:: python

            @client.once()
            async def ready():
                print('Beep bop, I\\'m ready!')

            @client.once(check=lambda msg: msg.author.id == 693088765333471284)
            async def message(message):
                await message.reply('Hey there, how are you?')
        """

        def decorator(func: Coro) -> Coro:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("event registered must be a coroutine function")

            async def wrapped() -> None:
                nonlocal name
                nonlocal check

                name = func.__name__ if name is MISSING else name
                if name[:3] == 'on_':
                    name = name[3:]

                args = await self.wait_for(name, check=check)

                arg_len = func.__code__.co_argcount
                if arg_len == 0 and args is None:
                    await func()
                elif arg_len == 1:
                    await func(args)
                else:
                    await func(*args)

            self.loop.create_task(wrapped())
            return func

        return decorator

    def on_click(
            self,
            custom_id: Optional[Union[Pattern[AnyStr], AnyStr]] = None
    ) -> Callable[[_ClickCallback], _ClickCallback]:
        """
         A decorator with wich you can assign a function to a specific :class:`~discord.Button` (or its custom_id).

        .. important::
            The function this is attached to must take the same parameters as a
            :func:`~discord.on_raw_button_click` event.

        .. warning::
            The func must be a coroutine, if not, :exc:`TypeError` is raised.

        Parameters
        ----------
        custom_id: Optional[Union[Pattern[AnyStr], AnyStr]]
            If the :attr:`custom_id` of the :class:`~discord.Button` could not be used as a function name,
            or you want to give the function a different name then the custom_id use this one to set the custom_id.
            You can also specify a regex and if the custom_id matches it, the function will be executed.

            .. note::
                As the ``custom_id`` is converted to a |pattern_object| put ``^`` in front and ``$`` at the end
                of the :attr:`custom_id` if you want that the custom_id must exactly match the specified value.
                Otherwise, something like 'cool blue Button is blue' will let the function bee invoked too.

        Example
        -------
        .. code-block:: python

            # the button
            Button(label='Hey im a cool blue Button',
                    custom_id='cool blue Button',
                    style=ButtonStyle.blurple)

            # function that's called when the button pressed
            @client.on_click(custom_id='^cool blue Button$')
            async def cool_blue_button(i: discord.ComponentInteraction, button: Button):
                await i.respond(f'Hey you pressed a {button.custom_id}!', hidden=True)

        Returns
        -------
        The decorator for the function called when the button clicked

        Raise
        -----
        :exc:`TypeError`
            The coroutine passed is not actually a coroutine.
        """
        def decorator(func: _ClickCallback) -> _ClickCallback:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('event registered must be a coroutine function')

            _custom_id = re.compile(custom_id) if (
                    custom_id is not None and not isinstance(custom_id, re.Pattern)
            ) else re.compile(f'^{func.__name__}$')

            try:
                listeners = self._listeners['raw_button_click']
            except KeyError:
                listeners = []
                self._listeners['raw_button_click'] = listeners

            def _check(i: ComponentInteraction, c: Button) -> bool:
                match = _custom_id.match(str(c.custom_id))
                if match:
                    i.match = match
                    return True
                return False

            listeners.append((func, _check))
            return func

        return decorator

    def on_select(
            self,
            custom_id: Optional[Union[Pattern[AnyStr], AnyStr]] = None
    ) -> Callable[[_SelectCallback], _SelectCallback]:
        """
        A decorator with which you can assign a function to a specific :class:`~discord.SelectMenu` (or its custom_id).

        .. important::
            The function this is attached to must take the same parameters as a
            :func:`~discord.on_raw_selection_select` event.

        .. warning::
            The func must be a coroutine, if not, :exc:`TypeError` is raised.

        Parameters
        -----------
        custom_id: Optional[Union[Pattern[AnyStr], AnyStr]] = None
            If the `custom_id` of the :class:`~discord.SelectMenu` could not be used as a function name,
            or you want to give the function a different name then the custom_id use this one to set the custom_id.
            You can also specify a regex and if the custom_id matches it, the function will be executed.

            .. note::
                As the ``custom_id`` is converted to a |pattern_object| put ``^`` in front and ``$`` at the end
                of the :attr:`custom_id` if you want that the custom_id must exactly match the specified value.
                Otherwise, something like 'choose_your_gender later' will let the function bee invoked too.

        Example
        -------
        .. code-block:: python

            # the SelectMenu
            SelectMenu(custom_id='choose_your_gender',
                       options=[
                           SelectOption(label='Female', value='Female', emoji='♀️'),
                           SelectOption(label='Male', value='Male', emoji='♂️'),
                           SelectOption(label='Trans/Non Binary', value='Trans/Non Binary', emoji='⚧')
                       ], placeholder='Choose your Gender')

            # function that's called when the SelectMenu is used
            @client.on_select()
            async def choose_your_gender(i: discord.Interaction, select_menu):
                await i.respond(f'You selected `{select_menu.values[0]}`!', hidden=True)

        Raises
        -------
        :exc:`TypeError`
            The coroutine passed is not actually a coroutine.
        """
        def decorator(func: _SelectCallback) -> _SelectCallback:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('event registered must be a coroutine function')

            _custom_id = re.compile(custom_id) if (
                    custom_id is not None and not isinstance(custom_id, re.Pattern)
            ) else re.compile(f'^{func.__name__}$')

            try:
                listeners = self._listeners['raw_selection_select']
            except KeyError:
                listeners = []
                self._listeners['raw_selection_select'] = listeners

            def _check(i: ComponentInteraction, c: Button) -> bool:
                match = _custom_id.match(str(c.custom_id))
                if match:
                    i.match = match
                    return True
                return False

            listeners.append((func, _check))
            return func

        return decorator

    def on_submit(
            self,
            custom_id: Optional[Union[Pattern[AnyStr], AnyStr]] = None
    ) -> Callable[[_SubmitCallback], _SubmitCallback]:
        """
         A decorator with wich you can assign a function to a specific :class:`~discord.Modal` (or its custom_id).

        .. important::
            The function this is attached to must take the same parameters as a
            :func:`~discord.on_modal_submit` event.

        .. warning::
            The func must be a coroutine, if not, :exc:`TypeError` is raised.


        Parameters
        ----------
        custom_id: Optional[Union[Pattern[AnyStr], AnyStr]]
            If the :attr:`~discord.Modal.custom_id` of the modal could not be used as a function name,
            or you want to give the function a different name then the custom_id use this one to set the custom_id.
            You can also specify a regex and if the custom_id matches it, the function will be executed.

            .. note::
                As the ``custom_id`` is converted to a |pattern_object| put ``^`` in front and ``$`` at the end
                of the :attr:`custom_id` if you want that the custom_id must exactly match the specified value.
                Otherwise, something like 'suggestions_modal_submit_private' will let the function bee invoked too.

            .. tip::
                The resulting |match_object| object will be
                available under the :class:`~discord.ModalSubmitInteraction.match` attribute of the interaction.

                **See example below.**

        Examples
        --------
        .. code-block:: python
            :caption: Simple example of a Modal with a custom_id and a function that's called when the Modal is submitted.
            :emphasize-lines: 9, 14

            # the Modal
            Modal(
                title='Create a new suggestion',
                custom_id='suggestions_modal',
                components=[...]
            )

            # function that's called when the Modal is submitted
            @client.on_submit(custom_id='^suggestions_modal$')
            async def suggestions_modal_callback(i: discord.ModalSubmitInteraction):
                ...

            # This can also be done based on the function name
            @client.on_submit()
            async def suggestions_modal(i: discord.ModalSubmitInteraction):
                ...


        .. code-block:: python
            :caption: You can also use a more advanced RegEx containing groups to easily allow dynamic custom-id's
            :emphasize-lines: 1, 3

            @client.on_submit(custom_id='^ticket_answer:(?P<id>[0-9]+)$')
            async def ticket_answer_callback(i: discord.ModalSubmitInteraction):
                user_id = int(i.match['id'])
                user = client.get_user(user_id) or await client.fetch_user(user_id)

        Raises
        ------
        :exc:`TypeError`
            The coroutine passed is not actually a coroutine.
        """
        def decorator(func: _SubmitCallback) -> _SubmitCallback:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('event registered must be a coroutine function')

            _custom_id = re.compile(custom_id) if (
                    custom_id is not None and not isinstance(custom_id, re.Pattern)
            ) else re.compile(f'^{func.__name__}$')

            try:
                listeners = self._listeners['modal_submit']
            except KeyError:
                listeners = []
                self._listeners['modal_submit'] = listeners

            def _check(i: ModalSubmitInteraction) -> bool:
                match = _custom_id.match(str(i.custom_id))
                if match:
                    i.match = match
                    return True
                return False

            listeners.append((func, _check))
            return func

        return decorator

    def slash_command(
            self,
            name: Optional[str] = None,
            name_localizations: Optional[Localizations] = Localizations(),
            description: Optional[str] = None,
            description_localizations: Optional[Localizations] = Localizations(),
            allow_dm: bool = MISSING,
            is_nsfw: bool = MISSING,
            default_required_permissions: Optional[Permissions] = None,
            options: Optional[List] = [],
            guild_ids: Optional[List[int]] = None,
            connector: Optional[dict] = {},
            option_descriptions: Optional[dict] = {},
            option_descriptions_localizations: Optional[Dict[str, Localizations]] = {},
            base_name: Optional[str] = None,
            base_name_localizations: Optional[Localizations] = Localizations(),
            base_desc: Optional[str] = None,
            base_desc_localizations: Optional[Localizations] = Localizations(),
            group_name: Optional[str] = None,
            group_name_localizations: Optional[Localizations] = Localizations(),
            group_desc: Optional[str] = None,
            group_desc_localizations: Optional[Localizations] = Localizations()
    ) -> Callable[
        [Awaitable[Any]],
        Union[SlashCommand, GuildOnlySlashCommand, SubCommand, GuildOnlySubCommand]
    ]:
        """A decorator that adds a slash-command to the client. The function this is attached to must be a :ref:`coroutine <coroutine>`.

        .. warning::
            :attr:`~discord.Client.sync_commands` of the :class:`Client` instance  must be set to :obj:`True`
            to register a command if it does not already exist and update it if changes where made.

        .. note::
            Any of the following parameters are only needed when the corresponding target was not used before
            (e.g. there is already a command in the code that has these parameters set) - otherwise it will replace the previous value:

            - ``allow_dm``
            - ``is_nsfw``
            - ``base_name_localizations``
            - ``base_desc``
            - ``base_desc_localizations``
            - ``group_name_localizations``
            - ``group_desc``
            - ``group_desc_localizations``

        Parameters
        -----------
        name: Optional[:class:`str`]
            The name of the command. Must only contain a-z, _ and - and be 1-32 characters long.
            Default to the functions name.
        name_localizations: Optional[:class:`~discord.Localizations`]
            Localizations object for name field. Values follow the same restrictions as :attr:`name`
        description: Optional[:class:`str`]
            The description of the command shows up in the client. Must be between 1-100 characters long.
            Default to the functions docstring or "No Description".
        description_localizations: Optional[:class:`~discord.Localizations`]
            Localizations object for description field. Values follow the same restrictions as :attr:`description`
        allow_dm: Optional[:class:`bool`]
            Indicates whether the command is available in DMs with the app, only for globally-scoped commands.
            By default, commands are visible.
        is_nsfw: :class:`bool`
            Whether this command is an `NSFW command <https://support.discord.com/hc/en-us/articles/10123937946007>`_, default :obj:`False`

            .. note::
                Currently all sub-commands of a command that is marked as *NSFW* are NSFW too.

        default_required_permissions: Optional[:class:`~discord.Permissions`]
             Permissions that a Member needs by default to execute(see) the command.
        options: Optional[List[:class:`~discord.SlashCommandOption`]]
            A list of max. 25 options for the command. If not provided the options will be generated
            using :meth:`generate_options` that creates the options out of the function parameters.
            Required options **must** be listed before optional ones.
            Use :attr:`options` to connect non-ascii option names with the parameter of the function.
        guild_ids: Optional[List[:class:`int`]]
            ID's of guilds this command should be registered in. If empty, the command will be global.
        connector: Optional[Dict[:class:`str`, :class:`str`]]
            A dictionary containing the name of function-parameters as keys and the name of the option as values.
            Useful for using non-ascii Letters in your option names without getting ide-errors.
        option_descriptions: Optional[Dict[:class:`str`, :class:`str`]]
            Descriptions the :func:`generate_options` should take for the Options that will be generated.
            The keys are the :attr:`~discord.SlashCommandOption.name` of the option and the value the :attr:`~discord.SlashCommandOption.description`.

            .. note::
                This will only be used if ``options`` is not set.

        option_descriptions_localizations: Optional[Dict[:class:`str`, :class:`~discord.Localizations`]]
            Localized :attr:`~discord.SlashCommandOption.description` for the options.
            In the format ``{'option_name': Localizations(...)}``
        base_name: Optional[:class:`str`]
            The name of the base-command(a-z, _ and -, 1-32 characters) if you want the command
            to be in a command-/sub-command-group.
            If the base-command does not exist yet, it will be added.
        base_name_localizations: Optional[:class:`~discord.Localizations`]
            Localized ``base_name``'s for the command.
        base_desc: Optional[:class:`str`]
            The description of the base-command(1-100 characters).
        base_desc_localizations: Optional[:class:`~discord.Localizations`]
            Localized ``base_description``'s for the command.
        group_name: Optional[:class:`str`]
            The name of the command-group(a-z, _ and -, 1-32 characters) if you want the command to be in a sub-command-group.
        group_name_localizations: Optional[:class:`~discord.Localizations`]
            Localized ``group_name``'s for the command.
        group_desc: Optional[:class:`str`]
            The description of the sub-command-group(1-100 characters).
        group_desc_localizations: Optional[:class:`~discord.Localizations`]
            Localized ``group_desc``'s for the command.

        Raises
        ------
        :exc:`TypeError`:
            The function the decorator is attached to is not actual a :ref:`coroutine <coroutine>`
            or a parameter passed to :class:`SlashCommandOption` is invalid for the ``option_type`` or the ``option_type``
            itself is invalid.
        :exc:`~discord.InvalidArgument`:
            You passed ``group_name`` but no ``base_name``.
        :exc:`ValueError`:
            Any of ``name``, ``description``, ``options``, ``base_name``, ``base_desc``, ``group_name`` or ``group_desc`` is not valid.

        Returns
        -------
        Union[:class:`SlashCommand`, :class:`GuildOnlySlashCommand`, :class:`SubCommand`, :class:`GuildOnlySubCommand`]:
            - If neither ``guild_ids`` nor ``base_name`` passed: An instance of :class:`~discord.SlashCommand`.
            - If ``guild_ids`` and no ``base_name`` where passed: An instance of :class:`~discord.GuildOnlySlashCommand` representing the guild-only slash-commands.
            - If ``base_name`` and no ``guild_ids`` where passed: An instance of :class:`~discord.SubCommand`.
            - If ``base_name`` and ``guild_ids`` passed: instance of :class:`~discord.GuildOnlySubCommand` representing the guild-only sub-commands.
        """

        def decorator(func: Awaitable[Any]) -> Union[SlashCommand, GuildOnlySlashCommand, SubCommand, GuildOnlySubCommand]:
            """

            Parameters
            ----------
            func: Awaitable[Any]
                The function for the decorator. This must be a :ref:`coroutine <coroutine>`.

            Returns
            -------
            The slash-command registered.
                - If neither ``guild_ids`` nor ``base_name`` passed: An instance of :class:`~discord.SlashCommand`.
                - If ``guild_ids`` and no ``base_name`` where passed: An instance of :class:`~discord.GuildOnlySlashCommand` representing the guild-only slash-commands.
                - If ``base_name` and no ``guild_ids`` where passed: An instance of :class:`~discord.SubCommand`.
                - If ``base_name`` and ``guild_ids`` passed: instance of :class:`~discord.GuildOnlySubCommand` representing the guild-only sub-commands.
            """
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The slash-command registered  must be a coroutine.')
            _name = (name or func.__name__).lower()
            _description = description if description else (inspect.cleandoc(func.__doc__)[:100] if func.__doc__ else 'No Description')
            _options = options or generate_options(
                func,
                descriptions=option_descriptions,
                descriptions_localizations=option_descriptions_localizations,
                connector=connector
            )
            if group_name and not base_name:
                raise InvalidArgument(
                    'You have to provide the `base_name` parameter if you want to create a sub-command or sub-command-group.'
                )
            guild_cmds = []
            if guild_ids:
                guild_app_cmds = self._guild_specific_application_commands
                for guild_id in guild_ids:
                    base, base_command, sub_command_group = None, None, None
                    try:
                        guild_app_cmds[guild_id]
                    except KeyError:
                        guild_app_cmds[guild_id] = {'chat_input': {}, 'message': {}, 'user': {}}
                    if base_name:
                        try:
                            base_command = guild_app_cmds[guild_id]['chat_input'][base_name]
                        except KeyError:
                            base_command = guild_app_cmds[guild_id]['chat_input'][base_name] = SlashCommand(
                                name=base_name,
                                name_localizations=base_name_localizations,
                                description=base_desc or 'No Description',
                                description_localizations=base_desc_localizations,
                                default_member_permissions=default_required_permissions,
                                is_nsfw=is_nsfw if is_nsfw is not MISSING else False,
                                guild_id=guild_id
                            )
                        else:

                            if base_desc:
                                base_command.description = base_command.description
                            if is_nsfw is not MISSING:
                                base_command.is_nsfw = is_nsfw
                            if allow_dm is not MISSING:
                                base_command.allow_dm = allow_dm
                            base_command.name_localizations.update(base_name_localizations)
                            base_command.description_localizations.update(base_desc_localizations)
                        base = base_command
                    if group_name:
                        try:
                            sub_command_group = guild_app_cmds[guild_id]['chat_input'][base_name]._sub_commands[group_name]
                        except KeyError:
                            sub_command_group = guild_app_cmds[guild_id]['chat_input'][base_name]._sub_commands[group_name] = SubCommandGroup(
                                parent=base_command,
                                name=group_name,
                                name_localizations=group_name_localizations,
                                description=group_desc or 'No Description',
                                description_localizations=group_desc_localizations,
                                guild_id=guild_id
                            )
                        else:
                            if group_desc:
                                sub_command_group.description = group_desc
                            sub_command_group.name_localizations.update(group_name_localizations)
                            sub_command_group.description_localizations.update(group_desc_localizations)
                        base = sub_command_group
                    if base:
                        base._sub_commands[_name] = SubCommand(
                            parent=base,
                            name=_name,
                            name_localizations=name_localizations,
                            description=_description,
                            description_localizations=description_localizations,
                            options=_options,
                            connector=connector,
                            func=func
                        )
                        guild_cmds.append(base._sub_commands[_name])
                    else:
                        guild_app_cmds[guild_id]['chat_input'][_name] = SlashCommand(
                            func=func,
                            guild_id=guild_id,
                            name=_name,
                            name_localizations=name_localizations,
                            description=_description,
                            description_localizations=description_localizations,
                            default_member_permissions=default_required_permissions,
                            is_nsfw=is_nsfw if is_nsfw is not MISSING else False,
                            options=_options,
                            connector=connector
                        )
                        guild_cmds.append(guild_app_cmds[guild_id]['chat_input'][_name])
                if base_name:
                    base = GuildOnlySlashCommand(
                        client=self,
                        guild_ids=guild_ids,
                        name=_name,
                        description=_description,
                        default_member_permissions=default_required_permissions,
                        is_nsfw=is_nsfw if is_nsfw is not MISSING else False,
                        options=_options
                    )
                    if group_name:
                        base = GuildOnlySubCommandGroup(
                            client=self,
                            parent=base,
                            guild_ids=guild_ids,
                            name=_name,
                            description=_description,
                            default_member_permissions=default_required_permissions,
                            options=_options
                        )
                    return GuildOnlySubCommand(
                        client=self,
                        parent=base,
                        func=func,
                        guild_ids=guild_ids,
                        commands=guild_cmds,
                        name=_name,
                        description=_description,
                        options=_options,
                        connector=connector
                    )
                return GuildOnlySlashCommand(
                    client=self,
                    func=func,
                    guild_ids=guild_ids,
                    commands=guild_cmds,
                    name=_name,
                    description=_description,
                    default_member_permission=default_required_permissions,
                    is_nsfw=is_nsfw if is_nsfw is not MISSING else False,
                    options=_options,
                    connector=connector
                )
            else:
                app_cmds = self._application_commands_by_type
                base, base_command, sub_command_group = None, None, None
                if base_name:
                    try:
                        base_command = app_cmds['chat_input'][base_name]
                    except KeyError:
                        base_command = app_cmds['chat_input'][base_name] = SlashCommand(
                            name=base_name,
                            name_localizations=base_name_localizations,
                            description=base_desc or 'No Description',
                            description_localizations=base_desc_localizations,
                            default_member_permissions=default_required_permissions,
                            allow_dm=allow_dm if allow_dm is not MISSING else True,
                            is_nsfw=is_nsfw if is_nsfw is not MISSING else False
                        )
                    else:
                        if base_desc:
                            base_command.description = base_desc
                        if is_nsfw is not MISSING:
                            base_command.is_nsfw = is_nsfw
                        if allow_dm is not MISSING:
                            base_command.allow_dm = allow_dm
                        base_command.name_localizations.update(base_name_localizations)
                        base_command.description_localizations.update(base_desc_localizations)
                    base = base_command
                if group_name:
                    try:
                        sub_command_group = app_cmds['chat_input'][base_name]._sub_commands[group_name]
                    except KeyError:
                        sub_command_group = app_cmds['chat_input'][base_name]._sub_commands[group_name] = SubCommandGroup(
                            parent=base_command,
                            name=group_name,
                            name_localizations=group_name_localizations,
                            description=group_desc or 'No Description',
                            description_localizations=group_desc_localizations
                        )
                    else:
                        if group_desc:
                            sub_command_group.description = group_desc
                        sub_command_group.name_localizations.update(group_name_localizations)
                        sub_command_group.description_localizations.update(group_desc_localizations)
                    base = sub_command_group
                if base:
                    command = base._sub_commands[_name] = SubCommand(
                        parent=base,
                        func=func,
                        name=_name,
                        name_localizations=name_localizations,
                        description=_description,
                        description_localizations=description_localizations,
                        options=_options,
                        connector=connector
                    )
                else:
                    command = app_cmds['chat_input'][_name] = SlashCommand(
                        func=func,
                        name=_name,
                        name_localizations=name_localizations,
                        description=_description or 'No Description',
                        description_localizations=description_localizations,
                        default_member_permissions=default_required_permissions,
                        allow_dm=allow_dm if allow_dm is not MISSING else True,
                        is_nsfw=is_nsfw if is_nsfw is not MISSING else False,
                        options=_options,
                        connector=connector
                    )

                return command
        return decorator

    def message_command(
            self,
            name: Optional[str] = None,
            name_localizations: Localizations = Localizations(),
            default_required_permissions: Optional[Permissions] = None,
            allow_dm: bool = True,
            is_nsfw: bool = False,
            guild_ids: Optional[List[int]] = None
    ) -> Callable[[Awaitable[Any]], MessageCommand]:
        """
        A decorator that registers a :class:`MessageCommand` (shows up under ``Apps`` when right-clicking on a message)
        to the client. The function this is attached to must be a :ref:`coroutine <coroutine>`.

        .. note::

            :attr:`~discord.Client.sync_commands` of the :class:`~discord.Client` instance  must be set to :obj:`True`
            to register a command if it does not already exit and update it if changes where made.

        Parameters
        ----------
        name: Optional[:class:`str`]
            The name of the message-command, default to the functions name.
            Must be between 1-32 characters long.
        name_localizations: :class:`Localizations`
            Localized ``name``'s.
        default_required_permissions: Optional[:class:`Permissions`]
            Permissions that a member needs by default to execute(see) the command.
        allow_dm: :class:`bool`
            Indicates whether the command is available in DMs with the app, only for globally-scoped commands.
            By default, commands are visible.
        is_nsfw: :class:`bool`
            Whether this command is an `NSFW command <https://support.discord.com/hc/en-us/articles/10123937946007>`_, default :obj:`False`.
        guild_ids: Optional[List[:class:`int`]]
            ID's of guilds this command should be registered in. If empty, the command will be global.

        Returns
        -------
        ~discord.MessageCommand:
            The message-command registered.

        Raises
        ------
        :exc:`TypeError`:
            The function the decorator is attached to is not actual a :ref:`coroutine <coroutine>`.
        """
        def decorator(func: Awaitable[Any]) -> MessageCommand:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The message-command function registered  must be a coroutine.')
            _name = name or func.__name__
            cmd = MessageCommand(
                guild_ids=guild_ids,
                func=func,
                name=_name,
                name_localizations=name_localizations,
                default_member_permissions=default_required_permissions,
                allow_dm=allow_dm,
                is_nsfw=is_nsfw
            )
            if guild_ids:
                for guild_id in guild_ids:
                    guild_cmd = MessageCommand(
                        guild_id=guild_id,
                        func=func,
                        name=_name,
                        name_localizations=name_localizations,
                        default_member_permissions=default_required_permissions,
                        allow_dm=allow_dm,
                        is_nsfw=is_nsfw
                    )
                    try:
                        self._guild_specific_application_commands[guild_id]['message'][_name] = guild_cmd
                    except KeyError:
                        self._guild_specific_application_commands[guild_id] = {
                            'chat_input': {},
                            'message': {_name: guild_cmd},
                            'user': {}
                        }
            else:
                self._application_commands_by_type['message'][_name] = cmd

            return cmd
        return decorator

    def user_command(
            self,
            name: Optional[str] = None,
            name_localizations: Localizations = Localizations(),
            default_required_permissions: Optional[Permissions] = None,
            allow_dm: bool = True,
            is_nsfw: bool = False,
            guild_ids: Optional[List[int]] = None
    ) -> Callable[[Awaitable[Any]], UserCommand]:
        """
        A decorator that registers a :class:`UserCommand` (shows up under ``Apps`` when right-clicking on a user) to the client.
        The function this is attached to must be a :ref:`coroutine <coroutine>`.

        .. note::
            :attr:`~discord.Client.sync_commands` of the :class:`~discord.Client` instance  must be set to :obj:`True`
            to register a command if it does not already exist and update it if changes where made.

        Parameters
        ----------
        name: Optional[:class:`str`]
            The name of the user-command, default to the functions name.
            Must be between 1-32 characters long.
        name_localizations: :class:`Localizations`
            Localized ``name``'s.
        default_required_permissions: Optional[:class:`Permissions`]
            Permissions that a member needs by default to execute(see) the command.
        allow_dm: :class:`bool`
            Indicates whether the command is available in DMs with the app, only for globally-scoped commands.
            By default, commands are visible.
        is_nsfw: :class:`bool`
            Whether this command is an `NSFW command <https://support.discord.com/hc/en-us/articles/10123937946007>`_, default :obj:`False`.
        guild_ids: Optional[List[:class:`int`]]
            ID's of guilds this command should be registered in. If empty, the command will be global.

        Returns
        -------
        ~discord.UserCommand:
            The user-command registered.

        Raises
        ------
        :exc:`TypeError`:
            The function the decorator is attached to is not actual a :ref:`coroutine <coroutine>`.
        """
        def decorator(func: Awaitable[Any]) -> UserCommand:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The user-command function registered  must be a coroutine.')
            _name = name or func.__name__
            cmd = UserCommand(
                guild_ids=guild_ids,
                func=func,
                name=_name,
                name_localizations=name_localizations,
                default_member_permissions=default_required_permissions,
                allow_dm=allow_dm,
                is_nsfw=is_nsfw
            )
            if guild_ids:
                for guild_id in guild_ids:
                    guild_cmd = UserCommand(
                        guild_id=guild_id,
                        func=func,
                        name=_name,
                        name_localizations=name_localizations,
                        default_member_permissions=default_required_permissions,
                        allow_dm=allow_dm,
                        is_nsfw=is_nsfw
                    )
                    try:
                        self._guild_specific_application_commands[guild_id]['user'][_name] = guild_cmd
                    except KeyError:
                        self._guild_specific_application_commands[guild_id] = {
                            'chat_input': {},
                            'message': {},
                            'user': {_name: guild_cmd}
                        }
            else:
                self._application_commands_by_type['user'][_name] = cmd

            return cmd
        return decorator

    async def _sync_commands(self) -> None:
        if not hasattr(self, 'app'):
            await self.application_info()
        state = self._connection  # Speedup attribute access
        get_commands = self.http.get_application_commands
        application_id = self.app.id

        to_send = []
        to_cep = []
        to_maybe_remove = []

        any_changed = False
        has_update = False

        log.info('Checking for changes on application-commands for application %s (%s)...', self.app.name, application_id)

        global_registered_raw: List[Dict] = await get_commands(application_id)
        global_registered: Dict[str, List[ApplicationCommand]] = ApplicationCommand._sorted_by_type(global_registered_raw)
        self._minimal_registered_global_commands_raw = minimal_registered_global_commands_raw = []

        for x, commands in global_registered.items():
            for command in commands:
                if command['name'] in self._application_commands_by_type[x].keys():
                    cmd = self._application_commands_by_type[x][command['name']]
                    if cmd != command:
                        any_changed = has_update = True
                        c = cmd.to_dict()
                        c['id'] = command['id']
                        to_send.append(c)
                    else:
                        to_cep.append(command)
                else:
                    to_maybe_remove.append(command)
                    any_changed = True
            cmd_names = [c['name'] for c in commands]
            for command in self._application_commands_by_type[x].values():
                if command.name not in cmd_names:
                    any_changed = True
                    to_send.append(command.to_dict())

        if any_changed is True:
            updated = None
            if (to_send_count := len(to_send)) == 1 and has_update and not to_maybe_remove:
                log.info('Detected changes on global application-command %s, updating.', to_send[0]['name'])
                updated = await self.http.edit_application_command(application_id, to_send[0]['id'], to_send[0])
            elif len == 1 and not has_update and not to_maybe_remove:
                log.info('Registering one new global application-command %s.', to_send[0]['name'])
                updated = await self.http.create_application_command(application_id, to_send[0])
            else:
                if to_send_count > 0:
                    log.info(
                        f'Detected %s updated/new global application-commands, bulk overwriting them...',
                        to_send_count
                    )
                if not self.delete_not_existing_commands:
                    to_send.extend(to_maybe_remove)
                else:
                    if (to_maybe_remove_count := len(to_maybe_remove)) > 0:
                        log.info(
                            'Removing %s global application-command(s) that isn\'t/arent used in this code anymore.'
                            ' To prevent this set `delete_not_existing_commands` of %s to False',
                            to_maybe_remove_count,
                            self.__class__.__name__
                        )
                to_send.extend(to_cep)
                global_registered_raw = await self.http.bulk_overwrite_application_commands(application_id, to_send)
            if updated:
                global_registered_raw = await self.http.get_application_commands(application_id)
            log.info('Synced global application-commands.')
        else:
            log.info('No changes on global application-commands found.')

        for updated in global_registered_raw:
            command_type = str(ApplicationCommandType.try_value(updated['type']))
            minimal_registered_global_commands_raw.append({'id': int(updated['id']), 'type': command_type, 'name': updated['name']})
            try:
                command = self._application_commands_by_type[command_type][updated['name']]
            except KeyError:
                command = ApplicationCommand._from_type(state, data=updated)
                command.func = None
                self._application_commands[command.id] = command
            else:
                command._fill_data(updated)
                command._state = state
                self._application_commands[command.id] = command

        log.info('Checking for changes on guild-specific application-commands...')

        any_guild_commands_changed = False
        self._minimal_registered_guild_commands_raw = minimal_registered_guild_commands_raw = {}

        for guild_id, command_types in self._guild_specific_application_commands.items():
            to_send = []
            to_cep = []
            to_maybe_remove = []
            any_changed = False
            has_update = False
            try:
                registered_guild_commands_raw = await self.http.get_application_commands(
                    application_id,
                    guild_id=guild_id
                )
            except HTTPException:
                warnings.warn(
                    'Missing access to guild %s or don\'t have the application.commands scope in there, skipping!'
                    % guild_id
                )
                continue
            minimal_registered_guild_commands_raw[int(guild_id)] = minimal_registered_guild_commands = []
            registered_guild_commands = ApplicationCommand._sorted_by_type(registered_guild_commands_raw)

            for x, commands in registered_guild_commands.items():
                for command in commands:
                    if command['name'] in self._guild_specific_application_commands[guild_id][x].keys():
                        cmd = self._guild_specific_application_commands[guild_id][x][command['name']]
                        if cmd != command:
                            any_changed = has_update = any_guild_commands_changed = True
                            c = cmd.to_dict()
                            c['id'] = command['id']
                            to_send.append(c)
                        else:
                            to_cep.append(command)
                    else:
                        to_maybe_remove.append(command)
                        any_changed = True
                cmd_names = [c['name'] for c in commands]
                for command in self._guild_specific_application_commands[guild_id][x].values():
                    if command.name not in cmd_names:
                        any_changed = True
                        to_send.append(command.to_dict())

            if any_changed is True:
                updated = None
                if len(to_send) == 1 and has_update and not to_maybe_remove:
                    log.info(
                        'Detected changes on application-command %s in guild %s (%s), updating.',
                        to_send[0]['name'],
                        self.get_guild(int(guild_id)),
                        guild_id
                    )
                    updated = await self.http.edit_application_command(
                        application_id,
                        to_send[0]['id'],
                        to_send[0],
                        guild_id
                    )
                elif len(to_send) == 1 and not has_update and not to_maybe_remove:
                    log.info(
                        'Registering one new application-command %s in guild %s (%s).',
                        to_send[0]['name'],
                        self.get_guild(int(guild_id)),
                        guild_id
                    )
                    updated = await self.http.create_application_command(application_id, to_send[0], guild_id)
                else:
                    if not self.delete_not_existing_commands:
                        if to_send:
                            to_send.extend(to_maybe_remove)
                    else:
                        if len(to_maybe_remove) > 0:
                            log.info(
                                'Removing %s application-command(s) from guild %s (%s) that isn\'t/arent used in this code anymore.'
                                'To prevent this set `delete_not_existing_commands` of %s to False',
                                len(to_maybe_remove),
                                self.get_guild(int(guild_id)),
                                guild_id,
                                self.__class__.__name__
                            )
                    if len(to_send) != 0:
                        log.info(
                            'Detected %s updated/new application-command(s) for guild %s (%s), bulk overwriting them...',
                            len(to_send),
                            self.get_guild(int(guild_id)),
                            guild_id
                        )
                    to_send.extend(to_cep)
                    registered_guild_commands_raw = await self.http.bulk_overwrite_application_commands(
                        application_id,
                        to_send,
                        guild_id
                    )
                if updated:
                    registered_guild_commands_raw = await self.http.get_application_commands(
                        application_id,
                        guild_id=guild_id
                    )
                log.info('Synced application-commands for %s (%s).' % (guild_id, self.get_guild(int(guild_id))))
                any_guild_commands_changed = True

            for updated in registered_guild_commands_raw:
                command_type = str(ApplicationCommandType.try_value(updated['type']))
                minimal_registered_guild_commands.append({'id': int(updated['id']), 'type': command_type, 'name': updated['name']})
                try:
                    command = self._guild_specific_application_commands[int(guild_id)][command_type][updated['name']]
                except KeyError:
                    command = ApplicationCommand._from_type(state, data=updated)
                    command.func = None
                    self._application_commands[command.id] = command
                    self.get_guild(int(guild_id))._application_commands[command.id] = command
                else:
                    command._fill_data(updated)
                    command._state = self._connection
                    self._application_commands[command.id] = command

        if not any_guild_commands_changed:
            log.info('No changes on guild-specific application-commands found.')

        log.info('Successful synced all global and guild-specific application-commands.')

    def _get_application_command(self, cmd_id: int) -> Optional[ApplicationCommand]:
        return self._application_commands.get(cmd_id)

    def _remove_application_command(self, command: ApplicationCommand, from_cache: bool = True):
        if isinstance(command, GuildOnlySlashCommand):
            for guild_id in command.guild_ids:
                try:
                    cmd = self._guild_specific_application_commands[guild_id][command.type.name][command.name]
                except KeyError:
                    continue
                else:
                    if from_cache:
                        del cmd
                    else:
                        cmd.disabled = True
                        self._application_commands[cmd.id] = copy.copy(cmd)
                        del cmd
            del command
        else:
            if from_cache:
                del command
            else:
                command.disabled = True
                self._application_commands[command.id] = copy.copy(command)
                if command.guild_id:
                    self._guild_specific_application_commands[command.guild_id][command.type.name].pop(command.name, None)
                else:
                    self._application_commands_by_type[command.type.name].pop(command.name, None)

    @property
    def application_commands(self) -> List[ApplicationCommand]:
        """List[:class:`ApplicationCommand`]: Returns a list of any application command that is registered for the bot`"""
        return list(self._application_commands.values())

    @property
    def global_application_commands(self) -> List[ApplicationCommand]:
        """
        Returns a list of all global application commands that are registered for the bot

        .. note::
            This requires the bot running and all commands cached, otherwise the list will be empty

        Returns
        --------
        List[:class:`ApplicationCommand`]
            A list of registered global application commands for the bot
        """
        commands = []
        for command in self.application_commands:
            if not command.guild_id:
                commands.append(command)
        return commands

    async def change_presence(
            self,
            *,
            activity: Optional[BaseActivity] = None,
            status: Optional[Status] = 'online'
    ) -> None:
        """|coro|

        Changes the client's presence.

        .. versionchanged:: 2.0
                Removed the ``afk`` parameter

        Example
        ---------

        .. code-block:: python3

            game = discord.Game("with the API")
            await client.change_presence(status=discord.Status.idle, activity=game)

        Parameters
        ----------
        activity: Optional[:class:`.BaseActivity`]
            The activity being done. ``None`` if no currently active activity is done.
        status: Optional[:class:`.Status`]
            Indicates what status to change to. If ``None``, then
            :attr:`.Status.online` is used.

        Raises
        ------
        :exc:`.InvalidArgument`
            If the ``activity`` parameter is not the proper type.
        """

        if status is None:
            status = 'online'
            status_enum = Status.online
        elif status is Status.offline:
            status = 'invisible'
            status_enum = Status.offline
        else:
            status_enum = status
            status = str(status)

        await self.ws.change_presence(activity=activity, status=status)

        for guild in self._connection.guilds:
            me = guild.me
            if me is None:
                continue

            if activity is not None:
                me.activities = (activity,)
            else:
                me.activities = ()

            me.status = status_enum

    # Guild stuff

    def fetch_guilds(
            self,
            *,
            limit: Optional[int] = 100,
            before: Union[Snowflake, datetime.datetime, None] = None,
            after: Union[Snowflake, datetime.datetime, None] = None
    ) -> GuildIterator:
        """Retrieves an :class:`.AsyncIterator` that enables receiving your guilds.

        .. note::

            Using this, you will only receive :attr:`.Guild.owner`, :attr:`.Guild.icon`,
            :attr:`.Guild.id`, and :attr:`.Guild.name` per :class:`.Guild`.

        .. note::

            This method is an API call. For general usage, consider :attr:`guilds` instead.

        Examples
        ---------

        Usage ::

            async for guild in client.fetch_guilds(limit=150):
                print(guild.name)

        Flattening into a list ::

            guilds = await client.fetch_guilds(limit=150).flatten()
            # guilds is now a list of Guild...

        All parameters are optional.

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of guilds to retrieve.
            If ``None``, it retrieves every guild you have access to. Note, however,
            that this would make it a slow operation.
            Defaults to ``100``.
        before: Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]
            Retrieves guilds before this date or object.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        after: Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]
            Retrieve guilds after this date or object.
            If a date is provided it must be a timezone-naive datetime representing UTC time.

        Raises
        ------
        discord.HTTPException
            Getting the guilds failed.

        Yields
        --------
        :class:`.Guild`
            The guild with the guild data parsed.
        """
        return GuildIterator(self, limit=limit, before=before, after=after)

    async def fetch_template(self, code: Union[Template, str]) -> Template:
        """|coro|

        Gets a :class:`.Template` from a discord.new URL or code.

        Parameters
        -----------
        code: Union[:class:`.Template`, :class:`str`]
            The Discord Template Code or URL (must be a discord.new URL).

        Raises
        -------
        :exc:`.NotFound`
            The template is invalid.
        :exc:`.HTTPException`
            Getting the template failed.

        Returns
        --------
        :class:`.Template`
            The template from the URL/code.
        """
        code = utils.resolve_template(code)
        data = await self.http.get_template(code)
        return Template(data=data, state=self._connection)

    async def fetch_guild(self, guild_id: int) -> Guild:
        """|coro|

        Retrieves a :class:`.Guild` from an ID.

        .. note::

            Using this, you will **not** receive :attr:`.Guild.channels`, :attr:`.Guild.members`,
            :attr:`.Member.activity` and :attr:`.Member.voice` per :class:`.Member`.

        .. note::

            This method is an API call. For general usage, consider :meth:`get_guild` instead.

        Parameters
        -----------
        guild_id: :class:`int`
            The guild's ID to fetch from.

        Raises
        ------
        :exc:`.Forbidden`
            You do not have access to the guild.
        :exc:`.HTTPException`
            Getting the guild failed.

        Returns
        --------
        :class:`.Guild`
            The guild from the ID.
        """
        data = await self.http.get_guild(guild_id)
        return Guild(data=data, state=self._connection)

    async def create_guild(
            self,
            name: str,
            region: Optional[VoiceRegion] = None,
            icon: Optional[bytes] = None,
            *,
            code: Optional[str] = None
    ) -> Guild:
        """|coro|

        Creates a :class:`.Guild`.

        Bot accounts in more than 10 guilds are not allowed to create guilds.

        Parameters
        ----------
        name: :class:`str`
            The name of the guild.
        region: :class:`.VoiceRegion`
            The region for the voice communication server.
            Defaults to :attr:`.VoiceRegion.us_west`.
        icon: :class:`bytes`
            The :term:`py:bytes-like object` representing the icon. See :meth:`.ClientUser.edit`
            for more details on what is expected.
        code: Optional[:class:`str`]
            The code for a template to create the guild with.

            .. versionadded:: 1.4

        Raises
        ------
        :exc:`.HTTPException`
            Guild creation failed.
        :exc:`.InvalidArgument`
            Invalid icon image format given. Must be PNG or JPG.

        Returns
        -------
        :class:`.Guild`
            The guild created. This is not the same guild that is
            added to cache.
        """
        if icon is not None:
            icon = utils._bytes_to_base64_data(icon)

        region = region or VoiceRegion.us_west
        region_value = region.value

        if code:
            data = await self.http.create_from_template(code, name, region_value, icon)
        else:
            data = await self.http.create_guild(name, region_value, icon)
        return Guild(data=data, state=self._connection)

    # Invite management

    async def fetch_invite(self, url: Union[Invite, str], *, with_counts: bool = True) -> Invite:
        """|coro|

        Gets an :class:`.Invite` from a discord.gg URL or ID.

        .. note::

            If the invite is for a guild you have not joined, the guild and channel
            attributes of the returned :class:`.Invite` will be :class:`.PartialInviteGuild` and
            :class:`.PartialInviteChannel` respectively.

        Parameters
        -----------
        url: Union[:class:`.Invite`, :class:`str`]
            The Discord invite ID or URL (must be a discord.gg URL).
        with_counts: :class:`bool`
            Whether to include count information in the invite. This fills the
            :attr:`.Invite.approximate_member_count` and :attr:`.Invite.approximate_presence_count`
            fields.

        Raises
        -------
        :exc:`.NotFound`
            The invite has expired or is invalid.
        :exc:`.HTTPException`
            Getting the invite failed.

        Returns
        --------
        :class:`.Invite`
            The invite from the URL/ID.
        """

        invite_id = utils.resolve_invite(url)
        data = await self.http.get_invite(invite_id, with_counts=with_counts)
        return Invite.from_incomplete(state=self._connection, data=data)

    async def delete_invite(self, invite: Union[Invite, str]) -> None:
        """|coro|

        Revokes an :class:`.Invite`, URL, or ID to an invite.

        You must have the :attr:`~.Permissions.manage_channels` permission in
        the associated guild to do this.

        Parameters
        ----------
        invite: Union[:class:`.Invite`, :class:`str`]
            The invite to revoke.

        Raises
        -------
        :exc:`.Forbidden`
            You do not have permissions to revoke invites.
        :exc:`.NotFound`
            The invite is invalid or expired.
        :exc:`.HTTPException`
            Revoking the invite failed.
        """

        invite_id = utils.resolve_invite(invite)
        await self.http.delete_invite(invite_id)

    # Miscellaneous stuff

    async def fetch_widget(self, guild_id: int) -> Widget:
        """|coro|

        Gets a :class:`.Widget` from a guild ID.

        .. note::

            The guild must have the widget enabled to get this information.

        Parameters
        -----------
        guild_id: :class:`int`
            The ID of the guild.

        Raises
        -------
        :exc:`.Forbidden`
            The widget for this guild is disabled.
        :exc:`.HTTPException`
            Retrieving the widget failed.

        Returns
        --------
        :class:`.Widget`
            The guild's widget.
        """
        data = await self.http.get_widget(guild_id)

        return Widget(state=self._connection, data=data)

    async def application_info(self) -> AppInfo:
        """|coro|

        Retrieves the bot's application information.

        Raises
        -------
        :exc:`.HTTPException`
            Retrieving the information failed somehow.

        Returns
        --------
        :class:`.AppInfo`
            The bot's application information.
        """
        data = await self.http.application_info()
        if 'rpc_origins' not in data:
            data['rpc_origins'] = None
        self.app = app = AppInfo(state=self._connection, data=data)
        return app

    async def fetch_user(self, user_id):
        """|coro|

        Retrieves a :class:`~discord.User` based on their ID. This can only
        be used by bot accounts. You do not have to share any guilds
        with the user to get this information, however many operations
        do require that you do.

        .. note::

            This method is an API call. If you have :attr:`Intents.members` and member cache enabled, consider :meth:`get_user` instead.

        Parameters
        -----------
        user_id: :class:`int`
            The user's ID to fetch from.

        Raises
        -------
        :exc:`.NotFound`
            A user with this ID does not exist.
        :exc:`.HTTPException`
            Fetching the user failed.

        Returns
        --------
        :class:`~discord.User`
            The user you requested.
        """
        data = await self.http.get_user(user_id)
        return User(state=self._connection, data=data)

    async def fetch_channel(self, channel_id: int):
        """|coro|

        Retrieves a :class:`.abc.GuildChannel` or :class:`.abc.PrivateChannel` with the specified ID.

        .. note::

            This method is an API call. For general usage, consider :meth:`get_channel` instead.

        .. versionadded:: 1.2

        Raises
        -------
        :exc:`.InvalidData`
            An unknown channel type was received from Discord.
        :exc:`.HTTPException`
            Retrieving the channel failed.
        :exc:`.NotFound`
            Invalid Channel ID.
        :exc:`.Forbidden`
            You do not have permission to fetch this channel.

        Returns
        --------
        Union[:class:`.abc.GuildChannel`, :class:`.abc.PrivateChannel`]
            The channel from the ID.
        """
        data = await self.http.get_channel(channel_id)

        factory, ch_type = _channel_factory(data['type'])
        if factory is None:
            raise InvalidData('Unknown channel type {type} for channel ID {id}.'.format_map(data))

        if ch_type in (ChannelType.group, ChannelType.private):
            channel = factory(me=self.user, data=data, state=self._connection)
        else:
            guild_id = int(data['guild_id'])
            guild = self.get_guild(guild_id) or Object(id=guild_id)
            channel = factory(guild=guild, state=self._connection, data=data)

        return channel

    async def fetch_webhook(self, webhook_id: int):
        """|coro|

        Retrieves a :class:`.Webhook` with the specified ID.

        Raises
        --------
        :exc:`.HTTPException`
            Retrieving the webhook failed.
        :exc:`.NotFound`
            Invalid webhook ID.
        :exc:`.Forbidden`
            You do not have permission to fetch this webhook.

        Returns
        ---------
        :class:`.Webhook`
            The webhook you requested.
        """
        data = await self.http.get_webhook(webhook_id)
        return Webhook.from_state(data, state=self._connection)

    async def fetch_all_nitro_stickers(self) -> List[StickerPack]:
        """|coro|

        Retrieves a :class:`list` with all build-in :class:`~discord.StickerPack` 's.

        Returns
        --------
        :class:`~discord.StickerPack`
            A list containing all build-in sticker-packs.
        """
        data = await self.http.get_all_nitro_stickers()
        packs = [StickerPack(state=self._connection, data=d) for d in data['sticker_packs']]
        return packs

    async def fetch_voice_regions(self) -> List[VoiceRegionInfo]:
        """|coro|

        Returns a list of :class:`.VoiceRegionInfo` that can be used when creating or editing a
        :attr:`VoiceChannel` or :attr:`StageChannel`\'s region.

        .. note::

            This method is an API call.
            For general usage, consider using the :class:`VoiceRegion` enum instead.

        Returns
        --------
        List[:class:`.VoiceRegionInfo`]
            The voice regions that can be used.
        """
        data = await self.http.get_voice_regions()
        return [VoiceRegionInfo(data=d) for d in data]

    async def create_test_entitlement(
            self,
            sku_id: int,
            target: Union[User, Guild, Snowflake],
            owner_type: Optional[Literal['guild', 'user']] = MISSING
    ) -> Entitlement:
        """|coro|

        .. note::

            This method is only temporary and probably will be removed with or even before a stable v2 release
            as discord is already redesigning the testing system based on developer feedback.

            See https://github.com/discord/discord-api-docs/pull/6502 for more information.

        Creates a test entitlement to a given :class:`SKU` for a given guild or user.
        Discord will act as though that user or guild has entitlement to your premium offering.

        After creating a test entitlement, you'll need to reload your Discord client.
        After doing so, you'll see that your server or user now has premium access.

        Parameters
        ----------
        sku_id: :class:`int`
            The ID of the SKU to create a test entitlement for.
        target: Union[:class:`User`, :class:`Guild`, :class:`Snowflake`]
            The target to create a test entitlement for.

            This can be a user, guild or just the ID, if so the owner_type parameter must be set.
        owner_type: :class:`str`
            The type of the ``target``, could be ``guild`` or ``user``.

        Returns
        --------
        :class:`Entitlement`
            The created test entitlement.
        """
        target = target.id

        if isinstance(target, Guild):
            owner_type = 1
        elif isinstance(target, User):
            owner_type = 2
        else:
            if owner_type is MISSING:
                raise TypeError('owner_type must be set if target is not a Guild or user-like object.')
            else:
                owner_type = 1 if owner_type == 'guild' else 2

        data = await self.http.create_test_entitlement(
            self.app.id,
            sku_id=sku_id,
            owner_id=target,
            owner_type=owner_type
        )
        return Entitlement(data=data, state=self._connection)

    async def delete_test_entitlement(self, entitlement_id: int) -> None:
        """|coro|

        .. note::

            This method is only temporary and probably will be removed with or even before a stable v2 release
            as discord is already redesigning the testing system based on developer feedback.

            See https://github.com/discord/discord-api-docs/pull/6502 for more information.

        Deletes a currently-active test entitlement.
        Discord will act as though that user or guild no longer has entitlement to your premium offering.

        Parameters
        ----------
        entitlement_id: :class:`int`
            The ID of the entitlement to delete.
        """
        await self.http.delete_test_entitlement(self.app.id, entitlement_id)

    async def fetch_entitlements(
            self,
            *,
            limit: int = 100,
            user: Optional[User] = None,
            guild: Optional[Guild] = None,
            sku_ids: Optional[List[int]] = None,
            before: Optional[Union[datetime.datetime, Snowflake]] = None,
            after: Optional[Union[datetime.datetime, Snowflake]] = None,
            exclude_ended: bool = False
    ) -> EntitlementIterator:
        """|coro|

        Parameters
        ----------
        limit: :class:`int`
            The maximum amount of entitlements to fetch.
            Defaults to ``100``.
        user: Optional[:class:`User`]
            The user to fetch entitlements for.
        guild: Optional[:class:`Guild`]
            The guild to fetch entitlements for.
        sku_ids: Optional[List[:class:`int`]]
            Optional list of SKU IDs to check entitlements for
        before: Optional[Union[:class:`datetime.datetime`, :class:`Snowflake`]]
            Retrieve entitlements before this date or object.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        after: Optional[Union[:class:`datetime.datetime`, :class:`Snowflake`]]
            Retrieve entitlements after this date or object.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        exclude_ended: :class:`bool`
            Whether ended entitlements should be fetched or not. Defaults to ``False``.

        Return
        ------
        :class:`AsyncIterator`
            An iterator to fetch all entitlements for the current application.
        """
        return EntitlementIterator(
            state=self._connection,
            limit=limit,
            user_id=user.id,
            guild_id=guild.id,
            sku_ids=sku_ids,
            before=before,
            after=after,
            exclude_ended=exclude_ended
        )

    async def consume_entitlement(self, entitlement_id: int) -> None:
        """|coro|

        For one-time purchase :attr:`~discord.SKUType.consumable` SKUs,
        marks a given entitlement for the user as consumed.
        :attr:`~discord.Entitlement.consumed` will be ``False`` for this entitlement
        when using :meth:`.fetch_entitlements`.

        Parameters
        ----------
        entitlement_id: :class:`int`
            The ID of the entitlement to consume.
        """
        await self.http.consume_entitlement(self.app.id, entitlement_id)
