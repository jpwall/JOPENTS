GRANT ALL PRIVILEGES ON DATABASE jopents to jopents;

CREATE TABLE auth(
    uid SERIAL PRIMARY KEY,
    username VARCHAR(25) NOT NULL,
    pw_hash VARCHAR(64) NOT NULL
);

CREATE TABLE vendors(
    vid SERIAL PRIMARY KEY,
    name VARCHAR(110) NOT NULL
);

CREATE TABLE products(
    pid SERIAL PRIMARY KEY,
    vid INT NOT NULL,
    name VARCHAR(110) NOT NULL
);