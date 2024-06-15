.. currentmodule:: discord

.. _discord-api-enums:

Enumerations
-------------

The API provides some enumerations for certain types of strings to avoid the API
from being stringly typed in case the strings change in the future.

All enumerations are subclasses of an internal class which mimics the behaviour
of :class:`enum.Enum`.

.. hint::
    You can use any of the enum classe members as an attribute of an instance of it to get a :class:`bool`
    whether the instance has this value.

    Example:

    .. code-block:: python3

        # channel could be any channel like object
        if channel.type.private:  # True if channel is a DMChannel
            ...

        # This is the same as
        if channel.type == discord.ChannelType.private:
            ...


.. class:: ChannelType

    Specifies the type of channel.

    .. attribute:: text

        A text channel.
    .. attribute:: voice

        A voice channel.
    .. attribute:: private

        A private text channel. Also called a direct message.
    .. attribute:: group

        A private group text channel.
    .. attribute:: category

        A category channel.
    .. attribute:: news

        A guild news channel.

    .. attribute:: store

        A guild store channel.

    .. attribute:: stage_voice

        A guild stage voice channel.

        .. versionadded:: 1.7

.. class:: MessageType

    Specifies the type of :class:`Message`. This is used to denote if a message
    is to be interpreted as a system message or a regular message.

    .. container:: operations

      .. describe:: x == y

          Checks if two messages are equal.
      .. describe:: x != y

          Checks if two messages are not equal.

    .. attribute:: default

        The default message type. This is the same as regular messages.
    .. attribute:: recipient_add

        The system message when a recipient is added to a group private
        message, i.e. a private channel of type :attr:`ChannelType.group`.
    .. attribute:: recipient_remove

        The system message when a recipient is removed from a group private
        message, i.e. a private channel of type :attr:`ChannelType.group`.
    .. attribute:: call

        The system message denoting call state, e.g. missed call, started call,
        etc.
    .. attribute:: channel_name_change

        The system message denoting that a channel's name has been changed.
    .. attribute:: channel_icon_change

        The system message denoting that a channel's icon has been changed.
    .. attribute:: pins_add

        The system message denoting that a pinned message has been added to a channel.
    .. attribute:: new_member

        The system message denoting that a new member has joined a Guild.

    .. attribute:: premium_guild_subscription

        The system message denoting that a member has "nitro boosted" a guild.
    .. attribute:: premium_guild_tier_1

        The system message denoting that a member has "nitro boosted" a guild
        and it achieved level 1.
    .. attribute:: premium_guild_tier_2

        The system message denoting that a member has "nitro boosted" a guild
        and it achieved level 2.
    .. attribute:: premium_guild_tier_3

        The system message denoting that a member has "nitro boosted" a guild
        and it achieved level 3.
    .. attribute:: channel_follow_add

        The system message denoting that an announcement channel has been followed.

        .. versionadded:: 1.3
    .. attribute:: guild_stream

        The system message denoting that a member is streaming in the guild.

        .. versionadded:: 1.7
    .. attribute:: guild_discovery_disqualified

        The system message denoting that the guild is no longer eligible for Server
        Discovery.

        .. versionadded:: 1.7
    .. attribute:: guild_discovery_requalified

        The system message denoting that the guild has become eligible again for Server
        Discovery.

        .. versionadded:: 1.7
    .. attribute:: guild_discovery_grace_period_initial_warning

        The system message denoting that the guild has failed to meet the Server
        Discovery requirements for one week.

        .. versionadded:: 1.7
    .. attribute:: guild_discovery_grace_period_final_warning

        The system message denoting that the guild has failed to meet the Server
        Discovery requirements for 3 weeks in a row.

        .. versionadded:: 1.7
    .. attribute:: thread_created

        The system message denoting that a thread has been created.

        .. versionadded:: 2.0
    .. attribute:: reply

        A message that is a reply to another message.

        .. versionadded:: 2.0
    .. attribute::  chat_input_command

        A message that is a slash command.

        .. versionadded:: 2.0
    .. attribute::  thread_starter_message

        A message that is the first message in a thread.

        .. versionadded:: 2.0
    .. attribute:: guild_invite_reminder

        The system message denoting that a guild invite reminder has been sent.

        .. versionadded:: 2.0
    .. attribute:: context_menu_command

        A message that is a context menu command.

        .. versionadded:: 2.0
    .. attribute:: automoderation_action

        A log message from discords auto moderation system.

        .. versionadded:: 2.0
    .. attribute:: role_subscription_purchase

        A message informing about a role subscription purchase.

        .. versionadded:: 2.0
    .. attribute:: interaction_premium_upsell

        A message informing about a premium upsell.

        .. versionadded:: 2.0
    .. attribute:: stage_start

        A message informing about a stage starting.

        .. versionadded:: 2.0
    .. attribute:: stage_end

        A message informing about a stage ending.

        .. versionadded:: 2.0
    .. attribute:: stage_speaker_change

        A message informing about a stage having a new speaker.

        .. versionadded:: 2.0
    .. attribute:: stage_raise_hand

        A message informing about someone raising their hand in a stage.

        .. versionadded:: 2.0
    .. attribute:: stage_topic_change

        A message informing about the topic of a stage been changed.

        .. versionadded:: 2.0
    .. attribute:: guild_application_premium_subscription

        The system message denoting that a member has subscribed to a guild application.

        .. versionadded:: 2.4

.. class:: ReactionType

    The type of a :class:`Reaction`.

    .. versionadded:: 2.0

    .. attribute:: normal

        A normal reaction

    .. attribute:: burst

        A :dis-gd:`burst reaction <super-reactions>`.

.. class:: ComponentType

    .. attribute:: ActionRow

        Container for other components

    .. attribute:: Button

        Button object

    .. attribute:: StringSelect

        Select menu for picking from defined text options

    .. attribute:: TextInput

        Text input object

    .. attribute:: UserSelect

        Select menu for users

    .. attribute:: RoleSelect

        Select menu for roles

    .. attribute:: MentionableSelect

        Select menu for mentionables (users and roles)

    .. attribute:: ChannelSelect

        Select menu for channels

.. class:: SelectDefaultValueType

    .. attribute:: user

        The :attr:`~DefaultSelectValue.id` represents a user, only valid for :class:`UserSelect` and :class:`MentionableSelect`

    .. attribute:: role

        The :attr:`~DefaultSelectValue.id` represents a role, only valid for :class:`RoleSelect` and :class:`MentionableSelect`

    .. attribute:: channel

        The :attr:`~DefaultSelectValue.id` represents a channel, only valid for :class:`ChannelSelect`

.. class:: ButtonStyle

   The possible styles for a :class:`~discord.Button`

   +------------------------+-------+----------------+--------------------------------+
   | NAME                   | VALUE | ALIASES        | EXAMPLE                        |
   +========================+=======+================+================================+
   | .. attribute:: blurple |   1   |                | .. image:: /imgs/blurple.png   |
   |                        |       | ``Primary``    |    :alt: Blurple Button Picture|
   |                        |       |                |                                |
   +------------------------+-------+----------------+--------------------------------+
   | .. attribute:: grey    |   2   | ``gray``,      | .. image:: /imgs/grey.png      |
   |                        |       | ``Secondary``  |    :alt: Grey Button Picture   |
   |                        |       |                |                                |
   +------------------------+-------+----------------+--------------------------------+
   | .. attribute:: green   |   3   | ``Success``    | .. image:: /imgs/green.png     |
   |                        |       |                |    :alt: Green Button Picture  |
   |                        |       |                |                                |
   +------------------------+-------+----------------+--------------------------------+
   | .. attribute:: red     |   4   | ``Danger``     | .. image:: /imgs/red.png       |
   |                        |       |                |    :alt: Red Button Picture    |
   |                        |       |                |                                |
   +------------------------+-------+----------------+--------------------------------+
   | .. attribute:: url     |   5   | ``link``,      | .. image:: /imgs/url.png       |
   |                        |       | ``grey_url``,  |    :alt: URL Button Picture    |
   |                        |       | ``Link_Button``|                                |
   +------------------------+-------+----------------+--------------------------------+

.. class:: InteractionType

    Specifies the type of an interaction received from discord.

    .. attribute:: PingAck

        A ping interaction, those are only used for
        `http-only interactions <https://discord.com/developers/docs/interactions/receiving-and-responding#receiving-an-interaction>`_
        which are currently not supported by discord4py.

    .. attribute:: ApplicationCommand

        A user invoked a slash, user or message command.

    .. attribute:: Component

        A user pressed a button, or submitted a select menu.

    .. attribute:: ApplicationCommandAutocomplete

        Sent regularly when a user is filling out a slash-command option, that has autocomplete enabled.

    .. attribute:: ModalSubmit

        A user submitted a modal.

.. _defer: :meth:`discord.BaseInteraction.defer`

.. class:: InteractionCallbackType

   InteractionCallbackType to react to an :class:`~discor.BaseInteraction`

   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+
   | NAME                                    | VALUE | DESCRIPTION                                      | USAGE                       | EXAMPLE                                    |
   +=========================================+=======+==================================================+=============================+============================================+
   | .. attribute:: pong                     |   1   | ACK a ``Ping``                                   | ACK a Ping to Discord       |                     ~                      |
   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+
   | .. attribute:: msg_with_source          |   4   | respond to an interaction with a message         | :class:`Interaction.respond`| .. toggle-header::                         |
   |                                         |       |                                                  |                             |    :header: **Click to view example**      |
   |                                         |       |                                                  |                             |                                            |
   |                                         |       |                                                  |                             |    .. image:: /imgs/ict4example.gif        |
   |                                         |       |                                                  |                             |       :alt: Example for msg_with_source    |
   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+
   |                                         |       |                                                  |                             | .. toggle-header::                         |
   | .. attribute:: deferred_msg_with_source |   5   | ACK an interaction and edit a response later,    | Possible                    |    :header: **Click to view example**      |
   |                                         |       | the user sees a loading state                    | :attr:`response_type`       |                                            |
   |                                         |       |                                                  | for _defer                  |    .. image:: /imgs/ict5example.gif        |
   |                                         |       |                                                  |                             |       :alt: Example for                    |
   |                                         |       |                                                  |                             |             deferred_msg_with_source       |
   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+
   | .. attribute:: deferred_update_msg      |   6   | for components, ACK an interaction and edit      | Possible                    | .. toggle-header::                         |
   |                                         |       | the original message later;                      | :attr:`response_type`       |    :header: **Click to view example**      |
   |                                         |       | the user does not see a loading state            | for _defer                  |                                            |
   |                                         |       |                                                  |                             |    .. image:: /imgs/ict6example.gif        |
   |                                         |       |                                                  |                             |       :alt: Example for deferred_update_msg|
   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+
   | .. attribute:: update_msg               |   7   | for components,                                  | :class:`Interaction.edit`   | .. toggle-header::                         |
   |                                         |       | edit the message the component was attached to   |                             |    :header: **Click to view example**      |
   |                                         |       |                                                  |                             |                                            |
   |                                         |       |                                                  |                             |    .. image:: /imgs/ict7example.gif        |
   |                                         |       |                                                  |                             |       :alt: Example for update_msg         |
   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+

.. class:: Locale

    Valid locals that are used at different places in the discord api.

    .. note::
        Usually you can use the lowercase ``Language Name`` (spaces replaced with underscores) as a valid locale too.

    ==================== ==========================  =====================
    Locale               Language Name               Native Name
    ==================== ==========================  =====================
    .. attribute:: da    Danish                        Dansk
    .. attribute:: de    German                        Deutsch
    .. attribute:: en_GB English, UK                   English, UK
    .. attribute:: en_US English, US                   English, US
    .. attribute:: es_ES Spanish                       Español
    .. attribute:: fr    French                        Français
    .. attribute:: hr    Croatian                      Hrvatski
    .. attribute:: it    Italian                       Italiano
    .. attribute:: lt    Lithuanian                    Lietuviškai
    .. attribute:: hu    Hungarian                     Magyar
    .. attribute:: nl    Dutch                         Nederlands
    .. attribute:: no    Norwegian                     Norsk
    .. attribute:: pl    Polish                        Polski
    .. attribute:: pt_BR Portuguese/Brazilian          Português do Brasil
    .. attribute:: ro    Romanian, Romania             Română
    .. attribute:: fi    Finnish                       Suomi
    .. attribute:: sv_SE Swedish                       Svenska
    .. attribute:: vi    Vietnamese                    Tiếng Việt
    .. attribute:: tr    Turkish                       Türkçe
    .. attribute:: cs    Czech                         Čeština
    .. attribute:: el    Greek                         Ελληνικά
    .. attribute:: bg    Bulgarian                     български
    .. attribute:: ru    Russian                       Pусский
    .. attribute:: uk    Ukrainian                     Українська
    .. attribute:: hi    Hindi                         हिन्दी
    .. attribute:: th    Thai                          ไทย
    .. attribute:: zh_CN Chinese, China                中文
    .. attribute:: ja    Japanese                      日本語
    .. attribute:: zh_TW Chinese, Taiwan               繁體中文
    .. attribute:: ko    Korean                        한국어
    ==================== ==========================  =====================

.. class:: ActivityType

    Specifies the type of :class:`Activity`. This is used to check how to
    interpret the activity itself.

    .. attribute:: unknown

        An unknown activity type. This should generally not happen.
    .. attribute:: playing

        A "Playing" activity type.
    .. attribute:: streaming

        A "Streaming" activity type.
    .. attribute:: listening

        A "Listening" activity type.
    .. attribute:: watching

        A "Watching" activity type.
    .. attribute:: custom

        A custom activity type.
    .. attribute:: competing

        A competing activity type.

        .. versionadded:: 1.5

.. class:: HypeSquadHouse

    Specifies the HypeSquad house a user belongs to.

    .. attribute:: bravery

        The "Bravery" house.
    .. attribute:: brilliance

        The "Brilliance" house.
    .. attribute:: balance

        The "Balance" house.

.. class:: VoiceRegion

    Specifies the region a voice server belongs to.

    .. note::
        If you wan\'t to fetch all currently available voice regions, consider using :meth:`Client.fetch_voice_regions`.

    .. attribute:: amsterdam

        The Amsterdam region.
    .. attribute:: brazil

        The Brazil region.
    .. attribute:: dubai

        The Dubai region.

        .. versionadded:: 1.3

    .. attribute:: eu_central

        The EU Central region.
    .. attribute:: eu_west

        The EU West region.
    .. attribute:: europe

        The Europe region.

        .. versionadded:: 1.3

    .. attribute:: frankfurt

        The Frankfurt region.
    .. attribute:: hongkong

        The Hong Kong region.
    .. attribute:: india

        The India region.

        .. versionadded:: 1.2

    .. attribute:: japan

        The Japan region.
    .. attribute:: london

        The London region.
    .. attribute:: russia

        The Russia region.
    .. attribute:: singapore

        The Singapore region.
    .. attribute:: southafrica

        The South Africa region.
    .. attribute:: south_korea

        The South Korea region.
    .. attribute:: sydney

        The Sydney region.
    .. attribute:: us_central

        The US Central region.
    .. attribute:: us_east

        The US East region.
    .. attribute:: us_south

        The US South region.
    .. attribute:: us_west

        The US West region.
    .. attribute:: vip_amsterdam

        The Amsterdam region for VIP guilds.
    .. attribute:: vip_us_east

        The US East region for VIP guilds.
    .. attribute:: vip_us_west

        The US West region for VIP guilds.

.. class:: VideoQualityMode

    Specifies the camera video quality for all channel participants in a :class:`VoiceChannel` / :class:`StageChannel`.

    .. attribute:: auto
         Automatic set per-user for optimal performance.

    .. attribute:: full

        The quality is enforced to 720p for all participants.

    .. attribute:: 720p
        An aliase to :attr:`.full`


.. class:: VerificationLevel

    Specifies a :class:`Guild`\'s verification level, which is the criteria in
    which a member must meet before being able to send messages to the guild.

    .. container:: operations

        .. describe:: x == y

            Checks if two verification levels are equal.
        .. describe:: x != y

            Checks if two verification levels are not equal.
        .. describe:: x > y

            Checks if a verification level is higher than another.
        .. describe:: x < y

            Checks if a verification level is lower than another.
        .. describe:: x >= y

            Checks if a verification level is higher or equal to another.
        .. describe:: x <= y

            Checks if a verification level is lower or equal to another.

    .. attribute:: none

        No criteria set.
    .. attribute:: low

        Member must have a verified email on their Discord account.
    .. attribute:: medium

        Member must have a verified email and be registered on Discord for more
        than five minutes.
    .. attribute:: high

        Member must have a verified email, be registered on Discord for more
        than five minutes, and be a member of the guild itself for more than
        ten minutes.
    .. attribute:: table_flip

        An alias for :attr:`high`.
    .. attribute:: extreme

        Member must have a verified phone on their Discord account.

    .. attribute:: double_table_flip

        An alias for :attr:`extreme`.

    .. attribute:: very_high

        An alias for :attr:`extreme`.

        .. versionadded:: 1.4

.. class:: NotificationLevel

    Specifies whether a :class:`Guild` has notifications on for all messages or mentions only by default.

    .. attribute:: all_messages

        Members receive notifications for every message regardless of them being mentioned.
    .. attribute:: only_mentions

        Members receive notifications for messages they are mentioned in.

.. class:: ContentFilter

    Specifies a :class:`Guild`\'s explicit content filter, which is the machine
    learning algorithms that Discord uses to detect if an image contains
    pornography or otherwise explicit content.

    .. container:: operations

        .. describe:: x == y

            Checks if two content filter levels are equal.
        .. describe:: x != y

            Checks if two content filter levels are not equal.
        .. describe:: x > y

            Checks if a content filter level is higher than another.
        .. describe:: x < y

            Checks if a content filter level is lower than another.
        .. describe:: x >= y

            Checks if a content filter level is higher or equal to another.
        .. describe:: x <= y

            Checks if a content filter level is lower or equal to another.

    .. attribute:: disabled

        The guild does not have the content filter enabled.
    .. attribute:: no_role

        The guild has the content filter enabled for members without a role.
    .. attribute:: all_members

        The guild has the content filter enabled for every member.

.. class:: Status

    Specifies a :class:`Member` 's status.

    .. attribute:: online

        The member is online.
    .. attribute:: offline

        The member is offline.
    .. attribute:: idle

        The member is idle.
    .. attribute:: dnd

        The member is "Do Not Disturb".
    .. attribute:: do_not_disturb

        An alias for :attr:`dnd`.
    .. attribute:: invisible

        The member is "invisible". In reality, this is only used in sending
        a presence a la :meth:`Client.change_presence`. When you receive a
        user's presence this will be :attr:`offline` instead.


.. class:: AuditLogAction

    Represents the type of action being done for a :class:`AuditLogEntry`\,
    which is retrievable via :meth:`Guild.audit_logs`.

    .. attribute:: guild_update

        The guild has updated. Things that trigger this include:

        - Changing the guild vanity URL
        - Changing the guild invite splash
        - Changing the guild AFK channel or timeout
        - Changing the guild voice server region
        - Changing the guild icon
        - Changing the guild moderation settings
        - Changing things related to the guild widget

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Guild`.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.afk_channel`
        - :attr:`~AuditLogDiff.system_channel`
        - :attr:`~AuditLogDiff.afk_timeout`
        - :attr:`~AuditLogDiff.default_message_notifications`
        - :attr:`~AuditLogDiff.explicit_content_filter`
        - :attr:`~AuditLogDiff.mfa_level`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.owner`
        - :attr:`~AuditLogDiff.splash`
        - :attr:`~AuditLogDiff.vanity_url_code`

    .. attribute:: channel_create

        A new channel was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        either a :class:`abc.GuildChannel` or :class:`Object` with an ID.

        A more filled out object in the :class:`Object` case can be found
        by using :attr:`~AuditLogEntry.after`.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.type`
        - :attr:`~AuditLogDiff.overwrites`

    .. attribute:: channel_update

        A channel was updated. Things that trigger this include:

        - The channel name or topic was changed
        - The channel bitrate was changed

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`abc.GuildChannel` or :class:`Object` with an ID.

        A more filled out object in the :class:`Object` case can be found
        by using :attr:`~AuditLogEntry.after` or :attr:`~AuditLogEntry.before`.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.type`
        - :attr:`~AuditLogDiff.position`
        - :attr:`~AuditLogDiff.overwrites`
        - :attr:`~AuditLogDiff.topic`
        - :attr:`~AuditLogDiff.bitrate`

    .. attribute:: channel_delete

        A channel was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        an :class:`Object` with an ID.

        A more filled out object can be found by using the
        :attr:`~AuditLogEntry.before` object.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.type`
        - :attr:`~AuditLogDiff.overwrites`

    .. attribute:: overwrite_create

        A channel permission overwrite was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`abc.GuildChannel` or :class:`Object` with an ID.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        either a :class:`Role` or :class:`Member`. If the object is not found
        then it is a :class:`Object` with an ID being filled, a name, and a
        ``type`` attribute set to either ``'role'`` or ``'member'`` to help
        dictate what type of ID it is.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.deny`
        - :attr:`~AuditLogDiff.allow`
        - :attr:`~AuditLogDiff.id`
        - :attr:`~AuditLogDiff.type`

    .. attribute:: overwrite_update

        A channel permission overwrite was changed, this is typically
        when the permission values change.

        See :attr:`overwrite_create` for more information on how the
        :attr:`~AuditLogEntry.target` and :attr:`~AuditLogEntry.extra` fields
        are set.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.deny`
        - :attr:`~AuditLogDiff.allow`
        - :attr:`~AuditLogDiff.id`
        - :attr:`~AuditLogDiff.type`

    .. attribute:: overwrite_delete

        A channel permission overwrite was deleted.

        See :attr:`overwrite_create` for more information on how the
        :attr:`~AuditLogEntry.target` and :attr:`~AuditLogEntry.extra` fields
        are set.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.deny`
        - :attr:`~AuditLogDiff.allow`
        - :attr:`~AuditLogDiff.id`
        - :attr:`~AuditLogDiff.type`

    .. attribute:: kick

        A member was kicked.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`User` who got kicked.

        When this is the action, :attr:`~AuditLogEntry.changes` is empty.

    .. attribute:: member_prune

        A member prune was triggered.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        set to ``None``.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with two attributes:

        - ``delete_members_days``: An integer specifying how far the prune was.
        - ``members_removed``: An integer specifying how many members were removed.

        When this is the action, :attr:`~AuditLogEntry.changes` is empty.

    .. attribute:: ban

        A member was banned.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`User` who got banned.

        When this is the action, :attr:`~AuditLogEntry.changes` is empty.

    .. attribute:: unban

        A member was unbanned.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`User` who got unbanned.

        When this is the action, :attr:`~AuditLogEntry.changes` is empty.

    .. attribute:: member_update

        A member has updated. This triggers in the following situations:

        - A nickname was changed
        - They were server muted or deafened (or it was undo'd)

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` who got updated.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.nick`
        - :attr:`~AuditLogDiff.mute`
        - :attr:`~AuditLogDiff.deaf`

    .. attribute:: member_role_update

        A member's role has been updated. This triggers when a member
        either gains a role or losses a role.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` who got the role.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.roles`

    .. attribute:: member_move

        A member's voice channel has been updated. This triggers when a
        member is moved to a different voice channel.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with two attributes:

        - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the members were moved.
        - ``count``: An integer specifying how many members were moved.

        .. versionadded:: 1.3

    .. attribute:: member_disconnect

        A member's voice state has changed. This triggers when a
        member is force disconnected from voice.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with one attribute:

        - ``count``: An integer specifying how many members were disconnected.

        .. versionadded:: 1.3

    .. attribute:: bot_add

        A bot was added to the guild.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` which was added to the guild.

        .. versionadded:: 1.3

    .. attribute:: role_create

        A new role was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Role` or a :class:`Object` with the ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.colour`
        - :attr:`~AuditLogDiff.mentionable`
        - :attr:`~AuditLogDiff.hoist`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.permissions`

    .. attribute:: role_update

        A role was updated. This triggers in the following situations:

        - The name has changed
        - The permissions have changed
        - The colour has changed
        - Its hoist/mentionable state has changed

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Role` or a :class:`Object` with the ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.colour`
        - :attr:`~AuditLogDiff.mentionable`
        - :attr:`~AuditLogDiff.hoist`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.permissions`

    .. attribute:: role_delete

        A role was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Role` or a :class:`Object` with the ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.colour`
        - :attr:`~AuditLogDiff.mentionable`
        - :attr:`~AuditLogDiff.hoist`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.permissions`

    .. attribute:: invite_create

        An invite was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Invite` that was created.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.max_age`
        - :attr:`~AuditLogDiff.code`
        - :attr:`~AuditLogDiff.temporary`
        - :attr:`~AuditLogDiff.inviter`
        - :attr:`~AuditLogDiff.channel`
        - :attr:`~AuditLogDiff.uses`
        - :attr:`~AuditLogDiff.max_uses`

    .. attribute:: invite_update

        An invite was updated.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Invite` that was updated.

    .. attribute:: invite_delete

        An invite was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Invite` that was deleted.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.max_age`
        - :attr:`~AuditLogDiff.code`
        - :attr:`~AuditLogDiff.temporary`
        - :attr:`~AuditLogDiff.inviter`
        - :attr:`~AuditLogDiff.channel`
        - :attr:`~AuditLogDiff.uses`
        - :attr:`~AuditLogDiff.max_uses`

    .. attribute:: webhook_create

        A webhook was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the webhook ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.channel`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.type` (always set to ``1`` if so)

    .. attribute:: webhook_update

        A webhook was updated. This trigger in the following situations:

        - The webhook name changed
        - The webhook channel changed

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the webhook ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.channel`
        - :attr:`~AuditLogDiff.name`

    .. attribute:: webhook_delete

        A webhook was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the webhook ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.channel`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.type` (always set to ``1`` if so)

    .. attribute:: emoji_create

        An emoji was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Emoji` or :class:`Object` with the emoji ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`

    .. attribute:: emoji_update

        An emoji was updated. This triggers when the name has changed.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Emoji` or :class:`Object` with the emoji ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`

    .. attribute:: emoji_delete

        An emoji was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the emoji ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`

    .. attribute:: message_delete

        A message was deleted by a moderator. Note that this
        only triggers if the message was deleted by someone other than the author.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` who had their message deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with two attributes:

        - ``count``: An integer specifying how many messages were deleted.
        - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the message got deleted.

    .. attribute:: message_bulk_delete

        Messages were bulk deleted by a moderator.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`TextChannel` or :class:`Object` with the ID of the channel that was purged.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with one attribute:

        - ``count``: An integer specifying how many messages were deleted.

        .. versionadded:: 1.3

    .. attribute:: message_pin

        A message was pinned in a channel.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` who had their message pinned.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with two attributes:

        - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the message was pinned.
        - ``message_id``: the ID of the message which was pinned.

        .. versionadded:: 1.3

    .. attribute:: message_unpin

        A message was unpinned in a channel.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` who had their message unpinned.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with two attributes:

        - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the message was unpinned.
        - ``message_id``: the ID of the message which was unpinned.

        .. versionadded:: 1.3

    .. attribute:: integration_create

        A guild integration was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the integration ID of the integration which was created.

        .. versionadded:: 1.3

    .. attribute:: integration_update

        A guild integration was updated.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the integration ID of the integration which was updated.

        .. versionadded:: 1.3

    .. attribute:: integration_delete

        A guild integration was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the integration ID of the integration which was deleted.

        .. versionadded:: 1.3


.. class:: AuditLogActionCategory

    Represents the category that the :class:`AuditLogAction` belongs to.

    This can be retrieved via :attr:`AuditLogEntry.category`.

    .. attribute:: create

        The action is the creation of something.

    .. attribute:: delete

        The action is the deletion of something.

    .. attribute:: update

        The action is the update of something.

.. class:: PremiumType

    Represents the user's Discord Nitro subscription type.

    .. deprecated:: 1.7

    .. note::

        This only applies to users, *not* bots.

    .. attribute:: nitro

        Represents the Discord Nitro with Nitro-exclusive games.

    .. attribute:: nitro_classic

        Represents the Discord Nitro with no Nitro-exclusive games.


.. class:: Theme

    Represents the theme synced across all Discord clients.

    .. deprecated:: 1.7

    .. note::

        This only applies to users, *not* bots.

    .. attribute:: light

        Represents the Light theme on Discord.

    .. attribute:: dark

        Represents the Dark theme on Discord.


.. class:: TeamMembershipState

    Represents the membership state of a team member retrieved through :func:`Bot.application_info`.

    .. versionadded:: 1.3

    .. attribute:: invited

        Represents an invited member.

    .. attribute:: accepted

        Represents a member currently in the team.

.. class:: TeamRole:

    A :class:`TeamMember` can be one of four roles (owner, admin, developer, and read-only),
    and each role inherits the access of those below it.
    Represents the role of a team member retrieved through :func:`Bot.application_info`.

    .. versionadded:: 2.0

    .. attribute:: owner

        Owners are the most permissiable role, and can take destructive, irreversible actions like deleting team-owned
        apps or the team itself. Teams are limited to 1 owner.

    .. attribute:: admin

        Admins have similar access as an :attr:`~TeamRole.owner`,
        except they cannot take destructive actions on the team or team-owned apps.

    .. attribute:: developer

        Developers can access information about team-owned apps, like the client secret or public key.
        They can also take limited actions on team-owned apps,
        like configuring interaction endpoints or resetting the bot token.
        Members with the Developer role cannot manage the team or its members,
        or take destructive actions on team-owned apps.

    .. attribute:: read_only

        Read-only members can access information about a team and any team-owned apps.
        Some examples include getting the IDs of applications and exporting payout records.

.. class:: WebhookType

    Represents the type of webhook that can be received.

    .. versionadded:: 1.3

    .. attribute:: incoming

        Represents a webhook that can post messages to channels with a token.

    .. attribute:: channel_follower

        Represents a webhook that is internally managed by Discord, used for following channels.

.. class:: TimestampStyle

    The Styles you could use for the :attr:`style` of a :meth:`discord.utils.styled_timestamp`

    See also in the `Discord-Documentation <https://discord.com/developers/docs/reference#message-formatting-timestamp-styles>`_

    +----------------------------------+-------+-----------------+---------------------------------+
    | NAME                             | VALUE | DESCRIPTION     | EXAMPLE                         |
    +==================================+=======+=================+=================================+
    | .. attribute:: short_time        |  't'  | Short Time      | .. image:: /imgs/short_time.png |
    +----------------------------------+-------+-----------------+---------------------------------+
    | .. attribute:: long_time         |  'T'  | Long Time       | .. image:: /imgs/long_time.png  |
    +----------------------------------+-------+-----------------+---------------------------------+
    | .. attribute:: short_date        |  'd'  | Short Date      | .. image:: /imgs/short_date.png |
    +----------------------------------+-------+-----------------+---------------------------------+
    | .. attribute:: long_date         |  'D'  | Long Date       | .. image:: /imgs/long_date.png  |
    +----------------------------------+-------+-----------------+---------------------------------+
    | .. attribute:: short             |  'f'  | Short Date/Time | .. image:: /imgs/short.png      |
    +----------------------------------+-------+-----------------+---------------------------------+
    | .. attribute:: long              |  'F'  | Long Date/Time  | .. image:: /imgs/long.png       |
    +----------------------------------+-------+-----------------+---------------------------------+
    | .. attribute:: relative          |  'R'  | Relative Time   | .. image:: /imgs/relative.png   |
    +----------------------------------+-------+-----------------+---------------------------------+

.. class:: ExpireBehaviour

    Represents the behaviour the :class:`Integration` should perform
    when a user's subscription has finished.

    There is an alias for this called ``ExpireBehavior``.

    .. versionadded:: 1.4

    .. attribute:: remove_role

        This will remove the :attr:`Integration.role` from the user
        when their subscription is finished.

    .. attribute:: kick

        This will kick the user when their subscription is finished.

.. class:: DefaultAvatar

    Represents the default avatar of a Discord :class:`User`

    .. attribute:: blurple

        Represents the default avatar with the color blurple.
        See also :attr:`Colour.blurple`
    .. attribute:: grey

        Represents the default avatar with the color grey.
        See also :attr:`Colour.greyple`
    .. attribute:: gray

        An alias for :attr:`grey`.
    .. attribute:: green

        Represents the default avatar with the color green.
        See also :attr:`Colour.green`
    .. attribute:: orange

        Represents the default avatar with the color orange.
        See also :attr:`Colour.orange`
    .. attribute:: red

        Represents the default avatar with the color red.
        See also :attr:`Colour.red`
    .. attribute:: pink

        Represents the default avatar with the color pink.


.. class:: StickerType

    Represents the type of sticker images.

    .. versionadded:: 1.6

    .. attribute:: png

        Represents a sticker with a png image.

    .. attribute:: apng

        Represents a sticker with an apng image.

    .. attribute:: lottie

        Represents a sticker with a lottie image.

    .. attribute:: gif

        Represents a sticker with a gif image.


.. class:: EventEntityType

    The location where a :class:`GuildScheduledEvent` will be scheduled at

    .. attribute:: stage

        The event wil be in a stage channel

    .. attribute:: voice

        The event wil be in a voice channel

    .. attribute:: external

        The event wil be outside of discord, like on a website or in the real world

.. class:: EventStatus

    The status of a :class:`GuildScheduledEvent`

    .. attribute:: scheduled

        The event hasn't startet yet

    .. attribute:: active

        The event is currently active

    .. attribute:: completed

        The event is over

    .. attribute:: canceled

        The scheduled event was canceled

    .. note::

        \* Once :attr:`~GuildScheduledEvent.status` is set to ``completed`` or ``canceled``, the ``status`` can no longer be updated

    Valid Guild Scheduled Event Status Transitions

        - ``scheduled`` --> ``active``

        - ``active`` --------> ``completed``

        - ``scheduled`` --> ``canceled``


.. class:: AutoModEventType

    Indicates in what event context a :class:`AutoModRule` should be checked.

    .. attribute:: message_send

        When a member sends or edits a message (in the guild the rule belongs to)

.. class:: AutoModKeywordPresetType

    .. attribute:: profanity

        Words that may be considered forms of swearing or cursing

    .. attribute:: sexual_content

        Words that refer to sexually explicit behavior or activity

    .. attribute:: slurs

        Personal insults or words that may be considered hate speech

.. class:: AutoModTriggerType

    Characterizes the type of content which can trigger the rule.

    .. attribute:: keyword

        Check if content contains words from a user defined list of keywords

    .. attribute:: spam

        Check if content represents generic spam

    .. attribute:: keyword_preset

        Check if content contains words from internal pre-defined wordsets

.. class:: AutoModActionType

    The type of action that should be taken in an :class:`AutoModAction`.

    .. attribute:: block_message

        Blocks the content of a message according to the rule

    .. attribute:: send_alert_message

        Logs user content to a specified channel

    .. attribute:: timeout_user

        Timeout the user for a specific duration

        .. note::

            This can only be used when the :attr:`~AutoModRule.trigger_type` is ``keyword``

.. class:: TextInputStyle

    The style a :class:`TextInput` should have

    .. attribute:: short

        A single-line input

    .. attribute:: singleline

        An aliase for :attr:`~TextInputStyle.short`

    .. attribute:: paragraph

        A multi-line input

    .. attribute:: multiline

        An aliase for :attr:`~TextInputStyle.paragraph`

.. class:: OptionType

    Option types for :class:`SlashCommandOption`

    .. attribute:: sub_command

        A sub command. Internal use only.

    .. attribute:: sub_command_group

        A sub command group. Internal use only.

    .. attribute:: string

        A string (:class:`str`)

    .. attribute:: integer

       	Any integer between -2^53 and 2^53 (:class:`int`)

    .. attribute:: boolean

        A boolean (:class:`bool`)

    .. attribute:: user

        A user/member (:class:`~discord.User`/:class:`Member`)

    .. attribute:: channel

        Includes all channel types + categories

        .. note::

            To only accept specific channel types use :attr:`SlashCommandOption.channel_types`

    .. attribute:: role

        A role (:class:`Role`)

    .. attribute:: mentionable

        Includes user and roles (:class:`~discord.User`/:class:`Member` & :class:`Role`)

    .. attribute:: number

        Any double between -2^53 and 2^53 (:class:`float`)

    .. attribute:: attachment

        An :class:`Attachment`

.. class:: PostSortOrder

    Type used to order posts in :class:`ForumChannel` channels.

    .. attribute:: latest_activity

        Sort forum posts by activity

    .. attribute:: creation_date

        Sort forum posts by creation time (from most recent to oldest)

.. class:: ForumLayout

    Type used to display posts in `ForumChannel` channels.

    .. attribute:: not_set

        No default has been set for forum channel

    .. attribute:: list_view

        Display posts as a list

    .. attribute:: gallery_view

        Display posts as a collection of tiles (grid)

.. class:: OnboardingMode

    Defines the criteria used to satisfy Onboarding constraints that are required for enabling.

    .. attribute:: default

        Counts only Default Channels towards constraints

    .. attribute:: advanced

        Counts Default Channels and Questions towards constraints

.. class:: OnboardingPromptType

        Defines the way a prompts' options are displayed.

        .. attribute:: multiple_choice

            The options are displayed as a grid of buttons

        .. attribute:: dropdown

            The options are displayed in a dropdown menu


.. class:: SKUType

    Represents the type of a :class:`SKU`.

    .. attribute:: application
        An application SKU

    .. attribute:: durable

        Durable one-time purchase

    .. attribute:: consumable

        Consumable one-time purchase

    .. attribute:: bundle

        A bundle SKU

    .. attribute:: subscription

        Represents a recurring subscription

    .. attribute:: subscription_group

        System-generated group for each :attr:`.subscription` SKU created


.. class:: EntitlementType

    Represents the type of a :class:`Entitlement`.

    .. attribute:: purchase

        Entitlement was purchased by user

    .. attribute:: premium_subscription

        Entitlement for Discord Nitro subscription

    .. attribute:: developer_gift

        Entitlement was gifted by developer

    .. attribute:: test_mode_purchase

        Entitlement was purchased by a developer in application test mode

    .. attribute:: free_purchase

        Entitlement was granted when the SKU was free

    .. attribute:: user_gift

        Entitlement was gifted by another user

    .. attribute:: premium_purchase

        Entitlement was claimed by user for free as a Nitro Subscriber

    .. attribute:: application_subscription

        Entitlement was purchased as an app subscription
