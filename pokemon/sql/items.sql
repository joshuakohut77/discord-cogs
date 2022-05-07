-- Table: public.items

-- DROP TABLE IF EXISTS public.items;

CREATE TABLE IF NOT EXISTS public.items
(
    "Id" integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    "Name" character varying(25) COLLATE pg_catalog."default",
    "Price" integer NOT NULL,
    "Description" character varying COLLATE pg_catalog."default",
    CONSTRAINT items_pkey PRIMARY KEY ("Id")
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.items
    OWNER to redbot;


INSERT INTO items ("Name", "Price", "Description") VALUES ('Poke Ball', 200, 'A device for catching wild Pokémon. It''s thrown like a ball, comfortably encapsulating its target.');
INSERT INTO items ("Name", "Price", "Description") VALUES ('Great Ball', 600, 'A high-performance Ball with a higher catch rate than a standard Poké Ball.');
INSERT INTO items ("Name", "Price", "Description") VALUES ('Ultra Ball', 1200, 'An ultra-performance Ball with a higher catch rate than a Great Ball.');

INSERT INTO items ("Name", "Price", "Description") VALUES ('Potion', 300, 'Restores HP that have been lost in battle by 20 HP.');
INSERT INTO items ("Name", "Price", "Description") VALUES ('Super Potion', 700, 'Restores HP that have been lost in battle by 50 HP.');
INSERT INTO items ("Name", "Price", "Description") VALUES ('Hyper Potion', 1500, 'Restores HP that have been lost in battle by 200 HP.');
INSERT INTO items ("Name", "Price", "Description") VALUES ('Max Potion', 2500, 'Fully restores HP that have been lost in battle.');
