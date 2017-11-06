"""
Cog that will print out various bot statistics
"""
from .utils import checks
import json
import discord
from discord.ext import commands


CARBONITEX_API_BOTDATA = 'https://www.carbonitex.net/discord/data/botdata.php'
DISCORD_BOTS_API = 'https://bots.discord.pw/api'


class Stats():
    """
    Simple bot statistics as well as server logging
    """
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def update(self):
        guild_count = len(self.bot.guilds)

        """ Comment this out because bot isn't on carbonitix
        carbon_payload = {
            'key': self.bot.carbon_key,
            'servercount': guild_count
        }

        async with self.bot.session.post(
                CARBONITEX_API_BOTDATA, data=carbon_payload) as resp:
            log.info(
                f'Carbon statistics returned {resp.status} for {carbon_payload}')
        """

        payload = json.dumps({
            'server_count': guild_count
        })

        headers = {
            'authorization': self.bot.discord_bots_key,
            'content-type': 'application/json'
        }

        url = f'{DISCORD_BOTS_API}/bots/{self.bot.user.id}/stats'
        async with self.bot.session.post(
                url, data=payload, headers=headers) as resp:
            self.bot.logger.info(
                f'DBots statistics returned {resp.status} for {payload}')

    async def on_guild_join(self, guild):
        """
        await self.update()
        """
        await self.bot.postgres_controller.add_server(guild.id)
        self.bot.server_settings = \
            await self.postgres_controller.get_server_settings()

    @commands.command()
    async def Stats(self):
        """
        Creates an embed with basic bot stats
        """
        return