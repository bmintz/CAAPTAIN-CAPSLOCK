# CAPTAIN CAPSLOCK

[![Unit Test Status](https://img.shields.io/travis/iomintz/CAPTAIN-CAPSLOCK/master.svg?label=tests)](https://travis-ci.org/iomintz/CAPTAIN-CAPSLOCK)
[![Discord Bots](https://discordbots.org/api/widget/status/469736963277062166.svg?noavatar=true)](https://discordbots.org/bot/469736963277062166)

A Discord bot that shouts at you when you shout at it.

## How does it operate?

Say something. Say anything. But say it LOUDLY. The cap' will log what you say (for your server only), and
60% of the time, shout something random back at you. The more you shout at it, the bigger its repertoire gets.
Duplicate text will not be logged.

## Why doesn't it respond all the time?

In practice, responding 100% of the time causes shouting matches and bickering with the bot. Responding 40% of the time
prevents it from always having the last word.

## What about message deletes/edits?

Deleting a message will delete its correspond entry in the database, if there is one.
Editing a message will update the entry to match, however,
if you sneakily edit a shout so that it's no longer a shout,
the bot will delete the correspond entry in the database instead.
For example, saying "YOOOOO" and then editing it to "yo" will mean that the cap' will not say "YOOOOO" anymore.

If a channel is deleted, all of its corresponding messages are deleted from the database.

When Captain Caps is kicked from a server, all shouts for that server are deleted from its database.

## What commands does it have?

Not many.

- @CAPTAIN CAPSLOCK toggle will enable or disable the shout response and logging for you.
- If you have the Manage Messages permission *server-wide* then you can use the @CAPTAIN CAPSLOCK toggleserver
  command. This will make the shouting auto response opt-in or opt-out for the entire server. If it is opt-in,
  users will need to run @CAPTAIN CAPSLOCK toggle before the bot will log their shouts and repeat them.
- If you have permission to delete a message then you can also remove it from the database by using the
  @CAPTAIN CAPSLOCK remove command.

## What's in a shout?

*Would a scream by any other name still be as loud?*

The algorithm for determining shouts is in [utils/shout.py](https://github.com/bmintz/CAPTAIN-CAPSLOCK/blob/master/utils/shout.py).
All word characters are considered, and if more than half of them are uppercase, the sentence is a shout.
Certain strings are ignored (mostly emoticons). See the utils/shout.py file for more details.

## How do I run this?

You'll need PostgreSQL 11+ and python3.6+.

```
$ createdb captain_capslock
$ psql captain_capslock -f schema.sql
$ cp data/config.example.json data/config.json
$ # edit config.json as needed
$ python3 -m venv .venv
$ source .venv/bin/activate
$ ./bot.py
```

## License

Copyright © 2018–2020 lambda#0987

CAPTAIN CAPSLOCK is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CAPTAIN CAPSLOCK is distributed in the hope that it will be fun,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with CAPTAIN CAPSLOCK.  If not, see <https://www.gnu.org/licenses/>.
