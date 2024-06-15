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
    List,
    Optional,
    Tuple,
    TYPE_CHECKING,
    Union
)

from .asset import Asset
from .enums import StickerType, try_enum
from .mixins import Hashable
from .utils import get as utils_get, snowflake_time

if TYPE_CHECKING:
    from datetime import datetime
    
    from .guild import Guild
    from .user import User
    from .state import ConnectionState


__all__ = (
    'StickerPack',
    'Sticker',
    'GuildSticker'
)


class StickerPack(Hashable):
    """Represents a pack of build-in stickers

    Attributes
    ----------
    name: :class:`str`
        The name of the sticker pack.
    id: :class:`int`
        The id of the sticker pack.
    description: :class:`str`
        The description of the sticker pack.
    sku_id: :class:`int`
        The id of the pack's SKU.
    banner_asset_id: :class:`int`
        The id of the sticker pack's banner image.
    cover_sticker_id: Optional[:class:`int`]
        The id of a sticker in the pack which is shown in the client as the pack's icon.
    """
    def __init__(self, state: ConnectionState, data) -> None:
        self._state = state
        self.id = int(data['id'])
        self.name: str = data['name']
        self.sku_id: int = int(data['sku_id'])
        self.cover_sticker_id: Optional[int] = int(data.get('cover_sticker_id', 0)) or None
        self.description: str = data['description']
        self.banner_asset_id = int(data['banner_asset_id'])
        self.__stickers: Tuple[Sticker] = tuple(map(lambda d: state.store_sticker(d, self), data['stickers']))

    @property
    def stickers(self) -> Tuple[Sticker]:
        """Tuple[:class:`Sticker`]: The stickers of the pack"""
        return self.__stickers

    @stickers.setter
    def stickers(self, value):
        raise TypeError('Sticker Packs are immutable.')

    @property
    def banner_url(self) -> Asset:
        """Returns an :class:`Asset` for the sticker pack's banner.

        Returns
        -------
        :class:`Asset`
            The resulting CDN asset.
        """
        return self.banner_url_as()

    def banner_url_as(self, format: str = 'png', size=1024) -> Asset:
        """Returns an :class:`Asset` for the sticker pack's banner.

        The size must be a power of 2 between 16 and 4096.

        Returns
        -------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_sticker_pack(self._state, self, format=format, size=size)

    @property
    def cover_sticker(self) -> Sticker:
        """:class:`Sticker`: Returns the sticker in the pack which is shown in the client as the pack's icon."""
        return self.get_sticker(self.cover_sticker_id)

    def get_sticker(self, id: int) -> Optional[Sticker]:
        """
        Returns a sticker of the pack with the given id or :obj:`None` if not found.
        
        Parameters
        -----------
        id: :class:`int`
            The id of the sticker to get 
        
        Returns
        --------
        Optional[:class:`Sticker`]
            The sticker or ``None`` if not found.
        """
        return utils_get(self.stickers, id=id)


class Sticker(Hashable):
    """Represents a sticker.

    .. versionadded:: 1.6

    .. container:: operations

        .. describe:: str(x)

            Returns the name of the sticker.

        .. describe:: x == y

           Checks if the sticker is equal to another sticker.

        .. describe:: x != y

           Checks if the sticker is not equal to another sticker.

    Attributes
    ----------
    name: :class:`str`
        The sticker's name.
    id: :class:`int`
        The id of the sticker.
    description: :class:`str`
        The description of the sticker.
    pack_id: :class:`int`
        The id of the sticker's pack.
    format: :class:`StickerType`
        The format for the sticker's image.
    tags: List[:class:`str`]
        A list of tags for the sticker.
    pack: Optional[:class:`StickerPack`]
        The pack the sticker belongs to. Could be :obj:`None` even if :attr:`Sticker.pack_id` is present.
    sort_value: :class:`int`
        The sticker's sort order within its :attr:`Sticker.pack`.
    """
    __slots__ = ('_state', 'id', 'name', 'description', 'pack_id', 'format', 'tags', 'sort_value' , 'pack')

    def __init__(self, *, state, data, pack: Optional[StickerPack] = None) -> None:
        self._state = state
        self.id = int(data['id'])
        self.name: str = data['name']
        self.description: str = data.get('description', None)
        self.pack_id: int = int(data.get('pack_id', 0))
        self.format: StickerType = try_enum(StickerType, data['format_type'])
        self.sort_value = data.get('sort_value', 0)
        try:
            self.tags = [tag.strip() for tag in data['tags'].split(',')]
        except KeyError:
            self.tags = []
        self.pack = pack

    def __repr__(self):
        return '<{0.__class__.__name__} id={0.id} name={0.name!r}>'.format(self)

    def __str__(self):
        return self.name

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the sticker's creation time in UTC as a naive datetime."""
        return snowflake_time(self.id)

    @property
    def image_url(self) -> Asset:
        """Returns an :class:`Asset` for the sticker's image.

        .. note::
            This will return ``None`` if the format is ``StickerType.lottie``.

        Returns
        -------
        Optional[:class:`Asset`]
            The resulting CDN asset.
        """
        return self.image_url_as()

    def image_url_as(self) -> Asset:
        """Optionally returns an :class:`Asset` for the sticker's image.

        The size must be a power of 2 between 16 and 4096.

        .. note::
            This will return ``None`` if the format is ``StickerType.lottie``.

        Returns
        -------
        Optional[:class:`Asset`]
            The resulting CDN asset or ``None``.
        """
        if self.format is StickerType.lottie:
            return None

        return Asset._from_sticker(self._state, self, format='png')


class GuildSticker(Sticker):
    """
    Represents a "custom" sticker in a guild

    Attributes
    ----------
    name: :class:`str`
        The sticker's name.
    id: :class:`int`
        The id of the sticker.
    description: :class:`str`
        The description of the sticker.
    format: :class:`StickerType`
        The format for the sticker's image.
    tags: List[:class:`str`]
        A list of tags for the sticker.
    guild_id: :class:`int`
        The id of the guild which this sticker belongs to.
    available: :class:`bool`
        Whether this guild sticker can be used, may be :obj:`False` due to loss of Server Boosts
    user: :class:`User`
        The user that uploaded the guild sticker
    """
    __slots__ = ('_state', 'id', 'name', 'description', 'format', 'tags', 'available', 'guild_id', 'user')

    def __init__(self, *, state: ConnectionState, data) -> None:
        super().__init__(state=state, data=data)
        self.guild_id: int = int(data['guild_id'])
        self.available = data.get('available', True)
        try:
            user = data['user']
        except KeyError:
            self.user: Optional[User] = None
        else:
            self.user: Optional[User] = state.store_user(user)

    @property
    def guild(self) -> Guild:
        """:class:`Guild`: The guild the sticker belongs to"""
        return self._state._get_guild(self.guild_id)

    def _update(self, data):
        for k, v in data.items():
            setattr(self, k, v)
        return self

    async def edit(self, *, reason: Optional[str] = None, **fields) -> GuildSticker:
        """|coro|

        Modify the sticker.

        Requires the ``MANAGE_EMOJIS_AND_STICKERS`` permission.

        Parameters
        ----------
        name: :class:`str`
            The name of the sticker; 2-30 characters long.
        description: Optional[:class:`str`]
            The description of the sticker; ``None`` or 2-100 characters long.
        tags: Union[:class:`str`, List[:class:`str`]]
            The autocomplete/suggestion tags for the sticker.
            A string in which the individual tags are separated by ``,`` or a list of tags; (max 200 characters).
        reason: Optional[:class:`str`]
            The reason for modifying the sticker, shows up in the audit-log.

        Raises
        ------
        discord.Forbidden:
            You don't have the required permission to edit the sticker.
        discord.HTTPException:
            Editing the sticker failed.
        ValueError:
            Any of name, description or tags is invalid.

        Returns
        -------
        discord.GuildSticker:
            The updated sticker on success.
        """

        try:
            name: str = fields['name']
        except KeyError:
            pass
        else:
            if 2 > len(name) > 30:
                raise ValueError(f'The length of sticker name must be between 2 and 30 characters long; got {len(name)}.')

        try:
            description: Optional[str] = fields['description']
        except KeyError:
            pass
        else:
            if description is not None and 2 > len(description) > 100:
                raise ValueError(f'The length of sticker description must be between 2 and 30 characters long; got {len(description)}.')

        try:
            tags: Union[str, List[str]] = fields['tags']
        except KeyError:
            pass
        else:
            if isinstance(tags, list):
                fields['tags'] = tags = ','.join(tags)
            if len(tags) > 200:
                raise ValueError(f'The length of the sticker tags must not exceed 200 characters; got {len(tags)}.')

        data = await self._state.http.edit_guild_sticker(guild_id=self.guild_id, sticker_id=self.id, data=fields, reason=reason)
        return self._update(data)

    async def delete(self, *, reason: Optional[str]) -> GuildSticker:
        """|coro|

        Delete the sticker.

        Requires the ``MANAGE_EMOJIS_AND_STICKERS`` permission.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting the sticker, shows up in the audit-log.

        Raises
        ------
        discord.Forbidden:
            You don't have the required permissions to delete the sticker.
        discord.HTTPException:
            Deleting the sticker failed.

        Returns
        -------
        discord.GuildSticker:
            The sticker that was deleted.
        """

        await self._state.http.delete_guid_sticker(guild_id=self.guild_id, sticker_id=self.id, reason=reason)
        return self
