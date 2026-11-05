-- Runs once, when the db volume is first initialised (as the superuser, connected to `travya`).
-- pytest uses `travya_test` (TEST_DATABASE_URL) so test runs never touch the development data.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE DATABASE travya_test OWNER travya;
\connect travya_test
CREATE EXTENSION IF NOT EXISTS vector;
