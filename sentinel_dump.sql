pg_dump: warning: there are circular foreign-key constraints on this table:
pg_dump:   hypertable
pg_dump: You might not be able to restore the dump without using --disable-triggers or temporarily dropping the constraints.
pg_dump: Consider using a full dump instead of a --data-only dump to avoid this problem.
pg_dump: warning: there are circular foreign-key constraints on this table:
pg_dump:   chunk
pg_dump: You might not be able to restore the dump without using --disable-triggers or temporarily dropping the constraints.
pg_dump: Consider using a full dump instead of a --data-only dump to avoid this problem.
pg_dump: warning: there are circular foreign-key constraints on this table:
pg_dump:   continuous_agg
pg_dump: You might not be able to restore the dump without using --disable-triggers or temporarily dropping the constraints.
pg_dump: Consider using a full dump instead of a --data-only dump to avoid this problem.
--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17
-- Dumped by pg_dump version 14.17

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: timescaledb; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;


--
-- Name: EXTENSION timescaledb; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION timescaledb IS 'Enables scalable inserts and complex queries for time-series data (Community Edition)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: events; Type: TABLE; Schema: public; Owner: sentinel_user
--

CREATE TABLE public.events (
    event_id uuid NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    sensor_id text NOT NULL,
    sensor_type text NOT NULL,
    source_ip inet NOT NULL,
    source_port integer,
    destination_ip inet,
    destination_port integer,
    protocol text,
    event_type text NOT NULL,
    data jsonb,
    severity text,
    tags text[],
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.events OWNER TO sentinel_user;

--
-- Name: security_events; Type: TABLE; Schema: public; Owner: sentinel_user
--

CREATE TABLE public.security_events (
    event_id uuid NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    sensor_id character varying(50) NOT NULL,
    sensor_location character varying(50),
    source_ip character varying(45) NOT NULL,
    vector character varying(20) NOT NULL,
    interaction_level character varying(10),
    username_attempted text,
    password_attempted text,
    commands_executed jsonb,
    files_dropped jsonb
);


ALTER TABLE public.security_events OWNER TO sentinel_user;

--
-- Data for Name: hypertable; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.hypertable (id, schema_name, table_name, associated_schema_name, associated_table_prefix, num_dimensions, chunk_sizing_func_schema, chunk_sizing_func_name, chunk_target_size, compression_state, compressed_hypertable_id, status) FROM stdin;
1	public	events	_timescaledb_internal	_hyper_1	1	_timescaledb_functions	calculate_chunk_interval	0	0	\N	0
\.


--
-- Data for Name: chunk; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.chunk (id, hypertable_id, schema_name, table_name, compressed_chunk_id, dropped, status, osm_chunk, creation_time) FROM stdin;
\.


--
-- Data for Name: chunk_column_stats; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.chunk_column_stats (id, hypertable_id, chunk_id, column_name, range_start, range_end, valid) FROM stdin;
\.


--
-- Data for Name: dimension; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.dimension (id, hypertable_id, column_name, column_type, aligned, num_slices, partitioning_func_schema, partitioning_func, interval_length, compress_interval_length, integer_now_func_schema, integer_now_func) FROM stdin;
1	1	timestamp	timestamp with time zone	t	\N	\N	\N	604800000000	\N	\N	\N
\.


--
-- Data for Name: dimension_slice; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.dimension_slice (id, dimension_id, range_start, range_end) FROM stdin;
\.


--
-- Data for Name: chunk_constraint; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.chunk_constraint (chunk_id, dimension_slice_id, constraint_name, hypertable_constraint_name) FROM stdin;
\.


--
-- Data for Name: chunk_index; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.chunk_index (chunk_id, index_name, hypertable_id, hypertable_index_name) FROM stdin;
\.


--
-- Data for Name: compression_chunk_size; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.compression_chunk_size (chunk_id, compressed_chunk_id, uncompressed_heap_size, uncompressed_toast_size, uncompressed_index_size, compressed_heap_size, compressed_toast_size, compressed_index_size, numrows_pre_compression, numrows_post_compression, numrows_frozen_immediately) FROM stdin;
\.


--
-- Data for Name: compression_settings; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.compression_settings (relid, compress_relid, segmentby, orderby, orderby_desc, orderby_nullsfirst) FROM stdin;
\.


--
-- Data for Name: continuous_agg; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.continuous_agg (mat_hypertable_id, raw_hypertable_id, parent_mat_hypertable_id, user_view_schema, user_view_name, partial_view_schema, partial_view_name, direct_view_schema, direct_view_name, materialized_only, finalized) FROM stdin;
\.


--
-- Data for Name: continuous_agg_migrate_plan; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.continuous_agg_migrate_plan (mat_hypertable_id, start_ts, end_ts, user_view_definition) FROM stdin;
\.


--
-- Data for Name: continuous_agg_migrate_plan_step; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.continuous_agg_migrate_plan_step (mat_hypertable_id, step_id, status, start_ts, end_ts, type, config) FROM stdin;
\.


--
-- Data for Name: continuous_aggs_bucket_function; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.continuous_aggs_bucket_function (mat_hypertable_id, bucket_func, bucket_width, bucket_origin, bucket_offset, bucket_timezone, bucket_fixed_width) FROM stdin;
\.


--
-- Data for Name: continuous_aggs_hypertable_invalidation_log; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.continuous_aggs_hypertable_invalidation_log (hypertable_id, lowest_modified_value, greatest_modified_value) FROM stdin;
\.


--
-- Data for Name: continuous_aggs_invalidation_threshold; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.continuous_aggs_invalidation_threshold (hypertable_id, watermark) FROM stdin;
\.


--
-- Data for Name: continuous_aggs_materialization_invalidation_log; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.continuous_aggs_materialization_invalidation_log (materialization_id, lowest_modified_value, greatest_modified_value) FROM stdin;
\.


--
-- Data for Name: continuous_aggs_watermark; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.continuous_aggs_watermark (mat_hypertable_id, watermark) FROM stdin;
\.


--
-- Data for Name: metadata; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.metadata (key, value, include_in_telemetry) FROM stdin;
install_timestamp	2026-03-03 08:46:51.939747+00	t
timescaledb_version	2.19.3	f
exported_uuid	a3dd60a5-6a7e-400f-a727-572d74dd55cc	t
\.


--
-- Data for Name: tablespace; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: sentinel_user
--

COPY _timescaledb_catalog.tablespace (id, hypertable_id, tablespace_name) FROM stdin;
\.


--
-- Data for Name: bgw_job; Type: TABLE DATA; Schema: _timescaledb_config; Owner: sentinel_user
--

COPY _timescaledb_config.bgw_job (id, application_name, schedule_interval, max_runtime, max_retries, retry_period, proc_schema, proc_name, owner, scheduled, fixed_schedule, initial_start, hypertable_id, config, check_schema, check_name, timezone) FROM stdin;
\.


--
-- Data for Name: events; Type: TABLE DATA; Schema: public; Owner: sentinel_user
--

COPY public.events (event_id, "timestamp", sensor_id, sensor_type, source_ip, source_port, destination_ip, destination_port, protocol, event_type, data, severity, tags, created_at) FROM stdin;
pg_dump: NOTICE:  hypertable data are in the chunks, no data will be copied
DETAIL:  Data for hypertables are stored in the chunks of a hypertable so COPY TO of a hypertable will not copy any data.
HINT:  Use "COPY (SELECT * FROM <hypertable>) TO ..." to copy all data in hypertable, or copy each chunk individually.
\.


--
-- Data for Name: security_events; Type: TABLE DATA; Schema: public; Owner: sentinel_user
--

COPY public.security_events (event_id, "timestamp", sensor_id, sensor_location, source_ip, vector, interaction_level, username_attempted, password_attempted, commands_executed, files_dropped) FROM stdin;
550e8400-e29b-41d4-a716-446655440000	2026-03-03 15:30:00+00	test-sensor-alpha	frankfurt	198.51.100.22	ssh	medium	root	toor	["whoami", "cat /etc/passwd"]	["d41d8cd98f00b204e9800998ecf8427e"]
f3548ad5-69f1-4e06-8e6a-8e24019c055e	2026-03-03 15:55:21+00	ssh-eu-1	london	127.0.0.1	ssh	low	admin	password123	[]	[]
c895a712-237b-4445-a312-afff5db2d1d2	2026-03-03 16:04:30+00	ssh-eu-1	london	127.0.0.1	ssh	low	admin	main keha laadle miau ghop ghop	[]	[]
65a954aa-b98c-4744-b7d6-66a7d1ee7d54	2026-03-04 16:32:57+00	http-eu-1	london	127.0.0.1	http	low	admin	supersecret123	[]	[]
031bbb9d-3f14-4b46-9dca-fd94d870009c	2026-03-04 16:33:21+00	http-eu-1	london	127.0.0.1	http	low	admin	supersecret123	[]	[]
7373ddff-4975-478c-999d-21427a7e67fc	2026-03-04 16:36:11+00	http-eu-1	london	127.0.0.1	http	low	admin	do not ask the leader for password	[]	[]
\.


--
-- Name: chunk_column_stats_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: sentinel_user
--

SELECT pg_catalog.setval('_timescaledb_catalog.chunk_column_stats_id_seq', 1, false);


--
-- Name: chunk_constraint_name; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: sentinel_user
--

SELECT pg_catalog.setval('_timescaledb_catalog.chunk_constraint_name', 1, false);


--
-- Name: chunk_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: sentinel_user
--

SELECT pg_catalog.setval('_timescaledb_catalog.chunk_id_seq', 1, false);


--
-- Name: continuous_agg_migrate_plan_step_step_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: sentinel_user
--

SELECT pg_catalog.setval('_timescaledb_catalog.continuous_agg_migrate_plan_step_step_id_seq', 1, false);


--
-- Name: dimension_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: sentinel_user
--

SELECT pg_catalog.setval('_timescaledb_catalog.dimension_id_seq', 1, true);


--
-- Name: dimension_slice_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: sentinel_user
--

SELECT pg_catalog.setval('_timescaledb_catalog.dimension_slice_id_seq', 1, false);


--
-- Name: hypertable_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: sentinel_user
--

SELECT pg_catalog.setval('_timescaledb_catalog.hypertable_id_seq', 1, true);


--
-- Name: bgw_job_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_config; Owner: sentinel_user
--

SELECT pg_catalog.setval('_timescaledb_config.bgw_job_id_seq', 1000, false);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: sentinel_user
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (event_id, "timestamp");


--
-- Name: security_events security_events_pkey; Type: CONSTRAINT; Schema: public; Owner: sentinel_user
--

ALTER TABLE ONLY public.security_events
    ADD CONSTRAINT security_events_pkey PRIMARY KEY (event_id);


--
-- Name: events_timestamp_idx; Type: INDEX; Schema: public; Owner: sentinel_user
--

CREATE INDEX events_timestamp_idx ON public.events USING btree ("timestamp" DESC);


--
-- Name: idx_events_event_type; Type: INDEX; Schema: public; Owner: sentinel_user
--

CREATE INDEX idx_events_event_type ON public.events USING btree (event_type, "timestamp" DESC);


--
-- Name: idx_events_sensor_id; Type: INDEX; Schema: public; Owner: sentinel_user
--

CREATE INDEX idx_events_sensor_id ON public.events USING btree (sensor_id, "timestamp" DESC);


--
-- Name: idx_events_severity; Type: INDEX; Schema: public; Owner: sentinel_user
--

CREATE INDEX idx_events_severity ON public.events USING btree (severity, "timestamp" DESC);


--
-- Name: idx_events_source_ip; Type: INDEX; Schema: public; Owner: sentinel_user
--

CREATE INDEX idx_events_source_ip ON public.events USING btree (source_ip, "timestamp" DESC);


--
-- Name: events ts_insert_blocker; Type: TRIGGER; Schema: public; Owner: sentinel_user
--

CREATE TRIGGER ts_insert_blocker BEFORE INSERT ON public.events FOR EACH ROW EXECUTE FUNCTION _timescaledb_functions.insert_blocker();


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: sentinel_user
--

GRANT USAGE ON SCHEMA public TO sentinel_api;


--
-- Name: TABLE events; Type: ACL; Schema: public; Owner: sentinel_user
--

GRANT SELECT,INSERT,UPDATE ON TABLE public.events TO sentinel_api;


--
-- PostgreSQL database dump complete
--

