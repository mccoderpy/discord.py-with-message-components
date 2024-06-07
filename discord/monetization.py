#  The MIT License (MIT)
#
#  Copyright (c) 2015-2021 Rapptz & (c) 2021-present mccoderpy
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

#  The MIT License (MIT)
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#
from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from datetime import datetime

from .types import monetization as m

from . import utils
from .enums import SKUType, try_enum
from .flags import SKUFlags

if TYPE_CHECKING:
    from .state import ConnectionState

__all__ = (
    'SKU',
    'Entitlement',
)


# App Subscriptions
class SKU:
    """
    SKUs (stock-keeping units) in Discord represent premium offerings
    that can be made available to your application's users or guilds.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the SKU
    type: :class:`SKUType`
        The type of the SKU
    application_id: :class:`int`
        The ID of the application this SKU belongs to
    name: :class:`str`
        Customer-facing name of the SKU
    slug: :class:`str`
        Discord-generated URL slug based on the :attr:`~discord.SKU.name`
    flags: :class:`SKUFlags`
        Flags of the SKU, see :class:`~discord.SKUFlags` for more info.

        .. note::
            This can be used to differentiate between a user and a server subscription.
    """
    __slots__ = ('id', 'type', 'application_id', 'name', 'slug', 'flags',)

    def __init__(self, data: m.SKU) -> None:
        self.id: int = int(data['id'])
        self.type: SKUType = try_enum(SKUType, data['type'])
        self.application_id: int = int(data['application_id'])
        self.name: str = data['name']
        self.slug: str = data['slug']
        self.flags: SKUFlags = SKUFlags._from_value(data['flags'])


class Entitlement:
    """
    Entitlements represent a user's claim to a premium offering for your application.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the entitlement
    sku_id: :class:`int`
        The ID of the :class:`SKU` this entitlement is for
    application_id: :class:`int`
        The ID of the application this entitlement belongs to
    user_id: Optional[:class:`int`]
        :attr:`~discord.SKUFlags.app_user_subscription` only: The ID of the user that is granted access to the
        entitlement's sku
    guild_id: Optional[:class:`int`]
        :attr:`~discord.SKUFlags.app_guild_subscription` only: The ID of the guild that is granted access to the
        entitlement's sku
    deleted: :class:`bool`
        Whether this entitlement was deleted
    starts_at: Optional[:class:`datetime.datetime`]
        Start date at which the entitlement is valid. ``None`` for test entitlements.
    ends_at: Optional[:class:`datetime.datetime`]
        Time at which the entitlement is no longer valid. ``None`` for test entitlements.

    """
    __slots__ = ('_state', 'id', 'sku_id', 'application_id', 'user_id', 'guild_id', 'deleted', 'starts_at', 'ends_at',)

    def __init__(self, data: m.EntitlementData, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        """ID of the entitlement"""
        self.sku_id: int = int(data['sku_id'])
        """ID of the SKU"""
        self.application_id: int = int(data['application_id'])
        """ID of the parent application"""
        self.user_id: Optional[int] = utils._get_as_snowflake(data, 'user_id')
        """	ID of the user that is granted access to the entitlement's sku | can be `None`"""
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        """ID of the guild that is granted access to the entitlement's SKU"""
        self.deleted: bool = data['deleted']
        """If the entitlement was deleted | `True` if the user has cancelled their entitlement."""
        self.starts_at: datetime = utils.parse_time(data.get('starts_at'))
        """Start date at which the entitlement is valid. `None` when using test entitlements."""
        self.ends_at: datetime = utils.parse_time(data.get('ends_at'))
        """Date at which the entitlement is no longer valid. `None` when using test entitlements."""
        self.consumed: Optional[bool] = bool(data.get("consumed", None))
        """
        For consumable items, whether or not the entitlement has been consumed.
        
        Can be `None` in certain cases.
        """

    @property
    def target(self):
        """
        Returns the target of the entitlement.

        .. note::
            This can be either a :class:`~discord.User` or a :class:`~discord.Guild` depending on the
            :attr:`~discord.SKUFlags` of the :class:`~discord.SKU` this entitlement belongs to.
        """
        if self.user_id is not None:
            return self._state.get_user(self.user_id)
        elif self.guild_id is not None:
            return self._state._get_guild(self.guild_id)

    # TODO: Add additional attributes used for gift entitlements
    # TODO: Finish documentation
