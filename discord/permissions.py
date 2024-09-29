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

from typing import (
    ClassVar,
    Dict,
    Iterator,
    Optional,
    Set,
    Tuple,
    TYPE_CHECKING
)
from typing_extensions import Final

from .flags import alias_flag_value, BaseFlags, fill_with_flags, flag_value

if TYPE_CHECKING:
    from .types.guild import PermissionFlag


__all__ = (
    'Permissions',
    'PermissionOverwrite',
)

# A permission alias works like a regular flag but is marked
# So the PermissionOverwrite knows to work with it
class permission_alias(alias_flag_value):
    pass

def make_permission_alias(alias):
    def decorator(func):
        ret = permission_alias(func)
        ret.alias = alias
        return ret
    return decorator

@fill_with_flags()
class Permissions(BaseFlags):
    """Wraps up the Discord permission value.

    The properties provided are two-way. You can set and retrieve individual
    bits using the properties as if they were regular bools. This allows
    you to edit permissions.

    .. versionchanged:: 1.3
        You can now use keyword arguments to initialize :class:`Permissions`
        similar to :meth:`update`.

    .. container:: operations

        .. describe:: x == y

            Checks if two permissions are equal.
        .. describe:: x != y

            Checks if two permissions are not equal.
        .. describe:: x <= y

            Checks if a permission is a subset of another permission.
        .. describe:: x >= y

            Checks if a permission is a superset of another permission.
        .. describe:: x < y

             Checks if a permission is a strict subset of another permission.
        .. describe:: x > y

             Checks if a permission is a strict superset of another permission.
        .. describe:: hash(x)

               Return the permission's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(perm, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.
               Note that aliases are not shown.

    Attributes
    -----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available permissions. You should query
        permissions via the properties rather than using this raw value.
    """

    __slots__ = ()
    
    if TYPE_CHECKING:
        VALID_FLAGS: Final[ClassVar[Dict[PermissionFlag, int]]]
        DEFAULT_VALUE: ClassVar[int]
        
    def __init__(self, permissions: int = 0, **kwargs: bool) -> None:
        if not isinstance(permissions, int):
            raise TypeError(
                f'Expected int parameter, received {permissions.__class__.__name__} instead.'
            )

        self.value: int = permissions
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError('%r is not a valid permission name.' % key)
            setattr(self, key, value)

    def is_subset(self, other: Permissions) -> bool:
        """Returns ``True`` if self has the same or fewer permissions as other."""
        if isinstance(other, Permissions):
            return (self.value & other.value) == self.value
        else:
            raise TypeError(
                f"cannot compare {self.__class__.__name__} with {other.__class__.__name__}"
            )

    def is_superset(self, other: Permissions) -> bool:
        """Returns ``True`` if self has the same or more permissions as other."""
        if isinstance(other, Permissions):
            return (self.value | other.value) == self.value
        else:
            raise TypeError(
                f"cannot compare {self.__class__.__name__} with {other.__class__.__name__}"
            )

    def is_strict_subset(self, other: Permissions) -> bool:
        """Returns ``True`` if the permissions on other are a strict subset of those on self."""
        return self.is_subset(other) and self != other

    def is_strict_superset(self, other: Permissions) -> bool:
        """Returns ``True`` if the permissions on other are a strict superset of those on self."""
        return self.is_superset(other) and self != other

    __le__ = is_subset
    __ge__ = is_superset
    __lt__ = is_strict_subset
    __gt__ = is_strict_superset

    @classmethod
    def none(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to ``False``."""
        return cls(0)

    @classmethod
    def all(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to ``True``.
        """
        return cls(0b11111111111111111111111111111111111111111111111)

    @classmethod
    def all_channel(cls):
        """A :class:`Permissions` with all channel-specific permissions set to
        ``True`` and the guild-specific ones set to ``False``. The guild-specific
        permissions are currently:

        - :attr:`manage_emojis`
        - :attr:`view_audit_log`
        - :attr:`view_guild_insights`
        - :attr:`manage_guild`
        - :attr:`change_nickname`
        - :attr:`manage_nicknames`
        - :attr:`kick_members`
        - :attr:`ban_members`
        - :attr:`administrator`

        .. versionchanged:: 1.7
           Added :attr:`stream`, :attr:`priority_speaker` and :attr:`use_slash_commands` permissions.

        .. versionchanged:: 2.0
            Added :attr:`start_embedded_activities`, :attr:`moderate_members`, :attr:`manage_events`, :attr:`create_private_threads`,
            :attr:`create_puplic_threads`, :attr:`manage_threads`, :attr:`send_messages_in_threads`, :attr:`request_to_speak` and :attr:`use_external_stickers`
        """
        return cls(0b11111111110110011111101111111111101010001)

    @classmethod
    def general(cls):
        """A factory method that creates a :class:`Permissions` with all
        "General" permissions from the official Discord UI set to ``True``.

        .. versionchanged:: 1.7
           Permission :attr:`read_messages` is now included in the general permissions, but
           permissions :attr:`administrator`, :attr:`create_instant_invite`, :attr:`kick_members`,
           :attr:`ban_members`, :attr:`change_nickname` and :attr:`manage_nicknames` are
           no longer part of the general permissions.

        .. versionchanged:: 2.0
            Added :attr:`moderate_members`, :attr:`manage_expressions` and :attr:`create_expressions` permission.
        """
        return cls(0b10010000000001110000000010000000010010110000)

    @classmethod
    def membership(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Membership" permissions from the official Discord UI set to ``True``.

        .. versionadded:: 1.7

        .. versionchanged:: 2.0
            Added :attr:`moderate_members` permission.
        """
        return cls(0b10000000000001100000000000000000000000111)

    @classmethod
    def text(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Text" permissions from the official Discord UI set to ``True``.

        .. versionchanged:: 1.7
           Permission :attr:`read_messages` is no longer part of the text permissions.
           Added :attr:`use_slash_commands` permission.

        .. versionchanged:: 2.0
            Added :attr:`send_voice_messages`, :attr:`manage_threads`, :attr:`create_public_threads`,
            :attr:`create_private_threads`, :attr:`send_messages_in_threads` and :attr:`use_external_stickers` permission.
        """
        return cls(0b10000000111110010000000000001111111100001000000)

    @classmethod
    def voice(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Voice" permissions from the official Discord UI set to ``True``.

        .. versionchanged:: 2.0
            Added :attr:`start_embedded_activities`, :attr:`use_soundboard` :attr:`use_external_sounds` and
            :attr:`set_voice_channel_status` permission.
        """
        return cls(0b1001001001000000000000011111100000000001100000000)

    @classmethod
    def stage(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Stage Channel" permissions from the official Discord UI set to ``True``.

        .. versionadded:: 1.7
        """
        return cls(1 << 32)

    @classmethod
    def stage_moderator(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Stage Moderator" permissions from the official Discord UI set to ``True``.

        .. versionadded:: 1.7
        """
        return cls(0b100000001010000000000000000000000)

    @classmethod
    def events(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Events" permissions from the official Discord UI set to ``True``.

        .. versionadded:: 2.0
        """
        return cls(0b100000000001000000000000000000000000000000000)

    @classmethod
    def advanced(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Advanced" permissions from the official Discord UI set to ``True``.

        .. versionadded:: 1.7
        """
        return cls(1 << 3)

    def update(self, **kwargs: bool) -> None:
        r"""Bulk updates this permission object.

        Allows you to set multiple attributes by using keyword
        arguments. The names must be equivalent to the properties
        listed. Extraneous key/value pairs will be silently ignored.

        Parameters
        ------------
        \*\*kwargs
            A list of key/value pairs to bulk update permissions with.
        """
        for key, value in kwargs.items():
            if key in self.VALID_FLAGS:
                setattr(self, key, value)

    def handle_overwrite(self, allow: int, deny: int) -> None:
        # Basically this is what's happening here.
        # We have an original bit array, e.g. 1010
        # Then we have another bit array that is 'denied', e.g. 1111
        # And then we have the last one which is 'allowed', e.g. 0101
        # We want original OP denied to end up resulting in
        # whatever is in denied to be set to 0.
        # So 1010 OP 1111 -> 0000
        # Then we take this value and look at the allowed values.
        # And whatever is allowed is set to 1.
        # So 0000 OP2 0101 -> 0101
        # The OP is base  & ~denied.
        # The OP2 is base | allowed.
        self.value = (self.value & ~deny) | allow

    @flag_value
    def create_instant_invite(self):
        """:class:`bool`: Returns ``True`` if the user can create instant invites."""
        return 1 << 0

    @flag_value
    def kick_members(self):
        """:class:`bool`: Returns ``True`` if the user can kick users from the guild."""
        return 1 << 1

    @flag_value
    def ban_members(self):
        """:class:`bool`: Returns ``True`` if a user can ban users from the guild."""
        return 1 << 2

    @flag_value
    def administrator(self):
        """:class:`bool`: Returns ``True`` if a user is an administrator. This role overrides all other permissions.

        This also bypasses all channel-specific overrides.
        """
        return 1 << 3

    @flag_value
    def manage_channels(self):
        """:class:`bool`: Returns ``True`` if a user can edit, delete, or create channels in the guild.

        This also corresponds to the "Manage Channel" channel-specific override."""
        return 1 << 4

    @flag_value
    def manage_guild(self):
        """:class:`bool`: Returns ``True`` if a user can edit guild properties."""
        return 1 << 5

    @flag_value
    def add_reactions(self):
        """:class:`bool`: Returns ``True`` if a user can add reactions to messages."""
        return 1 << 6

    @flag_value
    def view_audit_log(self):
        """:class:`bool`: Returns ``True`` if a user can view the guild's audit log."""
        return 1 << 7

    @flag_value
    def priority_speaker(self):
        """:class:`bool`: Returns ``True`` if a user can be more easily heard while talking."""
        return 1 << 8

    @flag_value
    def stream(self):
        """:class:`bool`: Returns ``True`` if a user can stream in a voice channel."""
        return 1 << 9

    @flag_value
    def read_messages(self):
        """:class:`bool`: Returns ``True`` if a user can read messages from all or specific text channels."""
        return 1 << 10

    @make_permission_alias('read_messages')
    def view_channel(self):
        """:class:`bool`: An alias for :attr:`read_messages`.

        .. versionadded:: 1.3
        """
        return 1 << 10

    @flag_value
    def send_messages(self):
        """:class:`bool`: Returns ``True`` if a user can send messages from all or specific text channels
        and create posts in forum channels."""
        return 1 << 11

    @make_permission_alias('send_messages')
    def create_posts(self):
        """:class:`bool`: An alias for :attr:`send_messages`.

        .. versionadded:: 2.0
        """
        return 1 << 11

    @flag_value
    def send_tts_messages(self):
        """:class:`bool`: Returns ``True`` if a user can send TTS messages from all or specific text channels."""
        return 1 << 12

    @flag_value
    def manage_messages(self):
        """:class:`bool`: Returns ``True`` if a user can delete or pin messages in a text channel.

        .. note::

            Note that there are currently no ways to edit other people's messages.
        """
        return 1 << 13

    @flag_value
    def embed_links(self):
        """:class:`bool`: Returns ``True`` if a user's messages will automatically be embedded by Discord."""
        return 1 << 14

    @flag_value
    def attach_files(self):
        """:class:`bool`: Returns ``True`` if a user can send files in their messages."""
        return 1 << 15

    @flag_value
    def read_message_history(self):
        """:class:`bool`: Returns ``True`` if a user can read a text channel's previous messages."""
        return 1 << 16

    @flag_value
    def mention_everyone(self):
        """:class:`bool`: Returns ``True`` if a user's @everyone or @here will mention everyone in the text channel."""
        return 1 << 17

    @flag_value
    def external_emojis(self):
        """:class:`bool`: Returns ``True`` if a user can use emojis from other guilds."""
        return 1 << 18

    @make_permission_alias('external_emojis')
    def use_external_emojis(self):
        """:class:`bool`: An alias for :attr:`external_emojis`.

        .. versionadded:: 1.3
        """
        return 1 << 18

    @flag_value
    def view_guild_insights(self):
        """:class:`bool`: Returns ``True`` if a user can view the guild's insights.

        .. versionadded:: 1.3
        """
        return 1 << 19

    @flag_value
    def connect(self):
        """:class:`bool`: Returns ``True`` if a user can connect to a voice channel."""
        return 1 << 20

    @flag_value
    def speak(self):
        """:class:`bool`: Returns ``True`` if a user can speak in a voice channel."""
        return 1 << 21

    @flag_value
    def mute_members(self):
        """:class:`bool`: Returns ``True`` if a user can mute other users."""
        return 1 << 22

    @flag_value
    def deafen_members(self):
        """:class:`bool`: Returns ``True`` if a user can deafen other users."""
        return 1 << 23

    @flag_value
    def move_members(self):
        """:class:`bool`: Returns ``True`` if a user can move users between other voice channels."""
        return 1 << 24

    @flag_value
    def use_voice_activation(self):
        """:class:`bool`: Returns ``True`` if a user can use voice activation in voice channels."""
        return 1 << 25

    @flag_value
    def change_nickname(self):
        """:class:`bool`: Returns ``True`` if a user can change their nickname in the guild."""
        return 1 << 26

    @flag_value
    def manage_nicknames(self):
        """:class:`bool`: Returns ``True`` if a user can change other user's nickname in the guild."""
        return 1 << 27

    @flag_value
    def manage_roles(self):
        """:class:`bool`: Returns ``True`` if a user can create or edit roles less than their role's position.

        This also corresponds to the "Manage Permissions" channel-specific override.
        """
        return 1 << 28

    @make_permission_alias('manage_roles')
    def manage_permissions(self):
        """:class:`bool`: An alias for :attr:`manage_roles`.

        .. versionadded:: 1.3
        """
        return 1 << 28

    @flag_value
    def manage_webhooks(self):
        """:class:`bool`: Returns ``True`` if a user can create, edit, or delete webhooks."""
        return 1 << 29
    
    @flag_value
    def manage_expressions(self):
        """:class:`bool`: Returns ``True`` if a user can create, edit, or delete emojis, stickers and sounds."""
        return 1 << 30
    
    @make_permission_alias('manage_expressions')
    def manage_emojis(self):
        """:class:`bool`: An aliase for :attr:`manage_expressions`"""
        return 1 << 30
    
    @make_permission_alias('manage_expressions')
    def manage_stickers(self):
        """:class:`bool`: An aliase for :attr:`manage_expressions`"""
        return 1 << 30
    
    @make_permission_alias('manage_expressions')
    def manage_emojis_and_stickers(self):
        """:class:`bool`: An aliase for :attr:`manage_expressions`"""
        return 1 << 30
    
    @make_permission_alias('manage_expressions')
    def manage_sounds(self):
        """:class:`bool`: An aliase for :attr:`manage_expressions`"""
        return 1 << 30
    
    @flag_value
    def create_expressions(self):
        """:class:`bool`: Returns ``True`` if a user can create emojis, stickers or
        `sounds <https://support.discord.com/hc/de/articles/12612888127767-Soundboard-FAQ>`_ in a server.
        
        .. versionadded:: 2.0
        """
        return 1 << 43
    
    @make_permission_alias('create_expressions')
    def create_emojis(self):
        """:class:`bool`: An aliase for :attr:`create_expressions`"""
        return 1 << 43
    
    @make_permission_alias('create_expressions')
    def create_stickers(self):
        """:class:`bool`: An aliase for :attr:`create_expressions`"""
        return 1 << 43
    
    @make_permission_alias('create_expressions')
    def create_sounds(self):
        """:class:`bool`: An aliase for :attr:`create_expressions`"""
        return 1 << 43
    
    @flag_value
    def use_application_commands(self):
        """:class:`bool`: Returns ``True`` if a user can use application commands.

        .. versionadded:: 1.7
        """
        return 1 << 31

    @make_permission_alias('use_application_commands')
    def use_slash_commands(self):
        """:class:`bool`: An aliase for :attr:`use_application_commands`"""
        return 1 << 31

    @flag_value
    def request_to_speak(self):
        """:class:`bool`: Returns ``True`` if a user can request to speak in a stage channel.

        .. versionadded:: 1.7
        """
        return 1 << 32

    @flag_value
    def manage_events(self):
        """:class:`bool`: Returns ``True`` if a user can create and manage Guild-Scheduled-Events.
        
        .. versionadded:: 2.0
        """
        return 1 << 33
    
    @flag_value
    def create_events(self):
        """:class:`bool`: Returns ``True`` if a user can create Guild-Scheduled-Events.
        
        .. versionadded:: 2.0
        """
        return 1 << 44

    @flag_value
    def manage_threads(self):
        """:class:`bool`: Returns ``True`` if a user can delete and archive threads and viewing all private threads.
        
        .. versionadded:: 2.0"""
        return 1 << 34

    @flag_value
    def create_public_threads(self):
        """:class:`bool`: Returns ``True`` if a user can create and participate in threads.
        
        .. versionadded:: 2.0"""
        return 1 << 35

    @flag_value
    def create_private_threads(self):
        """:class:`bool`: Returns ``True`` if a user can create and participate in private threads.
        
        .. versionadded:: 2.0"""
        return 1 << 36

    @flag_value
    def use_external_stickers(self):
        """:class:`bool`: Returns ``True`` if a user can use custom stickers from other servers.
        
        .. versionadded:: 2.0
        """
        return 1 << 37

    @flag_value
    def send_messages_in_threads(self):
        """:class:`bool`: Returns ``True`` if a user can send messages in threads and forum posts.
        
        .. versionadded:: 2.0
        """
        return 1 << 38

    @make_permission_alias('send_messages_in_threads')
    def send_messages_in_posts(self):
        """:class:`bool`: An alias for :attr:`send_messages_in_threads`."""
        return 1 << 38

    # TODO: Remove this alias in 2.0 release
    @make_permission_alias('send_messages_in_threads')
    def send_thread_messages(self):
        """:class:`bool`: An alias for :attr:`send_messages_in_threads`."""
        return 1 << 38

    @flag_value
    def start_embedded_activities(self):
        """:class:`bool`: Returns ``True`` if a user can start embedded activities in a voice channel
        (e.g. voice-activities).
        
        .. versionadded:: 2.0"""
        return 1 << 39

    @make_permission_alias('start_embedded_activities')
    def start_voice_activities(self):
        """:class:`bool`: An alias for :attr:`start_embedded_activities`."""
        return 1 << 39

    @flag_value
    def moderate_members(self):
        """:class:`bool`: Returns ``True`` if a user can moderate other members (like timeout or verify them).
        
        .. versionadded:: 2.0"""
        return 1 << 40

    @make_permission_alias('moderate_members')
    def timeout_members(self):
        """:class:`bool`: An alias for :attr:`moderate_members`."""
        return 1 << 40
    
    @flag_value
    def view_creator_monetization_analytics(self):
        """:class:`bool`: Returns ``True`` if a user can view analytics for monetization of their content.
        
        .. versionadded:: 2.0"""
        return 1 << 41
    
    @flag_value
    def use_soundboard(self):
        """:class:`bool`: Returns ``True`` if a user can use the soundboard in a voice channel.
        
        .. versionadded:: 2.0"""
        return 1 << 42
    
    @flag_value
    def use_external_sounds(self):
        """:class:`bool`: Returns ``True`` if a user can use custom soundboard sounds from other servers.
        
        .. versionadded:: 2.0"""
        return 1 << 45

    @flag_value
    def send_voice_messages(self):
        """:class:`bool`: Returns ``True`` if a user can send voice messages.
        
        .. versionadded:: 2.0"""
        return 1 << 46

    @flag_value
    def set_voice_channel_status(self):
        """:class:`bool`: Returns ``True`` if a user can set the status of a voice channel.

        .. versionadded:: 2.0"""
        return 1 << 48

    @flag_value
    def send_polls(self):
        """:class:`bool`: Returns ``True`` if a user can send polls in a channel.

        .. versionadded:: 2.0"""
        return 1 << 49

    @flag_value
    def use_external_apps(self):
        """:class:`bool`: Returns ``True`` if user-installed apps are allowed to send public responses.

        .. note::
            - When ``False``, users will still be allowed to use their apps but the responses will be ephemeral.
            - This only applies to apps not also installed to the server

        .. versionadded:: 2.0"""
        return 1 << 50


def augment_from_permissions(cls):
    cls.VALID_NAMES = set(Permissions.VALID_FLAGS)
    aliases = set()

    # make descriptors for all the valid names and aliases
    for name, value in Permissions.__dict__.items():
        if isinstance(value, permission_alias):
            key = value.alias
            aliases.add(name)
        elif isinstance(value, flag_value):
            key = name
        else:
            continue

        # god bless Python
        def getter(self, x=key):
            return self._values.get(x)
        def setter(self, value, x=key):
            self._set(x, value)

        prop = property(getter, setter)
        setattr(cls, name, prop)

    cls.PURE_FLAGS = cls.VALID_NAMES - aliases
    return cls


@augment_from_permissions
class PermissionOverwrite:
    r"""A type that is used to represent a channel specific permission.

    Unlike a regular :class:`Permissions`\, the default value of a
    permission is equivalent to ``None`` and not ``False``. Setting
    a value to ``False`` is **explicitly** denying that permission,
    while setting a value to ``True`` is **explicitly** allowing
    that permission.

    The values supported by this are the same as :class:`Permissions`
    with the added possibility of it being set to ``None``.
    """

    __slots__ = ('_values',)
    
    if TYPE_CHECKING:
        VALID_NAMES: ClassVar[Set[str]]
        PURE_FLAGS: ClassVar[Set[str]]
        
        create_instant_invite: Optional[bool]
        kick_members: Optional[bool]
        ban_members: Optional[bool]
        administrator: Optional[bool]
        manage_channels: Optional[bool]
        manage_guild: Optional[bool]
        add_reactions: Optional[bool]
        view_audit_log: Optional[bool]
        priority_speaker: Optional[bool]
        stream: Optional[bool]
        read_messages: Optional[bool]
        view_channel: Optional[bool]
        send_messages: Optional[bool]
        send_tts_messages: Optional[bool]
        manage_messages: Optional[bool]
        embed_links: Optional[bool]
        attach_files: Optional[bool]
        read_message_history: Optional[bool]
        mention_everyone: Optional[bool]
        external_emojis: Optional[bool]
        use_external_emojis: Optional[bool]
        view_guild_insights: Optional[bool]
        connect: Optional[bool]
        speak: Optional[bool]
        mute_members: Optional[bool]
        deafen_members: Optional[bool]
        move_members: Optional[bool]
        use_voice_activation: Optional[bool]
        change_nickname: Optional[bool]
        manage_nicknames: Optional[bool]
        manage_roles: Optional[bool]
        manage_permissions: Optional[bool]
        manage_webhooks: Optional[bool]
        manage_expressions: Optional[bool]
        manage_emojis: Optional[bool]
        manage_stickers: Optional[bool]
        manage_emojis_and_stickers: Optional[bool]
        manage_sounds: Optional[bool]
        create_expressions: Optional[bool]
        create_emojis: Optional[bool]
        create_stickers: Optional[bool]
        create_sounds: Optional[bool]
        use_slash_commands: Optional[bool]
        use_application_commands: Optional[bool]
        request_to_speak: Optional[bool]
        manage_events: Optional[bool]
        create_events: Optional[bool]
        manage_threads: Optional[bool]
        create_public_threads: Optional[bool]
        create_private_threads: Optional[bool]
        use_external_stickers: Optional[bool]
        send_messages_in_threads: Optional[bool]
        send_thread_messages: Optional[bool]
        start_embedded_activities: Optional[bool]
        start_voice_activities: Optional[bool]
        moderate_members: Optional[bool]
        timeout_members: Optional[bool]
        view_creator_monetization_analytics: Optional[bool]
        use_soundboard: Optional[bool]
        use_external_sounds: Optional[bool]
        send_voice_messages: Optional[bool]
        set_voice_channel_status: Optional[bool]
    
    def __init__(self, **kwargs: Optional[bool]) -> None:
        self._values = {}

        for key, value in kwargs.items():
            if key not in self.VALID_NAMES:
                raise ValueError('no permission called {0}.'.format(key))

            setattr(self, key, value)

    def __eq__(self, other) -> bool:
        """Checks if two overwrites are equal."""
        return isinstance(other, PermissionOverwrite) and self._values == other._values
    def __ne__(self, other) -> bool:
        """Checks if two overwrites are not equal."""
        return not self.__eq__(other)

    def _set(self, key: PermissionFlag, value: Optional[bool]) -> None:
        if value not in (True, None, False):
            raise TypeError('Expected bool or NoneType, received {0.__class__.__name__}'.format(value))

        if value is None:
            self._values.pop(key, None)
        else:
            self._values[key] = value

    def pair(self) -> Tuple[Permissions, Permissions]:
        """Tuple[:class:`Permissions`, :class:`Permissions`]: Returns the (allow, deny) pair from this overwrite."""

        allow = Permissions.none()
        deny = Permissions.none()

        for key, value in self._values.items():
            if value is True:
                setattr(allow, key, True)
            elif value is False:
                setattr(deny, key, True)

        return allow, deny

    @classmethod
    def from_pair(cls, allow: Permissions, deny: Permissions) -> PermissionOverwrite:
        """Creates an overwrite from an allow/deny pair of :class:`Permissions`."""
        ret = cls()
        for key, value in allow:
            if value is True:
                setattr(ret, key, True)

        for key, value in deny:
            if value is True:
                setattr(ret, key, False)

        return ret

    def is_empty(self) -> bool:
        """Checks if the permission overwrite is currently empty.

        An empty permission overwrite is one that has no overwrites set
        to ``True`` or ``False``.

        Returns
        -------
        :class:`bool`
            Indicates if the overwrite is empty.
        """
        return len(self._values) == 0

    def update(self, **kwargs: Optional[bool]) -> None:
        r"""Bulk updates this permission overwrite object.

        Allows you to set multiple attributes by using keyword
        arguments. The names must be equivalent to the properties
        listed. Extraneous key/value pairs will be silently ignored.

        Parameters
        ------------
        \*\*kwargs
            A list of key/value pairs to bulk update with.
        """
        for key, value in kwargs.items():
            if key not in self.VALID_NAMES:
                continue

            setattr(self, key, value)

    def __iter__(self) -> Iterator[Tuple[PermissionFlag, bool]]:
        """Returns an iterator of ``(perm, value)`` pairs.
        This allows it to be, for example, constructed as a dict or a list  of pairs.

        Note that aliases are not shown."""
        for key in self.PURE_FLAGS:
            yield key, self._values.get(key)
