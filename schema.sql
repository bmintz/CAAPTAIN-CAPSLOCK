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
