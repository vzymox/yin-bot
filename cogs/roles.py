"""
Handling the auto assignable roles and such
"""

import discord
from discord import AuditLogAction
from discord.ext import commands
from .utils import checks
from datetime import datetime, timedelta


class Roles():
    """
    Cog to handle the ability of users to
    add roles to themselves through use of a command
    """

    def __init__(self, bot):
        """
        Init class
        """
        super().__init__()
        self.bot = bot

    @commands.command(aliases=['prunerole'])
    @commands.guild_only()
    @checks.has_permissions(manage_roles=True)
    async def cleanrole(self, ctx, role_name, lcl_hours=24):
        """
        Removes all members from a certain
        """
        safe_users = []
        found_role = None
        dt_24hr = datetime.utcnow() - timedelta(hours=lcl_hours)
        for role in ctx.guild.roles:
            if role.name.lower() == role_name.lower():
                found_role = role
        if not found_role:
            return
        audit_logs = await ctx.guild.audit_logs(
            after=dt_24hr,
            action=AuditLogAction.member_role_update
        )
        async for entry in audit_logs:
            if found_role in entry.after.roles:
                safe_users.append(entry.target)

    @commands.command()
    @commands.guild_only()
    async def iam(self, ctx, role_name):
        found_role = None
        users_roles = ctx.message.author.roles
        for role in ctx.guild.roles:
            if role.name.lower() == role_name.lower():
                found_role = role
        if found_role:
            for role in users_roles:
                if role == found_role:
                    local_embed = discord.Embed(
                        title=f'@{ctx.message.author}, you already have the '
                              f'**{found_role.name}** role',
                        description=' ',
                        color=0x651111
                    )
                    await ctx.send(embed=local_embed)
                    return
            assignable = await self.bot.postgres_controller.is_role_assignable(
                ctx.guild.id, found_role.id)
            if assignable:
                users_roles.append(found_role)
                try:
                    await ctx.author.edit(roles=users_roles)
                    local_embed = discord.Embed(
                        title=f'@{ctx.message.author}, you now have the'
                              f'**{found_role.name}** role',
                        description=' ',
                        color=0x419400
                    )
                except discord.Forbidden:
                    local_embed = discord.Embed(
                        title='I don\'t have the necessary permissions'
                              'to do this',
                        description=' ',
                        color=0x651111
                    )
            else:
                local_embed = discord.Embed(
                    title=f'**{found_role.name}** is not self-assignable',
                    description=' ',
                    color=0x651111
                )
        else:
            local_embed = discord.Embed(
                title=f'Couldn\'t find role {role_name}',
                description=' ',
                color=0x651111
            )
        await ctx.send(embed=local_embed)

    @commands.command()
    @commands.guild_only()
    async def iamnot(self, ctx, role_name):
        """
        Removes a role from the user
        """
        found_role = None
        users_roles = ctx.message.author.roles
        for role in users_roles:
            if role.name == role_name:
                found_role = role
        if not found_role:
            local_embed = discord.Embed(
                title=f'Role not removed:',
                description=f'You don\'t have the'
                f' **{role_name}** role already',
                color=0x651111
            )
            await ctx.send(embed=local_embed)
            return
        assignable_roles = await \
            self.bot.postgres_controller.get_assignable_roles(
                ctx.guild.id)
        if found_role.id in assignable_roles:
            users_roles.remove(found_role)
            local_embed = discord.Embed(
                title=f'Role removed:',
                description=f'You no longer have the '
                f'**{found_role.name}** role.',
                color=0x419400
            )
            await ctx.send(embed=local_embed, delete_after=5)
            await ctx.message.delete()
        else:
            local_embed = discord.Embed(
                title=f'Role not removed:',
                description=f'**{found_role.name}** is not a '
                'self-assignable role.',
                color=0x651111
            )
            await ctx.send(embed=local_embed)

    @commands.group(aliases=['ar'])
    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    async def assignableroles(self, ctx):
        """
        manages servers assignable roles
        """
        if ctx.invoked_subcommand is None:
            message = ' \n'
            assignable_roles = []
            assignable_role_ids = await \
                self.bot.postgres_controller.get_assignable_roles(ctx.guild.id)
            for role in ctx.guild.roles:
                if role.id in assignable_role_ids:
                    assignable_roles.append(role)
            for role in assignable_roles:
                message += f'{role.name}\n'
            local_embed = discord.Embed(
                title='Current self-assignable roles:',
                description=message,
                color=0x419400
            )
            await ctx.send(embed=local_embed)

    @assignableroles.command()
    async def add(self, ctx, role_name):
        """
        Adds a role to the servers assignable roles list
        """
        found_role = None
        for role in ctx.guild.roles:
            if role.name.lower() == role_name.lower():
                found_role = role
        if found_role:
            if not ctx.message.author.\
                    top_role >= found_role:
                local_embed = discord.Embed(
                    title=f'You can\'t add a role that is a higher '
                          'level than your highest role',
                    description=' ',
                    color=0x651111
                )
                await ctx.send(embed=local_embed)
                return
            success = await self.bot.postgres_controller.add_assignable_role(
                ctx.guild.id, found_role.id, self.bot.logger)
            if success:
                local_embed = discord.Embed(
                    title=f'Added {found_role.name} to self-assignable roles',
                    description=' ',
                    color=0x419400
                )
            else:
                local_embed = discord.Embed(
                    title=f'Internal error when adding {found_role.name} to '
                          'self-assignable roles, contact @dashwav#7785',
                    description=' ',
                    color=0x651111
                )
        else:
            local_embed = discord.Embed(
                title=f'Couldn\'t find role {role_name}',
                description=' ',
                color=0x651111
            )
        await ctx.send(embed=local_embed)

    @assignableroles.command()
    async def remove(self, ctx, role_name):
        """
        Removes a role from the serves assignable roles list
        """
        found_role = None
        for role in ctx.guild.roles:
            if role.name.lower() == role_name.lower():
                found_role = role
        if found_role:
            try:
                success = await \
                    self.bot.postgres_controller.remove_assignable_role(
                        ctx.guild.id, found_role.id, self.bot.logger)
            except ValueError:
                local_embed = discord.Embed(
                    title=f'{found_role.name} is already'
                          ' not on the self-assignable list',
                    description=' ',
                    color=0x651111
                )
                await ctx.send(embed=local_embed)
                return
            if success:
                local_embed = discord.Embed(
                    title=f'Removed {found_role.name} '
                          'from self-assignable roles',
                    description=' ',
                    color=0x419400
                )
            else:
                local_embed = discord.Embed(
                    title=f'Internal error occured,'
                          ' please contact @dashwav#7785',
                    description=' ',
                    color=0x651111
                )
            await ctx.send(embed=local_embed)
        else:
            local_embed = discord.Embed(
                title=f'Couldn\'t find role {role_name}',
                description=' ',
                color=0x651111
            )
            await ctx.send(embed=local_embed)