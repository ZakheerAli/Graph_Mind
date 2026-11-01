create extension if not exists vector with schema extensions;

create table public.documents (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    title text not null,
    filename text not null,
    storage_path text not null,
    status text not null default 'QUEUED'
        check (status in ('QUEUED', 'PROCESSING', 'READY', 'FAILED')),
    error text,
    page_count integer not null default 0 check (page_count >= 0),
    created_at timestamptz not null default now(),
    unique (id, user_id)
);

create index documents_user_created_at_idx
    on public.documents (user_id, created_at desc);

create table public.chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null,
    user_id uuid not null references auth.users (id) on delete cascade,
    chunk_index integer not null check (chunk_index >= 0),
    page integer not null check (page > 0),
    content text not null check (length(content) > 0),
    token_count integer not null default 0 check (token_count >= 0),
    embedding extensions.vector(384),
    tsv tsvector generated always as (
        to_tsvector('english'::regconfig, content)
    ) stored,
    foreign key (document_id, user_id)
        references public.documents (id, user_id)
        on delete cascade,
    unique (document_id, chunk_index)
);

create index chunks_user_document_idx
    on public.chunks (user_id, document_id);

create index chunks_tsv_idx
    on public.chunks using gin (tsv);

create index chunks_embedding_hnsw_idx
    on public.chunks using hnsw (embedding extensions.vector_cosine_ops);

alter table public.documents enable row level security;
alter table public.documents force row level security;
create policy "Users can manage their own documents"
    on public.documents
    for all
    to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

alter table public.chunks enable row level security;
alter table public.chunks force row level security;
create policy "Users can manage their own chunks"
    on public.chunks
    for all
    to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);
