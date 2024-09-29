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

import types
from collections import namedtuple
from typing import Union, List, Tuple, Any, Type

__all__ = (
    'Enum',
    'ChannelType',
    'PrivacyLevel',
    'EventEntityType',
    'EventStatus',
    'ApplicationCommandType',
    'AppCommandPermissionType',
    'ComponentType',
    'SelectDefaultValueType',
    'ButtonColor',
    'ButtonStyle',
    'PermissionType',
    'IntegrationType',
    'InteractionType',
    'InteractionCallbackType',
    'AppIntegrationType',
    'InteractionContextType',
    'EntryPointHandlerType',
    'OptionType',
    'TimestampStyle',
    'Locale',
    'InviteTargetType',
    'AutoArchiveDuration',
    'MessageType',
    'ReactionType',
    'VoiceRegion',
    'VideoQualityMode',
    'SpeakingState',
    'VerificationLevel',
    'ContentFilter',
    'Status',
    'DefaultAvatar',
    'AuditLogAction',
    'AuditLogActionCategory',
    'UserFlags',
    'ActivityType',
    'HypeSquadHouse',
    'NotificationLevel',
    'PremiumType',
    'FriendFlags',
    'TeamMembershipState',
    'TeamRole',
    'TextInputStyle',
    'Theme',
    'WebhookType',
    'ExpireBehaviour',
    'ExpireBehavior',
    'StickerType',
    'AutoModActionType',
    'AutoModEventType',
    'AutoModTriggerType',
    'AutoModKeywordPresetType',
    'PostSortOrder',
    'ForumLayout',
    'OnboardingMode',
    'OnboardingPromptType',
    'SKUType',
    'EntitlementType',
)


def _create_value_cls(name) -> Type[tuple]:
    cls = namedtuple(f'_EnumValue_{name}', 'name value')
    cls.__repr__ = lambda self: '<%s.%s: %r>' % (name, self.name, self.value)
    cls.__str__ = lambda self: f'{name}.{self.name}'

    def __getattribute__(self, n) -> Union[bool, Any]:
        # With this you can use something like some_channel.type.text to check if it is of this type
        # It is similar to "some_channel.type == ChannelType.text"
        if n in dir(cls):
            return super(cls, self).__getattribute__(n)
        else:
            if n in self._actual_enum_cls_.__members__:
                return self.name == n
            raise AttributeError(f'{self.__class__.__name__} has no attribute {n}.')

    cls.__getattribute__ = __getattribute__
    return cls


def _is_descriptor(obj):
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')


class EnumMeta(type):
    def __new__(mcs, name, bases, attrs):
        value_mapping = {}
        member_mapping = {}
        member_names = []

        value_cls = _create_value_cls(name)
        for key, value in list(attrs.items()):
            is_descriptor = _is_descriptor(value)
            if key[0] == '_' and not is_descriptor:
                continue

            # Special case classmethod to just pass through
            if isinstance(value, classmethod):
                continue

            if is_descriptor:
                setattr(value_cls, key, value)
                del attrs[key]
                continue

            try:
                new_value = value_mapping[value]
            except KeyError:
                new_value = value_cls(name=key, value=value)  # type: ignore
                value_mapping[value] = new_value
                member_names.append(key)

            member_mapping[key] = new_value
            attrs[key] = new_value

        attrs['_enum_value_map_'] = value_mapping
        attrs['_enum_member_map_'] = member_mapping
        attrs['_enum_member_names_'] = member_names
        actual_cls = super().__new__(mcs, name, bases, attrs)
        value_cls._actual_enum_cls_ = actual_cls
        return actual_cls

    def __iter__(cls):
        return (cls._enum_member_map_[name] for name in cls._enum_member_names_)  # type: ignore

    def __reversed__(cls):
        return (cls._enum_member_map_[name] for name in reversed(cls._enum_member_names_))  # type: ignore

    def __len__(cls):
        return len(cls._enum_member_names_)  # type: ignore

    def __repr__(cls):
        return '<enum %r>' % cls.__name__

    @property
    def __members__(cls):
        return types.MappingProxyType(cls._enum_member_map_)  # type: ignore

    def __call__(cls, value):
        try:
            return cls._enum_value_map_[value]  # type: ignore
        except (KeyError, TypeError):
            raise ValueError("%r is not a valid %s" % (value, cls.__name__))

    def __getitem__(cls, key):
        return cls._enum_member_map_[key]  # type: ignore

    def __setattr__(cls, name, value):
        raise TypeError('Enums are immutable.')

    def __delattr__(cls, attr):
        raise TypeError('Enums are immutable')

    def __instancecheck__(self, instance):
        # isinstance(x, Y)
        # -> __instancecheck__(Y, x)
        try:
            return instance._actual_enum_cls_ is self  # type: ignore
        except AttributeError:
            return False


class Enum(metaclass=EnumMeta):
    @classmethod
    def try_value(cls, value):
        try:
            return cls._enum_value_map_[value]  # type: ignore
        except (KeyError, TypeError):
            return value

    def __str__(self) -> str:
        return self.name

    def __int__(self) -> int:
        return self.value

    @property
    def name(self):
        return getattr(self, 'name')

    @property
    def value(self):
        return getattr(self, 'value')


class ChannelType(Enum):
    text            = 0
    private         = 1
    voice           = 2
    group           = 3
    category        = 4
    news            = 5
    news_thread     = 10
    public_thread   = 11
    private_thread  = 12
    stage_voice     = 13
    guild_directory = 14  # don't think bots can access them but yea... to have all listed here
    forum_channel   = 15

    def __str__(self):
        return getattr(self, 'name')

    def __int__(self):
        return getattr(self, 'value')

    @classmethod
    def from_type(cls, obj):
        if isinstance(obj, int):
            return cls.try_value(obj)
        return obj.channel_type() if hasattr(obj, 'channel_type') else obj


class PermissionType(Enum):
    role   = 0
    member = 1

    def __str__(self):
        return self.name

    def __int__(self):
        return self.value


class PrivacyLevel(Enum):
    public     = 1
    guild_only = 2


class EventEntityType(Enum):
    stage    = 1
    voice    = 2
    external = 3

    def __str__(self):
        return getattr(self, 'name')

    def __int__(self):
        return getattr(self, 'value')

EntityType = EventEntityType


class EventStatus(Enum):
    scheduled = 1
    active    = 2
    completed = 3
    canceled  = 4


class IntegrationType(Enum):
    TWITCH = 'twitch'
    YOUTUBE = 'youtube'
    DISCORD = 'discord'
    GUILD_SUBSCRIPTION = 'guild_subscription'


class InteractionType(Enum):
    PingAck                        = 1
    ApplicationCommand             = 2
    Component                      = 3
    ApplicationCommandAutocomplete = 4
    ModalSubmit                    = 5


class ApplicationCommandType(Enum):
    chat_input = 1
    user       = 2
    message    = 3

    def __str__(self):
        return getattr(self, 'name')

    def __int__(self):
        return getattr(self, 'value')

    def __eq__(self, other):
        return self is other or int(self) == other or str(self) == other

    @classmethod
    def from_value(cls, value):
        return try_enum(cls, value)


class AppCommandPermissionType(Enum):
    ROLE    = 1
    USER    = 2
    CHANNEL = 3


class ComponentType(Enum):
    ActionRow         = 1
    Button            = 2
    StringSelect      = 3
    TextInput         = 4
    UserSelect        = 5
    RoleSelect        = 6
    MentionableSelect = 7
    ChannelSelect     = 8

    def __str__(self):
        return getattr(self, 'name')

    def __int__(self):
        return getattr(self, 'value')

    def __eq__(self, other):
        return self is other or int(self) == other or str(self) == other


class ButtonStyle(Enum):
    """
    :class:`ButtonStyle`
    Represents the Style for a :class:`discord.Button`

    .. note ::
        For more information about the Button-Styles, visit the `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#buttons-button-styles>`_.

    """

    blurple     = 1
    Primary     = 1
    grey        = 2
    gray        = 2
    Secondary   = 2
    green       = 3
    Success     = 3
    red         = 4
    Danger      = 4
    url         = 5
    link        = 5
    grey_url    = 5
    gray_url    = 5
    Link_Button = 5
    Premium     = 6

    @classmethod
    def from_value(cls, value):
        return try_enum(cls, value)

    # the same as in the class above.
    def __str__(self):
        return getattr(self, 'name')

    def __int__(self):
        return getattr(self, 'value')


class ButtonColor(ButtonStyle):
    """
    :class:`ButtonColor`

    .. note ::
        This is just an Aliase to :class:`ButtonStyle`.
    """


class TextInputStyle(Enum):
    """
    :class:`TextInputStyle`

    Represents the style for a :class:`discord.TTextInput`
    """
    short       = 1
    singleline  = 1
    paragraph   = 2
    multiline   = 2

    @classmethod
    def from_value(cls, value):
        return try_enum(cls, value)

    # the same as in the class above.
    def __str__(self):
        return getattr(self, 'name')

    def __int__(self):
        return getattr(self, 'value')


class SelectDefaultValueType(Enum):
    user = 'user'
    role = 'role'
    channel = 'channel'

    def __str__(self):
        return self.value

    @classmethod
    def from_type(cls, t):
        class_name = t.__class__.__name__
        if class_name == 'Role':
            return cls.role
        elif 'User' in class_name or 'Member' in class_name:  # To support user objects like from the oauth2 module
            return cls.user
        else:
            return cls.channel


class InteractionCallbackType(Enum):
    pong                     = 1
    msg_with_source          = 4
    deferred_msg_with_source = 5
    deferred_update_msg      = 6
    update_msg               = 7
    autocomplete_callback    = 8
    modal                    = 9
    premium_required         = 10


    @classmethod
    def from_value(cls, value):
        return try_enum(cls, value)

    # the same as in the class above.
    def __str__(self):
        return getattr(self, 'name')

    def __int__(self):
        return getattr(self, 'value')


class OptionType(Enum):
    sub_command       = 1
    sub_command_group = 2
    string            = 3
    integer           = 4
    boolean           = 5
    user              = 6
    channel           = 7
    role              = 8
    mentionable       = 9
    number            = 10
    attachment        = 11

    def __int__(self):
        return getattr(self, 'value')

    def __str__(self):
        return getattr(self, 'name')

    @classmethod
    def from_type(cls, t) -> Tuple[OptionType, List[ChannelType]]:

        if isinstance(t, tuple):  # typing.Union has been used
            datatypes = [cls.from_type(op) for op in t if op is not type(None)]
            if all(x == cls.channel for x, _ in datatypes):
                return cls.channel, [c for _, c in datatypes]
            elif {t for t, _ in datatypes} <= {cls.role, cls.user}:
                return cls.mentionable
            else:
                raise TypeError("Invalid usage of typing.Union")

        py_3_10_union_type = hasattr(types, "UnionType") and isinstance(t, types.UnionType)

        if py_3_10_union_type or getattr(t, '__origin__', None) is Union:
            return cls.from_type(t.__args__)

        if isinstance(t, int):
            return try_enum(cls, t), None
        elif isinstance(t, str):
            return cls[t], None

        if issubclass(t, str):
            return cls.string, None
        elif issubclass(t, bool):
            return cls.boolean, None
        elif issubclass(t, int):
            return cls.integer, None
        elif issubclass(t, float):
            return cls.number, None

        t_name = t.__name__

        if t_name in {"User", "Member"}:
            return cls.user, None
        elif t_name == "Role":
            return cls.role, None

        elif t_name in {
            "GuildChannel",
            "TextChannel",
            "VoiceChannel",
            "StageChannel",
            "CategoryChannel",
            "ForumChannel",
            "ForumPost",
            "DMChannel",
        }:
            if hasattr(t, 'channel_type'):
                return cls.channel, [t.channel_type()]
            else:
                return cls.channel, None
        elif t_name == "ThreadChannel":
            return cls.channel, [ChannelType.public_thread, ChannelType.private_thread, ChannelType.news_thread]

        elif t_name == "Attachment":
            return cls.attachment, None

        raise TypeError(f"Invalid class {t!r} used as an option type. ")


class TimestampStyle(Enum):
    """
    The Style to use in :meth:`discord.utils.styled_timestamp`.

    See Also:  `The Discord-API-Documentation <https://discord.com/developers/docs/reference#message-formating-timestamp-styles>`_
    """

    short_time  = 't'
    long_time   = 'T'
    short_date  = 'd'
    long_date   = 'D'
    short       = 'f'
    long        = 'F'
    relative    = 'R'

    def __repr__(self):
        """Represents the :class:`TimestampStyle`."""
        return getattr(self, 'name')

    def __str__(self):
        return getattr(self, 'value')


    @classmethod
    def from_value(cls, value):
        return try_enum(cls, value)


class InviteTargetType(Enum):
    stream = 1
    embedded = 2
    embedded_application = 2


class VoiceActivityApplication(Enum):
    WatchTogether       = 880218394199220334
    PokerNight          = 755827207812677713
    BetrayalIO          = 773336526917861400
    FishingtonIO        = 814288819477020702
    ChessInThePark      = 832012774040141894
    SketchyArtist       = 879864070101172255
    Awkword             = 879863881349087252
    DoodleCrew          = 878067389634314250
    SketchHeads         = 902271654783242291
    LetterTile          = 879863686565621790
    WordSnacks          = 879863976006127627
    SpellCast           = 852509694341283871
    CheckersInThePark   = 832013003968348200
    CG3Prod             = CheckersInThePark
    Blazing8s           = 832025144389533716
    CG4Prod             = Blazing8s
    Ocho                = Blazing8s
    PuttParty           = 945737671223947305
    LandIO              = 903769130790969345


class Locale(Enum):
    english_US = 'en-US'
    en_US = 'en-US'
    english_GB = 'en-GB'
    en_GB = 'en-GB'
    bulgarian = 'bg'
    bg = 'bg'
    chinese_china = 'zh-CN'
    zh_CN = 'zh-CN'
    chinese_taiwan = 'zh-TW'
    zh_TW = 'zh-TW'
    croatian = 'hr'
    hr = 'hr'
    czech = 'cs'
    cs = 'cs'
    danish = 'da'
    da = 'da'
    dutch = 'nl'
    nl = 'nl'
    finnish = 'fi'
    fi = 'fi'
    french = 'fr'
    fr = 'fr'
    german = 'de'
    de = 'de'
    greek = 'el'
    el = 'el'
    hindi = 'hi'
    hi = 'hi'
    hungarian = 'hu'
    hu = 'hu'
    italian = 'it'
    it = 'it'
    japanese = 'ja'
    ja = 'ja'
    korean = 'ko'
    ko = 'ko'
    lithuanian = 'lt'
    lt = 'lt'
    norwegian = 'no'
    no = 'no'
    polish = 'pl'
    pl = 'pl'
    portuguese_brazil = 'pt-BR'
    pt_BR = 'pt-BR'
    romanian = 'ro'
    ro = 'ro'
    russian = 'ru'
    ru = 'ru'
    spanish_spain = 'es-ES'
    es_ES = 'es-ES'
    swedish = 'sv-SE'
    sv_SE = 'sv-SE'
    thai = 'th'
    th = 'th'
    turkish = 'tr'
    tr = 'tr'
    ukrainian = 'uk'
    uk = 'uk'
    vietnamese = 'vi'
    vi = 'vi'


class AutoArchiveDuration(Enum):
    one_hour    = 60
    one_day     = 1440
    three_days  = 4320
    seven_days  = 10080
    one_week    = 10080

    def __str__(self):
        return getattr(self, 'name')

    def __int__(self):
        return getattr(self, 'value')


class MessageType(Enum):
    default                                      = 0
    recipient_add                                = 1
    recipient_remove                             = 2
    call                                         = 3
    channel_name_change                          = 4
    channel_icon_change                          = 5
    pins_add                                     = 6
    new_member                                   = 7
    premium_guild_subscription                   = 8
    premium_guild_tier_1                         = 9
    premium_guild_tier_2                         = 10
    premium_guild_tier_3                         = 11
    channel_follow_add                           = 12
    guild_stream                                 = 13
    guild_discovery_disqualified                 = 14
    guild_discovery_requalified                  = 15
    guild_discovery_grace_period_initial_warning = 16
    guild_discovery_grace_period_final_warning   = 17
    thread_created                               = 18
    reply                                        = 19
    chat_input_command                           = 20
    thread_starter_message                       = 21
    guild_invite_reminder                        = 22
    context_menu_command                         = 23
    automoderation_action                        = 24
    role_subscription_purchase                   = 25
    interaction_premium_upsell                   = 26
    stage_start                                  = 27
    stage_end                                    = 28
    stage_speaker_change                         = 29
    stage_raise_hand                             = 30
    stage_topic_change                           = 31
    guild_application_premium_subscription       = 32


class ReactionType(Enum):
    normal = 0
    burst  = 1
    super  = 1


class VoiceRegion(Enum):
    us_west       = 'us-west'
    us_east       = 'us-east'
    us_south      = 'us-south'
    us_central    = 'us-central'
    eu_west       = 'eu-west'
    eu_central    = 'eu-central'
    singapore     = 'singapore'
    london        = 'london'
    sydney        = 'sydney'
    amsterdam     = 'amsterdam'
    frankfurt     = 'frankfurt'
    brazil        = 'brazil'
    hongkong      = 'hongkong'
    russia        = 'russia'
    japan         = 'japan'
    southafrica   = 'southafrica'
    south_korea   = 'south-korea'
    india         = 'india'
    europe        = 'europe'
    dubai         = 'dubai'
    vip_us_east   = 'vip-us-east'
    vip_us_west   = 'vip-us-west'
    vip_amsterdam = 'vip-amsterdam'

    def __str__(self):
        return self.value


class VideoQualityMode(Enum):
    auto     = 1
    full     = 2

    def __str__(self):
        return self.name

    def __int__(self):
        return self.value


class SpeakingState(Enum):
    none       = 0
    voice      = 1
    soundshare = 2
    priority   = 4

    def __str__(self):
        return self.name

    def __int__(self):
        return self.value


class VerificationLevel(Enum):
    none              = 0
    low               = 1
    medium            = 2
    high              = 3
    table_flip        = 3
    extreme           = 4
    double_table_flip = 4
    very_high         = 4

    def __str__(self):
        return self.name


class ContentFilter(Enum):
    disabled    = 0
    no_role     = 1
    all_members = 2

    def __str__(self):
        return self.name


class FriendFlags(Enum):
    noone = 0
    mutual_guilds = 1
    mutual_friends = 2
    guild_and_friends = 3
    everyone = 4


class Theme(Enum):
    light = 'light'
    dark = 'dark'


class Status(Enum):
    online = 'online'
    offline = 'offline'
    idle = 'idle'
    dnd = 'dnd'
    do_not_disturb = 'dnd'
    invisible = 'invisible'

    def __str__(self):
        return self.value


class DefaultAvatar(Enum):
    blurple = 0
    grey    = 1
    gray    = 1
    green   = 2
    orange  = 3
    red     = 4
    pink    = 5

    def __str__(self):
        return self.name


class NotificationLevel(Enum):
    all_messages  = 0
    only_mentions = 1


class AuditLogActionCategory(Enum):
    create = 1
    delete = 2
    update = 3


class AuditLogAction(Enum):
    guild_update                            = 1
    channel_create                          = 10
    channel_update                          = 11
    channel_delete                          = 12
    overwrite_create                        = 13
    overwrite_update                        = 14
    overwrite_delete                        = 15
    kick                                    = 20
    member_prune                            = 21
    ban                                     = 22
    unban                                   = 23
    member_update                           = 24
    member_role_update                      = 25
    member_move                             = 26
    member_disconnect                       = 27
    bot_add                                 = 28
    role_create                             = 30
    role_update                             = 31
    role_delete                             = 32
    invite_create                           = 40
    invite_update                           = 41
    invite_delete                           = 42
    webhook_create                          = 50
    webhook_update                          = 51
    webhook_delete                          = 52
    emoji_create                            = 60
    emoji_update                            = 61
    emoji_delete                            = 62
    message_delete                          = 72
    message_bulk_delete                     = 73
    message_pin                             = 74
    message_unpin                           = 75
    integration_create                      = 80
    integration_update                      = 81
    integration_delete                      = 82
    stage_instance_create                   = 83
    stage_instance_update                   = 84
    stage_instance_delete                   = 85
    sticker_create                          = 90
    sticker_update                          = 91
    sticker_delete                          = 92
    scheduled_event_create                  = 100
    scheduled_event_update                  = 101
    scheduled_event_delete                  = 102
    thread_create                           = 110
    thread_update                           = 111
    thread_delete                           = 112
    application_command_permission_update   = 121
    soundboard_sound_create                 = 130  # or is it general expression create?
    soundboard_sound_update                 = 131
    soundboard_sound_delete                 = 132
    auto_moderation_rule_create             = 140
    auto_moderation_rule_update             = 141
    auto_moderation_rule_delete             = 142
    auto_moderation_block_message           = 143
    auto_moderation_flag_message            = 144
    auto_moderation_user_communication_disabled = 145
    onboarding_question_create              = 163
    onboarding_question_update              = 164
    onboarding_update                       = 167
    server_guide_create                     = 190
    server_guide_update                     = 191
    voice_channel_status_update             = 192
    voice_channel_status_clear              = 193

    @property
    def category(self):
        lookup = {
            AuditLogAction.guild_update:        AuditLogActionCategory.update,
            AuditLogAction.channel_create:      AuditLogActionCategory.create,
            AuditLogAction.channel_update:      AuditLogActionCategory.update,
            AuditLogAction.channel_delete:      AuditLogActionCategory.delete,
            AuditLogAction.overwrite_create:    AuditLogActionCategory.create,
            AuditLogAction.overwrite_update:    AuditLogActionCategory.update,
            AuditLogAction.overwrite_delete:    AuditLogActionCategory.delete,
            AuditLogAction.kick:                None,
            AuditLogAction.member_prune:        None,
            AuditLogAction.ban:                 None,
            AuditLogAction.unban:               None,
            AuditLogAction.member_update:       AuditLogActionCategory.update,
            AuditLogAction.member_role_update:  AuditLogActionCategory.update,
            AuditLogAction.member_move:         None,
            AuditLogAction.member_disconnect:   None,
            AuditLogAction.bot_add:             None,
            AuditLogAction.role_create:         AuditLogActionCategory.create,
            AuditLogAction.role_update:         AuditLogActionCategory.update,
            AuditLogAction.role_delete:         AuditLogActionCategory.delete,
            AuditLogAction.invite_create:       AuditLogActionCategory.create,
            AuditLogAction.invite_update:       AuditLogActionCategory.update,
            AuditLogAction.invite_delete:       AuditLogActionCategory.delete,
            AuditLogAction.webhook_create:      AuditLogActionCategory.create,
            AuditLogAction.webhook_update:      AuditLogActionCategory.update,
            AuditLogAction.webhook_delete:      AuditLogActionCategory.delete,
            AuditLogAction.emoji_create:        AuditLogActionCategory.create,
            AuditLogAction.emoji_update:        AuditLogActionCategory.update,
            AuditLogAction.emoji_delete:        AuditLogActionCategory.delete,
            AuditLogAction.message_delete:      AuditLogActionCategory.delete,
            AuditLogAction.message_bulk_delete: AuditLogActionCategory.delete,
            AuditLogAction.message_pin:         None,
            AuditLogAction.message_unpin:       None,
            AuditLogAction.integration_create:  AuditLogActionCategory.create,
            AuditLogAction.integration_update:  AuditLogActionCategory.update,
            AuditLogAction.integration_delete:  AuditLogActionCategory.delete,
            AuditLogAction.stage_instance_create: AuditLogActionCategory.create,
            AuditLogAction.stage_instance_update: AuditLogActionCategory.update,
            AuditLogAction.stage_instance_delete: AuditLogActionCategory.delete,
            AuditLogAction.sticker_create:      AuditLogActionCategory.create,
            AuditLogAction.sticker_update:      AuditLogActionCategory.update,
            AuditLogAction.sticker_delete:      AuditLogActionCategory.delete,
            AuditLogAction.scheduled_event_create: AuditLogActionCategory.create,
            AuditLogAction.scheduled_event_update: AuditLogActionCategory.update,
            AuditLogAction.scheduled_event_delete: AuditLogActionCategory.delete,
            AuditLogAction.thread_create:           AuditLogActionCategory.create,
            AuditLogAction.thread_update:           AuditLogActionCategory.update,
            AuditLogAction.thread_delete:           AuditLogActionCategory.delete,
            AuditLogAction.application_command_permission_update: AuditLogActionCategory.update,
            AuditLogAction.soundboard_sound_create: AuditLogActionCategory.create,
            AuditLogAction.soundboard_sound_update: AuditLogActionCategory.update,
            AuditLogAction.soundboard_sound_delete: AuditLogActionCategory.delete,
            AuditLogAction.auto_moderation_rule_create: AuditLogActionCategory.create,
            AuditLogAction.auto_moderation_rule_update: AuditLogActionCategory.update,
            AuditLogAction.auto_moderation_rule_delete: AuditLogActionCategory.delete,
            AuditLogAction.auto_moderation_block_message: None,
            AuditLogAction.auto_moderation_flag_message: None,
            AuditLogAction.auto_moderation_user_communication_disabled: None,
            AuditLogAction.onboarding_question_create: AuditLogActionCategory.create,
            AuditLogAction.onboarding_question_update: AuditLogActionCategory.update,
            AuditLogAction.onboarding_update: AuditLogActionCategory.update,
            AuditLogAction.server_guide_create: AuditLogActionCategory.create,
            AuditLogAction.server_guide_update: AuditLogActionCategory.update,
            AuditLogAction.voice_channel_status_update: AuditLogActionCategory.update,
            AuditLogAction.voice_channel_status_clear: AuditLogActionCategory.delete,
        }
        return lookup[self]

    @property
    def target_type(self):
        v = self.value
        if v == -1:
            return 'all'
        elif v < 10:
            return 'guild'
        elif v < 20:
            return 'channel'
        elif v < 30:
            return 'user'
        elif v < 40:
            return 'role'
        elif v < 50:
            return 'invite'
        elif v < 60:
            return 'webhook'
        elif v < 70:
            return 'emoji'
        elif v < 80:
            return 'message'
        elif v < 83:
            return 'integration'
        elif v < 90:
            return 'stage'
        elif v < 100:
            return 'sticker'
        elif v < 110:
            return 'scheduled_event'
        elif v < 121:
            return 'thread'
        elif v < 130:
            return 'application_command'
        elif v < 133:
            return 'soundboard_sound'
        elif v < 143:
            return 'auto_moderation_rule'
        elif v < 146:
            return 'auto_moderation_action'
        elif v < 165:
            return 'onboarding_question'
        elif v < 168:
            return 'onboarding'
        elif 189 < v < 192:
            return 'server_guide'
        elif v < 194:
            return 'voice_channel_status'



class UserFlags(Enum):
    staff = 1
    partner = 2
    hypesquad = 4
    bug_hunter = 8
    mfa_sms = 16
    premium_promo_dismissed = 32
    hypesquad_bravery = 64
    hypesquad_brilliance = 128
    hypesquad_balance = 256
    early_supporter = 512
    team_user = 1024
    system = 4096
    has_unread_urgent_messages = 8192
    bug_hunter_level_2 = 16384
    verified_bot = 65536
    verified_bot_developer = 131072
    certified_moderator = 262144
    bot_http_interactions = 524288
    spammer = 1048576
    active_developer = 4194304


class ActivityType(Enum):
    unknown = -1
    playing = 0
    streaming = 1
    listening = 2
    watching = 3
    custom = 4
    competing = 5

    def __int__(self):
        return self.value


class HypeSquadHouse(Enum):
    bravery = 1
    brilliance = 2
    balance = 3


class PremiumType(Enum):
    none = 0
    nitro_classic = 1
    nitro = 2
    nitro_basic = 3


class TeamMembershipState(Enum):
    invited = 1
    accepted = 2


class TeamRole(Enum):
    owner = 'owner'
    admin = 'admin'
    developer = 'developer'
    read_only = 'read_only'


class WebhookType(Enum):
    incoming = 1
    channel_follower = 2
    application = 3


class ExpireBehaviour(Enum):
    remove_role = 0
    kick = 1

ExpireBehavior = ExpireBehaviour


class StickerType(Enum):
    png     = 1
    apng    = 2
    lottie  = 3
    gif     = 4

    def __str__(self):
        return getattr(self, 'name', None)


class AutoModEventType(Enum):
    message_send  = 1
    member_update = 2


class AutoModKeywordPresetType(Enum):
    profanity       = 1
    sexual_content  = 2
    slurs           = 3


class AutoModTriggerType(Enum):
    keyword         = 1
    spam            = 3
    keyword_preset  = 4
    mention_spam    = 5
    member_profile  = 6


class AutoModActionType(Enum):
    block_message            = 1
    send_alert_message       = 2
    timeout_user             = 3
    block_member_interaction = 4


class PostSortOrder(Enum):
    latest_activity = 0
    creation_date   = 1


class ForumLayout(Enum):
    not_set       = 0
    classic       = 1
    list          = 1
    list_view     = 1
    grid          = 2
    grid_view     = 2
    gallery       = 2
    gallery_view  = 2


class OnboardingMode(Enum):
    default  = 0
    advanced = 1


class OnboardingPromptType(Enum):
    multiple_choice = 0
    dropdown        = 1


class SKUType(Enum):
    application         = 1
    durable             = 2
    consumable          = 3
    bundle              = 4
    subscription        = 5
    subscription_group  = 6


class EntitlementType(Enum):
    purchase                    = 1
    premium_subscription        = 2
    developer_gift              = 3  # not a feature yet
    test_mode_purchase          = 4
    free_purchase               = 5
    user_gift                   = 6
    premium_purchase            = 7
    application_subscription    = 8


class AppIntegrationType(Enum):
    guild_install = 0
    user_install  = 1


class InteractionContextType(Enum):
    guild           = 1
    bot_dm          = 2
    private_channel = 3
    user_dm         = 3
    group_dm        = 3


class EntryPointHandlerType(Enum):
    app_handler             = 1
    self                    = 1
    discord_launch_activity = 2
    discord                 = 2


def try_enum(cls: Type[Enum], val: Any):
    """A function that tries to turn the value into enum ``cls``.

    If it fails it returns the value instead.
    """

    # I use :meth:`getattr` so `codacy` don't cry and *my own* code is as clean as possible.
    try:
        return getattr(cls, '_enum_value_map_')[val]
    except (KeyError, TypeError, AttributeError):
        return val
