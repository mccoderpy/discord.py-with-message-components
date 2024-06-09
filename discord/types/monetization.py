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

from typing import TypedDict, Union

from typing_extensions import Literal, NotRequired

from .snowflake import SnowflakeID

__all__ = (
    'SKU',
    'TestEntitlement',
    'Entitlement',
)

SKUType = Literal[1, 2, 3, 4, 5, 6]
EntitlementType = Literal[1, 2, 3, 4, 5, 6, 7, 8]


class SKU(TypedDict):
    id: SnowflakeID
    type: SKUType
    application_id: SnowflakeID
    name: str
    slug: str
    flags: int


class TestEntitlement(TypedDict):
    id: SnowflakeID
    application_id: SnowflakeID
    sku_id: SnowflakeID
    user_id: NotRequired[SnowflakeID]
    guild_id: NotRequired[SnowflakeID]
    type: EntitlementType
    consumed: bool
    deleted: bool


class Entitlement(TestEntitlement):
    subscription_id: SnowflakeID
    starts_at: str
    ends_at: str


EntitlementData = Union[TestEntitlement, Entitlement]
