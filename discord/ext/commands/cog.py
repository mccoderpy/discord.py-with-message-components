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

import re
import copy
import inspect

from typing import (
    Any,
    AnyStr,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Pattern,
    TypeVar,
    TYPE_CHECKING,
    Union,
)
from typing_extensions import TypeAlias

from ._types import _BaseCommand

__all__ = (
    'CogMeta',
    'Cog',
)

from discord import MISSING, InvalidArgument, Permissions
from discord.application_commands import *

if TYPE_CHECKING:
    from discord.interactions import ApplicationCommandInteraction, ComponentInteraction, ModalSubmitInteraction
    from discord.components import Button, Select
    from discord.message import Message
    from discord.user import User
    from discord.member import Member

    _Coro: TypeAlias = Coroutine[None, None, ...]
    _SelectCallback: TypeAlias = Callable[[ComponentInteraction, Select], _Coro]
    _ButtonCallback: TypeAlias = Callable[[ComponentInteraction, Button], _Coro]
    _ModalCallback: TypeAlias = Callable[[ModalSubmitInteraction], _Coro]
    _SlashCommandCallback: TypeAlias = Callable[[ApplicationCommandInteraction, ...], _Coro]
    _MessageCommandCallback: TypeAlias = Callable[[ApplicationCommandInteraction, Message], _Coro]
    _UserCommandCallback: TypeAlias = Callable[[ApplicationCommandInteraction, Union[User, Member]], _Coro]


class CogMeta(type):
    """A metaclass for defining a cog.

    Note that you should probably not use this directly. It is exposed
    purely for documentation purposes along with making custom metaclasses to intermix
    with other metaclasses such as the :class:`abc.ABCMeta` metaclass.

    For example, to create an abstract cog mixin class, the following would be done.

    .. code-block:: python3

        import abc

        class CogABCMeta(commands.CogMeta, abc.ABCMeta):
            pass

        class SomeMixin(metaclass=abc.ABCMeta):
            pass

        class SomeCogMixin(SomeMixin, commands.Cog, metaclass=CogABCMeta):
            pass

    .. note::

        When passing an attribute of a metaclass that is documented below, note
        that you must pass it as a keyword-only argument to the class creation
        like the following example:

        .. code-block:: python3

            class MyCog(commands.Cog, name='My Cog'):
                pass

    Attributes
    -----------
    name: :class:`str`
        The cog name. By default, it is the name of the class with no modification.
    description: :class:`str`
        The cog description. By default, it is the cleaned docstring of the class.

        .. versionadded:: 1.6

    command_attrs: :class:`dict`
        A list of attributes to apply to every command inside this cog. The dictionary
        is passed into the :class:`Command` options at ``__init__``.
        If you specify attributes inside the command attribute in the class, it will
        override the one specified inside this attribute. For example:

        .. code-block:: python3

            class MyCog(commands.Cog, command_attrs=dict(hidden=True)):
                @commands.command()
                async def foo(self, ctx):
                    pass # hidden -> True

                @commands.command(hidden=False)
                async def bar(self, ctx):
                    pass # hidden -> False
    """
    __application_commands_by_type__ = {'chat_input': {}, 'message': {}, 'user': {}}
    __guild_specific_application_commands__ = {}

    def __new__(cls, *args, **kwargs):
        name, bases, attrs = args
        attrs['__cog_name__'] = kwargs.pop('name', name)
        attrs['__cog_settings__'] = kwargs.pop('command_attrs', {})

        description = kwargs.pop('description', None)
        if description is None:
            description = inspect.cleandoc(attrs.get('__doc__', ''))
        attrs['__cog_description__'] = description

        commands = {}
        listeners = {}
        interaction_listeners = {}

        no_bot_cog = 'Commands or listeners must not start with cog_ or bot_ (in method {0.__name__}.{1})'

        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)
        for base in reversed(new_cls.__mro__):
            for elem, value in base.__dict__.items():
                if elem in commands:
                    del commands[elem]
                if elem in listeners:
                    del listeners[elem]

                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__
                if isinstance(value, _BaseCommand):
                    if is_static_method:
                        raise TypeError('Command in method {0}.{1!r} must not be staticmethod.'.format(base, elem))
                    if elem.startswith(('cog_', 'bot_')):
                        raise TypeError(no_bot_cog.format(base, elem))
                    commands[elem] = value

                elif inspect.iscoroutinefunction(value):
                    try:
                        getattr(value, '__cog_listener__')
                    except AttributeError:
                        try:
                            getattr(value, '__cog_interaction_listener__')
                        except AttributeError:
                            continue
                        else:
                            if elem.startswith(('cog_', 'bot_')):
                                raise TypeError(no_bot_cog.format(base, elem))
                            interaction_listeners[elem] = value
                    else:
                        if elem.startswith(('cog_', 'bot_')):
                            raise TypeError(no_bot_cog.format(base, elem))
                        listeners[elem] = value

        new_cls.__cog_commands__ = list(commands.values()) # this will be copied in Cog.__new__

        listeners_as_list = []
        for listener in listeners.values():
            for listener_name in listener.__cog_listener_names__:
                # I use __name__ instead of just storing the value, so I can inject
                # the self attribute when the time comes to add them to the bot
                listeners_as_list.append((listener_name, listener.__name__))

        new_cls.__cog_listeners__ = listeners_as_list

        interaction_listeners_as_list = []
        for interaction_listener in interaction_listeners.values():
            for listener_name, pattern in interaction_listener.__interaction_listener_names__:
                interaction_listeners_as_list.append((listener_name, interaction_listener.__name__, pattern))

        new_cls.__cog_interaction_listeners__ = interaction_listeners_as_list

        return new_cls

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

    @classmethod
    def qualified_name(cls):
        return cls.__cog_name__


def _cog_special_method(func):
    func.__cog_special_method__ = None
    return func


class Cog(metaclass=CogMeta):
    """The base class that all cogs must inherit from.

    A cog is a collection of commands, listeners, and optional state to
    help group commands together. More information on them can be found on
    the :ref:`ext_commands_cogs` page.

    When inheriting from this class, the options shown in :class:`CogMeta`
    are equally valid here.
    """

    def __new__(cls, *args, **kwargs):
        # For :old-issue:`426`, we need to store a copy of the command objects
        # since we modify them to inject `self` to them.
        # To do this, we need to interfere with the Cog creation process.
        self = super().__new__(cls)
        cmd_attrs = cls.__cog_settings__

        # Either update the command with the cog provided defaults or copy it.
        self.__cog_commands__ = tuple(c._update_copy(cmd_attrs) for c in cls.__cog_commands__)

        # set the functions of the commands to the method itself

        self.__application_commands_by_type__ = copy.copy(cls.__application_commands_by_type__)

        self.__guild_specific_application_commands__ = copy.copy(cls.__guild_specific_application_commands__)

        # TODO: solve this thing on a better way
        cls.__class__.__application_commands_by_type__ = {'chat_input': {}, 'message': {}, 'user': {}}
        cls.__class__.__guild_specific_application_commands__ = {}

        lookup = {
            cmd.qualified_name: cmd
            for cmd in self.__cog_commands__
        }

        # Update the Command instances dynamically as well
        for command in self.__cog_commands__:
            setattr(self, command.callback.__name__, command)
            parent = command.parent
            if parent is not None:
                # Get the latest parent reference
                parent = lookup[parent.qualified_name]

                # Update our parent's reference to our self
                parent.remove_command(command.name)
                parent.add_command(command)
        return self

    def get_commands(self):
        r"""
        Returns
        --------
        List[:class:`.Command`]
            A :class:`list` of :class:`.Command`\s that are
            defined inside this cog.

            .. note::

                This does not include subcommands.
        """
        return [c for c in self.__cog_commands__ if c.parent is None]

    @property
    def qualified_name(self):
        """:class:`str`: Returns the cog's specified name, not the class name."""
        return self.__cog_name__

    @property
    def description(self):
        """:class:`str`: Returns the cog's description, typically the cleaned docstring."""
        return self.__cog_description__

    @description.setter
    def description(self, description):
        self.__cog_description__ = description

    def walk_commands(self):
        """An iterator that recursively walks through this cog's commands and subcommands.

        Yields
        ------
        Union[:class:`.Command`, :class:`.Group`]
            A command or group from the cog.
        """
        from .core import GroupMixin
        for command in self.__cog_commands__:
            if command.parent is None:
                yield command
                if isinstance(command, GroupMixin):
                    yield from command.walk_commands()

    def get_listeners(self):
        """Returns a :class:`list` of (name, function) listener pairs that are defined in this cog.

        Returns
        --------
        List[Tuple[:class:`str`, :ref:`coroutine <coroutine>`]]
            The listeners defined in this cog.
        """
        return [(name, getattr(self, method_name)) for name, method_name in self.__cog_listeners__]

    @classmethod
    def _get_overridden_method(cls, method):
        """Return None if the method is not overridden. Otherwise, returns the overridden method."""
        return getattr(method.__func__, '__cog_special_method__', method)

    @classmethod
    def listener(cls, name: Optional[str] = None):
        """A decorator that marks a function as a listener.

        This is the cog equivalent of :meth:`.Bot.listen`.

        Parameters
        ------------
        name: :class:`str`
            The name of the event being listened to. If not provided, it
            defaults to the function's name.

        Raises
        --------
        TypeError
            The function is not a coroutine function or a string was not passed as
            the name.
        """

        if name is not None and not isinstance(name, str):
            raise TypeError('Cog.listener expected str but received {0.__class__.__name__!r} instead.'.format(name))

        def decorator(func):
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError('Listener function must be a coroutine function.')
            actual.__cog_listener__ = True
            to_assign = name or actual.__name__
            try:
                actual.__cog_listener_names__.append(to_assign)
            except AttributeError:
                actual.__cog_listener_names__ = [to_assign]
            # we have to return `func` instead of `actual` because
            # we need the type to be `staticmethod` for the metaclass
            # to pick it up but the metaclass unfurls the function and
            # thus the assignments need to be on the actual function
            return func
        return decorator
    
    @classmethod
    def on_click(
            cls,
            custom_id: Optional[Union[Pattern[AnyStr], AnyStr]] = None
    ) -> Callable[[_ButtonCallback], _ButtonCallback]:
        """
        A decorator with which you can assign a function to a specific :class:`~discord.Button` (or its custom_id).

        .. important::
            The function this is attached to must take the same parameters as a
            :func:`~discord.on_raw_button_click` event.

        .. warning::
            The func must be a coroutine, if not, :exc:`TypeError` is raised.

        Parameters
        ----------
        custom_id: Optional[Union[Pattern[AnyStr], AnyStr]]
            If the :attr:`custom_id` of the :class:`discord.Button` could not use as a function name,
            or you want to give the function a different name then the custom_id use this one to set the custom_id.
            You can also specify a regex and if the custom_id matches it, the function will be executed.

            .. note::
                As the ``custom_id`` is converted to a |pattern_object| put ``^`` in front and ``$`` at the end
                of the :attr:`custom_id` if you want that the custom_id must exactly match the specified value.
                Otherwise, something like 'cool blue Button is blue' will let the function bee invoked too.

        Example
        -------
        .. code-block:: python3

            # the button
            Button(label='Hey im a cool blue Button',
                   custom_id='cool blue Button',
                   style=ButtonStyle.blurple)

            # function that's called when the button pressed
            @command.Cog.on_click(custom_id='cool blue Button')
            async def cool_blue_button(self, i: discord.ComponentInteraction, button):
                await i.respond(f'Hey you pressed a `{button.custom_id}`!', hidden=True)

        Raises
        ------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        def decorator(func: _ButtonCallback) -> _ButtonCallback:
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError('event registered must be a coroutine function')
            actual.__cog_interaction_listener__ = True
            pattern = re.compile(custom_id) if (
                    custom_id is not None and not isinstance(custom_id, re.Pattern)
            ) else re.compile(f'^{actual.__name__}$')
            try:
                actual.__interaction_listener_names__.append(('raw_button_click', pattern))
            except AttributeError:
                actual.__interaction_listener_names__ = [('raw_button_click', pattern)]
            return func
        return decorator

    @classmethod
    def on_select(
            cls,
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
        custom_id: Optional[Union[Pattern[AnyStr], AnyStr]]
            If the :attr:`custom_id` of the :class:`~discord.SelectMenu` could not use as a function name,
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
                            select_option(label='Female', value='Female', emoji='♀️'),
                            select_option(label='Male', value='Male', emoji='♂️'),
                            select_option(label='Trans/Non Binary', value='Trans/Non Binary', emoji='⚧')
                            ], placeholder='Choose your Gender')

            # function that's called when the SelectMenu is used
            @commands.Cog.on_select()
            async def choose_your_gender(self, i: discord.ComponentInteraction, select_menu):
                await i.respond(f'You selected `{select_menu.values[0]}`!', hidden=True)

        Raises
        --------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        def decorator(func: _SelectCallback) -> _SelectCallback:
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError('event registered must be a coroutine function')
            actual.__cog_interaction_listener__ = True
            pattern = re.compile(custom_id) if (
                    custom_id is not None and not isinstance(custom_id, re.Pattern)
            ) else re.compile(f'^{actual.__name__}$')
            try:
                actual.__interaction_listener_names__.append(('raw_selection_select', pattern))
            except AttributeError:
                actual.__interaction_listener_names__ = [('raw_selection_select', pattern)]
            return func
        return decorator

    @classmethod
    def on_submit(
            cls,
            custom_id: Optional[Union[Pattern[AnyStr], AnyStr]] = None
    ) -> Callable[[_ModalCallback], _ModalCallback]:
        """
        A decorator with which you can assign a function to a specific :class:`~discord.Modal` (or its custom_id).

        .. important::
            The function this is attached to must take the same parameters as a
            :func:`~discord.on_modal_submit` event.

        .. warning::
            The func must be a coroutine, if not, :exc:`TypeError` is raised.

        Parameters
        ----------
        custom_id: Optional[Union[Pattern[AnyStr], AnyStr]]
            If the :attr:`~discord.Modal.custom_id` of the modal could not use as a function name,
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

        Example
        -------
        .. code-block:: python

            # the Modal
            Modal(title='Create a new suggestion',
                  custom_id='suggestions_modal',
                  components=[...])

            # function that's called when the Modal is submitted
            @commands.Cog.on_submit(custom_id='^suggestions_modal$')
            async def suggestions_modal_callback(self, i: discord.ModalSubmitInteraction):
                ...

            # You can also use a more advanced RegEx containing groups to easily allow dynamic id's
            @commands.Cog.on_submit(custom_id='^ticket_answer:(?P<id>[0-9]+)$')
            async def ticket_answer_callback(i: discord.ModalSubmitInteraction):
                user_id = int(i.match['id'])
                user = client.get_user(user_id) or await client.fetch_user(user_id)


        Raises
        ------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        def decorator(func: _ModalCallback) -> _ModalCallback:
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError('event registered must be a coroutine function')
            actual.__cog_interaction_listener__ = True
            pattern = re.compile(custom_id) if (
                    custom_id is not None and not isinstance(custom_id, re.Pattern)
            ) else re.compile(f'^{actual.__name__}$')
            try:
                actual.__interaction_listener_names__.append(('modal_submit', pattern))
            except AttributeError:
                actual.__interaction_listener_names__ = [('modal_submit', pattern)]
            return func

        return decorator

    @classmethod
    def slash_command(
            cls,
            name: str = None,
            name_localizations: Localizations = Localizations(),
            description: Optional[str] = None,
            description_localizations: Localizations = Localizations(),
            allow_dm: bool = True,
            is_nsfw: bool = MISSING,
            default_required_permissions: Optional[Permissions] = None,
            options: Optional[List] = [],
            guild_ids: Optional[List[int]] = None,
            connector: dict = {},
            option_descriptions: dict = {},
            option_descriptions_localizations: Dict[str, Localizations] = {},
            base_name: Optional[str] = None,
            base_name_localizations: Optional[Localizations] = Localizations(),
            base_desc: Optional[str] = None,
            base_desc_localizations: Optional[Localizations] = Localizations(),
            group_name: Optional[str] = None,
            group_name_localizations: Optional[Localizations] = Localizations(),
            group_desc: Optional[str] = None,
            group_desc_localizations: Optional[Localizations] = Localizations()
    ) -> Callable[
        [_SlashCommandCallback],
        Union[SlashCommand, GuildOnlySlashCommand, SubCommand, GuildOnlySubCommand]
    ]:
        """
        A decorator that adds a slash-command to the client. The method this is attached to must be a :ref:`coroutine <coroutine>`.

        .. note::

            :attr:`~discord.ext.commands.Bot.sync_commands` of the :class:`~discord.ext.commands.Bot` instance must be set to :obj:`True`
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
            Use the ``connector`` parameter to connect non-ascii option names with the parameter of the function.
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
        The slash-command registered.
            - If neither ``guild_ids`` nor ``base_name`` passed: An instance of :class:`~discord.SlashCommand`.
            - If ``guild_ids`` and no ``base_name`` where passed: An instance of :class:`~discord.GuildOnlySlashCommand` representing the guild-only slash-commands.
            - If ``base_name`` and no ``guild_ids`` where passed: An instance of :class:`~discord.SubCommand`.
            - If ``base_name`` and ``guild_ids`` passed: instance of :class:`~discord.GuildOnlySubCommand` representing the guild-only sub-commands.
        """

        def decorator(func: _SlashCommandCallback) -> Union[
            SlashCommand, GuildOnlySlashCommand, SubCommand, GuildOnlySubCommand
        ]:
            """

            Parameters
            ----------
            func: Awaitable[Any]
                The function for the decorator.

            Returns
            -------
            Union[:class:`SlashCommand`, :class:`GuildOnlySlashCommand`, :class:`SubCommand`, :class:`GuildOnlySubCommand`]:
                - If neither ``guild_ids`` nor ``base_name`` passed: An instance of :class:`~discord.SlashCommand`.
                - If ``guild_ids`` and no ``base_name`` where passed: An instance of :class:`~discord.GuildOnlySlashCommand` representing the guild-only slash-commands.
                - If ``base_name` and no ``guild_ids`` where passed: An instance of :class:`~discord.SubCommand`.
                - If ``base_name`` and ``guild_ids`` passed: instance of :class:`~discord.GuildOnlySubCommand` representing the guild-only sub-commands.
            """
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError('The slash-command function registered  must be a coroutine.')
            _name = (name or actual.__name__).lower()
            _description = description or ((inspect.cleandoc(actual.__doc__)[:100]) if actual.__doc__ else 'No Description')
            _options = options or generate_options(
                actual,
                descriptions=option_descriptions,
                descriptions_localizations=option_descriptions_localizations,
                connector=connector,
                is_cog=True
            )
            if group_name and not base_name:
                raise InvalidArgument('You have to provide the `base_name` parameter if you want to create a sub-command or sub-command-group.')
            guild_cmds = []
            if guild_ids:
                guild_app_cmds = cls.__guild_specific_application_commands__
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
                                cog=cls,
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
                                base_command.description = base_desc
                            base_command.name_localizations.update(base_name_localizations)
                            base_command.description_localizations.update(base_desc_localizations)
                        base = base_command
                    if group_name:
                        try:
                            sub_command_group = guild_app_cmds[guild_id]['chat_input'][base_name]._sub_commands[group_name]
                        except KeyError:
                            sub_command_group = guild_app_cmds[guild_id]['chat_input'][base_name]._sub_commands[group_name] = SubCommandGroup(
                                cog=cls,
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
                            cog=cls,
                            parent=base,
                            func=actual,
                            name=_name,
                            name_localizations=name_localizations,
                            description=_description,
                            description_localizations=description_localizations,
                            options=_options,
                            connector=connector
                        )
                        guild_cmds.append(base._sub_commands[_name])
                    else:
                        guild_app_cmds[guild_id]['chat_input'][_name] = SlashCommand(
                                cog=cls,
                                guild_id=guild_id,
                                func=actual,
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
                        cog=cls,
                        guild_ids=guild_ids,
                        func=actual,
                        name=_name,
                        description=_description,
                        default_member_permissions=default_required_permissions,
                        is_nsfw=is_nsfw if is_nsfw is not MISSING else False,
                        options=_options
                    )
                    if group_name:
                        base = GuildOnlySubCommandGroup(
                            cog=cls,
                            guild_ids=guild_ids,
                            parent=base,
                            name=_name,
                            description=_description,
                            default_member_permissions=default_required_permissions,
                            options=_options
                        )
                    return GuildOnlySubCommand(
                        cog=cls,
                        guild_ids=guild_ids,
                        parent=base,
                        func=actual,
                        name=_name,
                        description=_description,
                        options=_options,
                        connector=connector,
                        commands=guild_cmds
                    )
                return GuildOnlySlashCommand(
                    cog=cls,
                    guild_ids=guild_ids,
                    func=actual,
                    name=_name,
                    description=_description,
                    default_member_permissions=default_required_permissions,
                    options=_options,
                    connector=connector,
                    commands=guild_cmds
                )
            else:
                app_cmds = cls.__application_commands_by_type__
                base, base_command, sub_command_group = None, None, None
                if base_name:
                    try:
                        base_command = app_cmds['chat_input'][base_name]
                    except KeyError:
                        base_command = app_cmds['chat_input'][base_name] = SlashCommand(
                            cog=cls,
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
                        if allow_dm is not MISSING:
                            base_command.allow_dm = allow_dm
                        if is_nsfw is not MISSING:
                            base_command.is_nsfw = is_nsfw
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
                        cog=cls,
                        parent=base,
                        func=actual,
                        name=_name,
                        name_localizations=name_localizations,
                        description=_description,
                        description_localizations=description_localizations,
                        options=_options,
                        connector=connector
                    )
                else:
                    command = cls.__application_commands_by_type__['chat_input'][_name] = SlashCommand(
                        cog=cls,
                        func=actual,
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

    @classmethod
    def message_command(
            cls,
            name: Optional[str] = None,
            name_localizations: Localizations = Localizations(),
            default_required_permissions: Optional[Permissions] = None,
            allow_dm: bool = True,
            is_nsfw: bool = False,
            guild_ids: Optional[List[int]] = None
    ) -> Callable[[_MessageCommandCallback], MessageCommand]:
        """
        A decorator that registers a :class:`~discord.MessageCommand` (shows up under ``Apps`` when right-clicking on a message)
        to the client. The function this is attached to must be a :ref:`coroutine <coroutine>`.

        .. note::
            :attr:`~Bot.sync_commands` of the :class:`~discord.ext.commands.Bot` instance must be set to :obj:`True`
            to register a command if it does not already exist and update it if changes where made.

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
        TypeError:
            The function the decorator is attached to is not actual a :ref:`coroutine <coroutine>`.
        """
        def decorator(func: _MessageCommandCallback) -> MessageCommand:
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError('The message-command function registered must be a coroutine.')
            _name = name or actual.__name__
            cmd = MessageCommand(
                cog=cls,
                guild_ids=guild_ids,
                func=actual,
                name=_name,
                name_localizations=name_localizations,
                default_member_permissions=default_required_permissions,
                allow_dm=allow_dm,
                is_nsfw=is_nsfw
            )
            if guild_ids:
                for guild_id in guild_ids:
                    guild_cmd = MessageCommand(
                        cog=cls,
                        guild_id=guild_id,
                        func=func,
                        name=_name,
                        name_localizations=name_localizations,
                        default_member_permissions=default_required_permissions,
                        allow_dm=allow_dm,
                        is_nsfw=is_nsfw
                    )
                    try:
                        cls.__guild_specific_application_commands__[guild_id]['message'][_name] = guild_cmd
                    except KeyError:
                        cls.__guild_specific_application_commands__[guild_id] = {
                            'chat_input': {},
                            'message': {_name: guild_cmd},
                            'user': {}
                        }
            else:
                cls.__application_commands_by_type__['message'][cmd.name] = cmd

            return cmd
        return decorator

    @classmethod
    def user_command(
            cls,
            name: str = None,
            name_localizations: Localizations = Localizations(),
            default_required_permissions: Optional[Permissions] = None,
            allow_dm: bool = True,
            is_nsfw: bool = False,
            guild_ids: Optional[List[int]] = None
    ) -> Callable[[_UserCommandCallback], UserCommand]:
        """A decorator that registers a :class:`UserCommand` (shows up under ``Apps`` when right-clicking on a user) to the client.
        The function this is attached to must be a :ref:`coroutine <coroutine>`.

        .. note::
            :attr:`~Bot.sync_commands` of the :class:`~discord.ext.commands.Bot` instance must be set to :obj:`True`
            to register a command if he not already exists and update him if changes where made.

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
        TypeError:
            The function the decorator is attached to is not actual a :ref:`coroutine <coroutine>`.
        """
        def decorator(func: _UserCommandCallback) -> UserCommand:
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError('The user-command function registered must be a coroutine.')
            _name = name or actual.__name__
            cmd = UserCommand(
                cog=cls,
                guild_ids=guild_ids,
                func=actual,
                name=_name,
                name_localizations=name_localizations,
                default_member_permissions=default_required_permissions,
                allow_dm=allow_dm,
                is_nsfw=is_nsfw
            )
            if guild_ids:
                for guild_id in guild_ids:
                    guild_cmd = UserCommand(
                        cog=cls,
                        guild_id=guild_id,
                        func=actual,
                        name=_name,
                        name_localizations=name_localizations,
                        default_member_permissions=default_required_permissions,
                        allow_dm=allow_dm,
                        is_nsfw=is_nsfw
                    )
                    try:
                        cls.__guild_specific_application_commands__[guild_id]['user'][_name] = guild_cmd
                    except KeyError:
                        cls.__guild_specific_application_commands__[guild_id] = {
                            'chat_input': {},
                            'message': {},
                            'user': {_name: guild_cmd}
                        }
            else:
                cls.__application_commands_by_type__['user'][_name] = cmd

            return cmd
        return decorator

    def has_error_handler(self):
        """:class:`bool`: Checks whether the cog has an error handler.

        .. versionadded:: 1.7
        """
        return not hasattr(self.cog_command_error.__func__, '__cog_special_method__')

    @_cog_special_method
    def cog_unload(self):
        """A special method that is called when the cog gets removed.

        This function **cannot** be a coroutine. It must be a regular
        function.

        Subclasses must replace this if they want special unloading behaviour.
        """
        pass

    @_cog_special_method
    def bot_check_once(self, ctx):
        """A special method that registers as a :meth:`.Bot.check_once`
        check.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    def bot_check(self, ctx):
        """A special method that registers as a :meth:`.Bot.check`
        check.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    def cog_check(self, ctx):
        """A special method that registers as a :func:`commands.check`
        for every command and subcommand in this cog.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    async def cog_command_error(self, ctx, error):
        """A special method that is called whenever an error
        is dispatched inside this cog.

        This is similar to :func:`.on_command_error` except only applying
        to the commands inside this cog.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context where the error happened.
        error: :class:`CommandError`
            The error that happened.
        """
        pass

    @_cog_special_method
    async def cog_before_invoke(self, ctx):
        """A special method that acts as a cog local pre-invoke hook.

        This is similar to :meth:`.Command.before_invoke`.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context.
        """
        pass

    @_cog_special_method
    async def cog_after_invoke(self, ctx):
        """A special method that acts as a cog local post-invoke hook.

        This is similar to :meth:`.Command.after_invoke`.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context.
        """
        pass

    @_cog_special_method
    async def cog_application_command_error(self, cmd, interaction, error):
        """A special method that is called whenever an error

        is dispatched inside this cog.

        This is similar to :func:`.on_application_command_error` except only applying
        to the application-commands inside this cog.

        This **must** be a coroutine.

        Parameters
        -----------
        cmd: Union[:class:`~discord.SlashCommand`, :class:`~discord.SubCommand`]
            The invoked command.
        interaction: :class:`discord.ApplicationCommandInteraction`
            The interaction.
        error: :class:`Exception`
            The error that happened.
        """
        pass

    def _inject(self, bot):
        cls = self.__class__

        # realistically, the only thing that can cause loading errors
        # is essentially just the command loading, which raises if there are
        # duplicates. When this condition is met, we want to undo all what
        # we've added so far for some form of atomic loading.
        for index, command in enumerate(self.__cog_commands__):
            command.cog = self
            if command.parent is None:
                try:
                    bot.add_command(command)
                except Exception as e:
                    # undo our additions
                    for to_undo in self.__cog_commands__[:index]:
                        if to_undo.parent is None:
                            bot.remove_command(to_undo.name)
                    raise e

        # check if we're overriding the default
        if cls.bot_check is not Cog.bot_check:
            bot.add_check(self.bot_check)

        if cls.bot_check_once is not Cog.bot_check_once:
            bot.add_check(self.bot_check_once, call_once=True)

        # while Bot.add_listener can raise if it's not a coroutine,
        # this precondition is already met by the listener decorator
        # already, thus this should never raise.
        # Outside of memory errors and the like...
        for name, method_name in self.__cog_listeners__:
            bot.add_listener(getattr(self, method_name), name)

        for (_type, method_name, custom_id) in self.__cog_interaction_listeners__:
            bot.add_interaction_listener(_type, getattr(self, method_name), custom_id)

        bot.add_application_cmds_from_cog(self)

        return self

    def _eject(self, bot):
        cls = self.__class__

        try:
            for command in self.__cog_commands__:
                if command.parent is None:
                    bot.remove_command(command.name)

            for _, method_name in self.__cog_listeners__:
                bot.remove_listener(getattr(self, method_name))

            for (_type, method_name, custom_id) in self.__cog_interaction_listeners__:
                bot.remove_interaction_listener(_type, getattr(self, method_name))

            bot.remove_application_cmds_from_cog(self)

            if cls.bot_check is not Cog.bot_check:
                bot.remove_check(self.bot_check)

            if cls.bot_check_once is not Cog.bot_check_once:
                bot.remove_check(self.bot_check_once, call_once=True)
        finally:
            try:
                self.cog_unload()
            except Exception:
                pass
