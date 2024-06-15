import asyncio
from datetime import datetime
from typing import Optional, List

import discord
from discord import SlashCommandOption as Option, Localizations, Permissions, ApplicationCommandInteraction as APPCI
from discord.ext import commands


# The examples for using localizations are german in this case because it is my native language. Of curse you can add your native language too
class ClearCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.slash_command(
        name='clear',
        description='Deletes the last x messages in the chat.',
        description_localizations=Localizations(german='Löscht die letzten x Nachrichten im Chat.'),
        default_required_permissions=Permissions(manage_messages=True),
        options=[
            Option(
                option_type=int,
                name='count',
                description='The number (x) of messages that should be deleted.',
                description_localizations=Localizations(german='Wie viele (x) Nachrichten gelöscht werden sollen.'),
                max_value=100,
                min_value=2
            ),
            Option(
                option_type=discord.Member,
                name='member',
                description='The member which last x messages should be deleted.',
                description_localizations=Localizations(
                    german='Der Member dessen letzten x Nachrichten gelöscht werden sollen.'),
                required=False
            ),
            Option(
                option_type=str,
                name='members',
                description='Separated by a , the member which last x messages should be deleted. Separated by a ,',
                description_localizations=Localizations(
                    german='Per , getrennt, die Member deren letzten x Nachrichten gelöscht werden sollen.'),
                required=False,
                converter=commands.Greedy[discord.Member]
            ),
            Option(
                option_type=str,
                name='before',
                name_localizations=Localizations(german='vor'),
                description='If specified, the last x messages before this message are deleted.',
                description_localizations=Localizations(
                    german='Wenn angegeben werden die letzten x Nachrichten nach dieser Nachricht gelöscht.'
                ),
                required=False,
                converter=commands.MessageConverter
            ),
            Option(
                option_type=str,
                name='after',
                name_localizations=Localizations(german='nach'),
                description='If specified, the last x messages after this message are deleted.',
                description_localizations=Localizations(
                    german='Wenn angegeben werden die letzten x Nachrichten vor dieser Nachricht gelöscht.'
                ),
                required=False,
                converter=commands.MessageConverter
            ),
            Option(
                option_type=str,
                name='reason',
                name_localizations=Localizations(german='grund'),
                description='The reason for deleting message are deleted.',
                description_localizations=Localizations(
                    german='Der Grund warum die Nachrichten gelöscht werden.'
                ),
                required=False,
            )

        ],
        guild_ids=[977326610334228502])
    async def clear(self,
                    ctx: APPCI,
                    count: int,
                    member: discord.Member = None,
                    members: Optional[List[discord.Member]] = [],
                    before: discord.Message = None,
                    after: discord.Message = None,
                    reason: str = None,
                    around: discord.Message = None):
        if not ctx.author.permissions_in(ctx.channel).manage_messages:
            return
        if members and len(members) == 1 and member == members[0]:
            member = members[0]
        question = await ctx.respond(
            embed=discord.Embed(
                title=f"deleting messages",
                description=f'[{ctx.author.mention}]\n are you sure to delete the'
                            f' last {count} messages {f"from {member.mention}" if member else (f"{len(members)} members" if members else "in this Channel")}?',
                color=discord.Color.red()),
            components=[
                [
                    discord.Button(
                        label="Yes",
                        emoji="✅",
                        style=discord.ButtonColor.green,
                        custom_id="Yes"
                    ),
                    discord.Button(
                        label="No",
                        emoji="❌",
                        style=discord.ButtonColor.red,
                        custom_id="No"
                    )
                ]
            ]
        )

        def check(i: discord.ComponentInteraction, b: discord.Button):
            return i.message.id == question.id and i.author.id == ctx.author.id

        try:
            i, b = await self.bot.wait_for("button_click", check=check, timeout=10)
            await i.defer()
            if b.custom_id == 'Yes':
                await question.delete()

                def check(m: discord.Message):
                    if member:
                        if m.author.id == member.id:
                            return True
                    else:
                        if members:
                            if m.author in members:
                                return True
                        else:
                            return True

                deleted = await ctx.channel.purge(limit=count, check=check, before=before, after=after,
                                                  around=around)
                deleted_from = []
                for m in deleted:
                    if m.author not in deleted_from:
                        deleted_from.append(m.author)
                m_count = len(deleted_from)
                embed = discord.Embed(
                    description=f'Deleted `{len(deleted)}` messages from {m_count} member{"s" if m_count > 1 else ""}| {discord.utils.styled_timestamp(datetime.now(), "R")}',
                    color=discord.Color.green()
                )
                if reason:
                    embed.add_field(name='Reason:', value=f'```\n{reason}\n```', inline=False)
                embed.add_field(
                    name='Deleted messages from:',
                    value=', '.join([m.mention for m in deleted_from])
                )
                await i.channel.send(embed=embed)
            else:
                await question.delete()
        except asyncio.TimeoutError:
            await question.delete()


def setup(bot):
    bot.add_cog(ClearCommand(bot))
