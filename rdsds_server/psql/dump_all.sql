--
-- PostgreSQL database cluster dump
--

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Roles
--

CREATE ROLE dsds_postgre;
ALTER ROLE dsds_postgre WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD 'md561a1f09fabc8a4e348a10efc41f2e43a';
CREATE ROLE dsimonovic;
ALTER ROLE dsimonovic WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN NOREPLICATION NOBYPASSRLS;
CREATE ROLE postgres;
ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS;






--
-- Database creation
--

CREATE DATABASE dsds WITH TEMPLATE = template0 OWNER = dsds_postgre;
CREATE DATABASE dsimonovic WITH TEMPLATE = template0 OWNER = dsimonovic;
REVOKE CONNECT,TEMPORARY ON DATABASE template1 FROM PUBLIC;
GRANT CONNECT ON DATABASE template1 TO PUBLIC;
CREATE DATABASE test WITH TEMPLATE = template0 OWNER = dsimonovic;


\connect dsds

SET default_transaction_read_only = off;

--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.0
-- Dumped by pg_dump version 9.6.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: dataset; Type: TABLE; Schema: public; Owner: dsds_postgre
--

CREATE TABLE dataset (
    dataset_id integer NOT NULL,
    dataset_pid character varying,
    datasetname character varying,
    sourcesitename character varying,
    transfersource character varying,
    protocol character varying,
    hostname character varying,
    port integer,
    filepath character varying,
    creatorname character varying,
    creatoremail character varying,
    version integer,
    status character varying,
    updatedtime text
);


ALTER TABLE dataset OWNER TO dsds_postgre;

--
-- Name: dataset_dataset_id_seq; Type: SEQUENCE; Schema: public; Owner: dsds_postgre
--

CREATE SEQUENCE dataset_dataset_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE dataset_dataset_id_seq OWNER TO dsds_postgre;

--
-- Name: dataset_dataset_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dsds_postgre
--

ALTER SEQUENCE dataset_dataset_id_seq OWNED BY dataset.dataset_id;


--
-- Name: file; Type: TABLE; Schema: public; Owner: dsds_postgre
--

CREATE TABLE file (
    file_id integer NOT NULL,
    dataset_pid character varying,
    filename character varying,
    filebytes character varying,
    filechecksum character varying,
    updatedtime text
);


ALTER TABLE file OWNER TO dsds_postgre;

--
-- Name: file_file_id_seq; Type: SEQUENCE; Schema: public; Owner: dsds_postgre
--

CREATE SEQUENCE file_file_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE file_file_id_seq OWNER TO dsds_postgre;

--
-- Name: file_file_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dsds_postgre
--

ALTER SEQUENCE file_file_id_seq OWNED BY file.file_id;


--
-- Name: dataset dataset_id; Type: DEFAULT; Schema: public; Owner: dsds_postgre
--

ALTER TABLE ONLY dataset ALTER COLUMN dataset_id SET DEFAULT nextval('dataset_dataset_id_seq'::regclass);


--
-- Name: file file_id; Type: DEFAULT; Schema: public; Owner: dsds_postgre
--

ALTER TABLE ONLY file ALTER COLUMN file_id SET DEFAULT nextval('file_file_id_seq'::regclass);


--
-- Data for Name: dataset; Type: TABLE DATA; Schema: public; Owner: dsds_postgre
--

COPY dataset (dataset_id, dataset_pid, datasetname, sourcesitename, transfersource, protocol, hostname, port, filepath, creatorname, creatoremail, version, status, updatedtime) FROM stdin;
\.


--
-- Name: dataset_dataset_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dsds_postgre
--

SELECT pg_catalog.setval('dataset_dataset_id_seq', 1, false);


--
-- Data for Name: file; Type: TABLE DATA; Schema: public; Owner: dsds_postgre
--

COPY file (file_id, dataset_pid, filename, filebytes, filechecksum, updatedtime) FROM stdin;
\.


--
-- Name: file_file_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dsds_postgre
--

SELECT pg_catalog.setval('file_file_id_seq', 1, false);


--
-- Name: dataset dataset_pkey; Type: CONSTRAINT; Schema: public; Owner: dsds_postgre
--

ALTER TABLE ONLY dataset
    ADD CONSTRAINT dataset_pkey PRIMARY KEY (dataset_id);


--
-- Name: file file_pkey; Type: CONSTRAINT; Schema: public; Owner: dsds_postgre
--

ALTER TABLE ONLY file
    ADD CONSTRAINT file_pkey PRIMARY KEY (file_id);


--
-- PostgreSQL database dump complete
--

\connect dsimonovic

SET default_transaction_read_only = off;

--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.0
-- Dumped by pg_dump version 9.6.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- PostgreSQL database dump complete
--

\connect postgres

SET default_transaction_read_only = off;

--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.0
-- Dumped by pg_dump version 9.6.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: postgres; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON DATABASE postgres IS 'default administrative connection database';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- PostgreSQL database dump complete
--

\connect template1

SET default_transaction_read_only = off;

--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.0
-- Dumped by pg_dump version 9.6.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: template1; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON DATABASE template1 IS 'default template for new databases';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- PostgreSQL database dump complete
--

\connect test

SET default_transaction_read_only = off;

--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.0
-- Dumped by pg_dump version 9.6.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database cluster dump complete
--

