BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_initial

INSERT INTO alembic_version (version_num) VALUES ('0001_initial') RETURNING alembic_version.version_num;

-- Running upgrade 0001_initial -> 0002_bibliographic_tables

CREATE TABLE authors (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE works (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    title VARCHAR(512) NOT NULL, 
    description TEXT, 
    first_publish_year SMALLINT, 
    default_cover_url TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE editions (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    work_id UUID NOT NULL, 
    isbn10 VARCHAR(10), 
    isbn13 VARCHAR(13), 
    publisher VARCHAR(255), 
    publish_date DATE, 
    language VARCHAR(32), 
    format VARCHAR(64), 
    cover_url TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(work_id) REFERENCES works (id)
);

CREATE TABLE work_authors (
    work_id UUID NOT NULL, 
    author_id UUID NOT NULL, 
    PRIMARY KEY (work_id, author_id), 
    FOREIGN KEY(work_id) REFERENCES works (id), 
    FOREIGN KEY(author_id) REFERENCES authors (id)
);

CREATE INDEX ix_editions_isbn10 ON editions (isbn10);

CREATE INDEX ix_editions_isbn13 ON editions (isbn13);

UPDATE alembic_version SET version_num='0002_bibliographic_tables' WHERE alembic_version.version_num = '0001_initial';

-- Running upgrade 0002_bibliographic_tables -> 0003_external_provider_tables

CREATE TABLE external_ids (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    entity_type VARCHAR(32) NOT NULL, 
    entity_id UUID NOT NULL, 
    provider VARCHAR(64) NOT NULL, 
    provider_id VARCHAR(255) NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_external_ids_entity_provider UNIQUE (entity_type, entity_id, provider), 
    CONSTRAINT uq_external_ids_provider_id UNIQUE (provider, provider_id, entity_type)
);

CREATE INDEX ix_external_ids_provider_lookup ON external_ids (provider, provider_id);

CREATE TABLE source_records (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    provider VARCHAR(64) NOT NULL, 
    entity_type VARCHAR(32) NOT NULL, 
    provider_id VARCHAR(255) NOT NULL, 
    raw JSONB NOT NULL, 
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_source_records_provider_entity UNIQUE (provider, entity_type, provider_id)
);

CREATE INDEX ix_source_records_provider_lookup ON source_records (provider, provider_id);

UPDATE alembic_version SET version_num='0003_external_provider_tables' WHERE alembic_version.version_num = '0002_bibliographic_tables';

-- Running upgrade 0003_external_provider_tables -> 0004_user_tables

CREATE TYPE library_item_status AS ENUM ('to_read', 'reading', 'completed', 'abandoned');

CREATE TYPE library_item_visibility AS ENUM ('private', 'public');

CREATE TABLE users (
    id UUID NOT NULL, 
    handle VARCHAR(64) NOT NULL, 
    display_name VARCHAR(255), 
    avatar_url TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_users_handle UNIQUE (handle), 
    FOREIGN KEY(id) REFERENCES auth.users (id) ON DELETE CASCADE
);

CREATE TABLE library_items (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    user_id UUID NOT NULL, 
    work_id UUID NOT NULL, 
    preferred_edition_id UUID, 
    status library_item_status NOT NULL, 
    visibility library_item_visibility NOT NULL, 
    rating SMALLINT, 
    tags VARCHAR(64)[], 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_library_items_user_work UNIQUE (user_id, work_id), 
    CONSTRAINT ck_library_items_rating_range CHECK (rating >= 0 AND rating <= 10), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(work_id) REFERENCES works (id) ON DELETE RESTRICT, 
    FOREIGN KEY(preferred_edition_id) REFERENCES editions (id) ON DELETE SET NULL
);

CREATE INDEX ix_library_items_user_id ON library_items (user_id);

CREATE INDEX ix_library_items_status ON library_items (status);

CREATE INDEX ix_library_items_visibility ON library_items (visibility);

CREATE INDEX ix_library_items_tags ON library_items USING gin (tags);

CREATE TABLE reading_sessions (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    user_id UUID NOT NULL, 
    library_item_id UUID NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    ended_at TIMESTAMP WITH TIME ZONE, 
    pages_read INTEGER, 
    progress_percent NUMERIC(5, 2), 
    note TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_reading_sessions_pages_read_nonnegative CHECK (pages_read >= 0), 
    CONSTRAINT ck_reading_sessions_progress_percent_range CHECK (progress_percent >= 0 AND progress_percent <= 100), 
    CONSTRAINT ck_reading_sessions_ended_after_start CHECK (ended_at IS NULL OR ended_at >= started_at), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(library_item_id) REFERENCES library_items (id) ON DELETE CASCADE
);

CREATE INDEX ix_reading_sessions_user_id ON reading_sessions (user_id);

CREATE INDEX ix_reading_sessions_library_item_id ON reading_sessions (library_item_id);

CREATE TABLE reading_state_events (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    user_id UUID NOT NULL, 
    library_item_id UUID NOT NULL, 
    event_type VARCHAR(32) NOT NULL, 
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(library_item_id) REFERENCES library_items (id) ON DELETE CASCADE
);

CREATE INDEX ix_reading_state_events_user_id ON reading_state_events (user_id);

CREATE INDEX ix_reading_state_events_library_item_id ON reading_state_events (library_item_id);

CREATE INDEX ix_reading_state_events_occurred_at ON reading_state_events (occurred_at);

UPDATE alembic_version SET version_num='0004_user_tables' WHERE alembic_version.version_num = '0003_external_provider_tables';

-- Running upgrade 0004_user_tables -> 0005_content_tables

CREATE TYPE content_visibility AS ENUM ('private', 'public');

CREATE TYPE highlight_location_type AS ENUM ('page', 'percent', 'location', 'cfi');

CREATE TABLE notes (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    user_id UUID NOT NULL, 
    library_item_id UUID NOT NULL, 
    title VARCHAR(255), 
    body TEXT NOT NULL, 
    visibility content_visibility DEFAULT 'private'::content_visibility NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(library_item_id) REFERENCES library_items (id) ON DELETE CASCADE
);

CREATE INDEX ix_notes_user_id ON notes (user_id);

CREATE INDEX ix_notes_library_item_id ON notes (library_item_id);

CREATE INDEX ix_notes_visibility ON notes (visibility);

CREATE INDEX ix_notes_created_at ON notes (created_at);

CREATE TABLE highlights (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    user_id UUID NOT NULL, 
    library_item_id UUID NOT NULL, 
    quote TEXT NOT NULL, 
    location JSONB, 
    location_type highlight_location_type, 
    location_sort NUMERIC(10, 2), 
    visibility content_visibility DEFAULT 'private'::content_visibility NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(library_item_id) REFERENCES library_items (id) ON DELETE CASCADE
);

CREATE INDEX ix_highlights_user_id ON highlights (user_id);

CREATE INDEX ix_highlights_library_item_id ON highlights (library_item_id);

CREATE INDEX ix_highlights_visibility ON highlights (visibility);

CREATE INDEX ix_highlights_created_at ON highlights (created_at);

CREATE TABLE reviews (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    user_id UUID NOT NULL, 
    library_item_id UUID NOT NULL, 
    title VARCHAR(255), 
    body TEXT NOT NULL, 
    rating SMALLINT, 
    visibility content_visibility DEFAULT 'private'::content_visibility NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_reviews_user_library_item UNIQUE (user_id, library_item_id), 
    CONSTRAINT ck_reviews_rating_range CHECK (rating >= 0 AND rating <= 10), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(library_item_id) REFERENCES library_items (id) ON DELETE CASCADE
);

CREATE INDEX ix_reviews_user_id ON reviews (user_id);

CREATE INDEX ix_reviews_library_item_id ON reviews (library_item_id);

CREATE INDEX ix_reviews_visibility ON reviews (visibility);

CREATE INDEX ix_reviews_created_at ON reviews (created_at);

UPDATE alembic_version SET version_num='0005_content_tables' WHERE alembic_version.version_num = '0004_user_tables';

-- Running upgrade 0005_content_tables -> 0006_platform_tables

CREATE TYPE api_client_status AS ENUM ('active', 'suspended');

CREATE TABLE api_clients (
    client_id UUID DEFAULT gen_random_uuid() NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    owner_user_id UUID NOT NULL, 
    status api_client_status DEFAULT 'active'::api_client_status NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (client_id), 
    FOREIGN KEY(owner_user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_api_clients_owner_user_id ON api_clients (owner_user_id);

CREATE TABLE api_audit_logs (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    client_id UUID NOT NULL, 
    user_id UUID, 
    method VARCHAR(16) NOT NULL, 
    path TEXT NOT NULL, 
    status SMALLINT NOT NULL, 
    latency_ms INTEGER NOT NULL, 
    ip INET NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(client_id) REFERENCES api_clients (client_id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_api_audit_logs_client_user ON api_audit_logs (client_id, user_id);

CREATE INDEX ix_api_audit_logs_occurred_at ON api_audit_logs (occurred_at);

UPDATE alembic_version SET version_num='0006_platform_tables' WHERE alembic_version.version_num = '0005_content_tables';

-- Running upgrade 0006_platform_tables -> 0007_rls_policies

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;;

CREATE POLICY users_owner
        ON public.users
        FOR ALL
        TO authenticated
        USING (id = auth.uid())
        WITH CHECK (id = auth.uid());;

ALTER TABLE public.library_items ENABLE ROW LEVEL SECURITY;;

CREATE POLICY library_items_owner
        ON public.library_items
        FOR ALL
        TO authenticated
        USING (user_id = auth.uid())
        WITH CHECK (user_id = auth.uid());;

ALTER TABLE public.reading_sessions ENABLE ROW LEVEL SECURITY;;

CREATE POLICY reading_sessions_owner
        ON public.reading_sessions
        FOR ALL
        TO authenticated
        USING (user_id = auth.uid())
        WITH CHECK (user_id = auth.uid());;

ALTER TABLE public.reading_state_events ENABLE ROW LEVEL SECURITY;;

CREATE POLICY reading_state_events_owner
        ON public.reading_state_events
        FOR ALL
        TO authenticated
        USING (user_id = auth.uid())
        WITH CHECK (user_id = auth.uid());;

ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;;

CREATE POLICY notes_owner
        ON public.notes
        FOR ALL
        TO authenticated
        USING (user_id = auth.uid())
        WITH CHECK (user_id = auth.uid());;

ALTER TABLE public.highlights ENABLE ROW LEVEL SECURITY;;

CREATE POLICY highlights_owner
        ON public.highlights
        FOR ALL
        TO authenticated
        USING (user_id = auth.uid())
        WITH CHECK (user_id = auth.uid());;

ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;;

CREATE POLICY reviews_owner
        ON public.reviews
        FOR ALL
        TO authenticated
        USING (user_id = auth.uid())
        WITH CHECK (user_id = auth.uid());;

ALTER TABLE public.api_clients ENABLE ROW LEVEL SECURITY;;

CREATE POLICY api_clients_owner
        ON public.api_clients
        FOR ALL
        TO authenticated
        USING (owner_user_id = auth.uid())
        WITH CHECK (owner_user_id = auth.uid());;

ALTER TABLE public.api_audit_logs ENABLE ROW LEVEL SECURITY;;

CREATE POLICY api_audit_logs_read
        ON public.api_audit_logs
        FOR SELECT
        TO authenticated
        USING (
            EXISTS (
                SELECT 1
                FROM public.api_clients
                WHERE api_clients.client_id = api_audit_logs.client_id
                  AND api_clients.owner_user_id = auth.uid()
            )
        );;

ALTER TABLE public.authors ENABLE ROW LEVEL SECURITY;;

CREATE POLICY authors_read
        ON public.authors
        FOR SELECT
        TO authenticated
        USING (true);;

ALTER TABLE public.works ENABLE ROW LEVEL SECURITY;;

CREATE POLICY works_read
        ON public.works
        FOR SELECT
        TO authenticated
        USING (true);;

ALTER TABLE public.editions ENABLE ROW LEVEL SECURITY;;

CREATE POLICY editions_read
        ON public.editions
        FOR SELECT
        TO authenticated
        USING (true);;

ALTER TABLE public.work_authors ENABLE ROW LEVEL SECURITY;;

CREATE POLICY work_authors_read
        ON public.work_authors
        FOR SELECT
        TO authenticated
        USING (true);;

ALTER TABLE public.external_ids ENABLE ROW LEVEL SECURITY;;

CREATE POLICY external_ids_read
        ON public.external_ids
        FOR SELECT
        TO authenticated
        USING (true);;

ALTER TABLE public.source_records ENABLE ROW LEVEL SECURITY;;

CREATE POLICY source_records_read
        ON public.source_records
        FOR SELECT
        TO authenticated
        USING (true);;

UPDATE alembic_version SET version_num='0007_rls_policies' WHERE alembic_version.version_num = '0006_platform_tables';

COMMIT;

