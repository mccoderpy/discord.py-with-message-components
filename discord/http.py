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
    Any,
    Coroutine,
    Dict,
    List,
    Optional,
    Sequence,
    TYPE_CHECKING,
    TypeVar,
    Union,
)
from typing_extensions import Literal

import asyncio
import json
import logging
import sys
from urllib.parse import quote as _uriquote
import weakref

import aiohttp

from .errors import HTTPException, Forbidden, NotFound, LoginFailure, DiscordServerError, GatewayNotFound, InvalidArgument
from .file import File
from .enums import Locale
from .gateway import DiscordClientWebSocketResponse
from .mentions import AllowedMentions
from .components import ActionRow, Button, BaseSelect
from . import __version__, utils


if TYPE_CHECKING:
    from .flags import MessageFlags
    from enums import InteractionCallbackType
    from .embeds import Embed
    from .message import Attachment, MessageReference
    from .types import (
        guild,
        monetization,
    )
    from .types.snowflake import SnowflakeID
    from .utils import SnowflakeList

    T = TypeVar('T')
    Response = Coroutine[Any, Any, T]


MISSING = utils.MISSING


log = logging.getLogger(__name__)


async def json_or_text(response):
    text = await response.text(encoding='utf-8')
    try:
        if 'application/json' in response.headers['content-type']:
            return json.loads(text)
    except KeyError:
        # Thanks Cloudflare
        pass

    return text


class MultipartParameters:
    def __init__(
            self,
            payload: Optional[Dict[str, Any]] = None,
            multipart: Optional[List[Dict[str, Any]]] = None,
            files: Optional[Sequence[File]] = None
    ):
        self.payload: Optional[Dict[str, Any]] = payload
        self.multipart: Optional[List[Dict[str, Any]]] = multipart
        self.files: Optional[Sequence[File]] = files

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.files:
            for file in self.files:
                file.close()


def handle_message_parameters(
        content: Optional[str] = MISSING,
        *,
        username: str = MISSING,
        avatar_url: Any = MISSING,
        tts: bool = False,
        nonce: Optional[Union[int, str]] = None,
        flags: MessageFlags = MISSING,
        file: Optional[File] = MISSING,
        files: Sequence[File] = MISSING,
        embed: Optional[Embed] = MISSING,
        embeds: Sequence[Embed] = MISSING,
        attachments: Sequence[Union[Attachment, File]] = MISSING,
        components: List[Union[ActionRow, List[Union[Button, BaseSelect]]]] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
        message_reference: Optional[MessageReference] = MISSING,
        stickers: Optional[SnowflakeList] = MISSING,
        previous_allowed_mentions: Optional[AllowedMentions] = None,
        mention_author: Optional[bool] = None,
        thread_name: str = MISSING,
        channel_payload: Dict[str, Any] = MISSING
) -> MultipartParameters:
    """
    Helper function to handle message parameters.
    """
    payload: Dict[str, Any] = {}

    if embed is not MISSING or embeds is not MISSING:
        _embeds = []
        if embed not in {MISSING, None}:
            _embeds.append(embed.to_dict())
        if embeds is not MISSING and embeds is not None:
            _embeds.extend([e.to_dict() for e in embeds])
        if len(_embeds) > 10:
            raise TypeError(f"Only can send up to 10 embeds per message; got {len(embeds)}")
        payload['embeds'] = _embeds

    if content is not MISSING:
        if content is None:
            payload['content'] = None
        else:
            payload['content'] = str(content)

    if components is not MISSING:
        if components is None:
            payload['components'] = []
        else:
            _components = []
            for component in (list(components) if not isinstance(components, list) else components):
                if isinstance(component, (Button, BaseSelect)):
                    _components.extend(ActionRow(component).to_dict())
                elif isinstance(component, ActionRow):
                    _components.extend(component.to_dict())
                elif isinstance(component, list):
                    _components.extend(
                        ActionRow(*[obj for obj in component]).to_dict()
                    )
            if len(_components) > 5:
                raise TypeError(f"Only can send up to 5 ActionRows per message; got {len(_components)}")
            payload['components'] = _components

    if nonce is not None:
        payload['nonce'] = str(nonce)

    if message_reference is not MISSING:
        payload['message_reference'] = message_reference

    if stickers is not MISSING:
        if stickers is None:
            payload['sticker_ids'] = []
        else:
            payload['sticker_ids'] = stickers

    payload['tts'] = tts
    if avatar_url:
        payload['avatar_url'] = str(avatar_url)
    if username:
        payload['username'] = username

    if flags is not MISSING:
        payload['flags'] = flags.value

    if thread_name is not MISSING:
        payload['thread_name'] = thread_name

    if allowed_mentions:
        if previous_allowed_mentions is not None:
            payload['allowed_mentions'] = previous_allowed_mentions.merge(allowed_mentions).to_dict()
        else:
            payload['allowed_mentions'] = allowed_mentions.to_dict()
    elif previous_allowed_mentions is not None:
        payload['allowed_mentions'] = previous_allowed_mentions.to_dict()

    if mention_author is not None:
        if 'allowed_mentions' not in payload:
            payload['allowed_mentions'] = AllowedMentions().to_dict()
        payload['allowed_mentions']['replied_user'] = mention_author

    if file is not MISSING:
        if files is not MISSING and files is not None:
            files = [file, *files]
        else:
            files = [file]

    if attachments is MISSING:
        attachments = files
    else:
        files = [a for a in attachments if isinstance(a, File)]

    if attachments is not MISSING:
        file_index = 0
        attachments_payload = []
        for attachment in attachments:
            if isinstance(attachment, File):
                attachments_payload.append(attachment.to_dict(file_index))
                file_index += 1
            else:
                attachments_payload.append(attachment.to_dict())  # type: ignore
        payload['attachments'] = attachments_payload

    if channel_payload is not MISSING:
        payload = {
            'message': payload,
        }
        payload.update(channel_payload)

    multipart = []
    if files:
        multipart.append({'name': 'payload_json', 'value': utils.to_json(payload)})
        payload = None
        for index, file in enumerate(files):
            multipart.append(
                {
                    'name': f'files[{index}]',
                    'value': file.fp,
                    'filename': file.filename,
                    'content_type': 'application/octet-stream'
                }
            )

    return MultipartParameters(payload=payload, multipart=multipart, files=files)


def handle_interaction_message_parameters(
        *,
        type: InteractionCallbackType,
        content: Optional[str] = MISSING,
        tts: bool = False,
        nonce: Optional[Union[int, str]] = None,
        flags: MessageFlags = MISSING,
        file: Optional[File] = MISSING,
        files: Sequence[File] = MISSING,
        embed: Optional[Embed] = MISSING,
        embeds: Sequence[Embed] = MISSING,
        attachments: Sequence[Union[Attachment, File]] = MISSING,
        components: List[Union[ActionRow, List[Union[Button, BaseSelect]]]] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
        message_reference: Optional[MessageReference] = MISSING,
        stickers: Optional[SnowflakeList] = MISSING,
        previous_allowed_mentions: Optional[AllowedMentions] = None,
        mention_author: Optional[bool] = None
) -> MultipartParameters:
    """
    Helper function to handle message parameters for interaction responses.
    """
    payload: Dict[str, Any] = {}

    if embed is not MISSING or embeds is not MISSING:
        _embeds = []
        if embed not in {MISSING, None}:
            _embeds.append(embed.to_dict())
        if embeds is not MISSING and embeds is not None:
            _embeds.extend([e.to_dict() for e in embeds])
        if len(_embeds) > 10:
            raise TypeError(f"Only can send up to 10 embeds per message; got {len(embeds)}")
        payload['embeds'] = _embeds

    if content is not MISSING:
        if content is None:
            payload['content'] = None
        else:
            payload['content'] = str(content)

    if components is not MISSING:
        if components is None:
            payload['components'] = []
        else:
            _components = []
            for component in ([components] if not isinstance(components, list) else components):
                if isinstance(component, (Button, BaseSelect)):
                    _components.extend(ActionRow(component).to_dict())
                elif isinstance(component, ActionRow):
                    _components.extend(component.to_dict())
                elif isinstance(component, list):
                    _components.extend(
                        ActionRow(*[obj for obj in component]).to_dict()
                    )
            if len(_components) > 5:
                raise TypeError(f"Only can send up to 5 ActionRows per message; got {len(_components)}")
            payload['components'] = _components

    if nonce is not None:
        payload['nonce'] = str(nonce)

    if message_reference is not MISSING:
        payload['message_reference'] = message_reference.to_message_reference_dict()

    if stickers is not MISSING:
        if stickers is None:
            payload['sticker_ids'] = []
        else:
            payload['sticker_ids'] = stickers

    payload['tts'] = tts

    if flags is not MISSING:
        payload['flags'] = flags.value

    if allowed_mentions:
        if previous_allowed_mentions is not None:
            payload['allowed_mentions'] = previous_allowed_mentions.merge(allowed_mentions).to_dict()
        else:
            payload['allowed_mentions'] = allowed_mentions.to_dict()
    elif previous_allowed_mentions is not None:
        payload['allowed_mentions'] = previous_allowed_mentions.to_dict()

    if mention_author is not None:
        if 'allowed_mentions' not in payload:
            payload['allowed_mentions'] = AllowedMentions().to_dict()
        payload['allowed_mentions']['replied_user'] = mention_author

    if file is not MISSING:
        if files is not MISSING and files is not None:
            files = [file, *files]
        else:
            files = [file]

    if attachments is MISSING:
        attachments = files
    else:
        files = [a for a in attachments if isinstance(a, File)]

    if attachments is not MISSING:
        file_index = 0
        attachments_payload = []
        for attachment in attachments:
            if isinstance(attachment, File):
                attachments_payload.append(attachment.to_dict(file_index))
                file_index += 1
            else:
                attachments_payload.append(attachment.to_dict())  # type: ignore
        payload['attachments'] = attachments_payload

    multipart = []
    payload = {'type': int(type), 'data': payload}
    if files:
        multipart.append({'name': 'payload_json', 'value': utils.to_json(payload)})
        payload = None
        for index, file in enumerate(files):
            multipart.append(
                {
                    'name': f'files[{index}]',
                    'value': file.fp,
                    'filename': file.filename,
                    'content_type': 'application/octet-stream'
                }
            )

    return MultipartParameters(payload=payload, multipart=multipart, files=files)


class Route:
    BASE = 'https://discord.com/api/v10'

    def __init__(self, method, path, **parameters):
        self.path = path
        self.method = method
        url = (self.BASE + self.path)
        if parameters:
            self.url = url.format(**{k: _uriquote(v) if isinstance(v, str) else v for k, v in parameters.items()})
        else:
            self.url = url

        # major parameters:
        self.channel_id = parameters.get('channel_id')
        self.guild_id = parameters.get('guild_id')

    @property
    def bucket(self):
        # the bucket is just method + path w/ major parameters
        return '{0.channel_id}:{0.guild_id}:{0.path}'.format(self)


class MaybeUnlock:
    def __init__(self, lock):
        self.lock = lock
        self._unlock = True

    def __enter__(self):
        return self

    def defer(self):
        self._unlock = False

    def __exit__(self, type, value, traceback):
        if self._unlock:
            self.lock.release()


# For some reason, the Discord voice websocket expects this header to be
# completely lowercase while aiohttp respects spec and does it as case-insensitive

aiohttp.hdrs.WEBSOCKET = 'websocket'


class HTTPClient:
    """Represents an HTTP client sending HTTP requests to the Discord API."""

    SUCCESS_LOG = '{method} {url} has received {text}'
    REQUEST_LOG = '{method} {url} with {json} has returned {status}'

    def __init__(
            self,
            connector=None,
            *,
            proxy: Optional[str] = None,
            proxy_auth: Optional[aiohttp.BasicAuth] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None,
            unsync_clock: bool = True,
            api_version: int = 10,
            api_error_locale: Optional[Locale] = 'en-US'
    ):
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.connector = connector
        self.__session: aiohttp.ClientSession = None  # filled in static_login
        self._locks = weakref.WeakValueDictionary()
        self._global_over = asyncio.Event()
        self._global_over.set()
        self.token = None
        self.proxy = proxy
        self.proxy_auth = proxy_auth
        self.use_clock = not unsync_clock
        self.api_version = api_version
        self.api_error_locale = str(api_error_locale)
        Route.BASE = f'https://discord.com/api/v{api_version}'

        user_agent = 'DiscordBot (https://github.com/mccoderpy/discord.py-message-components {0}) Python/{1[0]}.{1[1]} aiohttp/{2}'
        self.user_agent = user_agent.format(__version__, sys.version_info, aiohttp.__version__)

    def recreate(self):
        if self.__session.closed:
            self.__session = aiohttp.ClientSession(
                connector=self.connector,
                ws_response_class=DiscordClientWebSocketResponse
            )

    async def ws_connect(self, url, *, compress=0):
        kwargs = {
            'proxy_auth': self.proxy_auth,
            'proxy': self.proxy,
            'max_msg_size': 0,
            'timeout': 30.0,
            'autoclose': False,
            'headers': {
                'User-Agent': self.user_agent,
                'X-Discord-Locale': self.api_error_locale
            },
            'compress': compress
        }
        return await self.__session.ws_connect(url, **kwargs)

    async def request(self, route, *, files=None, form=None, **kwargs):
        bucket = route.bucket
        method = route.method
        url = route.url

        lock = self._locks.get(bucket)
        if lock is None:
            lock = asyncio.Lock()
            if bucket is not None:
                self._locks[bucket] = lock

        # header creation
        headers = kwargs.get('headers', {})
        headers.update({
            'User-Agent': self.user_agent,
            'X-Discord-Locale': self.api_error_locale
        })

        if self.token is not None:
            headers['Authorization'] = 'Bot ' + self.token
        # some checking if it's a JSON request
        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = utils.to_json(kwargs.pop('json'))

        if 'content_type' in kwargs:
            headers['Content-Type'] = kwargs.pop('content_type')

        try:
            reason = kwargs.pop('reason')
        except KeyError:
            pass
        else:
            if reason:
                headers['X-Audit-Log-Reason'] = _uriquote(reason, safe='/ ')

        kwargs['headers'] = headers

        # Proxy support
        if self.proxy is not None:
            kwargs['proxy'] = self.proxy
        if self.proxy_auth is not None:
            kwargs['proxy_auth'] = self.proxy_auth

        if not self._global_over.is_set():
            # wait until the global lock is complete
            await self._global_over.wait()

        await lock.acquire()
        with MaybeUnlock(lock) as maybe_lock:
            for tries in range(5):
                if files:
                    for f in files:
                        f.reset(seek=tries)

                if form:
                    form_data = aiohttp.FormData(quote_fields=False)
                    for params in form:
                        form_data.add_field(**params)
                    kwargs['data'] = form_data

                try:
                    async with self.__session.request(method, url, **kwargs) as r:
                        log.debug('%s %s with %s has returned %s', method, url, kwargs.get('data'), r.status)

                        # even errors have text involved in them so this is safe to call
                        data = await json_or_text(r)

                        # check if we have rate limit header information
                        remaining = r.headers.get('X-Ratelimit-Remaining')
                        if remaining == '0' and r.status != 429:
                            # we've depleted our current bucket
                            delta = utils._parse_ratelimit_header(r, use_clock=self.use_clock)
                            log.debug('A rate limit bucket has been exhausted (bucket: %s, retry: %s).', bucket, delta)
                            maybe_lock.defer()
                            self.loop.call_later(delta, lock.release)

                        # the request was successful so just return the text/json
                        if 300 > r.status >= 200:
                            log.debug('%s %s has received %s', method, url, data)
                            return data

                        # we are being rate limited
                        if r.status == 429:
                            if not r.headers.get('Via'):
                                # Banned by Cloudflare more than likely.
                                raise HTTPException(r, data)

                            fmt = 'We are being rate limited. Retrying in %.2f seconds. Handled under the bucket "%s"'

                            # sleep a bit
                            retry_after = data['retry_after']
                            log.warning(fmt, retry_after, bucket)

                            # check if it's a global rate limit
                            is_global = data.get('global', False)
                            if is_global:
                                log.warning('Global rate limit has been hit. Retrying in %.2f seconds.', retry_after)
                                self._global_over.clear()

                            await asyncio.sleep(retry_after)
                            log.debug('Done sleeping for the rate limit. Retrying...')

                            # release the global lock now that the
                            # global rate limit has passed
                            if is_global:
                                self._global_over.set()
                                log.debug('Global rate limit is now over.')

                            continue

                        # we've received a 500 or 502, unconditional retry
                        if r.status in {500, 502}:
                            await asyncio.sleep(1 + tries * 2)
                            continue

                        # the usual error cases
                        if r.status == 403:
                            raise Forbidden(r, data)
                        elif r.status == 404:
                            raise NotFound(r, data)
                        elif r.status == 503:
                            raise DiscordServerError(r, data)
                        else:
                            raise HTTPException(r, data)

                # This is handling exceptions from the request
                except OSError as e:
                    # Connection reset by peer
                    if tries < 4 and e.errno in (54, 10054):
                        continue
                    raise

            # We've run out of retries, raise.
            if r.status >= 500:
                raise DiscordServerError(r, data)

            raise HTTPException(r, data)

    async def get_from_cdn(self, url):
        async with self.__session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
            elif resp.status == 404:
                raise NotFound(resp, 'asset not found')
            elif resp.status == 403:
                raise Forbidden(resp, 'cannot retrieve asset')
            else:
                raise HTTPException(resp, 'failed to get asset')

    # state management

    async def close(self):
        if self.__session:
            await self.__session.close()
            await asyncio.sleep(0.025)  # wait for the connection to be released

    def _token(self, token):
        self.token = token
        self._ack_token = None

    # login management

    async def static_login(self, token):
        # Necessary to get aiohttp to stop complaining about _session creation
        self.__session = aiohttp.ClientSession(connector=self.connector, ws_response_class=DiscordClientWebSocketResponse)
        old_token = self.token
        self._token(token)

        try:
            data = await self.request(Route('GET', '/users/@me'))
        except HTTPException as exc:
            self._token(old_token)
            if exc.response.status == 401:
                raise LoginFailure('Improper token has been passed.') from exc
            raise

        return data

    def logout(self):
        return self.request(Route('POST', '/auth/logout'))

    # Group functionality

    def start_group(self, user_id, recipients):
        payload = {
            'recipients': recipients
        }

        return self.request(Route('POST', '/users/{user_id}/channels', user_id=user_id), json=payload)

    def leave_group(self, channel_id):
        return self.request(Route('DELETE', '/channels/{channel_id}', channel_id=channel_id))

    def add_group_recipient(self, channel_id, user_id):
        r = Route('PUT', '/channels/{channel_id}/recipients/{user_id}', channel_id=channel_id, user_id=user_id)
        return self.request(r)

    def remove_group_recipient(self, channel_id, user_id):
        r = Route('DELETE', '/channels/{channel_id}/recipients/{user_id}', channel_id=channel_id, user_id=user_id)
        return self.request(r)

    def edit_group(self, channel_id, **options):
        valid_keys = ('name', 'icon')
        payload = {
            k: v for k, v in options.items() if k in valid_keys
        }

        return self.request(Route('PATCH', '/channels/{channel_id}', channel_id=channel_id), json=payload)

    def convert_group(self, channel_id):
        return self.request(Route('POST', '/channels/{channel_id}/convert', channel_id=channel_id))

    # Message management

    def start_private_message(self, user_id):
        payload = {
            'recipient_id': user_id
        }

        return self.request(Route('POST', '/users/@me/channels'), json=payload)

    def send_message(self, channel_id, *, params: MultipartParameters):
        r = Route('POST', '/channels/{channel_id}/messages', channel_id=channel_id)
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload)
    
    def send_voice_message(self, channel_id, *, params: MultipartParameters, x_super_properties: str):
        r = Route('POST', '/channels/{channel_id}/messages', channel_id=channel_id)
        return self.request(r, files=params.files, form=params.multipart, headers={'x-super-properties': x_super_properties})
    
    def send_typing(self, channel_id):
        return self.request(Route('POST', '/channels/{channel_id}/typing', channel_id=channel_id))

    def delete_message(self, channel_id, message_id, *, reason=None):
        r = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}',
            channel_id=channel_id,
             message_id=message_id
        )
        return self.request(r, reason=reason)

    def delete_messages(self, channel_id, message_ids, *, reason=None):
        r = Route('POST', '/channels/{channel_id}/messages/bulk-delete', channel_id=channel_id)
        payload = {
            'messages': message_ids
        }
        return self.request(r, json=payload, reason=reason)

    def edit_message(self, channel_id, message_id, *, params: MultipartParameters):
        r = Route('PATCH', '/channels/{channel_id}/messages/{message_id}', channel_id=channel_id, message_id=message_id)
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload)

    def add_reaction(self, channel_id, message_id, emoji):
        r = Route(
            'PUT',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me',
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji
        )
        return self.request(r)

    def remove_reaction(self, channel_id, message_id, emoji, member_id):
        r = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{member_id}',
            channel_id=channel_id,
            message_id=message_id,
            member_id=member_id,
            emoji=emoji
        )
        return self.request(r)

    def remove_own_reaction(self, channel_id, message_id, emoji):
        r = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me',
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji
        )
        return self.request(r)

    def get_reaction_users(self, channel_id, message_id, emoji, limit, reaction_type, after=None):
        r = Route(
            'GET',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}',
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji
        )

        params = {'limit': limit}
        if after:
            params['after'] = after
        if reaction_type != 0:
            params['type'] = type
        return self.request(r, params=params)

    def clear_reactions(self, channel_id, message_id):
        r = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}/reactions',
            channel_id=channel_id,
            message_id=message_id
        )

        return self.request(r)

    def clear_single_reaction(self, channel_id, message_id, emoji):
        r = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}',
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji
        )
        return self.request(r)

    def get_message(self, channel_id, message_id):
        r = Route('GET', '/channels/{channel_id}/messages/{message_id}', channel_id=channel_id, message_id=message_id)
        return self.request(r)

    def get_channel(self, channel_id):
        r = Route('GET', '/channels/{channel_id}', channel_id=channel_id)
        return self.request(r)

    def logs_from(self, channel_id, limit, before=None, after=None, around=None):
        params = {
            'limit': limit
        }

        if before is not None:
            params['before'] = before
        if after is not None:
            params['after'] = after
        if around is not None:
            params['around'] = around
        return self.request(Route('GET', '/channels/{channel_id}/messages', channel_id=channel_id), params=params)

    def publish_message(self, channel_id, message_id):
        return self.request(
            Route(
                'POST',
                '/channels/{channel_id}/messages/{message_id}/crosspost',
                channel_id=channel_id,
                message_id=message_id
            )
        )

    def pin_message(self, channel_id, message_id, reason=None):
        return self.request(
            Route(
                'PUT',
                '/channels/{channel_id}/pins/{message_id}',
                channel_id=channel_id,
                message_id=message_id
            ),
            reason=reason
        )

    def unpin_message(self, channel_id, message_id, reason=None):
        return self.request(
            Route(
                'DELETE',
                '/channels/{channel_id}/pins/{message_id}',
                channel_id=channel_id,
                message_id=message_id
            ),
            reason=reason
        )

    def pins_from(self, channel_id):
        return self.request(Route('GET', '/channels/{channel_id}/pins', channel_id=channel_id))

    # Thread management
    def create_thread(
            self,
            channel_id: int,
            *,
            payload: Dict[str, Any],
            message_id: Optional[int] = None,
            reason=None
        ):
        if message_id:
            r = Route(
                'POST',
                '/channels/{channel_id}/messages/{message_id}/threads',
                channel_id=channel_id,
                message_id=message_id
            )
        else:
            r = Route('POST', '/channels/{channel_id}/threads', channel_id=channel_id)
        return self.request(r, json=payload, reason=reason)

    def create_forum_post(self, channel_id, *, params: MultipartParameters, reason: Optional[str] = None):
        r = Route('POST', '/channels/{channel_id}/threads', channel_id=channel_id)
        query_params = {'use_nested_fields': True}
        if params.files:
            return self.request(r, files=params.files, form=params.multipart, params=query_params, reason=reason)
        else:
            return self.request(r, json=params.payload, params=query_params, reason=reason)

    def add_thread_member(self, channel_id, member_id='@me'):
        r = Route(
            'PUT',
            '/channels/{channel_id}/thread-members/{member_id}',
            channel_id=channel_id,
            member_id=member_id
        )
        return self.request(r)

    def remove_thread_member(self, channel_id, member_id='@me'):
        r = Route(
            'DELETE',
            '/channels/{channel_id}/thread-members/{member_id}',
            channel_id=channel_id,
            member_id=member_id
        )
        return self.request(r)

    def list_thread_members(
            self,
            channel_id: int,
            with_member: bool = False,
            *,
            limit: int = 100,
            after: Optional[int] = None
    ):
        query_params = {
            'with_member': with_member,
            'limit': limit
        }
        if after:
            query_params['after'] = after
        return self.request(
            Route('GET', '/channels/{channel_id}/thread-members', channel_id=channel_id),
            params=query_params
        )

    def list_active_threads(self, guild_id: int):
        return self.request(
            Route('GET', '/guilds/{guild_id}/threads/active', guild_id=guild_id),
        )

    def list_archived_threads(
            self,
            channel_id: int,
            type: Literal['private', 'public'],
            joined_private: bool = False,
            *,
            before: Optional[int] = None,
            limit: int = 100
    ):
        if type not in ('public', 'private'):
            raise ValueError('type must be public or private, not %s' % type)
        if joined_private:
            r = Route(
                'GET',
                '/channels/{channel_id}/users/@me/threads/archived/private', channel_id=channel_id
            )
        else:
            r = Route(
                'GET',
                '/channels/{channel_id}/threads/archived/{type}', channel_id=channel_id, type=type
            )
        params = {'limit': limit}
        if before:
            params['before'] = before
        return self.request(r, params=params)

    def create_post(self, channel_id: int, params: MultipartParameters, reason: Optional[str] = None):
        r = Route('POST', '/channels/{channel_id}/threads', channel_id=channel_id)
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload, reason=reason)

    # Member management
    def kick(self, user_id, guild_id, reason=None):
        r = Route('DELETE', '/guilds/{guild_id}/members/{user_id}', guild_id=guild_id, user_id=user_id)
        return self.request(r, reason=reason)

    def ban(self, user_id, guild_id, delete_message_seconds, *, reason=None):
        r = Route('PUT', '/guilds/{guild_id}/bans/{user_id}', guild_id=guild_id, user_id=user_id)
        params = {
            'delete_message_seconds': delete_message_seconds
        }
        return self.request(r, params=params, reason=reason)

    def unban(self, user_id, guild_id, *, reason=None):
        r = Route('DELETE', '/guilds/{guild_id}/bans/{user_id}', guild_id=guild_id, user_id=user_id)
        return self.request(r, reason=reason)

    def guild_voice_state(self, user_id, guild_id, *, mute=None, deafen=None, reason=None):
        r = Route('PATCH', '/guilds/{guild_id}/members/{user_id}', guild_id=guild_id, user_id=user_id)
        payload = {}
        if mute is not None:
            payload['mute'] = mute

        if deafen is not None:
            payload['deaf'] = deafen

        return self.request(r, json=payload, reason=reason)

    def edit_profile(self, payload):
        return self.request(Route('PATCH', '/users/@me'), json=payload)

    def change_my_nickname(self, guild_id, nickname, *, reason=None):
        r = Route('PATCH', '/guilds/{guild_id}/members/@me/nick', guild_id=guild_id)
        payload = {
            'nick': nickname
        }
        return self.request(r, json=payload, reason=reason)

    def change_nickname(self, guild_id, user_id, nickname, *, reason=None):
        r = Route('PATCH', '/guilds/{guild_id}/members/{user_id}', guild_id=guild_id, user_id=user_id)
        payload = {
            'nick': nickname
        }
        return self.request(r, json=payload, reason=reason)

    def edit_my_voice_state(self, guild_id, payload):
        r = Route('PATCH', '/guilds/{guild_id}/voice-states/@me', guild_id=guild_id)
        return self.request(r, json=payload)

    def edit_voice_state(self, guild_id, user_id, payload):
        r = Route('PATCH', '/guilds/{guild_id}/voice-states/{user_id}', guild_id=guild_id, user_id=user_id)
        return self.request(r, json=payload)

    def edit_member(self, guild_id, user_id, *, reason=None, **fields):
        r = Route('PATCH', '/guilds/{guild_id}/members/{user_id}', guild_id=guild_id, user_id=user_id)
        return self.request(r, json=fields, reason=reason)

    # Channel management

    def edit_channel(self, channel_id, *, reason=None, **options):
        r = Route('PATCH', '/channels/{channel_id}', channel_id=channel_id)
        valid_keys = (
            'name',
            'parent_id',
            'topic',
            'template',
            'icon_emoji',
            'bitrate',
            'nsfw',
            'flags',
            'auto_archive_duration',
            'default_auto_archive_duration',
            'user_limit',
            'position',
            'permission_overwrites',
            'rate_limit_per_user',
            'default_reaction_emoji',
            'default_thread_rate_limit_per_user',
            'default_forum_layout',
            'default_sort_order',
            'available_tags',
            'applied_tags',
            'locked',
            'archived',
            'type',
            'rtc_region',
        )
        payload = {
            k: v for k, v in options.items() if k in valid_keys
        }
        return self.request(r, reason=reason, json=payload)

    def bulk_channel_update(self, guild_id, data, *, reason=None):
        r = Route('PATCH', '/guilds/{guild_id}/channels', guild_id=guild_id)
        return self.request(r, json=data, reason=reason)

    def create_channel(self, guild_id, channel_type, *, reason=None, **options):
        payload = {
            'type': channel_type
        }
        valid_keys = (
            'name',
            'parent_id',
            'topic',
            'template',
            'icon_emoji',
            'bitrate',
            'nsfw',
            'flags',
            'default_auto_archive_duration',
            'user_limit',
            'position',
            'permission_overwrites',
            'rate_limit_per_user',
            'default_reaction_emoji',
            'default_thread_rate_limit_per_user',
            'default_forum_layout',
            'default_sort_order',
            'available_tags',
            'rtc_region',
        )
        payload.update(
            {
                k: v for k, v in options.items() if k in valid_keys and v is not None
            }
        )

        return self.request(
            Route(
                'POST',
                '/guilds/{guild_id}/channels',
                guild_id=guild_id
            ),
            json=payload,
            reason=reason
        )

    def delete_channel(self, channel_id, *, reason=None):
        return self.request(Route('DELETE', '/channels/{channel_id}', channel_id=channel_id), reason=reason)

    # Stage instance management

    def create_stage_instance(
            self,
            channel_id,
            topic,
            privacy_level,
            send_start_notification,
            *,
            reason: Optional[str] = None
    ):
        payload = {
            'channel_id': channel_id,
            'topic': topic,
            'privacy_level': privacy_level.value,
            'send_start_notification': send_start_notification,

        }
        return self.request(Route('POST', '/stage-instances'), json=payload, reason=reason)

    def get_stage_instance(self, channel_id):
        return self.request(Route('GET', '/stage-instances/{channel_id}', channel_id=channel_id))

    def edit_stage_instance(self, channel_id, topic, privacy_level=None, *, reason=None):
        r = Route('PATCH', '/stage-instances/{channel_id}', channel_id=channel_id)
        payload = {
            'topic': topic
        }
        if privacy_level is not None:
            payload['privacy_level'] = privacy_level.value
        return self.request(r, json=payload, reason=reason)

    def delete_stage_instance(self, channel_id, *, reason=None):
        return self.request(Route('DELETE', '/stage-instances/{channel_id}', channel_id=channel_id), reason=reason)

    # TODO: Add/remove this when we got a statement from Discord why bots can't set the channel status
    # def set_voice_channel_status(
    #         self,
    #         channel_id: int,
    #         status: Optional[str],
    #         reason: Optional[str] = None
    # ):
    #     return self.request(
    #         Route('PUT', '/channels/{channel_id}/voice-status', channel_id=channel_id),
    #         json={'status': status},
    #         reason=reason
    #     )

    # Webhook management

    def create_webhook(self, channel_id, *, name, avatar=None, reason=None):
        payload = {
            'name': name
        }
        if avatar is not None:
            payload['avatar'] = avatar

        r = Route('POST', '/channels/{channel_id}/webhooks', channel_id=channel_id)
        return self.request(r, json=payload, reason=reason)

    def channel_webhooks(self, channel_id):
        return self.request(Route('GET', '/channels/{channel_id}/webhooks', channel_id=channel_id))

    def guild_webhooks(self, guild_id):
        return self.request(Route('GET', '/guilds/{guild_id}/webhooks', guild_id=guild_id))

    def get_webhook(self, webhook_id):
        return self.request(Route('GET', '/webhooks/{webhook_id}', webhook_id=webhook_id))

    def follow_webhook(self, channel_id, webhook_channel_id, reason=None):
        payload = {
            'webhook_channel_id': str(webhook_channel_id)
        }
        return self.request(
            Route(
                'POST',
                '/channels/{channel_id}/followers',
                channel_id=channel_id
            ),
            json=payload,
            reason=reason
        )

    # Guild management

    def get_guilds(self, limit, before=None, after=None):
        params = {
            'limit': limit
        }

        if before:
            params['before'] = before
        if after:
            params['after'] = after

        return self.request(Route('GET', '/users/@me/guilds'), params=params)

    def leave_guild(self, guild_id):
        return self.request(Route('DELETE', '/users/@me/guilds/{guild_id}', guild_id=guild_id))

    def get_guild(self, guild_id):
        return self.request(Route('GET', '/guilds/{guild_id}', guild_id=guild_id))

    def delete_guild(self, guild_id):
        return self.request(Route('DELETE', '/guilds/{guild_id}', guild_id=guild_id))

    def create_guild(self, name, region, icon):
        payload = {
            'name': name,
            'icon': icon,
            'region': region
        }

        return self.request(Route('POST', '/guilds'), json=payload)

    def edit_guild(self, guild_id, *, reason=None, **fields):
        return self.request(Route('PATCH', '/guilds/{guild_id}', guild_id=guild_id), json=fields, reason=reason)

    def edit_guild_incident_actions(self, guild_id, *, reason=None, **fields):
        r = Route('PUT', '/guilds/{guild_id}/incident-actions', guild_id=guild_id)
        return self.request(r, json=fields, reason=reason)

    def get_welcome_screen(self, guild_id):
        return self.request(Route('GET', '/guilds/{guild_id}/welcome-screen', guild_id=guild_id))

    def edit_welcome_screen(self, guild_id, reason, **fields):
        r = Route('PATCH', '/guilds/{guild_id}/welcome-screen', guild_id=guild_id)
        return self.request(r, json=fields, reason=reason)

    def get_template(self, code):
        return self.request(Route('GET', '/guilds/templates/{code}', code=code))

    def guild_templates(self, guild_id):
        return self.request(Route('GET', '/guilds/{guild_id}/templates', guild_id=guild_id))

    def create_template(self, guild_id, payload):
        return self.request(Route('POST', '/guilds/{guild_id}/templates', guild_id=guild_id), json=payload)

    def sync_template(self, guild_id, code):
        return self.request(Route('PUT', '/guilds/{guild_id}/templates/{code}', guild_id=guild_id, code=code))

    def edit_template(self, guild_id, code, payload):
        valid_keys = (
            'name',
            'description',
        )
        payload = {
            k: v for k, v in payload.items() if k in valid_keys
        }
        return self.request(
            Route(
                'PATCH',
                '/guilds/{guild_id}/templates/{code}',
                guild_id=guild_id,
                code=code
            ),
            json=payload
        )

    def delete_template(self, guild_id, code):
        return self.request(Route('DELETE', '/guilds/{guild_id}/templates/{code}', guild_id=guild_id, code=code))

    def create_from_template(self, code, name, region, icon):
        payload = {
            'name': name,
            'icon': icon,
            'region': region
        }
        return self.request(Route('POST', '/guilds/templates/{code}', code=code), json=payload)

    def get_bans(self, guild_id, limit: int, after: int = None, before: int = None):
        params = {
            'limit': limit
        }
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        return self.request(Route('GET', '/guilds/{guild_id}/bans', guild_id=guild_id), params=params)

    def get_ban(self, user_id, guild_id):
        return self.request(Route('GET', '/guilds/{guild_id}/bans/{user_id}', guild_id=guild_id, user_id=user_id))

    def get_vanity_code(self, guild_id):
        return self.request(Route('GET', '/guilds/{guild_id}/vanity-url', guild_id=guild_id))

    def change_vanity_code(self, guild_id, code, *, reason=None):
        payload = {'code': code}
        return self.request(
            Route(
                'PATCH',
                '/guilds/{guild_id}/vanity-url',
                guild_id=guild_id
            ),
            json=payload,
            reason=reason
        )

    def get_all_guild_channels(self, guild_id):
        return self.request(Route('GET', '/guilds/{guild_id}/channels', guild_id=guild_id))

    def get_members(self, guild_id, limit, after):
        params = {
            'limit': limit,
        }
        if after:
            params['after'] = after

        r = Route('GET', '/guilds/{guild_id}/members', guild_id=guild_id)
        return self.request(r, params=params)

    def get_member(self, guild_id, member_id):
        return self.request(
            Route('GET', '/guilds/{guild_id}/members/{member_id}', guild_id=guild_id, member_id=member_id)
            )

    def prune_members(self, guild_id, days, compute_prune_count, roles, *, reason=None):
        payload = {
            'days': days,
            'compute_prune_count': 'true' if compute_prune_count else 'false'
        }
        if roles:
            payload['include_roles'] = ', '.join(roles)

        return self.request(Route('POST', '/guilds/{guild_id}/prune', guild_id=guild_id), json=payload, reason=reason)

    def estimate_pruned_members(self, guild_id, days, roles):
        params = {
            'days': days
        }
        if roles:
            params['include_roles'] = ', '.join(roles)

        return self.request(Route('GET', '/guilds/{guild_id}/prune', guild_id=guild_id), params=params)

    def get_all_custom_emojis(self, guild_id):
        return self.request(Route('GET', '/guilds/{guild_id}/emojis', guild_id=guild_id))

    def get_custom_emoji(self, guild_id, emoji_id):
        return self.request(Route('GET', '/guilds/{guild_id}/emojis/{emoji_id}', guild_id=guild_id, emoji_id=emoji_id))

    def create_custom_emoji(self, guild_id, name, image, *, roles=None, reason=None):
        payload = {
            'name': name,
            'image': image,
            'roles': roles or []
        }

        r = Route('POST', '/guilds/{guild_id}/emojis', guild_id=guild_id)
        return self.request(r, json=payload, reason=reason)

    def delete_custom_emoji(self, guild_id, emoji_id, *, reason=None):
        r = Route('DELETE', '/guilds/{guild_id}/emojis/{emoji_id}', guild_id=guild_id, emoji_id=emoji_id)
        return self.request(r, reason=reason)

    def edit_custom_emoji(self, guild_id, emoji_id, *, name, roles=None, reason=None):
        payload = {
            'name': name,
            'roles': roles or []
        }
        r = Route('PATCH', '/guilds/{guild_id}/emojis/{emoji_id}', guild_id=guild_id, emoji_id=emoji_id)
        return self.request(r, json=payload, reason=reason)

    def create_guild_sticker(self, guild_id, file, reason=None, **fields):
        r = Route('POST', '/guilds/{guild_id}/stickers', guild_id=guild_id)
        initial_bytes = file.fp.read(16)

        try:
            mime_type = utils._get_mime_type_for_image(initial_bytes)
        except InvalidArgument:
            if initial_bytes.startswith(b'{'):
                mime_type = 'application/json'
            else:
                mime_type = 'application/octet-stream'
        finally:
            file.reset()

        form = [
            {
                'name': 'file',
                'value': file.fp,
                'filename': file.filename,
                'content_type': mime_type
            }
        ]
        for k, v in fields.items():
            if v is not None:
                form.append(
                    {
                        'name': k,
                        'value': str(v)
                    }
                )

        return self.request(r, form=form, files=[file], reason=reason)

    def edit_guild_sticker(self, guild_id, sticker_id, data, reason=None):
        r = Route('PATCH', '/guilds/{guild_id}/stickers/{sticker_id}', guild_id=guild_id, sticker_id=sticker_id)
        return self.request(r, json=data, reason=reason)

    def delete_guild_sticker(self, guild_id, sticker_id, reason=None):
        r = Route('DELETE', '/guilds/{guild_id}/stickers/{sticker_id}', guild_id=guild_id, sticker_id=sticker_id)
        return self.request(r, reason=reason)

    def get_all_integrations(self, guild_id):
        r = Route('GET', '/guilds/{guild_id}/integrations', guild_id=guild_id)

        return self.request(r)

    def create_integration(self, guild_id, type, id):
        payload = {
            'type': type,
            'id': id
        }

        r = Route('POST', '/guilds/{guild_id}/integrations', guild_id=guild_id)
        return self.request(r, json=payload)

    def edit_integration(self, guild_id, integration_id, **payload):
        r = Route(
            'PATCH',
            '/guilds/{guild_id}/integrations/{integration_id}',
            guild_id=guild_id,
            integration_id=integration_id
        )

        return self.request(r, json=payload)

    def sync_integration(self, guild_id, integration_id):
        r = Route(
            'POST',
            '/guilds/{guild_id}/integrations/{integration_id}/sync',
            guild_id=guild_id,
            integration_id=integration_id
        )

        return self.request(r)

    def delete_integration(self, guild_id, integration_id):
        r = Route(
            'DELETE',
            '/guilds/{guild_id}/integrations/{integration_id}',
            guild_id=guild_id,
            integration_id=integration_id
        )

        return self.request(r)

    def get_audit_logs(self, guild_id, limit=100, before=None, after=None, user_id=None, action_type=None):
        params = {'limit': limit}
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        if user_id:
            params['user_id'] = user_id
        if action_type:
            params['action_type'] = action_type

        r = Route('GET', '/guilds/{guild_id}/audit-logs', guild_id=guild_id)
        return self.request(r, params=params)

    def get_widget(self, guild_id):
        return self.request(Route('GET', '/guilds/{guild_id}/widget.json', guild_id=guild_id))

    # Invite management

    def create_invite(self, channel_id, *, reason=None, **options):
        r = Route('POST', '/channels/{channel_id}/invites', channel_id=channel_id)
        payload = {
            'max_age': options.get('max_age', 86400),
            'max_uses': options.get('max_uses', 0),
            'temporary': options.get('temporary', False),
            'unique': options.get('unique', False),
            'target_type': options.get('target_type', None),
            'target_user_id': options.get('target_user_id', None),
            'target_application_id': options.get('target_application_id', None)
        }

        return self.request(r, reason=reason, json=payload)

    def get_invite(self, invite_id, *, with_counts=True, with_expiration=True, event_id=None):
        params = {
            'with_counts': int(with_counts),
            'with_expiration': int(with_expiration),
        }
        if event_id:
            params['guild_scheduled_event_id'] = str(event_id)
        return self.request(Route('GET', '/invites/{invite_id}', invite_id=invite_id), params=params)

    def invites_from(self, guild_id):
        return self.request(Route('GET', '/guilds/{guild_id}/invites', guild_id=guild_id))

    def invites_from_channel(self, channel_id):
        return self.request(Route('GET', '/channels/{channel_id}/invites', channel_id=channel_id))

    def delete_invite(self, invite_id, *, reason=None):
        return self.request(Route('DELETE', '/invites/{invite_id}', invite_id=invite_id), reason=reason)

    # Event management

    def get_guild_event(self, guild_id, event_id, with_user_count=True):
        with_user_count = str(with_user_count).lower()
        r = Route(
            'GET', '/guilds/{guild_id}/scheduled-events/{event_id}?with_user_count={with_user_count}',
            guild_id=guild_id, event_id=event_id, with_user_count=with_user_count
        )
        return self.request(r)

    def get_guild_events(self, guild_id, with_user_count=True):
        r = Route(
            'GET', '/guilds/{guild_id}/scheduled-events/{event_id}?with_user_count={with_user_count}',
            guild_id=guild_id, with_user_count=with_user_count
        )
        return self.request(r)

    def get_guild_event_users(self, guild_id, event_id, limit=100, before=None, after=None, with_member=False):
        url = '/guilds/{guild_id}/scheduled-events/{event_id}/users?limit={limit}'
        if before:
            url += f'&before={before}'
        elif after:
            url += f'&after={after}'
        if with_member:
            url += '&with_member=true'
        return self.request(Route('GET', url, guild_id=guild_id, event_id=event_id, limit=limit))

    def create_guild_event(self, guild_id, fields, *, reason=None):
        r = Route('POST', '/guilds/{guild_id}/scheduled-events', guild_id=guild_id)
        return self.request(r, json=fields, reason=reason)

    def edit_guild_event(self, guild_id, event_id, *, reason=None, **fields):
        valid_keys = (
            'name',
            'description',
            'entity_type',
            'privacy_level',
            'entity_metadata',
            'channel_id',
            'scheduled_start_time',
            'scheduled_end_time',
            'status',
            'image'
        )
        payload = {
            k: v for k, v in fields.items() if k in valid_keys
        }
        r = Route('PATCH', '/guilds/{guild_id}/scheduled-events/{event_id}', guild_id=guild_id, event_id=event_id)
        return self.request(r, json=payload, reason=reason)

    def delete_guild_event(self, guild_id, event_id, *, reason=None):
        r = Route('DELETE', '/guilds/{guild_id}/scheduled-events/{event_id}', guild_id=guild_id, event_id=event_id)
        return self.request(r, reason=reason)

    # Role management

    def get_roles(self, guild_id):
        return self.request(Route('GET', '/guilds/{guild_id}/roles', guild_id=guild_id))

    def edit_role(self, guild_id, role_id, *, reason=None, **fields):
        r = Route('PATCH', '/guilds/{guild_id}/roles/{role_id}', guild_id=guild_id, role_id=role_id)
        valid_keys = ('name', 'permissions', 'color', 'hoist', 'mentionable', 'icon')
        payload = {
            k: v for k, v in fields.items() if k in valid_keys
        }
        return self.request(r, json=payload, reason=reason)

    def delete_role(self, guild_id, role_id, *, reason=None):
        r = Route('DELETE', '/guilds/{guild_id}/roles/{role_id}', guild_id=guild_id, role_id=role_id)
        return self.request(r, reason=reason)

    def replace_roles(self, user_id, guild_id, role_ids, *, reason=None):
        return self.edit_member(guild_id=guild_id, user_id=user_id, roles=role_ids, reason=reason)

    def create_role(self, guild_id, *, reason=None, fields):
        r = Route('POST', '/guilds/{guild_id}/roles', guild_id=guild_id)
        return self.request(r, json=fields, reason=reason)

    def move_role_position(self, guild_id, positions, *, reason=None):
        r = Route('PATCH', '/guilds/{guild_id}/roles', guild_id=guild_id)
        return self.request(r, json=positions, reason=reason)

    def add_role(self, guild_id, user_id, role_id, *, reason=None):
        r = Route(
            'PUT',
            '/guilds/{guild_id}/members/{user_id}/roles/{role_id}',
            guild_id=guild_id,
            user_id=user_id,
            role_id=role_id
        )
        return self.request(r, reason=reason)

    def remove_role(self, guild_id, user_id, role_id, *, reason=None):
        r = Route(
            'DELETE',
            '/guilds/{guild_id}/members/{user_id}/roles/{role_id}',
            guild_id=guild_id,
            user_id=user_id,
            role_id=role_id
        )
        return self.request(r, reason=reason)

    def edit_channel_permissions(self, channel_id, target, allow, deny, type, *, reason=None):
        payload = {
            'id': target,
            'allow': allow,
            'deny': deny,
            'type': type
        }
        r = Route('PUT', '/channels/{channel_id}/permissions/{target}', channel_id=channel_id, target=target)
        return self.request(r, json=payload, reason=reason)

    def delete_channel_permissions(self, channel_id, target, *, reason=None):
        r = Route('DELETE', '/channels/{channel_id}/permissions/{target}', channel_id=channel_id, target=target)
        return self.request(r, reason=reason)

    # Voice management

    def move_member(self, user_id, guild_id, channel_id, *, reason=None):
        return self.edit_member(guild_id=guild_id, user_id=user_id, channel_id=channel_id, reason=reason)

    # application-command's management
    def get_application_commands(self, application_id, command_id=None, guild_id=None):
        if guild_id:
            url = '/applications/{application_id}/guilds/{guild_id}/commands'
            if command_id:
                url += f'/{command_id}'
                r = Route(
                    'GET',
                    f'{url}?with_localizations=true',
                    application_id=application_id,
                    guild_id=guild_id,
                    command_id=command_id
                )
            else:
                r = Route('GET', f'{url}?with_localizations=true', application_id=application_id, guild_id=guild_id)
        else:
            url = '/applications/{application_id}/commands'
            if command_id:
                url += f'/{command_id}'
                r = Route('GET', f'{url}?with_localizations=true', application_id=application_id, command_id=command_id)
            else:
                r = Route('GET', f'{url}?with_localizations=true', application_id=application_id)
        return self.request(r)

    def create_application_command(self, application_id, data, guild_id=None):
        if guild_id:
            r = Route(
                'POST',
                '/applications/{application_id}/guilds/{guild_id}/commands',
                application_id=application_id,
                guild_id=guild_id
            )
        else:
            r = Route('POST', '/applications/{application_id}/commands', application_id=application_id)
        return self.request(r, json=data)

    def edit_application_command(self, application_id, command_id, data, guild_id=None):
        if guild_id:
            r = Route('PATCH', '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
                      application_id=application_id, guild_id=guild_id, command_id=command_id
                      )
        else:
            r = Route('PATCH', '/applications/{application_id}/commands/{command_id}',
                      application_id=application_id, command_id=command_id
                      )
        return self.request(r, json=data)

    def delete_application_command(self, application_id, command_id, guild_id=None):
        if guild_id:
            r = Route('DELETE', '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
                      application_id=application_id, guild_id=guild_id, command_id=command_id
                      )
        else:
            r = Route('DELETE', '/applications/{application_id}/commands/{command_id}',
                      application_id=application_id, command_id=command_id
                      )
        return self.request(r)

    def bulk_overwrite_application_commands(self, application_id, data, guild_id=None):
        if guild_id:
            r = Route('PUT', '/applications/{application_id}/guilds/{guild_id}/commands',
                      application_id=application_id, guild_id=guild_id
                      )
        else:
            r = Route('PUT', '/applications/{application_id}/commands', application_id=application_id)
        return self.request(r, json=data)

    def get_guild_application_command_permissions(self, application_id, guild_id, command_id=None):
        if command_id:
            r = Route('GET', '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions',
                      application_id=application_id, guild_id=guild_id, command_id=command_id
                      )
        else:
            r = Route('GET', '/applications/{application_id}/guilds/{guild_id}/commands/permissions',
                      application_id=application_id, guild_id=guild_id
                      )
        return self.request(r)

    def edit_application_command_permissions(self, application_id, guild_id, command_id, data):
        r = Route(
            'PUT',
            '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions',
            application_id=application_id,
            guild_id=guild_id,
            command_id=command_id
        )
        return self.request(r, json=data)

    # Interaction management
    def post_initial_response(self, interaction_id: int, token: str, data: Dict[str, Any]):
        return self.request(Route("POST", f'/interactions/{interaction_id}/{token}/callback'), json=data)

    def send_interaction_response(
            self,
            interaction_id: int,
            token: str,
            params: MultipartParameters,
    ):
        r = Route('POST', f"/interactions/{interaction_id}/{token}/callback")
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload)

    def edit_original_interaction_response(
            self,
            token: str,
            application_id: int,
            params: MultipartParameters
    ):
        r = Route('PATCH', f'/webhooks/{application_id}/{token}/messages/@original')
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload)

    def send_followup(
            self,
            token: str,
            application_id: int,
            params: MultipartParameters,
    ):
        r = Route('POST', f'/webhooks/{application_id}/{token}')
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload)

    def edit_followup(
            self,
            application_id: int,
            token: str,
            message_id: int,
            params: MultipartParameters
    ):
        r = Route('PATCH', f'/webhooks/{application_id}/{token}/messages/{message_id}')
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload)

    def get_original_interaction_response(self, token: str, application_id: int):
        r = Route('GET', f'/webhooks/{application_id}/{token}/messages/@original')
        return self.request(r)

    def get_followup_message(self, token: str, application_id: int, message_id: int):
        r = Route('GET', f'/webhooks/{application_id}/{token}/messages/{message_id}')
        return self.request(r)

    def delete_interaction_response(self, token: str, application_id: int, message_id: int = '@original'):
        r = Route('DELETE', f'/webhooks/{application_id}/{token}/messages/{message_id}')
        return self.request(r)

    def send_autocomplete_callback(self, token: str, interaction_id: int, choices: list):
        r = Route('POST', f'/interactions/{interaction_id}/{token}/callback')
        data = {'data': {'choices': choices}, 'type': 8}
        return self.request(r, json=data)

    # AutoMod management
    def get_automod_rules(self, guild_id: int):
        return self.request(Route('GET', '/guilds/{guild_id}/auto-moderation/rules', guild_id=guild_id))

    def get_automod_rule(self, guild_id: int, rule_id: int):
        return self.request(
            Route('GET', '/guilds/{guild_id}/auto-moderation/rules/{rule_id}', guild_id=guild_id, rule_id=rule_id)
            )

    def create_automod_rule(self, guild_id: int, data: dict, reason: str = None):
        r = Route('POST', '/guilds/{guild_id}/auto-moderation/rules', guild_id=guild_id)
        return self.request(r, json=data, reason=reason)

    def edit_automod_rule(self, guild_id: int, rule_id: int, fields: Dict[str, Any], reason: Optional[str] = None):
        r = Route('PATCH', '/guilds/{guild_id}/auto-moderation/rules/{rule_id}', guild_id=guild_id, rule_id=rule_id)
        return self.request(r, json=fields, reason=reason)

    def delete_automod_rule(self, guild_id: int, rule_id: int, reason: str = None):
        r = Route('DELETE', '/guilds/{guild_id}/auto-moderation/rules/{rule_id}', guild_id=guild_id, rule_id=rule_id)
        return self.request(r, reason=reason)

    # Onboarding management
    def get_guild_onboarding(self, guild_id: int) -> Response[guild.Onboarding]:
        return self.request(Route('GET', '/guilds/{guild_id}/onboarding', guild_id=guild_id))

    def edit_guild_onboarding(
            self,
            guild_id: int,
            *,
            prompts: Optional[List[guild.OnboardingPrompt]] = None,
            default_channel_ids: Optional[SnowflakeID] = None,
            enabled: Optional[bool] = None,
            mode: Optional[guild.OnboardingMode] = None,
            reason: Optional[str] = None
    ) -> Response[guild.Onboarding]:
        payload = {}

        if prompts is not None:
            payload['prompts'] = prompts

        if default_channel_ids is not None:
            payload['default_channel_ids'] = default_channel_ids

        if enabled is not None:
            payload['enabled'] = enabled

        if mode is not None:
            payload['mode'] = mode

        return self.request(
            Route('PUT', '/guilds/{guild_id}/onboarding', guild_id=guild_id),
            json=payload,
            reason=reason
        )

    # Misc
    def application_info(self):
        return self.request(Route('GET', '/oauth2/applications/@me'))

    def list_entitlements(
            self,
            application_id: int,
            *,
            limit: int = 100,
            user_id: int = MISSING,
            guild_id: int = MISSING,
            sku_ids: List[int] = MISSING,
            after: int = MISSING,
            before: int = MISSING,
            exclude_ended: int = False
    ) -> Response[List[monetization.Entitlement]]:
        params = {'limit': limit}

        if user_id is not MISSING:
            params['user_id'] = str(user_id)
        if guild_id is not MISSING:  # FIXME: Can both be passed at the same time? Consider using elif instead
            params['guild_id'] = str(guild_id)
        if sku_ids is not MISSING:
            params['sku_ids'] = [str(s) for s in sku_ids]
        if after is not MISSING:
            params['after'] = str(after)
        if before is not MISSING:  # FIXME: Can both be passed at the same time? Consider using elif instead
            params['before'] = str(before)
        if exclude_ended is not False:  # TODO: what is the api default value?
            params['exclude_ended'] = str(exclude_ended)

        r = Route('GET', '/applications/{application_id}/entitlements', application_id=application_id)
        return self.request(r, json=params)

    def create_test_entitlement(
            self,
            application_id: int,
            *,
            sku_id: int,
            owner_id: int,
            owner_type: int
    ) -> Response[monetization.TestEntitlement]:
        payload = {
            'sku_id': sku_id,
            'owner_id': owner_id,
            'owner_type': owner_type
        }
        r = Route('POST', '/applications/{application_id}/entitlements', application_id=application_id)
        return self.request(r, json=payload)

    def delete_test_entitlement(self, application_id: int, entitlement_id: int) -> Response[None]:
        r = Route(
            'DELETE',
            '/applications/{application_id}/entitlements/{entitlement_id}',
            application_id=application_id,
            entitlement_id=entitlement_id
        )
        return self.request(r)

    def consume_entitlement(self, application_id: int, entitlement_id: int) -> Response[None]:
        r = Route(
            'POST',
            '/applications/{application_id}/entitlements/{entitlement_id}/consume',
            application_id=application_id,
            entitlement_id=entitlement_id
        )
        return self.request(r)

    async def get_gateway(self, *, encoding='json', v=10, zlib=True):
        try:
            data = await self.request(Route('GET', '/gateway'))
        except HTTPException as exc:
            raise GatewayNotFound() from exc
        if zlib:
            value = '{0}?encoding={1}&v={2}&compress=zlib-stream'
        else:
            value = '{0}?encoding={1}&v={2}'
        return value.format(data['url'], encoding, v)

    async def get_bot_gateway(self, *, encoding='json', v=10, zlib=True):
        try:
            data = await self.request(Route('GET', '/gateway/bot'))
        except HTTPException as exc:
            raise GatewayNotFound() from exc

        if zlib:
            value = '{0}?encoding={1}&v={2}&compress=zlib-stream'
        else:
            value = '{0}?encoding={1}&v={2}'
        return data['shards'], value.format(data['url'], encoding, v)

    def get_voice_regions(self):
        return self.request(Route('GET', '/voice/regions'))

    def get_user(self, user_id: int):
        return self.request(Route('GET', '/users/{user_id}', user_id=user_id))

    def get_user_profile(self, user_id: int):
        return self.request(Route('GET', '/users/{user_id}/profile', user_id=user_id))

    def get_all_nitro_stickers(self):
        return self.request(Route('GET', '/sticker-packs'))
    