"""
This cog will handle logging all server actions to a specific channel
"""
import discord
from discord.ext import commands
from .utils import checks
from .utils import embeds


class Logging():

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    @commands.group()
    @commands.guild_only()
    @checks.is_admin()
    async def logging(self, ctx):
        """
        Either returns current prefix or sets new one
        """
        if ctx.invoked_subcommand is None:
            desc = ''
            modlogs = await self.bot.postgres_controller.get_logger_channels(
                ctx.guild.id)
            for channel in ctx.guild.channels:
                if channel.id in modlogs:
                    desc += f'{channel.name} \n'
            local_embed = discord.Embed(
                title=f'Current log channel list is: ',
                description=desc,
                color=0x419400
            )
            await ctx.send(embed=local_embed)

    @logging.command()
    async def add(self, ctx, *, channels):
        """
        sets the prefix for the server
        """
        added_channels = []
        desc = ''
        channel_mentions = ctx.message.channel_mentions
        if not channel_mentions:
            local_embed = discord.Embed(
                title=f'No channel mentions detected, try again.',
                description=' ',
                color=0x651111
            )
            await ctx.send(embed=local_embed)
            return
        try:
            for channel in channel_mentions:
                success = await \
                    self.bot.postgres_controller.add_logger_channel(
                        ctx.guild.id, channel.id, self.bot.logger
                    )
                if success:
                    added_channels.append(channel.name)
            if added_channels:
                for channel in added_channels:
                    desc += f'{channel} \n'
                local_embed = discord.Embed(
                    title=f'Channels added to log channel list:',
                    description=desc,
                    color=0x419400
                )
                self.bot.server_settings[ctx.guild.id]['logging_enabled'] = True
            else:
                local_embed = discord.Embed(
                    title=f'Internal error, please contact @dashwav#7785',
                    description=' ',
                    color=0x651111
                )
            await ctx.send(embed=local_embed)
        except Exception as e:
            self.bot.logger.info(f'Error adding channels {e}')
            local_embed = discord.Embed(
                title=f'Internal issue, please contact @dashwav#7785',
                description=' ',
                color=0x651111
            )
            await ctx.send(embed=local_embed)

    @logging.command(aliases=['rem'])
    async def remove(self, ctx, *, channels):
        """
        Removes a channel from the modlog list
        """
        removed_channels = []
        absent_channels = []
        desc = ''
        channel_mentions = ctx.message.channel_mentions
        if not channel_mentions:
            local_embed = discord.Embed(
                title=f'No channel mentions detected, try again.',
                description=' ',
                color=0x651111
            )
            await ctx.send(embed=local_embed)
            return
        try:
            for channel in channel_mentions:
                try:
                    success = False
                    success = await \
                        self.bot.postgres_controller.rem_logger_channel(
                            ctx.guild.id, channel.id, self.bot.logger
                        )
                except ValueError as e:
                    absent_channels.append(channel.name)
                if success:
                    removed_channels.append(channel.name)
            if removed_channels:
                for channel in removed_channels:
                    desc += f'{channel} \n'
                local_embed = discord.Embed(
                    title=f'Channels removed from log channel list:',
                    description=desc,
                    color=0x419400
                )
                logs = await self.bot.postgres_controller.get_logger_channels(
                    ctx.guild.id)
                if not logs:
                    self.bot.server_settings[ctx.guild.id]['logging_enabled']\
                        = False
                if absent_channels:
                    desc = ''
                    for channel in absent_channels:
                        desc += f'{channel}\n'
                    local_embed.add_field(
                        name='Channels not in log channel list :',
                        value=desc
                    )
            elif absent_channels:
                desc = ''
                for channel in absent_channels:
                    desc += f'{channel}\n'
                local_embed = discord.Embed(
                    title=f'Channels not in log channel list: ',
                    description=desc,
                    color=0x651111
                )
            else:
                local_embed = discord.Embed(
                    title=f'Internal error, please contact @dashwav#7785',
                    description=' ',
                    color=0x651111
                )
            await ctx.send(embed=local_embed)
        except Exception as e:
            self.bot.logger.warning(f'Issue: {e}')
            local_embed = discord.Embed(
                title=f'Internal issue, please contact @dashwav#7785',
                description=' ',
                color=0x651111
            )
            await ctx.send(embed=local_embed)

    async def on_member_join(self, member):
        """
        Sends message on a user join
        """
        if self.bot.server_settings[member.guild.id]['logging_enabled']:
            channels = await self.bot.postgres_controller.get_logger_channels(
                member.guild.id)
            local_embed = embeds.JoinEmbed(member)
            for channel in channels:
                ch = self.bot.get_channel(channel)
                await ch.send(embed=local_embed)

    async def on_member_remove(self, member):
        """
        Sends message on a user leaving
        """
        if self.bot.server_settings[member.guild.id]['logging_enabled']:
            channels = await self.bot.postgres_controller.get_logger_channels(
                member.guild.id)
            local_embed = embeds.LeaveEmbed(member)
            for channel in channels:
                ch = self.bot.get_channel(channel)
                await ch.send(embed=local_embed)

    async def on_message_edit(self, before, after):
        """
        sends message on a user editing messages
        """
        if self.bot.server_settings[before.guild.id]['logging_enabled']:
            if not before.content.strip() != after.content.strip():
                return
            channels = await self.bot.postgres_controller.get_logger_channels(
                before.guild.id)
            try:
                local_embed = embeds.MessageEditEmbed(
                    before.author,
                    before.channel.name,
                    before.content,
                    after.content
                )
                for channel in channels:
                    ch = self.bot.get_channel(channel)
                    await ch.send(embed=local_embed)
            except Exception as e:
                self.bot.logger.warning(f'Issue logging message edit: {e}')

    async def on_message_delete(self, message):
        """
        sends message on a user editing messages
        """
        if self.bot.server_settings[message.guild.id]['logging_enabled']:
            channels = await self.bot.postgres_controller.get_logger_channels(
                message.guild.id)
            try:
                local_embed = embeds.MessageDeleteEmbed(
                    message.author,
                    message.channel.name,
                    message.content,
                )
                for channel in channels:
                    ch = self.bot.get_channel(channel)
                    await ch.send(embed=local_embed)
            except Exception as e:
                self.bot.logger.warning(f'Issue logging message edit: {e}')

    async def on_member_update(self, before, after):
        """
        sends message on a user editing messages
        """
        if not self.bot.server_settings[before.guild.id]['logging_enabled']:
            return
        channels = await self.bot.postgres_controller.get_logger_channels(
                before.guild.id)
        if set(before.roles) < set(after.roles):
            self.bot.logger.info(f'1')
            for role in set(after.roles) - set(before.roles):
                local_embed = embeds.RoleAddEmbed(
                    after,
                    role.name
                )
                for channel in channels:
                    ch = self.bot.get_channel(channel)
                    await ch.send(embed=local_embed)
        elif set(after.roles) < set(before.roles):
            self.bot.logger.info(f'1')
            for role in set(before.roles) - set(after.roles):
                local_embed = embeds.RoleRemoveEmbed(
                    after,
                    role.name
                )
                for channel in channels:
                    ch = self.bot.get_channel(channel)
                    await ch.send(embed=local_embed)
        if before.name != after.name:
            local_embed = embeds.UsernameUpdateEmbed(
                after, before.name, after.name)
            for channel in channels:
                ch = self.bot.get_channel(channel)
                await ch.send(embed=local_embed)