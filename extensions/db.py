# Copyright © 2018–2019 lambda#0987
#
# CAPTAIN CAPSLOCK is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CAPTAIN CAPSLOCK is distributed in the hope that it will be fun,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with CAPTAIN CAPSLOCK.  If not, see <https://www.gnu.org/licenses/>.

import asyncpg
from discord.ext import commands

class Database(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def update_shout(self, message_id, content):
		try:
			await self.bot.pool.execute(
				'UPDATE shout SET content = $2 WHERE message = $1',
				message_id, content)
		except asyncpg.UniqueViolationError:
			# don't store duplicate shouts
			await self.bot.pool.execute('DELETE FROM shout WHERE message = $1', message_id)

	async def save_shout(self, message, content):
		guild_or_user = get_guild_or_user(message)
		await self.bot.pool.execute("""
			INSERT INTO shout (guild_or_user, message, content)
			VALUES ($1, $2, pgp_sym_encrypt($3, $4))
			ON CONFLICT DO NOTHING
		""", guild_or_user, message.id, content, self.bot.config['encryption_key'])

	async def get_random_shout(self, message):
		query = """
			SELECT pgp_sym_decrypt(content, $2)
			FROM shout
			WHERE guild_or_user = $1
			OFFSET FLOOR(RANDOM() * (
				SELECT COUNT(*)
				FROM shout
				WHERE guild_or_user = $1
			))
			LIMIT 1
		"""

		return await self.bot.pool.fetchval(query, get_guild_or_user(message), self.bot.config['encryption_key'])

	async def get_shout(self, message_id):
		return await self.bot.pool.fetchval("""
			SELECT pgp_sym_decrypt(content, $2)
			FROM shout
			WHERE message = $1
		""", message_id, self.bot.config['encryption_key'])

	async def delete_shout(self, message_id):
		tag = await self.bot.pool.execute('DELETE FROM shout WHERE message = $1', message_id)
		return int(tag.split()[-1])

	async def delete_shouts(self, message_ids):
		await self.bot.pool.executemany('DELETE FROM shout WHERE message = $1', [(id,) for id in message_ids])

	async def delete_by_guild_or_user(self, guild_or_user):
		await self.bot.pool.execute('DELETE FROM shout WHERE guild_or_user = $1', guild_or_user)

	async def _toggle_state(self, table_name, id, default_new_state):
		"""toggle the state for a user or guild. If there's no entry already, new state = default_new_state."""
		# see _get_state for why string formatting is OK here
		await self.bot.pool.execute(f"""
			INSERT INTO {table_name} (id, state) VALUES ($1, $2)
			ON CONFLICT (id) DO UPDATE SET state = NOT {table_name}.state
		""", id, default_new_state)

	async def set_guild_state(self, guild_id, new_state):
		"""Sets the state for a guild."""
		await self.bot.pool.execute(f"""
			INSERT INTO guild_opt (id, state)
			VALUES ($1, $2)
			ON CONFLICT (id) DO UPDATE
			SET state = EXCLUDED.state
		""", guild_id, new_state)

	async def toggle_user_state(self, user_id, guild_id=None) -> bool:
		"""Toggle whether the user has opted in to the bot.
		If the user does not have an entry already:
			If the guild_id is provided and not None, the user's state is set to the opposite of the guilds'
			Otherwise, the user's state is set to True (opted in), since the default state is False.
		Returns the new state.
		"""
		default_new_state = True
		guild_state = await self.get_guild_state(guild_id)
		if guild_state is not None:
			# if the auto response is enabled for the guild then toggling the user state should opt out
			default_new_state = not guild_state
		await self._toggle_state('user_opt', user_id, default_new_state)
		return await self.get_user_state(user_id)

	async def toggle_guild_state(self, guild_id):
		"""Togle whether this guild is opt out.
		If this guild is opt in, the shout auto response will be disabled
		except for users that have opted in to it using `toggle_user_state`.
		Otherwise, the response will be on for all users except those that have opted out.
		"""
		await self._toggle_state('guild_opt', guild_id, True)
		return await self.get_guild_state(guild_id)

	async def _get_state(self, table_name, id):
		# unfortunately, using $1 for table_name is a syntax error
		# however, since table name is always hardcoded input from other functions in this module,
		# it's ok to use string formatting here
		return await self.bot.pool.fetchval(f'SELECT state FROM {table_name} WHERE id = $1', id)

	async def get_user_state(self, user_id):
		"""return this user's global preference for the shout auto response and logging"""
		return await self._get_state('user_opt', user_id)

	async def get_guild_state(self, guild_id):
		"""return whether this guild is opt in"""
		return await self._get_state('guild_opt', guild_id)

	async def get_state(self, guild_id, user_id):
		user_state = await self.get_user_state(guild_id)
		if user_state is not None:
			return user_state

		if guild_id is None:
			return True
		return await self.get_guild_state(guild_id)

def get_guild_or_user(message):
	try:
		return message.guild.id
	except AttributeError:
		return message.author.id

def setup(bot):
	bot.add_cog(Database(bot))
