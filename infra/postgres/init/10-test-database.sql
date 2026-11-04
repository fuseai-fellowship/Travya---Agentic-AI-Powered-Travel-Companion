-- Runs once, when the db volume is first initialised. pytest uses this database (TEST_DATABASE_URL)
-- so test runs never touch the development data in `travya`.
CREATE DATABASE travya_test OWNER travya;
