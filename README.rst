.. |flag_ua| image:: ./images/flag_ua.png
   :alt: Ukraine
   :width: 30px
   :height: 30px
   :scale: 100%

|flag_ua| Welcome to discord.py-message-components'! |flag_ua|
==============================================================

.. figure:: https://cdn.discordapp.com/attachments/852872100073963532/854711446767796286/discord.py-message-components.png
   :name: discord.py-message-components
   :align: center
   :alt: Name of the Project (discord.py-message-components)

   ..
   .. image:: https://discord.com/api/guilds/852871920411475968/embed.png
      :target: https://discord.gg/sb69muSqsg
      :alt: Discord Server Invite

   .. image:: https://img.shields.io/pypi/v/discord.py-message-components.svg
      :target: https://pypi.python.org/pypi/discord.py-message-components
      :alt: PyPI version info

   .. image:: https://img.shields.io/pypi/pyversions/discord.py-message-components.svg
      :target: https://pypi.python.org/pypi/discord.py-message-components
      :alt: PyPI supported Python versions

   .. image:: https://static.pepy.tech/personalized-badge/discord-py-message-components?period=total&units=international_system&left_color=grey&right_color=green&left_text=Downloads
      :target: https://pepy.tech/project/discord.py-message-components
      :alt: Total downloads for the project

   .. image:: https://readthedocs.org/projects/discordpy-message-components/badge/?version=developer
      :target: https://discordpy-message-components.readthedocs.io/en/developer/
      :alt: Documentation Status

   .. image:: https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86
       :target: https://github.com/sponsors/mccoderpy
       :alt: Sponsor button

   A "fork" of `discord.py <https://pypi.org/project/discord.py/1.7.3>`_ library made by `Rapptz <https://github.com/Rapptz>`_ with implementation of the `Discord-Message-Components <https://discord.com/developers/docs/interactions/message-components>`_ & many other features by `mccoderpy <https://github.com/mccoderpy/>`_

**NOTE:**
     This library will be further developed independently of discord.py.
     New features are also implemented. It's not an extension!
     The name only comes from the fact that the original purpose of the library was to add support for message components and we haven't found a better one yet.

**❗Some of the new features may be only documented in code currently❗**

.. figure:: https://github.com/mccoderpy/discord.py-message-components/raw/main/images/rtd-logo-wordmark-light.png
   :name: discord.py-message-components documentation
   :alt: Link to the documentation of discord.py-message-components
   :align: center
   :scale: 20%
   :target: https://discordpy-message-components.readthedocs.io/en/developer/

   **Read the** `Documentation here <https://discordpy-message-components.readthedocs.io/en/developer/>`_

You need help? Or have ideas/feedback?
______________________________________

Open a Issue/Pull request on `GitHub <https://github.com/mccoderpy/discord.py-message-components/pulls>`_, join the `support-server <https://discord.gg/sb69muSqsg>`_ or send me a direct-message on `Discord <https://discord.com/channels/@me>`_: ``mccuber04#2960``

Installing
__________

**Python 3.5.3 or higher is required**

This library overwrite the original `discord.py <https://pypi.org/project/discord.py/1.7.3>`_ library (or any other that would be imported using `import discord`) so to be sure all will work fine
first uninstall the original discord.py Library if it is installed:

.. code:: sh

    # Linux/macOS
    python3 -m pip uninstall discord.py

    # Windows
    py -3 -m pip uninstall discord.py

Then install `this library <https://pypi.org/project/discord.py-message-components>`_ using:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U discord.py-message-components

    # Windows
    py -3 -m pip install -U discord.py-message-components

-----------------------------------------

‼️To install it from the `developer-branch <https://github.com/mccoderpy/discord.py-message-components/tree/developer>`_ of this library which is the **most up to date** and has **fewer bugs** use:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U git+https://github.com/mccoderpy/discord.py-message-components.git@developer

    # Windows
    py -m pip install -U git+https://github.com/mccoderpy/discord.py-message-components.git@developer 

Of curse you need to have git installed on your device. If you need help with this take a look `here <https://github.com/git-guides/install-git>`_

Examples
________

**ℹFor more examples take a look in the** `examples <https://github.com/mccoderpy/discord.py-message-components/tree/developer/examples>`_ **folder.**


.. note::

   All of these examples are not inside `Cogs <https://discordpy.readthedocs.io/en/v1.7.3/ext/commands/cogs.html>`_.
   To use them inside of Cogs you must replace the ``client`` in the `decorators <https://wiki.python.org/moin/PythonDecorators#What_is_a_Decorator>`_ with ``commands.Cog``, set ``self`` as the first argument inside the functions and replace any use of ``client`` (except inside the decorators) with your bot variable.(e.g. ``self.bot`` or ``self.client``)

Application Command Examples
++++++++++++++++++++++++++++


+---------------------------------------------------------------------------------------------------+
|   `sync_commands` of your `discord.Client` instance must bee set to `True`                        |
|   Otherwise these commands will not be registered to discord and so not usable.                   |
+---------------------------------------------------------------------------------------------------+

A Slash-Command(Chat-Input) which with that you can see the welcome screen of your guild and add new channels to it.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import discord
    from discord import SlashCommandOption as CommandOption, Permissions

    client = discord.Client(sync_commands=True)

    @client.slash_command(
        base_name='welcome-screen',
        base_desc='Shows or edit the welcome-screen of this guild.',
        name='show',
        guild_ids=[852871920411475968],
        default_required_permissions=Permissions(manage_guild=True) # Only Members with Manage Guild Permission can use (see) this command and it sub-commands
    )
    async def show_welcome_screen(interaction: discord.ApplicationCommandInteraction):
        """Shows the welcome-screen of this guild."""
        w_c = await interaction.guild.welcome_screen()
        if w_c:
            wc_embed = discord.Embed(title=f'Welcome screen for {interaction.guild}',
                                     description=f'```\n'
                                                 f'{w_c.description or "No Description set"}\n'
                                                 f'```')
            for channel in w_c.welcome_channels:
                wc_embed.add_field(name=channel.description,
                                   value=f'{str(channel.emoji) if channel.emoji else ""} {channel.channel.mention}',
                                   inline=False)
            await interaction.respond(embed=wc_embed)
        else:
            await interaction.respond('This guild has no welcome-screen set.', hidden=True)

    @client.slash_command(
        base_name='welcome-screen',
        base_desc='Shows or edit the welcome-screen of this guild.',
        group_name='edit',
        group_desc='Edit the welcome-screen of this guild.',
        name='add-channel',
        options=[
            CommandOption(
                option_type=discord.OptionType.channel,
                name='channel',
                description='The channel which the the welcome screen field goes to.',
                channel_types=[discord.TextChannel]),
            CommandOption(
                option_type=str,
                name='description',
                description='The description for the welcome screen field.'
            ),
            CommandOption(
                option_type=str,
                name='emoji',
                description='The emoji which shows in front of the channel.',
                required=False
            )
        ],
        guild_ids=[852871920411475968]
    )
    async def add_welcome_screen_channel(i: discord.ApplicationCommandInteraction, channel: discord.TextChannel, description: str, emoji: str = None):
        """Add a channel to the welcome-screen of this guild."""
        welcome_screen = await i.guild.welcome_screen()
        if emoji:
            try:
                emoji = discord.PartialEmoji.from_string(emoji)
            except ValueError:
                pass

        if len(welcome_screen.welcome_channels) == 5:
            return await i.respond('The maximum of welcome-screen channels is reached, you can\'t add more.')
        channels = welcome_screen.welcome_channels.copy()
        channels.append(discord.WelcomeScreenChannel(channel=channel, description=description, emoji=emoji))
        edited = await welcome_screen.edit(welcome_channels=channels, reason=f'{i.author} used the add-channel command')
        wc_embed = discord.Embed(
            title=f'The welcome-screen of {i.guild} is now:',
            description=f'```\n'
                        f'{emoji} {edited.description or "No Description set"}\n'
                        f'```'
        )

        for w_channel in edited.welcome_channels:
            wc_embed.add_field(
                name=w_channel.description,
                value=f'{str(w_channel.emoji) if w_channel.emoji else ""} {w_channel.channel.mention}',
                inline=False
            )

        await i.respond(embed=wc_embed)

    client.run('Your Bot-Token here')

A Message Command that translate the corresponding Message in to the invokers locale language
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import discord
    import asyncio
    import translators # need to be installed using "py -m pip install translators" (Win) or "python3 -m pip install translators" (Linux/macOS)
    from io import BytesIO

    client = discord.Client(sync_commands=True)


    @client.message_command(guild_ids=[852871920411475968]) # replace the guild id with your own or remove the parameter to make the command global
    async def translate(self, interaction: discord.ApplicationCommandInteraction, message):
       await interaction.defer(hidden=True)
       translated = await asyncio.to_thread(
           translators.google,
           query_text=message.content,
           to_language=interaction.author_locale.value,
           sleep_seconds=4
       )
       if len(translated) > 2000:
           # Message was send by a Nitro user which can send messages with up to 4000 characters.
           # As we can't do this sent it as a file instead.
           new_file = io.BytesIO()
           file = new_file.write(translated)
           return await interaction.respond(file=discord.File(file, filename=f'{interaction.id}_translated.txt'), hidden=True)

    client.run('Your Bot-Token here')

A User context-menu command which shows you information about the corresponding user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: python

    import discord

    client = discord.Client(sync_commands=True)

    @client.user_command(guild_ids=[852871920411475968])
    async def userinfo(interaction: discord.ApplicationCommandInteraction, member: discord.Member):
        _roles = member.roles.copy()
        _roles.remove(member.guild.default_role) # skipp @everyone
        _roles.reverse()

        embed = discord.Embed(
            title=f'Userinfo for {member}',
            description=f'This is a Userinfo for {member.mention}.',
            timestamp=datetime.utcnow(),
            color=member.color
            )

        to_add = [
            ('Name:', member.name, True),
            ('Tag:', member.discriminator, True),
            ('User-ID:', member.id, True),
            ('Nitro:', '✅ Yes' if member.premium_since else '❔ Unknown', True),
            ('Nick:', member.nick, True),
            ('Created-at:', discord.utils.styled_timestamp(member.created_at, 'R'), True),
            ('Joined at', discord.utils.styled_timestamp(member.joined_at, 'R'), True)
        ]
        if member.premium_since:
            to_add.append(('Premium since:', discord.utils.styled_timestamp(member.premium_since, 'R'), True))
        try:
            roles_list = f'{_roles.pop(0)}'
        except IndexError: # The Member don't has any roles
            roles_list = '`None`'
        else:
            for role in _roles:
                updated = f'{roles_list}, {role.mention}'
                if updated > 1024:
                    roles_list = updated
                else:
                    break
        to_add.append((f'Roles: {len(member.roles) - 1}', roles_list, True))

        for name, value, inline in to_add:
            embed.add_field(name=name, value=value, inline=inline)

        embed.set_author(name=member.display_name, icon_url=member.display_avatar_url, url=f'https://discord.com/users/{member.id}')
        embed.set_footer(text=f'Requested by {interaction.author}', icon_url=interaction.author.display_avatar_url)
        if not member.bot:
            user = await client.fetch_user(member.id) # to get the banner data we need to fetch the user
            if user.banner:
                embed.add_field(name='Banner', value=f'See the [banner]({user.banner_url}) below', inline=False)
            else:
                embed.add_field(name='Banner Color', value=f'See the [banner-color](https://serux.pro/rendercolour?hex={hex(user.banner_color.value).replace("0x", "")}?width=500) below', inline=False)
            if user.banner:
                embed.set_image(url=user.banner_url)
            else:
                embed.set_image(url=f'https://serux.pro/rendercolour?hex={hex(user.banner_color.value).replace("0x", "")}&width=500')
        await interaction.respond(embed=embed, hidden=True)

    client.run('Your Bot-Token here')

Buttons
+++++++

A Command that sends you a Message and edit it when you click a Button:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import typing
    import discord
    from discord.ext import commands
    from discord import ActionRow, Button, ButtonStyle

    client = commands.Bot(command_prefix=commands.when_mentioned_or('.!'), intents=discord.Intents.all(), case_insensitive=True)

    @client.command(name='buttons', description='sends you some nice Buttons')
    async def buttons(ctx: commands.Context):
        components = [ActionRow(Button(label='Option Nr.1',
                                       custom_id='option1',
                                       emoji="🆒",
                                       style=ButtonStyle.green
                                       ),
                                Button(label='Option Nr.2',
                                       custom_id='option2',
                                       emoji="🆗",
                                       style=ButtonStyle.blurple)),
                      ActionRow(Button(label='A Other Row',
                                       custom_id='sec_row_1st option',
                                       style=ButtonStyle.red,
                                       emoji='😀'),
                                Button(url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                       label="This is an Link",
                                       style=ButtonStyle.url,
                                       emoji='🎬'))
                      ]
        an_embed = discord.Embed(title='Here are some Button\'s', description='Choose an option', color=discord.Color.random())
        msg = await ctx.send(embed=an_embed, components=components)

        def _check(i: discord.Interaction, b):
            return i.message == msg and i.member == ctx.author

        interaction, button = await client.wait_for('button_click', check=_check)
        button_id = button.custom_id

        # This sends the Discord-API that the interaction has been received and is being "processed"
        await interaction.defer()
        # if this is not used and you also do not edit the message within 3 seconds as described below,
        # Discord will indicate that the interaction has failed.

        # If you use interaction.edit instead of interaction.message.edit, you do not have to defer the interaction,
        # if your response does not last longer than 3 seconds.
        await interaction.edit(embed=an_embed.add_field(name='Choose', value=f'Your Choose was `{button_id}`'),
                               components=[components[0].disable_all_buttons(), components[1].disable_all_buttons()])

        # The Discord API doesn't send an event when you press a link button so we can't "receive" that.


    client.run('Your Bot-Token here')


Another (complex) Example where a small Embed will be send; you can move a small white ⬜ with the Buttons:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    pointers = []


    class Pointer:
        def __init__(self, guild: discord.Guild):
            self.guild = guild
            self._position_x = 0
            self._position_y = 0

        @property
        def position_x(self):
            return self._position_x

        def set_x(self, x: int):
            self._position_x += x
            return self._position_x

        @property
        def position_y(self):
            return self._position_y

        def set_y(self, y: int):
            self._position_y += y
            return self._position_y


    def get_pointer(obj: typing.Union[discord.Guild, int]):
        if isinstance(obj, discord.Guild):
            for p in pointers:
                if p.guild.id == obj.id:
                    return p
            pointers.append(Pointer(obj))
            return get_pointer(obj)

        elif isinstance(obj, int):
            for p in pointers:
                if p.guild.id == obj:
                    return p
            guild = client.get_guild(obj)
            if guild:
                pointers.append(Pointer(guild))
                return get_pointer(guild)
            return None


    def display(x: int, y: int):
        base = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ]
        base[y][x] = 1
        base.reverse()
        return ''.join(f"\n{''.join([str(base[i][w]) for w in range(len(base[i]))]).replace('0', '⬛').replace('1', '⬜')}" for i in range(len(base)))


    empty_button = discord.Button(style=discord.ButtonStyle.Secondary, label=" ", custom_id="empty", disabled=True)


    def arrow_button():
        return discord.Button(style=discord.ButtonStyle.Primary)


    @client.command(name="start_game")
    async def start_game(ctx: commands.Context):
        pointer: Pointer = get_pointer(ctx.guild)
        await ctx.send(embed=discord.Embed(title="Little Game",
                                           description=display(x=0, y=0)),
                       components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up'), empty_button),
                                   discord.ActionRow(arrow_button().update(disabled=True).set_label('←').set_custom_id('left').disable_if(pointer.position_x <= 0),
                                                     arrow_button().set_label('↓').set_custom_id('down').disable_if(pointer.position_y <= 0),
                                                     arrow_button().set_label('→').set_custom_id('right'))
                                   ]
                       )


    @client.on_click()
    async def up(i: discord.Interaction, button):
        pointer: Pointer = get_pointer(interaction.guild)
        pointer.set_y(1)
        await i.edit(embed=discord.Embed(title="Little Game",
                                         description=display(x=pointer.position_x, y=pointer.position_y)),
                               components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up').disable_if(pointer.position_y >= 9), empty_button),
                                           discord.ActionRow(arrow_button().set_label('←').set_custom_id('left').disable_if(pointer.position_x <= 0),
                                                             arrow_button().set_label('↓').set_custom_id('down'),
                                                             arrow_button().set_label('→').set_custom_id('right').disable_if(pointer.position_x >= 9))]
                               )

    @client.on_click()
    async def down(i: discord.Interaction, button):
        pointer: Pointer = get_pointer(interaction.guild)
        pointer.set_y(-1)
        await i.edit(embed=discord.Embed(title="Little Game",
                                              description=display(x=pointer.position_x, y=pointer.position_y)),
                               components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up'), empty_button),
                                           discord.ActionRow(arrow_button().set_label('←').set_custom_id('left').disable_if(pointer.position_x <= 0),
                                                             arrow_button().set_label('↓').set_custom_id('down').disable_if(pointer.position_y <= 0),
                                                             arrow_button().set_label('→').set_custom_id('right').disable_if(pointer.position_x >= 9))]
                               )

    @client.on_click()
    async def right(i: discord.Interaction, button):
        pointer: Pointer = get_pointer(interaction.guild)
        pointer.set_x(1)
        await i.edit(embed=discord.Embed(title="Little Game",
                                               description=display(x=pointer.position_x, y=pointer.position_y)),
                               components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up'), empty_button),
                                           discord.ActionRow(arrow_button().set_label('←').set_custom_id('left'),
                                                             arrow_button().set_label('↓').set_custom_id('down'),
                                                             arrow_button().set_label('→').set_custom_id('right').disable_if(pointer.position_x >= 9))]
                               )

    @client.on_click()
    async def left(i: discord.Interaction, button):
        pointer: Pointer = get_pointer(interaction.guild)
        pointer.set_x(-1)
        await i.edit(embed=discord.Embed(title="Little Game",
                                               description=display(x=pointer.position_x, y=pointer.position_y)),
                               components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up'), empty_button),
                                           discord.ActionRow(arrow_button().set_label('←').set_custom_id('left').disable_if(pointer.position_x <= 0),
                                                             arrow_button().set_label('↓').set_custom_id('down'),
                                                             arrow_button().set_label('→').set_custom_id('right'))]
                               )

Select Menu & Modal (TextInput)
+++++++++++++++++++++++++++++++

Sending-SelectMenu's and respond to them
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: python

   import discord
   from discord.ext import commands
   from discord import Button, SelectMenu, SelectOption


   client = commands.Bot(command_prefix=commands.when_mentioned_or('!'))


   @client.command()
   async def select(ctx):
      msg_with_selects = await ctx.send('Hey here is an nice Select-Menu', components=[
         [
               SelectMenu(custom_id='_select_it', options=[
                  SelectOption(emoji='1️⃣', label='Option Nr° 1', value='1', description='The first option'),
                  SelectOption(emoji='2️⃣', label='Option Nr° 2', value='2', description='The second option'),
                  SelectOption(emoji='3️⃣', label='Option Nr° 3', value='3', description='The third option'),
                  SelectOption(emoji='4️⃣', label='Option Nr° 4', value='4', description='The fourth option')],
                        placeholder='Select some Options', max_values=3)
            ]])

      def check_selection(i: discord.Interaction, select_menu):
         return i.author == ctx.author and i.message == msg_with_selects

      interaction, select_menu = await client.wait_for('selection_select', check=check_selection)

      embed = discord.Embed(title='You have chosen:',
                           description=f"You have chosen "+'\n'.join([f'\nOption Nr° {o}' for o in select_menu.values]),
                           color=discord.Color.random())
      await interaction.respond(embed=embed)

   client.run('Your Bot-Token')

A Select Menu that shows you the different response-types for an interaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import asyncio
    import discord
    from discord.ext import commands
    from discord import Modal, TextInput
    from discord import ActionRow, SelectMenu, SelectOption, Modal, TextInput

    client = commands.Bot('!')


    @client.command()
    async def interaction_types(ctx):
        components = [ActionRow(
            SelectMenu(
                custom_id='interaction_types_example',
                placeholder='Select a interaction response type to show.',
                options=
                [
                    SelectOption('msg_with_source', '4', 'Respond with a message', '4️⃣'),
                    SelectOption('deferred_msg_with_source', '5', 'ACK an interaction[...]; user sees a loading state', '5️⃣'),
                    SelectOption('deferred_update_msg', '6', 'ACK an interaction[...]; no loading state', '6️⃣'),
                    SelectOption('update_msg', '7', 'Edit the message the component was attached to', '7️⃣'),
                    SelectOption('show_modal', '9', 'Respond to the interaction by sending a popup modal', '9️⃣')
                ]
            )
        )]

        embed = discord.Embed(title='Interaction Callback Type', description='These are all interaction-callback-types you could use for slash-commands and message-components:', color=discord.Color.green())
        await ctx.send(embed=embed, components=components)

    @client.on_select()
    async def interaction_types_example(i: discord.ComponentInteraction, s):
        _type = s.values[0]
        if _type == 4:
            await i.respond('This is of type `4`')
        elif _type == 5:
            await i.defer(5)
            await asyncio.sleep(5)
            await i.respond('Yes this is of type `5`')
        elif _type == 6:
            await i.defer()
            await asyncio.sleep(5)
            await i.edit(embeds=[i.message.embeds[0], discord.Embed(title='This is of type `6`')])
        elif _type == 7:
            msg = await i.edit(embed=i.message.embeds[0].add_field(name=i.author, value='This is of type `7`'))
            await asyncio.sleep(5)
            msg.embeds[0].clear_fields()
            await i.message.edit(embed=msg.embeds[0])
        elif _type == 9:
            await i.respond_with_modal(
                Modal(
                title='This is of type 9',
                custom_id='response_types_example_modal',
                components=[
                    TextInput(
                        style=1,
                        label='This is a short(single-line) input',
                        placeholder='Enter something in here.',
                        custom_id='short_input'
                    ),
                    TextInput(
                        style=2,
                        label='This is a long(multi-line) input',
                        placeholder='Enter something longer in here.',
                        custom_id='long_input'
                    )
                ]
            )
        )
        modal_interaction: discord.ModalSubmitInteraction = await client.wait_for('modal_submit', check=lambda mi: mi.author == i.author)
        embed = discord.Embed(title='This was response type 9', color=discord.Color.green())
        embed.add_field(
            name='Content of short input:',
            value=modal_interaction.get_field('short_input').value,
            inline=False
        )
        embed.add_field(
            name='Content of long input:',
            value=modal_interaction.get_field('long_input').value,
            inline=False
        )

        await modal_interaction.respond(embed=embed)


    client.run('Your Bot-Token here')


Take a look at `the documentation <https://discordpy-message-components.readthedocs.io/en/developer/>`_ to see more examples.

.. figure:: https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2Fmccoderpy%2Fdiscord.py-message-components%2Ftree%2Fdeveloper%2F&countColor=%23263759&style=flat
      :alt: Number(As image) how often this WebSite was visited
      :align: center
      :name: Visitor count
