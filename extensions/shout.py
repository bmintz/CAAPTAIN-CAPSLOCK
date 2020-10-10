# Copyright © 2018–2020 lambda#0987
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

import logging
import re
from random import random

from discord.ext import commands

import utils.shout
from utils.converter import Message

logger = logging.getLogger(__name__)
CODEBLOCK_RE = re.compile(r'(`{1,3}).+?\1', re.DOTALL)
MENTION_RE = re.compile(r'<(?:&|#|@!?)\d+>|@everyone|@here', re.ASCII)
# how likely the bot is to respond with a random shout (shouts will always be logged regardless of this value)
SHOUT_RESPONSE_PROBABILITY = 0.4

def is_shout(content):
	without_code = CODEBLOCK_RE.sub('', content)
	return utils.shout.is_shout(MENTION_RE.sub('', without_code))

# Used under the MIT license. Copyright (c) 2017 BeatButton
# https://github.com/BeatButton/beattie/blob/44fd795aef7b1c19233510cda8046baab5ecabf3/utils/checks.py
def owner_or_permissions(**perms):
	"""Checks if the member is a bot owner or has any of the guild permissions necessary."""
	async def predicate(ctx):
		if await ctx.bot.is_owner(ctx.author):
			return True
		return any(getattr(ctx.author.guild_permissions, perm, None) == value for perm, value in perms.items())
	return commands.check(predicate)

class Shout(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.db = bot.cogs['Database']

	@commands.command(name='remove')
	async def remove_shout(self, context, message: Message):
		"""removes a shout from the database without removing the message itself.

		You can specify the message in one of three ways:
		- message ID
		- channel_id-message_id (obtained by shift-clicking the "copy ID" button)
		- a jump link to a message
		"""
		if not (context.author == message.author or message.channel.permissions_for(context.author).manage_messages):
			await context.send(
				"YOU DON'T HAVE PERMISSION TO DELETE THAT SHOUT "
				"BECAUSE YOU DON'T HAVE PERMISSION TO DELETE THAT MESSAGE")
			return

		count = await self.db.delete_shout(message.id)
		if not count:
			await context.send('THAT MESSAGE IS NOT A SHOUT THAT I KNOW ABOUT')
			return

		await context.message.add_reaction(self.bot.config['success_or_failure_emojis'][True])

	@commands.command(aliases=['toggle-user'])
	async def toggle(self, context):
		"""Toggles the shout auto response and logging for you.
		This is global, ie it affects all servers you are in.

		If a server has been set to opt in, you will need to run this command before I can respond to you.
		"""
		guild = None
		if context.guild is not None:
			guild = context.guild.id
		if await self.db.toggle_user_state(context.author.id, guild):
			action = 'IN TO'
		else:
			action = 'OUT OF'
		await context.send(f'OPTED {action} THE SHOUT AUTO RESPONSE.')

	@commands.command(name='toggleserver', aliases=['toggle-server'])
	@owner_or_permissions(manage_messages=True)
	@commands.guild_only()
	async def toggle_guild(self, context):
		"""Toggle the shouting auto response for this server.
		If you have never run this command before, this server is opt-out: the shout auto response is
		on for all users, except those who run the toggle-user command.

		If this server is opt-out, the emote auto response is off for all users,
		and they must run the toggle-user command before the bot will respond to them.

		Opt in mode is useful for very large servers where the bot's response would be annoying or
		would conflict with that of other bots.
		"""
		if await self.db.toggle_guild_state(context.guild.id):
			new_state = 'OPT-OUT'
		else:
			new_state = 'OPT-IN'
		await context.send(f'SHOUT AUTO RESPONSE IS NOW {new_state} FOR THIS SERVER.')

	@commands.command(name='enable')
	@owner_or_permissions(manage_messages=True)
	@commands.guild_only()
	async def enable(self, context):
		"""Sets the shouting auto response to opt-out for this server. See the __toggleserver__ command
		for more information.
		"""
		await self.db.set_guild_state(context.guild.id, True)
		await context.send('SHOUT AUTO RESPONSE IS NOW OPT-OUT FOR THIS SERVER.')

	@commands.Cog.listener()
	async def on_message(self, message):
		if not message.guild:
			return

		if not is_shout(message.content) or not self.bot.should_reply(message):
			return

		context = await self.bot.get_context(message)
		if context.command:
			# don't respond here if the user has sent a command
			return

		if not await self.db.get_state(message.guild.id, message.author.id):
			return

		# Reduce spam and prevent the bot from always having the last word.
		# In practice, responding 100% of the time causes bickering with users.
		if random() < SHOUT_RESPONSE_PROBABILITY:
			shout = await self.db.get_random_shout(message)
			await message.channel.send(shout or "I AIN'T GOT NOTHIN' ON THAT")

		sanitized = self.bot.clean_content(content=message.content, guild=message.guild)
		await self.db.save_shout(message, sanitized)

	@commands.Cog.listener()
	async def on_raw_message_edit(self, payload):
		if 'webhook_id' in payload.data:
			return

		id = payload.message_id
		if 'content' not in payload.data:
			try:
				message = payload.cached_message or await self.bot.get_channel(payload.channel_id).fetch_message(id)
			except discord.HTTPException:
				return

			content = message.content
			guild = message.guild
		else:
			guild = 'guild_id' in payload.data and self.bot.get_guild(payload.data['guild_id'])
			content = payload.data['content']

		if not is_shout(content):
			# don't let people sneakily insert non-shouts into the database
			await self.db.delete_shout(id)
			return

		await self.db.update_shout(id, self.bot.clean_content(content=content, guild=guild))

	@commands.Cog.listener()
	async def on_raw_message_delete(self, payload):
		await self.db.delete_shout(payload.message_id)

	@commands.Cog.listener()
	async def on_raw_bulk_message_delete(self, payload):
		await self.db.delete_shouts(payload.message_ids)

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		# TODO also handle inconsistency caused by a guild being removed while the bot is offline
		await self.db.delete_by_guild_or_user(guild.id)

def setup(bot):
	bot.add_cog(Shout(bot))
