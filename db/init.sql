-- Here, we can specify any SQL we want executed on database startup
-- by default, postgres first off any init.sql script that
-- is located at /docker-entrypoint-initdb.d/init.sql
-- We copy this script to that location inside the postgres docker container.

-- For example, we may use this script to "seed" the database with some data
-- we can create databases, add data... whatever we need to do.