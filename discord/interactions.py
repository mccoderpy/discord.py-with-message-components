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

import re
import asyncio
import logging
from typing import (
    Any,
    Dict,
    List,
    Match,
    Optional,
    overload,
    Sequence,
    Set,
    Tuple,
    TYPE_CHECKING,
    Union
)

from typing_extensions import Literal

from . import abc, utils
from .monetization import Entitlement
from .object import Object
from .channel import _channel_factory, DMChannel, TextChannel, ThreadChannel, VoiceChannel, ForumPost, PartialMessageable
from .components import *
from .embeds import Embed
from .enums import (
    ApplicationCommandType,
    ComponentType,
    Locale,
    ChannelType,
    InteractionCallbackType,
    InteractionType, Locale,
    MessageType,
    OptionType,
    try_enum
)
from .errors import AlreadyResponded, HTTPException, NotFound, UnknownInteraction
from .file import File
from .flags import MessageFlags
from .guild import Guild
from .http import handle_interaction_message_parameters, handle_message_parameters, HTTPClient
from .member import Member
from .mentions import AllowedMentions
from .message import Attachment, Message
from .permissions import Permissions
from .reaction import Reaction
from .role import Role
from .user import User
from .utils import cached_slot_property, MISSING

if TYPE_CHECKING:
    import datetime
    from .types.interaction import (
        Interaction as InteractionPayload,
        InteractionData as InteractionDataPayload,
        ApplicationCommandInteractionDataOption as ApplicationCommandInteractionDataOptionPayload,
        ResolvedData as ResolvedDataPayload
    )
    from .state import ConnectionState
    from .components import BaseSelect
    from .application_commands import SlashCommandOptionChoice, SlashCommand, MessageCommand, UserCommand


log = logging.getLogger(__name__)

__all__ = (
    'EphemeralMessage',
    'BaseInteraction',
    'ApplicationCommandInteraction',
    'ComponentInteraction',
    'AutocompleteInteraction',
    'ModalSubmitInteraction',
    'option_str',
    'option_float',
    'option_int',
)


class EphemeralMessage:
    """
    Like a normal :class:`~discord.Message` but with a modified :meth:`edit` method and without
    :meth:`~discord.Message.delete` method.
    """
    # This class will be removed in the future when we switched to use the WebhookMessage model instead
    def __init__(self, *, state, channel, data, interaction):
        self._state: ConnectionState = state
        self.__interaction__: BaseInteraction = interaction
        self.id = int(data.get('id', 0))
        self.webhook_id = utils._get_as_snowflake(data, 'webhook_id')
        self.channel_id = utils._get_as_snowflake(data, 'channel_id')
        self.channel = channel
        self._update(data)

    def _update(self, data):
        self.application = data.get('application')
        self.activity = data.get('activity')
        self._edited_timestamp = utils.parse_time(data['edited_timestamp'])
        self.type = try_enum(MessageType, data['type'])
        self._thread = data.get('thread', None)
        self.pinned = data['pinned']
        self.mention_everyone = data['mention_everyone']

        for handler in (
                'tts',
                'content',
                'embeds',
                'author',
                'member',
                'mentions',
                'mention_roles',
                'flags',
                'components',
                'interaction',
                'attachments',
                'reactions'
        ):
            try:
                getattr(self, '_handle_%s' % handler)(data[handler])
            except KeyError:
                if not hasattr(self, handler):
                    setattr(
                        self,
                        handler,
                        None if handler not in {
                            'embeds',
                            'mentions',
                            'mentioned_roles',
                            'attachments',
                            'reactions',
                            'components'
                        } else []
                    )  # bad solution for now but works, will be removed anyway when rewrite the existing webhook system
        return self

    def _handle_flags(self, value):
        self.flags = MessageFlags._from_value(value)

    def _handle_application(self, value):
        self.application = value

    def _handle_activity(self, value):
        self.activity = value

    def _handle_mention_everyone(self, value):
        self.mention_everyone = value

    def _handle_tts(self, value):
        self.tts = value

    def _handle_type(self, value):
        self.type = try_enum(MessageType, value)

    def _handle_content(self, value):
        self.content = value

    def _handle_attachments(self, value):
        self.attachments = [Attachment(data=a, state=self._state) for a in value]

    def _handle_embeds(self, value):
        self.embeds = [Embed.from_dict(data) for data in value]

    def _handle_interaction(self, value):
        self.interaction = value

    def _handle_components(self, value):
        self.components = [ActionRow.from_dict(data) for data in value]

    def _handle_reactions(self, value):
        self.reactions = [Reaction(message=self, data=d) for d in value]

    def _handle_nonce(self, value):
        self.nonce = value

    def _handle_author(self, author):
        self.author = self._state.store_user(author)
        if isinstance(self.guild, Guild):
            found = self.guild.get_member(self.author.id)
            if found is not None:
                self.author = found

    def _handle_member(self, member):
        # The gateway now gives us full Member objects sometimes with the following keys
        # deaf, mute, joined_at, roles
        # For the sake of performance I'm going to assume that the only
        # field that needs *updating* would be the joined_at field.
        # If there is no Member object (for some strange reason), then we can upgrade
        # ourselves to a more "partial" member object.
        author = self.author
        try:
            # Update member reference
            author._update_from_message(member)
        except AttributeError:
            # It's a user here
            # TODO: consider adding to cache here
            self.author = Member._from_message(message=self, data=member)

    def _handle_mentions(self, mentions):
        self.mentions = r = []
        guild = self.guild
        state = self._state
        if not isinstance(guild, Guild):
            self.mentions = [state.store_user(m) for m in mentions]
            return

        for mention in filter(None, mentions):
            id_search = int(mention['id'])
            member = guild.get_member(id_search)
            if member is not None:
                r.append(member)
            else:
                r.append(Member._try_upgrade(data=mention, guild=guild, state=state))

    def _handle_mention_roles(self, role_mentions):
        self.role_mentions = []
        if isinstance(self.guild, Guild):
            for role_id in map(int, role_mentions):
                role = self.guild.get_role(role_id)
                if role is not None:
                    self.role_mentions.append(role)

    @utils.cached_slot_property('_cs_guild')
    def guild(self):
        """Optional[:class:`Guild`]: The guild that the message belongs to, if applicable."""
        return getattr(self.channel, 'guild', None)

    def __repr__(self):
        return '<EphemeralMessage id={0.id} channel={0.channel!r} type={0.type!r} author={0.author!r} flags={0.flags!r}>'.format(
            self)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    @property
    def all_components(self):
        """Union[:class:`Button`, :ref:`Select <select-like-objects>`]:
        Yields all buttons and selects that are contained in the message"""
        for action_row in self.components:
            yield from action_row

    @property
    def all_buttons(self):
        """Returns all :class:`Button`'s that are contained in the message"""
        for action_row in self.components:
            for component in action_row:
                yield component

    @property
    def all_select_menus(self):
        """Returns all :ref:`Select <select-like-objects>`'s that are contained in the message"""
        for action_row in self.components:
            for component in action_row:
                if int(component.type) in {3, 5, 6, 7, 8}:
                    yield component

    async def edit(
            self,
            *,
            content: Any = MISSING,
            embed: Optional[Embed] = MISSING,
            embeds: Sequence[Embed] = MISSING,
            components: List[Union[ActionRow, List[Union[Button, BaseSelect]]]] = MISSING,
            attachments: Sequence[Union[Attachment, File]] = MISSING,
            keep_existing_attachments: bool = False,
            allowed_mentions: Optional[AllowedMentions] = MISSING,
            suppress_embeds: bool = False,
            delete_after: Optional[float] = None
    ) -> Union[Message, EphemeralMessage]:
        """|coro|

        Edits the message.

        Parameters
        -----------
        content: Optional[:class:`str`]
            The new content to replace the message with.
            Could be ``None`` to remove the content.
        embed: Optional[:class:`Embed`]
            The new embed to replace the original with.
            Could be ``None`` to remove all embeds.
        embeds: Optional[List[:class:`Embed`]]
            A list containing up to 10 embeds to send.
            If ``None`` or empty, all embeds will be removed.
            
            If passed, ``embed`` does also count towards the limit of 10 embeds.
        components: List[Union[:class:`~discord.ActionRow`, List[Union[:class:`~discord.Button`, :ref:`Select <select-like-objects>`]]]]
            A list of up to five :class:`~discord.ActionRow`s or :class:`list`,
            each containing up to five :class:`~discord.Button` or one :ref:`Select <select-like-objects>` like object.
        attachments: List[Union[:class:`Attachment`, :class:`File`]]
            A list containing previous attachments to keep as well as new files to upload.
            You can use ``keep_existing_attachments`` to auto-add the existing attachments to the list.
            If  an empty list (``[]``) is passed, all attachment will be removed.

            .. note::

                New files will always appear under existing ones.

        keep_existing_attachments: :class:`bool`
            Whether to auto-add existing attachments to ``attachments``, default :obj:`False`.

            .. note::

                Only needed when ``attachments`` are passed, otherwise will be ignored.

        suppress_embeds: :class:`bool`
            Whether to suppress embeds for the message. If ``True`` this will remove all embeds from the message.
            If `´False`` it adds them back.
        delete_after: :class:`float`
            If provided, the number of seconds to wait in the background
            before deleting the response we just edited. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.


        """

        if suppress_embeds:
            flags = MessageFlags._from_value(self.flags.value)
            flags.suppress_embeds = True
        else:
            flags = MISSING

        if keep_existing_attachments:
            if attachments is not MISSING:
                attachments = [*self.attachments, *attachments]

        state = self._state
        interaction = self.__interaction__

        if not self.channel:
            self.channel = self._state.add_dm_channel(data=await state.http.get_channel(self.channel_id))

        is_original_response = interaction.callback_message and self.id == interaction.callback_message.id

        params = handle_message_parameters(
            content=content,
            flags=flags,
            embed=embed,
            embeds=embeds,
            attachments=attachments,
            components=components,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=state.allowed_mentions
        )

        if is_original_response:
            method = state.http.edit_original_interaction_response(
                token=interaction._token,
                application_id=interaction._application_id,
                params=params
            )
        else:
            method = state.http.edit_followup(
                token=interaction._token,
                application_id=interaction._application_id,
                message_id=self.id,
                params=params
            )

        with params:
            data = await method

        if not isinstance(data, dict):
            if is_original_response:
                return await interaction.get_original_callback()
            else:
                data = await state.http.get_followup_message(
                    token=interaction._token,
                    application_id=interaction._application_id,
                    message_id=self.id,
                )
        self._update(data)
        if delete_after:
            import warnings
            warnings.warn("You can\'t delete a ephemeral message manual.")
        return self

    async def delete(self, *, delay: Optional[float] = None) -> None:
        """|coro|

        Deletes the message.

        .. note::
            This can only be used while the interaction token is valid. So within 15 minutes after the interaction.

        Parameters
        -----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message. If the deletion fails then it is silently ignored.

        Raises
        ------
        NotFound
            The message was deleted already or the interaction token expired
        HTTPException
            Deleting the message failed.
        """
        interaction = self.__interaction__
        is_original_response = interaction.callback_message and self.id == interaction.callback_message.id
        if delay is not None:
            async def delete():
                await asyncio.sleep(delay)
                try:
                    await self._state.http.delete_interaction_response(
                        interaction._token,
                        interaction._application_id,
                        message_id=self.id if not is_original_response else '@original'
                    )
                except HTTPException:
                    pass

            asyncio.ensure_future(delete(), loop=self._state.loop)
        else:
            await self._state.http.delete_interaction_response(
                interaction._token,
                interaction._application_id,
                message_id=self.id if not is_original_response else '@original'
            )


class BaseInteraction:
    """
    The Base-Class for a discord-interaction like klick a :class:`~discord.Button`,
    select (an) option(s) of :class:`~discord.SelectMenu` or using an application-command in discord
    For more general information's about Interactions visit the Documentation of the
    `Discord-API <https://discord.com/developers/docs/interactions/receiving-and-responding#interaction-object>`_

    The following attributes are always available:

    Attributes
    ------------
    id: :class:`int`
        The id of the interaction.
    type: :class:`~discord.InteractionType`
        The type of the interaction.
    user_id: :class:`int`
        The id of the user who triggered the interaction.
    channel_id: :class:`int`
        The id of the channel where the interaction was triggered.
    entitlements: Optional[List[:class:`~discord.Entitlement`]]
        For :ddocs:`monetized apps <monetization/overview>` entitlements of the user who triggered the interaction
        and optionally, if any.

        This is available for all interaction types.
    data: :class:`~discord.InteractionData`
        Some internal needed metadata for the interaction, depending on the type.
    author_locale: Optional[:class:`~discord.Locale`]
        The locale of the user who triggered the interaction.
    guild_locale: Optional[:class:`~discord.Locale`]
        The locale of the guild where the interaction was triggered.
    guild_id: Optional[:class:`int`]
        The id of the guild where the interaction was triggered, if any.
    app_permissions: Optional[:class:`~discord.Permissions`]
        The permissions of the bot in the channel where the interaction was triggered, if it was in a guild.

        This is similar to `interaction.channel.permissions_for(interaction.guild.me)` but calculated on discord side.
    author_permissions: Optional[:class:`~discord.Permissions`]
        The author's permissions in the channel where the interaction was triggered, if it was in a guild.

        This is similar to `interaction.channel.permissions_for(interaction.author)`, but calculated on discord side.
    """
    if TYPE_CHECKING:
        type: InteractionType
        id: int
        guild_id: Optional[int]
        channel_id: int
        user_id: int
        user: User
        author_locale: Locale
        entitlements: Set[Entitlement]
        app_permissions: Optional[Permissions]
        author_permissions: Optional[Permissions]
        member: Optional[Member]
        guild_locale: Optional[Locale]
        data: Optional[InteractionData]
        message: Optional[Union[Message, EphemeralMessage]]
        cached_message: Optional[Union[Message, EphemeralMessage]]
        message_id: Optional[int]

    def __init__(self, state: ConnectionState, data: InteractionPayload) -> None:
        self._state: ConnectionState = state
        self._http: HTTPClient = state.http
        self._application_id = int(data.get('application_id'))
        self._token = data['token']
        self.type = InteractionType.try_value(data['type'])
        self.id = int(data['id'])
        self.guild_id = guild_id = utils._get_as_snowflake(data, 'guild_id')
        self.entitlements = {Entitlement(data=e, state=state) for e in data.get('entitlements', [])}
        channel_data = data.get('channel', {})
        self.channel_id = channel_id = int(data.get('channel_id', channel_data.get('id', 0)))

        guild = self.guild or Object(id=guild_id) if guild_id else None  # I'm not sure if we need the Object thing here
        channel, member = (None, None)
        
        if guild:
            member_data = data.get('member')
            user_data = member_data.get('user')
            self.user_id = user_id = int(user_data['id'])
            if isinstance(guild, Guild):
                channel = guild.get_channel(self.channel_id)
                member = guild.get_member(user_id)
            self.member = member or Member(state=state, data=member_data, guild=guild)  # consider updating the member here
            self.author_permissions = Permissions(int(member_data.get('permissions', 0)))
            self.guild_locale = try_enum(Locale, data.get('guild_locale'))
        else:
            channel = state._get_private_channel(channel_id)
            user_data = data.get('user')
            self.app_permissions = None
            self.author_permissions = None
            self.member = None
            self.guild_locale = None
            self.user_id = int(user_data['id'])
            
        self.user = state.store_user(user_data)


        if not channel:
            factory, ch_type = _channel_factory(channel_data['type'])
            if ch_type in (ChannelType.group, ChannelType.private):
                # In my tests the required fields for those channels where always present
                channel = factory(me=state.user, data=channel_data, state=state)
            else:
                channel = PartialMessageable(
                    state=state,
                    id=self.channel_id,
                    guild_id=self.guild_id,
                    type=ch_type,
                    partial_data=channel_data
                )

        self._channel = channel

        message_data = data.get('message')
        if message_data is not None:
            if MessageFlags._from_value(message_data['flags']).ephemeral:
                self.message = EphemeralMessage(state=state, channel=channel, data=message_data, interaction=self)
            else:
                self.message = Message(state=state, channel=channel, data=message_data)
            # Remove this on release, it's unnecessary as we always get the full message (except reactions for components)
            self.cached_message = self.message and state._get_message(self.message.id)
            self.message_id = int(message_data['id'])
        else:
            self.message = None
            self.cached_message = None
            self.message_id = None

        interaction_data = data.get('data')
        if interaction_data is not None:
            self.data = InteractionData(data=interaction_data,state=state, guild=self.guild, channel_id=self.channel_id)
        else:
            self.data = None

        self.author_locale = try_enum(Locale, data['locale'])
        self.deferred: bool = False
        self.deferred_hidden: bool = False
        self.deferred_modal: bool = False
        self._command = None
        self._callback_message: Optional[Union[Message, EphemeralMessage]] = None
        self.messages: Dict[Union[str, int], Union[Message, EphemeralMessage]] = {}

    def __repr__(self) -> str:
        """Represents a :class:`~discord.BaseInteraction` object."""
        return f'<{self.__class__.__name__} {", ".join([f"{k}={v}" for k, v in self.__dict__.items() if k[0] != "_"])}>'
    
    @property
    def callback_message(self) -> Optional[Union[Message, EphemeralMessage]]:
        """Optional[Union[:class:`Message`, :class:`EphemeralMessage`]: The initial interaction response message, if any. (``@original``)"""
        return self._callback_message
    
    @callback_message.setter
    def callback_message(self, value: Optional[Union[Message, EphemeralMessage]]) -> None:
        self._callback_message = value
        if value:
            self.messages['@original'] = value

    async def _defer(
            self,
            response_type: Optional[InteractionCallbackType] = InteractionCallbackType.deferred_update_msg,
            hidden: Optional[bool] = False
    ) -> Optional[Union[Message, EphemeralMessage]]:
        """
        |coro|

        'Defers' the response.

        If :attr:`response_type` is `InteractionCallbackType.deferred_msg_with_source` it shows a loading state to the user.

        response_type: Optional[:class:`InteractionCallbackType`]
            The type to response with, aiter :class:`InteractionCallbackType.deferred_msg_with_source` or :class:`InteractionCallbackType.deferred_update_msg` (e.g. 5 or 6)

        hidden: Optional[:class:`bool`]
            Whether to defer ephemerally(only the :attr:`author` of the interaction can see the message)

            .. note::
                Only for :class:`InteractionCallbackType.deferred_msg_with_source`.

        .. important::
            If you don't respond with a message using :meth:`respond`
            or edit the original message using :meth:`edit` within less than 3 seconds,
            discord will indicate that the interaction failed and the interaction-token will be invalidated.
            To provide this us this method

        .. note::
            A Token will be Valid for 15 Minutes, so you could edit the original :attr:`message` with :meth:`edit`,
             :meth:`respond` or doing anything other with this interaction for 15 minutes.
            After that time you have to edit the original message with the Methode :meth:`edit` of the :attr:`message`
             and send new messages with the :meth:`send` Methode of :attr:`channel`
            (you could not do this hidden as it isn't a response anymore).
        """
        if isinstance(response_type, int):
            response_type = InteractionCallbackType.from_value(response_type)
        if self.deferred:
            raise AlreadyResponded(self.id)
        base = {"type": int(response_type), "data": {'flags': 64 if hidden else None}}
        try:
            data = await self._http.post_initial_response(
                data=base,
                token=self._token,
                interaction_id=self.id
            )
        except NotFound:
            raise UnknownInteraction(self.id)
        else:
            self.deferred = True
            if hidden is True:
                self.deferred_hidden = True
            if not data and response_type.msg_with_source or response_type.deferred_msg_with_source:
                msg = self.callback_message = await self.get_original_callback()
                return msg

    async def _premium_required(self) -> None:
        """|coro|
        Respond with an upgrade button, only available for apps
        with :ddocs:`monetized apps <monetization/overview>` enabled.
        """
        await self._state.http.post_initial_response(
            self.id,
            self._token,
            data={'type': InteractionCallbackType.premium_required.value}
        )

    async def edit(
            self,
            *,
            content: Any = MISSING,
            embed: Optional[Embed] = MISSING,
            embeds: Sequence[Embed] = MISSING,
            components: List[Union[ActionRow, List[Union[Button, BaseSelect]]]] = MISSING,
            attachments: Sequence[Union[Attachment, File]] = MISSING,
            keep_existing_attachments: bool = False,
            delete_after: Optional[float] = None,
            allowed_mentions: Optional[AllowedMentions] = MISSING,
            suppress_embeds: Optional[bool] = False
    ) -> Union[Message, EphemeralMessage]:
        """|coro|

        Responds to the interaction by editing the original (:attr:`~ComponentInteraction.message`)
        or :attr:`callback_message`, depending on the :attr:`~BaseInteraction.type`.

        Parameters
        -----------
        content: Optional[:class:`str`]
            The new content to replace the message with.
            Could be ``None`` to remove the content.
        embed: Optional[:class:`Embed`]
            The new embed to replace the original with.
            Could be ``None`` to remove all embeds.
        embeds: Optional[List[:class:`Embed`]]
            A list containing up to 10 embeds to send.
            If ``None`` or empty, all embeds will be removed.
            
            If passed, ``embed`` does also count towards the limit of 10 embeds.
        components: List[Union[:class:`~discord.ActionRow`, List[Union[:class:`~discord.Button`, :ref:`Select <select-like-objects>`]]]]
            A list of up to five :class:`~discord.ActionRow` or :class:`list`,
            each containing up to five :class:`~discord.Button` or one :ref:`Select <select-like-objects>` like object.
        attachments: List[Union[:class:`Attachment`, :class:`File`]]
            A list containing previous attachments to keep as well as new files to upload.
            You can use ``keep_existing_attachments`` to auto-add the existing attachments to the list.
            If ``None`` or empty, all attachments will be removed.

            .. note::

                New files will always appear under existing ones.

        keep_existing_attachments: :class:`bool`
            Whether to auto-add existing attachments to ``attachments``, default :obj:`False`.
            
            .. note::

                Only needed when ``attachments`` are passed, otherwise will be ignored.

        suppress_embeds: :class:`bool`
            Whether to suppress embeds for the message. This removes
            all the embeds if set to ``True``. If set to ``False``
            this brings the embeds back if they were suppressed.
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the response we just edited. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.
        
        Raises
        -------
        TypeError
            The interaction was already responded to with a modal,
            or it is an application-command that was not responded to.
        NotFound:
            The interaction is expired.
        HTTPException
            Editing the message failed.
        
        Returns
        --------
        Union[:class:`~discord.Message`, :class:`~discord.EphemeralMessage`]
            The edited message.
        """
        if self.deferred_modal:
            if self.type.Component:
                return await self.message.edit(
                    content=content,
                    embed=embed,
                    embeds=embeds,
                    components=components,
                    attachments=attachments,
                    keep_existing_attachments=keep_existing_attachments,
                    allowed_mentions=allowed_mentions,
                    delete_after=delete_after,
                    suppress_embeds=suppress_embeds
                )
            else:
                raise TypeError('You can\'t edit the message as it does not exist when using `respond_with_modal`.')

        response_type = MISSING

        if not self.deferred:
            if self.type.ApplicationCommand:
                raise TypeError('You need to send a response first before you can edit it')
            else:
                response_type = InteractionCallbackType.update_msg

        m = self.callback_message if self.type.ApplicationCommand else self.message
        
        if suppress_embeds is not MISSING:
            flags = MessageFlags._from_value(m.flags.value) if m else MessageFlags._from_value(0)
            flags.suppress_embeds = suppress_embeds
        else:
            flags = MISSING

        state = self._state
        if not self.channel:
            ch = await self._http.get_channel(self.channel_id)
            self.channel = _channel_factory(ch['type'])[0](state=state, data=ch)

        if response_type is MISSING:
            params = handle_message_parameters(
                content=content,
                flags=flags,
                embed=embed,
                embeds=embeds,
                attachments=attachments,
                components=components,
                allowed_mentions=allowed_mentions,
                previous_allowed_mentions=state.allowed_mentions
            )
            method = state.http.edit_original_interaction_response(
                token=self._token,
                application_id=self._application_id,
                params=params
            )
        else:
            params = handle_interaction_message_parameters(
                type=response_type,
                content=content,
                flags=flags,
                embed=embed,
                attachments=attachments,
                components=components,
                allowed_mentions=allowed_mentions,
                previous_allowed_mentions=state.allowed_mentions
            )
            method = state.http.send_interaction_response(
                interaction_id=self.id,
                token=self._token,
                params=params
            )

        with params:
            data = await method

        if not isinstance(data, dict):
            msg = await self.get_original_callback()
        else:
            if m is not None:
                msg = m._update(data)
            else:
                if MessageFlags._from_value(data['flags']).ephemeral:
                    msg = EphemeralMessage(state=self._state, data=data, channel=self.channel, interaction=self)
                else:
                    msg = Message(state=self._state, channel=self.channel, data=data)
        if not self.deferred:
            self.callback_message = msg
        is_hidden = msg.flags.ephemeral

        if is_hidden:
            self.deferred_hidden = True
        self.deferred = True
        
        if delete_after is not None:
            await msg.delete(delay=delete_after)
        
        return msg

    async def respond(
            self,
            content: str = None, *,
            tts: bool = False,
            embed: Optional[Embed] = None,
            embeds: Optional[List[Embed]] = None,
            components: Optional[List[Union[ActionRow, List[Union[Button, BaseSelect]]]]] = None,
            file: Optional[File] = None,
            files: Optional[List[File]] = None,
            delete_after: Optional[float] = None,
            allowed_mentions: Optional[AllowedMentions] = None,
            suppress_embeds: bool = False,
            suppress_notifications: bool = False,
            hidden: bool = False
    ) -> Union[Message, EphemeralMessage]:
        """|coro|

        Responds to an interaction by sending a message.

        Parameters
        ------------
        content: :class:`str`
            The content of the message to send.
        tts: :class:`bool`
            Indicates if the message should be sent using text-to-speech.
        embed: :class:`~discord.Embed`
            The rich embed for the content.
        embeds: List[:class:`~discord.Embed`]
            A list containing up to 10 embeds.
            
            If passed, ``embed`` also counts towards the limit of 10.
        components: List[Union[:class:`~discord.ActionRow`, List[Union[:class:`~discord.Button`, :ref:`Select <select-like-objects>`]]]]
            A list of up to five :class:`~discord.ActionRow`s/:class:`list`s.
            Each containing up to five :class:`~discord.Button` or one :ref:`Select <select-like-objects>` like object.
        file: :class:`~discord.File`
            The file to upload.
        files: List[:class:`~discord.File`]
            A :class:`list` of files to upload. Must be a maximum of 10.
        suppress_embeds: :class:`bool`
            Whether to suppress embeds for the message.
        suppress_notifications: :class:`bool`
            Whether to suppress desktop- & push-notifications for the post starter-message.
        delete_after: :class:`float`
            If provided, the number of seconds to wait in the background
            before deleting the response we just sent. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: :class:`~discord.AllowedMentions`
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.
        hidden: Optional[:class:`bool`]
            If :obj:`True` the message will be only visible for the performer of the interaction (e.g. :attr:`.author`).
        
        Raises
        -------
        TypeError
            This interaction was already responded to with a modal.
        NotFound
            The interaction has expired.
        HTTPException
            Responding to the interaction failed.
        """

        if self.deferred_modal:
            raise TypeError('After responding to the interaction with a modal, you can\'t respond.')
        state = self._state

        flags = MessageFlags._from_value(0)
        flags.ephemeral = hidden
        flags.suppress_embeds = suppress_embeds
        flags.suppress_notifications = suppress_notifications

        is_initial = False
        response_type = MISSING

        if not self.deferred:
            response_type = InteractionCallbackType.msg_with_source
        else:
            if self.callback_message and (self.callback_message.flags.loading if self.type.ApplicationCommand else False):
                is_initial = True

        if response_type is MISSING:
            params = handle_message_parameters(
                content=content,
                tts=tts,
                flags=flags,
                embed=embed or MISSING,
                embeds=embeds or MISSING,
                file=file or MISSING,
                files=files or MISSING,
                components=components or MISSING,
                allowed_mentions=allowed_mentions,
                previous_allowed_mentions=state.allowed_mentions
            )
            if is_initial:
                method = state.http.edit_original_interaction_response(
                    token=self._token,
                    application_id=self._application_id,
                    params=params
                )
            else:
                method = state.http.send_followup(
                    token=self._token,
                    application_id=self._application_id,
                    params=params
                )
        else:
            params = handle_interaction_message_parameters(
                type=response_type,
                content=content,
                tts=tts,
                flags=flags,
                embed=embed or MISSING,
                embeds=embeds or MISSING,
                file=file or MISSING,
                files=files or MISSING,
                components=components or MISSING,
                allowed_mentions=allowed_mentions,
                previous_allowed_mentions=state.allowed_mentions
            )
            method = state.http.send_interaction_response(
                token=self._token,
                interaction_id=self.id,
                params=params
            )

        with params:
            data = await method

        if not isinstance(data, dict):
            data = await self.get_original_callback(raw=True)

        # We can't use the value from the params here because the message might be an edit/followup of the initial (hidden or not) response.
        # Anyway, this will be removed in the future when we switched to use the webhook message modell for interactions.
        is_hidden = MessageFlags._from_value(data['flags']).ephemeral
        if is_hidden:
            msg = EphemeralMessage(state=self._state, channel=self.channel, data=data, interaction=self)
        else:
            msg = Message(state=self._state, channel=self.channel, data=data)

        
        if not self.callback_message or is_initial:
            self.callback_message = msg
        else:
            self.messages[msg.id] = msg
        if response_type is not MISSING or is_initial:
            self.deferred = True
            if is_hidden:
                self.deferred_hidden = True
        if delete_after is not None:
            await msg.delete(delay=delete_after)
        return msg

    async def respond_with_modal(self, modal: Modal) -> Dict:
        """|coro|
        Respond to an interaction with a popup modal.

        Parameters
        ----------
        modal: :class:`~discord.Modal`
            The modal to send.
        
        Raises
        -------
        AlreadyResponded
            This interaction was already responded to.
        HTTPException
            Responding to the interaction failed.
        """
        if not self.deferred:
            data = await self._state.http.post_initial_response(
                token=self._token,
                interaction_id=self.id,
                data={'type': 9, 'data': modal.to_dict()}
            )
        else:
            raise AlreadyResponded(self.id)
        self.deferred = True
        self.deferred_modal = True
        return data

    async def get_original_callback(self, raw: bool = False) -> Union[Message, EphemeralMessage, dict]:
        """|coro|
        Fetch the original callback-message of the interaction.

        .. warning::

            This is an API-Call and should be used carefully

        Parameters
        ----------
        raw: Optional[:class:`bool`]
            Whether to return the raw data from the api instead of a :class:`~discord.Message`/:class:`EphemeralMessage`.
        
        Returns
        -------
        Union[:class:`~discord.Message`,:class:`EphemeralMessage`], :class:`dict`]
            The original callback-message of the interaction.
        """
        data = await self._state.http.get_original_interaction_response(self._token, self._application_id)
        if raw:
            return data
        if MessageFlags._from_value(data['flags']).ephemeral:
            msg = EphemeralMessage(state=self._state, data=data, channel=self.channel, interaction=self)
        else:
            msg = Message(state=self._state, channel=self.channel, data=data)
        self.callback_message = msg
        return msg

    def get_followup(self, id: int) -> Optional[Union[Message, EphemeralMessage]]:
        """
        Gets a followup message of this interaction with the given :attr:`~discord.BaseInteraction.id`.

        Parameters
        -----------
        id: :class:`int`
            The id of the followup message.

        Returns
        -------
        Optional[Union[:class:`~discord.Message`, :class:`~discord.EphemeralMessage`]]
            The followup or ``None`` if there is none.
        """
        return self.messages.get(id, None)

    @property
    def created_at(self) -> datetime.datetime:
        """
        Returns the Interaction’s creation time in UTC.

        :return: :class:`datetime.datetime`
        """
        return utils.snowflake_time(self.id)

    @property
    def author(self) -> Union[Member, User]:
        """
        Union[:class:`~discord.Member`, :class:`~discord.User`]: The :class:`~discord.Member` that invoked the interaction.
        If :attr:`.channel` is of type :class:`~discords.ChannelType.private` or the user has left the guild,
        then it is a :class:`~discord.User` instead.
        """
        return self.member if self.member is not None else self.user

    @property
    def channel(self) -> Union[DMChannel, TextChannel, ThreadChannel, ForumPost, VoiceChannel, PartialMessageable]:
        """
        Union[
            :class:`~discord.TextChannel`,
            :class:`~discord.ThreadChannel`,
            :class:`~discord.DMChannel`,
            :class:`~discord.VoiceChannel`,
            :class:`~discord.ForumPost`,
            :class:`~discord.PartialMessageable`
        ]: The channel where the interaction was invoked in.
        """
        # TODO: I think we can remove this now
        return getattr(
            self,
            '_channel',
            self.guild.get_channel(self.channel_id) if self.guild_id else self._state.get_channel(self.channel_id)
        ) or PartialMessageable(state=self._state, id=self.channel_id, guild_id=self.guild_id)

    @channel.setter
    def channel(self, channel):
        self._channel = channel

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`~discord.Guild`]: The guild the interaction was invoked in, if there is one."""
        return self._state._get_guild(self.guild_id)

    @property
    @utils.deprecated('is_dm')
    def message_is_dm(self) -> bool:
        """:class:`bool`: An deprecated alias to :attr:`is_dm`."""
        return not self.guild_id

    @property
    def is_dm(self) -> bool:
        """:class:`bool`: Whether the interaction was invoked in a :class:`~discord.DMChannel`."""
        return not self.guild_id

    @property
    def bot(self):
        """Union[:class:`~discord.Client`, :class:`~discord.ext.commands.Bot`]:
        The :class:`~discord.Client`/:class:`~discord.ext.commands.Bot` instance of the bot."""
        return self._state._get_client()

    @classmethod
    def from_type(cls, state: ConnectionState, data: InteractionPayload) -> Union[ApplicationCommandInteraction, ComponentInteraction, AutocompleteInteraction, ModalSubmitInteraction]:
        type = try_enum(InteractionType, data['type'])
        if type == InteractionType.ApplicationCommand:
            return ApplicationCommandInteraction(state=state, data=data)
        elif type == InteractionType.Component:
            return ComponentInteraction(state=state, data=data)
        elif type == InteractionType.ApplicationCommandAutocomplete:
            return AutocompleteInteraction(state=state, data=data)
        elif type == InteractionType.ModalSubmit:
            return ModalSubmitInteraction(state=state, data=data)


class ApplicationCommandInteraction(BaseInteraction):
    """
    Holds the data of an interaction when a `~discord.SlashCommand`,
    :class:`~discord.UserCommand` or :class:`~discord.MessageCommand` is used and allows responding to it.

    Attributes
    ------------
    id: :class:`int`
        The id of the interaction.
    type: :class:`~discord.InteractionType`
        The type of the interaction.
    user_id: :class:`int`
        The id of the user who triggered the interaction.
    channel_id: :class:`int`
        The id of the channel where the interaction was triggered.
    messages: Dict[:class:`int`, Union[:class:`~discord.Message`, :class:`~discord.EphemeralMessage`]]
        A mapping of message id's to the message objects that were sent using :attr:`respond`.
    author_locale: Optional[:class:`~discord.Locale`]
        The locale of the user who triggered the interaction.
    guild_locale: Optional[:class:`~discord.Locale`]
        The locale of the guild where the interaction was triggered.
    guild_id: Optional[:class:`int`]
        The id of the guild where the interaction was triggered, if any.
    app_permissions: Optional[:class:`~discord.Permissions`]
        The permissions of the bot in the channel where the interaction was triggered, if it was in a guild.
    target: Optional[Union[:class:`~discord.Member`, :class:`~discord.Message`]]
        The resolved target of the interaction, if it is a user or message command.
    """
    if TYPE_CHECKING:
        target: Optional[Union[Member, User, Message]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        target_id = self.data.target_id
        if target_id:
            target_type = self.data.type
            resolved = self.data.resolved
            if target_type == ApplicationCommandType.user:
                self.target = resolved.members.get(target_id) or resolved.users.get(target_id)
            elif target_type == ApplicationCommandType.message:
                self.target = resolved.messages[target_id]
        else:
            self.target = None

    @property
    def command(self) -> Optional[Union[SlashCommand, MessageCommand, UserCommand]]:
        """Union[:class:`~discord.SlashCommand`, :class:`~discord.UserCommand`, :class:`~discord.MessageCommand`]:
        The application-command that was invoked."""
        if getattr(self, '_command', None) is not None:
            return self._command
        return self._state._get_client()._get_application_command(self.data.id) \
            if (self.type.ApplicationCommand or self.type.ApplicationCommandAutocomplete) else None

    async def defer(self, hidden: bool = False) -> Union[Message, EphemeralMessage]:
        """
        Defers the interaction, the user sees a loading state

        Parameters
        ----------
        hidden: Optional[:class:`bool`]
            Weather only the author of the command should see this
        
        Raises
        ------
        AlreadyResponded
            The interaction has already been responded to.
        UnknownInteraction
            The interaction has expired.
        
        Returns
        -------
        Union[:class:`~discord.Message, :class:`~discord.EphemeralMessage`]:
            The Message containing the loading state
        """
        data = await super()._defer(InteractionCallbackType.deferred_msg_with_source, hidden)
        return data

    async def respond_with_premium_required(self) -> None:
        """|coro|
        Respond with an upgrade button, only available for apps
        with :ddocs:`monetized apps <monetization/overview>` enabled.

        .. note::
            You must respond with this one directly, without using any of
            :meth:`~discord.ApplicationCommandInteraction.defer` or
            :meth:`~discord.ApplicationCommandInteraction.respond`.
        """
        await super()._premium_required()


class ComponentInteraction(BaseInteraction):
    """
    Holds the data of an interaction with a button or select and allows responding to it.

    Attributes
    ------------
    id: :class:`int`
        The id of the interaction.
    type: :class:`~discord.InteractionType`
        The type of the interaction.
    user_id: :class:`int`
        The id of the user who triggered the interaction.
    channel_id: :class:`int`
        The id of the channel where the interaction was triggered.
    messages: Dict[:class:`int`, Union[:class:`~discord.Message`, :class:`~discord.EphemeralMessage`]]
        A mapping of message id's to the message objects that were sent using :attr:`respond`.
    author_locale: Optional[:class:`~discord.Locale`]
        The locale of the user who triggered the interaction.
    guild_locale: Optional[:class:`~discord.Locale`]
        The locale of the guild where the interaction was triggered.
    message: Optional[Union[:class:`~discord.Message`, :class:`~discord.EphemeralMessage`]
        The message the component is attached to.
    cached_message: Optional[Union[:class:`~discord.Message`, :class:`~discord.EphemeralMessage`]
        The cached version of :attr:`message`, if any.
    guild_id: Optional[:class:`int`]
        The id of the guild where the interaction was triggered, if any.
    app_permissions: Optional[:class:`~discord.Permissions`]
        The permissions of the bot in the channel where the interaction was triggered, if it was in a guild.
    match: Optional[:class:`~re.Match`]
        The RegEx |match_object| result of the custom_id of
        the component, if an ``on_click`` or ``on_select`` decorator was used.
    """
    if TYPE_CHECKING:
        match: Optional[Match]

    @property
    def message_is_hidden(self) -> bool:
        """:class:`bool`: Whether the :attr:`message` has the :func:`~discord.MessageFlags.ephemeral` flag."""
        return self.message and self.message.flags.ephemeral

    @cached_slot_property('_cs_component')
    def component(self) -> Union[Button, SelectMenu, UserSelect, RoleSelect, MentionableSelect, ChannelSelect]:
        """
        Union[:class:`~discord.Button`, :ref:`Select <select-like-objects>` like objects]: The component that was used
        """
        custom_id = self.data.custom_id
        component_type = self.data.component_type
        if custom_id.isdigit():
            custom_id = int(custom_id)

        if component_type == ComponentType.Button:
            return utils.get(self.message.all_buttons, custom_id=custom_id)
        elif component_type.value in {3, 5, 6, 7, 8}:
            select_menu = utils.get(self.message.all_select_menus, custom_id=custom_id)
            setattr(select_menu, '_values', self.data.values)
            setattr(select_menu, '_interaction', self)
            return select_menu
        else:
            raise ValueError(f'Unknown component type {self.data.component_type}')

    async def defer(
            self,
            type: Union[Literal[7], InteractionCallbackType] = InteractionCallbackType.deferred_update_msg,
            hidden: bool = False
    ) -> Message:
        """
        Defers the interaction.

        Parameters
        ----------
        type: Union[Literal[5, 6]]
            Use ``5`` to edit the original message later and ``6`` to let the user sees a loading state and edit it later.
        hidden: Optional[:class:`bool`]
            Weather only the author of the command should see this, default :obj:`True`

             .. note::
                Only for :attr:`~discord.InteractionCallbackType.deferred_msg_with_source` (``5``).
        
        Raises
        ------
        AlreadyResponded
            The interaction has already been responded to.
        UnknownInteraction
            The interaction has expired.
        
        Returns
        -------
        Optional[Union[:class:`~discord.Message, :class:`~discord.EphemeralMessage`]]:
            The message containing the loading-state if :class:`~discord.InteractionCallbackType.deferred_msg_with_source` (``5``) is used, else :obj:`None`.
        """
        return await super()._defer(type, hidden)

    async def respond_with_premium_required(self) -> None:
        """|coro|
        Respond with an upgrade button, only available for apps
        with :ddocs:`monetized apps <monetization/overview>` enabled.

        .. note::
            You must respond with this one directly, without using any of
            :meth:`~discord.ApplicationCommandInteraction.defer` or
            :meth:`~discord.ApplicationCommandInteraction.respond`.
        """
        await super()._premium_required()

class AutocompleteInteraction(BaseInteraction):
    """
    Holds the data of an application command autocomplete interaction that will be received when autocomplete for a
    :class:`~discord.SlashCommandOption` with :attr:`~discord.SlashCommandOption.autocomplete` is set to :obj:`True`.

    To respond with the autocomplete choices, use :meth:`send_choices`.

    Attributes
    ------------
    id: :class:`int`
        The id of the interaction.
    type: :class:`~discord.InteractionType`
        The type of the interaction.
    user_id: :class:`int`
        The id of the user who triggered the interaction.
    channel_id: :class:`int`
        The id of the channel where the interaction was triggered.
    author_locale: Optional[:class:`~discord.Locale`]
        The locale of the user who triggered the interaction.
    guild_locale: Optional[:class:`~discord.Locale`]
        The locale of the guild where the interaction was triggered.
    guild_id: Optional[:class:`int`]
        The id of the guild where the interaction was triggered, if any.
    app_permissions: Optional[:class:`~discord.Permissions`]
        The permissions of the bot in the channel where the interaction was triggered, if it was in a guild.
    """

    @property
    def command(self) -> Optional[Union[SlashCommand, MessageCommand, UserCommand]]:
        """Optional[:class:`~discord.SlashCommand`]: The slash-command for wich autocomplete was triggered."""
        if getattr(self, '_command', None) is not None:
            return self._command
        return self._state._get_client()._get_application_command(self.data.id) \
            if (self.type.ApplicationCommand or self.type.ApplicationCommandAutocomplete) else None

    @property
    def focused_option(self) -> 'InteractionDataOption':
        """:class:`~discord.interactions.InteractionDataOption`: Returns the currently focused option."""
        return self.focused  # type: ignore

    @property
    def focused_option_name(self) -> str:
        """:class:`str`: Returns the name of the currently focused option."""
        return self.focused_option.name

    async def send_choices(self, choices: List[SlashCommandOptionChoice]) -> None:
        """
        Respond to the interaction with the choices the user should have.

        Parameters
        ----------
        choices: List[:class:`~discord.SlashCommandOptionChoice`]
            A list of maximum 25 options the user could choose from.

        Raises
        ------
        ValueError
            When more than 25 choices are passed.
        NotFound
            You have been waited to long with responding to the interaction.
        """
        if len(choices) > 25:
            raise ValueError(f'The maximum of choices is 25. Got {len(choices)}.')
        else:
            await self._http.send_autocomplete_callback(
                token=self._token,
                interaction_id=self.id,
                choices=[choice.to_dict() for choice in choices]
            )

    @utils.copy_doc(send_choices)
    @utils.deprecated('send_choices')
    async def suggest(self, choices: List[SlashCommandOptionChoice]) -> None:
        """An aliase for :meth:`.send_choices`"""
        return await self.send_choices(choices)

    async def respond(self, *args, **kwargs):
        raise NotImplementedError

    async def defer(self, *args, **kwargs):
        raise NotImplementedError('You must directly respond to an autocomplete interaction.')


class ModalSubmitInteraction(BaseInteraction):
    """Holds the data of an interaction that will be received when the ``Submit`` button of a :class:`~discord.Modal`
    is pressed and allows responding to it.

    .. note::
        You **can't** respond to a modal submit interaction with another modal.

    Attributes
    -----------
    id: :class:`int`
        The id of the interaction.
    type: :class:`~discord.InteractionType`
        The type of the interaction.
    user_id: :class:`int`
        The id of the user who triggered the interaction.
    channel_id: :class:`int`
        The id of the channel where the interaction was triggered.
    messages: Dict[:class:`int`, Union[:class:`~discord.Message`, :class:`~discord.EphemeralMessage`]]
        A mapping of message id's to the message objects that were sent using :attr:`respond`.
    author_locale: Optional[:class:`~discord.Locale`]
        The locale of the user who triggered the interaction.
    guild_locale: Optional[:class:`~discord.Locale`]
        The locale of the guild where the interaction was triggered.
    cached_message: Optional[Union[:class:`~discord.Message`, :class:`~discord.EphemeralMessage`]
        The cached version of :attr:`message`, if any.
    guild_id: Optional[:class:`int`]
        The id of the guild where the interaction was triggered, if any.
    app_permissions: Optional[:class:`~discord.Permissions`]
        The permissions of the bot in the channel where the interaction was triggered, if it was in a guild.
    match: Optional[|match_object|]
        The RegEx |match_object| result of the custom_id of
        the modal, if an ``on_submit`` decorator was used.
    """

    if TYPE_CHECKING:
        match: Optional[Match]

    @overload
    def get_field(self, custom_id: str) -> Optional[TextInput]: ...

    @overload
    def get_field(self, custom_id: re.Pattern) -> Optional[Tuple[TextInput, Match]]: ...

    def get_field(self, custom_id: Union[str, re.Pattern]) -> Optional[Union[TextInput, Tuple[TextInput, Match]]]:
        """
        Gets the field wich :attr:`~discord.TextInput.custom_id` match, if any.

        Parameters
        ----------
        custom_id: Union[:class:`str`, |pattern_object|]
            The custom_id of the field to get.

            .. note::
                You can also pass a |pattern_object| when you want to use dynamic custom_id's.
                Only the first matching field will be returned.

        Returns
        -------
        Optional[Union[:class:`~discord.TextInput`, Tuple[:class:`~discord.TextInput`, |match_object|]]]:
            - If ``custom_id`` is a :class:`str`, the found :class:`TextInput` is returned, if any.
            - if ``custom_id`` is a |pattern_object| a :class:`tuple` is returned containing the field
                wich :attr:`~discord.TextInput.custom_id` matches and the corresponding |match_object|, if any.
        """
        if isinstance(custom_id, re.Pattern):
            def _check(_c: TextInput):
                match = custom_id.match(_c.custom_id)
                if match:
                    return _c, match
        else:
            def _check(_c: TextInput):
                if _c.custom_id == custom_id:
                    return _c
        for ar in self.data.components:
            for c in ar:
                result = _check(c)
                if result:
                    return result
        return None

    @property
    def fields(self) -> List[TextInput]:
        """
        List[:class:`~discord.TextInput`]: Returns a :class:`list` containing the fields of the :class:`~discord.Modal`.
        """
        field_list = []
        for ar in self.data.components:
            for c in ar:
                field_list.append(c)
        return field_list

    @property
    def custom_id(self) -> str:
        """
        The Custom ID of the :class:`~discord.Modal`

        Returns
        -------
        :class:`str`
            The :attr:`~discord.Modal.custom_id` of the :class:`~discord.Modal`.
        """
        return self.data.custom_id

    async def defer(self, hidden: Optional[bool] = False) -> Optional[Union[Message, EphemeralMessage]]:
        """
        Defers the interaction, the user sees a loading state

        Parameters
        ----------
        hidden: Optional[:class:`bool`]
            Weather only the author of the modal should see this
        
        Raises
        ------
        AlreadyResponded
            The interaction has already been responded to.
        UnknownInteraction
            The interaction has expired.
        
        Returns
        -------
        Union[:class:`~discord.Message, :class:`~discord.EphemeralMessage`]:
            The Message containing the loading-state.
        """
        return await super()._defer(InteractionCallbackType.deferred_msg_with_source, hidden)

    async def respond_with_modal(self, modal: Modal) -> NotImplementedError:
        raise NotImplementedError('You can\'t respond to a modal submit with another modal.')

    async def respond_with_premium_required(self) -> None:
        """|coro|
        Respond with an upgrade button, only available for apps
        with :ddocs:`monetized apps <monetization/overview>` enabled.

        .. note::
            You must respond with this one directly, without using any of
            :meth:`~discord.ApplicationCommandInteraction.defer` or
            :meth:`~discord.ApplicationCommandInteraction.respond`.
        """
        await super()._premium_required()


class InteractionData:
    def __init__(self, *, state: ConnectionState, data: InteractionDataPayload, guild: Optional[Guild] = None, **kwargs) -> None:
        self._data = data
        self._state: ConnectionState = state
        self._guild: Optional[Guild] = guild
        self._channel_id = kwargs.pop('channel_id', None)
        resolved = data.get('resolved')
        if resolved:
            self.resolved = ResolvedData(state=state, data=resolved, guild=guild, channel_id=self._channel_id)
        options = self._data.get('options', [])
        self.options = [InteractionDataOption(state=state, data=option, guild=guild) for option in options]

    def __getitem__(self, item):
        return getattr(self, item, NotImplemented)

    @property
    def name(self) -> Optional[str]:
        return self._data.get('name', None)

    @property
    def id(self) -> int:
        return int(self._data.get('id', 0))

    @property
    def type(self) -> Optional[ApplicationCommandType]:
        return try_enum(ApplicationCommandType, self._data.get('type', None))

    @property
    def component_type(self) -> Optional[ComponentType]:
        return ComponentType.try_value(self._data.get('component_type', None))

    @property
    def custom_id(self) -> Optional[str]:
        return self._data.get('custom_id', None)

    @property
    def target_id(self) -> Optional[int]:
        return utils._get_as_snowflake(self._data, 'target_id')

    @property
    def values(self) -> List[Union[str, int, float]]:
        return self._data.get('values', [])

    @property
    def components(self) -> Optional[List[ActionRow]]:
        c = self._data.get('components', None)
        if c:
            return [ActionRow.from_dict(a) for a in c]


class option_str(str):
    def __new__(cls, *args, **kwargs):
        focused = kwargs.pop('focused', False)
        __self = super().__new__(cls, *args, **kwargs)
        __self.focused = focused
        return __self


class option_int(int):
    def __new__(cls, *args, **kwargs):
        focused = kwargs.pop('focused', False)
        __self = super().__new__(cls, *args, **kwargs)
        __self.focused = focused
        return __self


class option_float(float):
    def __new__(cls, *args, **kwargs):
        focused = kwargs.pop('focused', False)
        __self = super().__new__(cls, *args, **kwargs)
        __self.focused = focused
        return __self


class InteractionDataOption:
    """
    Represents a slash-command option passed via a command.
    By default, you only get in contact with this using :attr:`~discord.AutocompleteInteraction.focused_option`.

    Attributes
    -----------
    name: :class:`str`
        The name of the option
    type: :class:`~discord.OptionType`
        The type of the option

    """

    def __init__(
            self,
            *,
            state: ConnectionState,
            data: ApplicationCommandInteractionDataOptionPayload,
            guild: Optional[Guild] = None,
            **kwargs
    ) -> None:
        self._state: ConnectionState = state
        self._data = data
        self._guild: Optional[Guild] = guild
        self._channel_id = kwargs.pop('channel_id', None)
        self.name: str = data['name']
        self.type: OptionType = OptionType.try_value(data['type'])

    @property
    def value(self) -> Optional[Union[str, int, float]]:
        """Union[:class:`str`, :class:`int`, :class:`float`]: Returns the value of the option (what the user passed)"""
        value = self._data.get('value', MISSING)
        if value is not MISSING:
            if isinstance(value, bool):  # because booleans are integers too
                return value
            if isinstance(value, int):
                return option_int(value, focused=self.focused)
            elif isinstance(value, str):
                return option_str(value, focused=self.focused)
            elif isinstance(value, float):
                return option_float(value, focused=self.focused)
            return value

    @property
    def focused(self) -> bool:
        """:class:`bool`: Whether this option is currently focused (for autocomplete)"""
        return self._data.get('focused', False)

    @property
    def options(self) -> Optional[List[InteractionDataOption]]:
        """Optional[List[:class:`InteractionDataOption`]]: For sub-command (groups) the sub-command or the actual options"""
        options = self._data.get('options', [])
        return [InteractionDataOption(state=self._state, data=option, guild=self._guild) for option in options]


class ResolvedData:
    def __init__(self, *, state: ConnectionState, data: ResolvedDataPayload, guild: Optional[Guild] = None, **kwargs) -> None:
        self._state: ConnectionState = state
        self._data = data
        self._guild: Guild = guild
        self._channel_id: Optional[int] = kwargs.pop('channel_id', None)
        for attr in ('users', 'members', 'channels', 'roles', 'messages', 'attachments'):
            setattr(self, f'_{attr}', {})
            value = data.get(attr, None)
            if value is not None:
                getattr(self, f'_{self.__class__.__name__}__handle_{attr}')(value)
        del self._data  # No longer needed

    @property
    def users(self) -> Optional[Dict[int, User]]:
        return getattr(self, '_users', {})

    def __handle_users(self, value: dict):
        _users = getattr(self, '_users', {})
        for _id, u in value.items():
            _users[int(_id)] = User(state=self._state, data=u)

    @property
    def members(self) -> Optional[Dict[int, Member]]:
        return getattr(self, '_members', {})

    def __handle_members(self, value: dict):
        _members = getattr(self, '_members', {})
        for _id, m in value.items():
            m['user'] = self._data['users'][_id]
            _members[int(_id)] = Member(state=self._state, data=m, guild=self._guild)
        return _members

    @property
    def channels(self) -> Optional[Dict[int, abc.GuildChannel]]:
        return getattr(self, '_channels', {})

    def __handle_channels(self, value: dict):
        _channels = getattr(self, '_channels', {})
        for _id, c in value.items():
            channel = self._guild.get_channel(int(_id))
            if not channel:
                factory, _ch_type_ = _channel_factory(c['type'])
                channel = factory(guild=self._guild, data=c, state=self._state)
            _channels[int(_id)] = channel

    @property
    def roles(self) -> Optional[Dict[int, Role]]:
        return getattr(self, '_roles', {})

    def __handle_roles(self, value: dict):
        _roles: dict = getattr(self, '_roles', {})
        for _id, r in value.items():
            _roles[int(_id)] = Role(guild=self._guild, data=r, state=self._state)

    @property
    def messages(self) -> Optional[Dict[int, Message]]:
        return getattr(self, '_messages', {})

    def __handle_messages(self, value: dict):
        _messages: dict = getattr(self, '_messages', {})
        for _id, m in value.items():
            _messages[int(_id)] = Message(state=self._state, channel=self._state.get_channel(self._channel_id), data=m)

    @property
    def attachments(self) -> Optional[Dict[int, Attachment]]:
        return getattr(self, '_attachments', {})

    def __handle_attachments(self, value: dict):
        _attachments: dict = getattr(self, '_attachments', {})
        for _id, a in value.items():
            _attachments[int(_id)] = Attachment(state=self._state, data=a)
