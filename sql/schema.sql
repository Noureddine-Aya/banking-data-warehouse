--
-- PostgreSQL database dump
--

\restrict i4NFcgX3IALLdJ6KOeJgqEHZJu9CdScsVdLPDwHDC1Y5fttHo39DPf9ofgzk29a

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: dw; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA dw;


--
-- Name: staging; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA staging;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: dim_account; Type: TABLE; Schema: dw; Owner: -
--

CREATE TABLE dw.dim_account (
    account_key integer NOT NULL,
    account_id integer NOT NULL,
    district_id integer,
    opening_date date,
    statement_frequency character varying(30)
);


--
-- Name: dim_account_account_key_seq; Type: SEQUENCE; Schema: dw; Owner: -
--

ALTER TABLE dw.dim_account ALTER COLUMN account_key ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME dw.dim_account_account_key_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: dim_client; Type: TABLE; Schema: dw; Owner: -
--

CREATE TABLE dw.dim_client (
    client_key integer NOT NULL,
    client_id integer NOT NULL,
    birth_date date,
    gender character varying(10),
    district_id integer
);


--
-- Name: dim_client_client_key_seq; Type: SEQUENCE; Schema: dw; Owner: -
--

ALTER TABLE dw.dim_client ALTER COLUMN client_key ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME dw.dim_client_client_key_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: dim_date; Type: TABLE; Schema: dw; Owner: -
--

CREATE TABLE dw.dim_date (
    date_key integer NOT NULL,
    full_date date NOT NULL,
    year integer NOT NULL,
    quarter integer NOT NULL,
    month integer NOT NULL,
    day integer NOT NULL,
    day_of_week integer NOT NULL,
    is_weekend boolean NOT NULL
);


--
-- Name: dim_district; Type: TABLE; Schema: dw; Owner: -
--

CREATE TABLE dw.dim_district (
    district_key integer NOT NULL,
    district_id integer NOT NULL,
    district_name character varying(100),
    region character varying(100),
    inhabitants integer,
    urban_ratio numeric(5,1),
    average_salary numeric(12,2),
    unemployment_95 numeric(6,2),
    unemployment_96 numeric(6,2),
    entrepreneurs integer
);


--
-- Name: dim_district_district_key_seq; Type: SEQUENCE; Schema: dw; Owner: -
--

ALTER TABLE dw.dim_district ALTER COLUMN district_key ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME dw.dim_district_district_key_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: dim_operation; Type: TABLE; Schema: dw; Owner: -
--

CREATE TABLE dw.dim_operation (
    operation_key integer NOT NULL,
    operation_code character varying(20) NOT NULL,
    operation_label character varying(100) NOT NULL,
    is_unknown boolean DEFAULT false NOT NULL
);


--
-- Name: dim_operation_operation_key_seq; Type: SEQUENCE; Schema: dw; Owner: -
--

ALTER TABLE dw.dim_operation ALTER COLUMN operation_key ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME dw.dim_operation_operation_key_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: fact_loans; Type: TABLE; Schema: dw; Owner: -
--

CREATE TABLE dw.fact_loans (
    loan_id integer NOT NULL,
    account_key integer NOT NULL,
    date_key integer NOT NULL,
    loan_amount numeric(15,2),
    duration_months integer,
    monthly_payment numeric(15,2),
    loan_status character varying(10)
);


--
-- Name: fact_payment_orders; Type: TABLE; Schema: dw; Owner: -
--

CREATE TABLE dw.fact_payment_orders (
    order_id integer NOT NULL,
    account_key integer NOT NULL,
    bank_to character varying(10),
    account_to character varying(20),
    amount numeric(15,2),
    k_symbol character varying(10)
);


--
-- Name: fact_transactions; Type: TABLE; Schema: dw; Owner: -
--

CREATE TABLE dw.fact_transactions (
    transaction_id integer NOT NULL,
    date_key integer NOT NULL,
    account_key integer NOT NULL,
    operation_key integer NOT NULL,
    transaction_type character varying(10),
    amount numeric(15,2),
    balance numeric(15,2),
    k_symbol character varying(20)
);


--
-- Name: account; Type: TABLE; Schema: staging; Owner: -
--

CREATE TABLE staging.account (
    account_id integer NOT NULL,
    district_id integer,
    date date,
    frequency character varying(30)
);


--
-- Name: card; Type: TABLE; Schema: staging; Owner: -
--

CREATE TABLE staging.card (
    card_id integer NOT NULL,
    disp_id integer,
    type character varying(10),
    issued date
);


--
-- Name: client; Type: TABLE; Schema: staging; Owner: -
--

CREATE TABLE staging.client (
    client_id integer NOT NULL,
    gender character varying(10),
    birth_date date,
    district_id integer
);


--
-- Name: disp; Type: TABLE; Schema: staging; Owner: -
--

CREATE TABLE staging.disp (
    disp_id integer NOT NULL,
    client_id integer,
    account_id integer,
    type character varying(10)
);


--
-- Name: district; Type: TABLE; Schema: staging; Owner: -
--

CREATE TABLE staging.district (
    district_id integer NOT NULL,
    district_name character varying(100),
    region character varying(100),
    inhabitants integer,
    municipalities_1 integer,
    municipalities_2 integer,
    municipalities_3 integer,
    municipalities_4 integer,
    cities integer,
    urban_ratio numeric(5,1),
    salary numeric(12,2),
    unemployment_95 numeric(6,2),
    unemployment_96 numeric(6,2),
    entrepreneurs integer,
    crimes_95 integer,
    crimes_96 integer
);


--
-- Name: loan; Type: TABLE; Schema: staging; Owner: -
--

CREATE TABLE staging.loan (
    loan_id integer NOT NULL,
    account_id integer,
    date date,
    amount numeric(15,2),
    duration integer,
    payments numeric(15,2),
    status character varying(1)
);


--
-- Name: payment_order; Type: TABLE; Schema: staging; Owner: -
--

CREATE TABLE staging.payment_order (
    order_id integer NOT NULL,
    account_id integer,
    bank_to character varying(10),
    account_to character varying(20),
    amount numeric(15,2),
    k_symbol character varying(10)
);


--
-- Name: trans; Type: TABLE; Schema: staging; Owner: -
--

CREATE TABLE staging.trans (
    trans_id integer NOT NULL,
    account_id integer,
    date date,
    amount numeric(15,2),
    balance numeric(15,2),
    type character varying(10),
    operation character varying(20),
    k_symbol character varying(20),
    bank character varying(20),
    account character varying(30)
);


--
-- Name: dim_account dim_account_account_id_key; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.dim_account
    ADD CONSTRAINT dim_account_account_id_key UNIQUE (account_id);


--
-- Name: dim_account dim_account_pkey; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.dim_account
    ADD CONSTRAINT dim_account_pkey PRIMARY KEY (account_key);


--
-- Name: dim_client dim_client_client_id_key; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.dim_client
    ADD CONSTRAINT dim_client_client_id_key UNIQUE (client_id);


--
-- Name: dim_client dim_client_pkey; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.dim_client
    ADD CONSTRAINT dim_client_pkey PRIMARY KEY (client_key);


--
-- Name: dim_date dim_date_full_date_key; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.dim_date
    ADD CONSTRAINT dim_date_full_date_key UNIQUE (full_date);


--
-- Name: dim_date dim_date_pkey; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.dim_date
    ADD CONSTRAINT dim_date_pkey PRIMARY KEY (date_key);


--
-- Name: dim_district dim_district_district_id_key; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.dim_district
    ADD CONSTRAINT dim_district_district_id_key UNIQUE (district_id);


--
-- Name: dim_district dim_district_pkey; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.dim_district
    ADD CONSTRAINT dim_district_pkey PRIMARY KEY (district_key);


--
-- Name: dim_operation dim_operation_operation_code_key; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.dim_operation
    ADD CONSTRAINT dim_operation_operation_code_key UNIQUE (operation_code);


--
-- Name: dim_operation dim_operation_pkey; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.dim_operation
    ADD CONSTRAINT dim_operation_pkey PRIMARY KEY (operation_key);


--
-- Name: fact_loans fact_loans_pkey; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.fact_loans
    ADD CONSTRAINT fact_loans_pkey PRIMARY KEY (loan_id);


--
-- Name: fact_payment_orders fact_payment_orders_pkey; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.fact_payment_orders
    ADD CONSTRAINT fact_payment_orders_pkey PRIMARY KEY (order_id);


--
-- Name: fact_transactions fact_transactions_pkey; Type: CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.fact_transactions
    ADD CONSTRAINT fact_transactions_pkey PRIMARY KEY (transaction_id);


--
-- Name: account account_pkey; Type: CONSTRAINT; Schema: staging; Owner: -
--

ALTER TABLE ONLY staging.account
    ADD CONSTRAINT account_pkey PRIMARY KEY (account_id);


--
-- Name: card card_pkey; Type: CONSTRAINT; Schema: staging; Owner: -
--

ALTER TABLE ONLY staging.card
    ADD CONSTRAINT card_pkey PRIMARY KEY (card_id);


--
-- Name: client client_pkey; Type: CONSTRAINT; Schema: staging; Owner: -
--

ALTER TABLE ONLY staging.client
    ADD CONSTRAINT client_pkey PRIMARY KEY (client_id);


--
-- Name: disp disp_pkey; Type: CONSTRAINT; Schema: staging; Owner: -
--

ALTER TABLE ONLY staging.disp
    ADD CONSTRAINT disp_pkey PRIMARY KEY (disp_id);


--
-- Name: district district_pkey; Type: CONSTRAINT; Schema: staging; Owner: -
--

ALTER TABLE ONLY staging.district
    ADD CONSTRAINT district_pkey PRIMARY KEY (district_id);


--
-- Name: loan loan_pkey; Type: CONSTRAINT; Schema: staging; Owner: -
--

ALTER TABLE ONLY staging.loan
    ADD CONSTRAINT loan_pkey PRIMARY KEY (loan_id);


--
-- Name: payment_order payment_order_pkey; Type: CONSTRAINT; Schema: staging; Owner: -
--

ALTER TABLE ONLY staging.payment_order
    ADD CONSTRAINT payment_order_pkey PRIMARY KEY (order_id);


--
-- Name: trans trans_pkey; Type: CONSTRAINT; Schema: staging; Owner: -
--

ALTER TABLE ONLY staging.trans
    ADD CONSTRAINT trans_pkey PRIMARY KEY (trans_id);


--
-- Name: fact_transactions fk_fact_account; Type: FK CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.fact_transactions
    ADD CONSTRAINT fk_fact_account FOREIGN KEY (account_key) REFERENCES dw.dim_account(account_key);


--
-- Name: fact_transactions fk_fact_date; Type: FK CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.fact_transactions
    ADD CONSTRAINT fk_fact_date FOREIGN KEY (date_key) REFERENCES dw.dim_date(date_key);


--
-- Name: fact_transactions fk_fact_operation; Type: FK CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.fact_transactions
    ADD CONSTRAINT fk_fact_operation FOREIGN KEY (operation_key) REFERENCES dw.dim_operation(operation_key);


--
-- Name: fact_loans fk_loan_account; Type: FK CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.fact_loans
    ADD CONSTRAINT fk_loan_account FOREIGN KEY (account_key) REFERENCES dw.dim_account(account_key);


--
-- Name: fact_loans fk_loan_date; Type: FK CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.fact_loans
    ADD CONSTRAINT fk_loan_date FOREIGN KEY (date_key) REFERENCES dw.dim_date(date_key);


--
-- Name: fact_payment_orders fk_payment_account; Type: FK CONSTRAINT; Schema: dw; Owner: -
--

ALTER TABLE ONLY dw.fact_payment_orders
    ADD CONSTRAINT fk_payment_account FOREIGN KEY (account_key) REFERENCES dw.dim_account(account_key);


--
-- PostgreSQL database dump complete
--

\unrestrict i4NFcgX3IALLdJ6KOeJgqEHZJu9CdScsVdLPDwHDC1Y5fttHo39DPf9ofgzk29a

