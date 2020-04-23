-- Copyright © 2018–2020 lambda#0987
--
-- CAPTAIN CAPSLOCK is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Affero General Public License as published
-- by the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- CAPTAIN CAPSLOCK is distributed in the hope that it will be fun,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Affero General Public License for more details.
--
-- You should have received a copy of the GNU Affero General Public License
-- along with CAPTAIN CAPSLOCK.  If not, see <https://www.gnu.org/licenses/>.

CREATE TABLE IF NOT EXISTS shout (
	guild_or_user BIGINT NOT NULL,
	message BIGINT NOT NULL PRIMARY KEY,
	content TEXT NOT NULL,
	time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);

CREATE UNIQUE INDEX IF NOT EXISTS shout_guild_content_unique_idx ON shout (guild_or_user, content);

-- https://stackoverflow.com/a/26284695/1378440
CREATE OR REPLACE FUNCTION update_time_column()
RETURNS TRIGGER AS $$ BEGIN
	IF row(NEW.content) IS DISTINCT FROM row(OLD.content) THEN
		NEW.time = CURRENT_TIMESTAMP;
		RETURN NEW;
	ELSE
		RETURN OLD; END IF; END; $$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_shout_time ON shout;

CREATE TRIGGER update_shout_time
BEFORE UPDATE ON shout
FOR EACH ROW EXECUTE PROCEDURE update_time_column();

CREATE TABLE IF NOT EXISTS guild_opt (
	id BIGINT NOT NULL UNIQUE,
	state BOOLEAN NOT NULL);

CREATE TABLE IF NOT EXISTS user_opt (
	id BIGINT NOT NULL UNIQUE,
	state BOOLEAN NOT NULL);
