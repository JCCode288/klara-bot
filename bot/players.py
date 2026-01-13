from guild_player import GuildPlayer

class Players:
    def __init__(self, bot):
        self.bot = bot
        self._players = {}

    def get_player(self, ctx) -> GuildPlayer:
        guild = ctx.guild
        if guild.id not in self._players:
            self._players[guild.id] = GuildPlayer(guild, self.bot)

        return self._players[guild.id]

    def is_exists(self, guild_id):
        return guild_id in self._players
    
    def remove_player(self, ctx):
        guild = ctx.guild

        if guild.id in self._players:
            self._players.pop(guild.id)