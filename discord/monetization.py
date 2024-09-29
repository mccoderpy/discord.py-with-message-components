#  The MIT License (MIT)
#
#  Copyright (c) 2021-present mccoderpy
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

from typing import Optional, Union, TYPE_CHECKING, List
from datetime import datetime

from .types import monetization as m

from . import utils
from .enums import SKUType, EntitlementType, try_enum, SubscriptionStatus
from .flags import SKUFlags

if TYPE_CHECKING:
    from .user import User
    from .guild import Guild
    from .state import ConnectionState

__all__ = (
    'SKU',
    'Entitlement',
    'Subscription',
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
    Entitlements represent that a user or guild has access to a premium offering in your application.

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
    starts_at: Optional[:class:`~datetime.datetime`]
        Start date at which the entitlement is valid. ``None`` for test entitlements.
    ends_at: Optional[:class:`~datetime.datetime`]
        Time at which the entitlement is no longer valid. ``None`` for test entitlements.
    consumed: Optional[:class:`bool`]
            :attr:`~discord.SKUType.consumable` entitlements only: Indicates whether the entitlement has been consumed

            .. seealso:: To consume an entitlement you can use either of those

                - :meth:`~discord.Entitlement.consume` from the Entitlement object directly
                - :meth:`discord.Client.consume_entitlement` by using only the ID
    """
    __slots__ = (
        '_state', '_type', 'id', 'sku_id', 'application_id', 'user_id', 'guild_id', 'deleted', 'starts_at', 'ends_at',
        'consumed',
    )

    def __init__(self, data: m.EntitlementData, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.sku_id: int = int(data['sku_id'])
        self.application_id: int = int(data['application_id'])
        self.user_id: Optional[int] = utils._get_as_snowflake(data, 'user_id')
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        self.deleted: bool = data['deleted']
        self.starts_at: datetime = utils.parse_time(data.get('starts_at'))
        self.ends_at: datetime = utils.parse_time(data.get('ends_at'))
        self.consumed: Optional[bool] = data.get('consumed')
        self._type: int = data['type']

    @property
    def type(self) -> EntitlementType:
        """:class:`~discord.EntitlementType`: The type of the entitlement"""
        return try_enum(EntitlementType, self._type)

    @property
    def target(self) -> Union[User, Guild]:
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

    async def consume(self) -> None:
        """|coro|

        For one-time purchase :attr:`~discord.SKUType.consumable` SKUs,
        marks a given entitlement for the user as consumed.
        :attr:`.consumed` will be ``False`` for this entitlement when using :meth:`~discord.Client.fetch_entitlements`.

        .. note::
            This can can also be done with just the ID using :meth:`~discord.Client.consume_entitlement`
        """
        await self._state.http.consume_entitlement(self.application_id, self.id)

    # TODO: Add additional attributes used for gift entitlements
    # TODO: Finish documentation


class Subscription:
    """
    Subscriptions in Discord represent a user making recurring payments for at least one SKU over an ongoing period.
    Successful payments grant the user access to entitlements associated with the SKU.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the subscription
    user_id: :class:`int`
        The ID of the user that is subscribed to the SKU(s)
    sku_ids: List[:class:`int`]
        List of SKU IDs the user is subscribed to
    entitlement_ids: List[:class:`int`]
        List of entitlements granted for this subscription
    current_period_start: :class:`~datetime.datetime`
        Start date of the current subscription period
    current_period_end: :class:`~datetime.datetime`
        End date of the current subscription period
    status: :class:`~discord.SubscriptionStatus`
        The status of the subscription
    canceled_at: Optional[:class:`~datetime.datetime`]
        Time at which the subscription was canceled
    country_code: Optional[:class:`str`]
        The country code of the user.

        ISO3166-1 alpha-2 country code of the payment source used to purchase the subscription.
        Missing unless queried with a private OAuth scope.
    """

    def __init__(self, data: m.Subscription, state: ConnectionState):
        self.id: int = int(data['id'])
        self.user_id: int = int(data['user_id'])
        self.sku_ids: List[int] = [int(sku_id) for sku_id in data['sku_ids']]
        self.entitlement_ids: List[int] = [int(entitlement_id) for entitlement_id in data['entitlement_ids']]
        self.current_period_start: datetime = utils.parse_time(data['starts_at'])
        self.current_period_end: datetime = utils.parse_time(data['ends_at'])
        self.status: SubscriptionStatus = try_enum(SubscriptionStatus, data['status'])
        self.canceled_at: Optional[datetime] = utils.parse_time(data.get('canceled_at'))
        self.country_code: Optional[str] = data.get('country')
        self._state: ConnectionState = state

    def __repr__(self) -> str:
        return f'<Subscription id={self.id} user_id={self.user_id} status={self.status.name}>'

    @property
    def user(self) -> User:
        """The user that is subscribed to the SKU(s)"""
        return self._state.get_user(self.user_id)
