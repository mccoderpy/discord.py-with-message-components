.. currentmodule:: discord

.. _discord_api_models:

Discord Models
---------------

Models are classes that are received from Discord and are not meant to be created by
the user of the library.

.. danger::

    The classes listed below are **not intended to be created by users** and are also
    **read-only**.

    For example, this means that you should not make your own :class:`User` instances
    nor should you modify the :class:`User` instance yourself.

    If you want to get one of these model classes instances they'd have to be through
    the cache, and a common way of doing so is through the :func:`utils.find` function
    or attributes of model classes that you receive from the events specified in the
    :ref:`discord-api-events`.

.. note::

    Nearly all classes here have :ref:`py:slots` defined which means that it is
    impossible to have dynamic attributes to the data classes.


ClientUser
~~~~~~~~~~~~

.. attributetable:: ClientUser

.. autoclass:: ClientUser()
    :members:
    :inherited-members:

User
~~~~~

.. attributetable:: User

.. autoclass:: User()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

Attachment
~~~~~~~~~~~

.. attributetable:: Attachment

.. autoclass:: Attachment()
    :members:

Asset
~~~~~

.. attributetable:: Asset

.. autoclass:: Asset()
    :members:

Message
~~~~~~~

.. attributetable:: Message

.. autoclass:: Message()
    :members:

EphemeralMessage
~~~~~~~~~~~~~~~~~

.. attributetable:: EphemeralMessage

.. autoclass:: EphemeralMessage()
    :members:

MessageInteraction
~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageInteraction

.. autoclass:: MessageInteraction()
    :members:

RoleSubscriptionInfo
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RoleSubscriptionInfo

.. autoclass:: RoleSubscriptionInfo()
    :members:

DeletedReferencedMessage
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: DeletedReferencedMessage

.. autoclass:: DeletedReferencedMessage()
    :members:


Reaction
~~~~~~~~~

.. attributetable:: Reaction

.. autoclass:: Reaction()
    :members:
    :exclude-members: users

    .. automethod:: users
        :async-for:

Guild
~~~~~~

.. attributetable:: Guild

.. autoclass:: Guild()
    :members:
    :exclude-members: fetch_members, audit_logs

    .. automethod:: fetch_members
        :async-for:

    .. automethod:: audit_logs
        :async-for:

.. autoclass:: GuildFeatures()
    :members:

.. class:: BanEntry

    A namedtuple which represents a ban returned from :meth:`~Guild.bans`.

    .. attribute:: reason

        The reason this user was banned.

        :type: Optional[:class:`str`]
    .. attribute:: user

        The :class:`User` that was banned.

        :type: :class:`User`

GuildScheduledEvent
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: GuildScheduledEvent

.. autoclass:: GuildScheduledEvent()
    :members:
    :exclude-members: users

    .. automethod:: users
        :async-for:

AutoModRule
~~~~~~~~~~~~

.. attributetable:: AutoModRule

.. autoclass:: AutoModRule()
    :members:

AutoModActionPayload
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: AutoModActionPayload

.. autoclass:: AutoModActionPayload()
    :members:

WelcomeScreen
~~~~~~~~~~~~~~

.. attributetable:: WelcomeScreen

.. autoclass:: WelcomeScreen()
    :members:

Integration
~~~~~~~~~~~~

.. autoclass:: Integration()
    :members:

.. autoclass:: IntegrationAccount()
    :members:

Member
~~~~~~

.. attributetable:: Member

.. autoclass:: Member()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

GuildMemberFlags
~~~~~~~~~~~~~~~~

.. attributetable:: GuildMemberFlags

.. autoclass:: GuildMemberFlags()
    :members:

Spotify
~~~~~~~~

.. attributetable:: Spotify

.. autoclass:: Spotify()
    :members:

VoiceState
~~~~~~~~~~~

.. attributetable:: VoiceState

.. autoclass:: VoiceState()
    :members:

Emoji
~~~~~

.. attributetable:: Emoji

.. autoclass:: Emoji()
    :members:

PartialEmoji
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialEmoji

.. autoclass:: PartialEmoji()
    :members:

Role
~~~~~

.. attributetable:: Role

.. autoclass:: Role()
    :members:

RoleTags
~~~~~~~~~~

.. attributetable:: RoleTags

.. autoclass:: RoleTags()
    :members:


PartialMessageable
~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialMessageable

.. autoclass:: PartialMessageable()
    :members:
    :inherited-members:
    :exclude-members: history, typing

        .. automethod:: history
            :async-for:

        .. automethod:: typing
            :async-with:

TextChannel
~~~~~~~~~~~~

.. attributetable:: TextChannel

.. autoclass:: TextChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing, archived_threads

    .. automethod:: archived_threads
        :async-for:

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

ThreadChannel
~~~~~~~~~~~~~~

.. attributetable:: ThreadChannel

.. autoclass:: ThreadChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing, fetch_members

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

    .. automethod:: fetch_members
        :async-for:

ThreadMember
~~~~~~~~~~~~~~

.. attributetable:: ThreadMember

.. autoclass:: ThreadMember()
    :members:
    :inherited-members:

VoiceChannel
~~~~~~~~~~~~~

.. attributetable:: VoiceChannel

.. autoclass:: VoiceChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

StageChannel
~~~~~~~~~~~~~

.. attributetable:: StageChannel

.. autoclass:: StageChannel()
    :members:
    :inherited-members:

ForumChannel
~~~~~~~~~~~~~

.. attributetable:: ForumChannel


.. autoclass:: ForumChannel()
    :members:
    :inherited-members:
    :exclude-members: archived_posts

    .. automethod:: archived_posts
        :async-for:

ForumPost
~~~~~~~~~~

.. attributetable:: ForumPost

.. autoclass:: ForumPost()
    :members:
    :inherited-members:
    :exclude-members: history, typing, fetch_members

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

    .. automethod:: fetch_members
        :async-for:

CategoryChannel
~~~~~~~~~~~~~~~~~

.. attributetable:: CategoryChannel

.. autoclass:: CategoryChannel()
    :members:
    :inherited-members:

DMChannel
~~~~~~~~~

.. attributetable:: DMChannel

.. autoclass:: DMChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

GroupChannel
~~~~~~~~~~~~

.. attributetable:: GroupChannel

.. autoclass:: GroupChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

PartialInviteGuild
~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialInviteGuild

.. autoclass:: PartialInviteGuild()
    :members:

PartialInviteChannel
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialInviteChannel

.. autoclass:: PartialInviteChannel()
    :members:

Invite
~~~~~~~

.. attributetable:: Invite

.. autoclass:: Invite()
    :members:

Template
~~~~~~~~~

.. attributetable:: Template

.. autoclass:: Template()
    :members:

WidgetChannel
~~~~~~~~~~~~~~~

.. attributetable:: WidgetChannel

.. autoclass:: WidgetChannel()
    :members:

WidgetMember
~~~~~~~~~~~~~

.. attributetable:: WidgetMember

.. autoclass:: WidgetMember()
    :members:
    :inherited-members:

Widget
~~~~~~~

.. attributetable:: Widget

.. autoclass:: Widget()
    :members:

StickerPack
~~~~~~~~~~~~

.. attributetable:: StickerPack

.. autoclass:: StickerPack()
    :members:

Sticker
~~~~~~~~

.. attributetable:: Sticker

.. autoclass:: Sticker()
    :members:

.. attributetable:: GuildSticker

.. autoclass:: GuildSticker()
    :inherited-members:
    :members:
    :exclude-members: pack, pack_id, sort_value

VoiceRegionInfo
~~~~~~~~~~~~~~~~

.. attributetable:: VoiceRegionInfo

.. autoclass:: VoiceRegionInfo()
    :members:

RawMessageDeleteEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawMessageDeleteEvent

.. autoclass:: RawMessageDeleteEvent()
    :members:

RawBulkMessageDeleteEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawBulkMessageDeleteEvent

.. autoclass:: RawBulkMessageDeleteEvent()
    :members:

RawMessageUpdateEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawMessageUpdateEvent

.. autoclass:: RawMessageUpdateEvent()
    :members:

RawReactionActionEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawReactionActionEvent

.. autoclass:: RawReactionActionEvent()
    :members:

RawReactionClearEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawReactionClearEvent

.. autoclass:: RawReactionClearEvent()
    :members:

RawReactionClearEmojiEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawReactionClearEmojiEvent

.. autoclass:: RawReactionClearEmojiEvent()
    :members:

VoiceChannelEffectSendEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: VoiceChannelEffectSendEvent

.. autoclass:: VoiceChannelEffectSendEvent()
    :members:
