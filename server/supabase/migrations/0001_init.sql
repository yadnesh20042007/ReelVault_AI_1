-- Global cache of public reel content (shared by all users; saves vendor credits)
create table public.source_posts (
  id            bigint generated always as identity primary key,
  platform      text not null check (platform in ('instagram','youtube','tiktok')),
  shortcode     text not null,
  url           text not null,
  author        text,
  transcript    text,
  caption       text,
  posted_at     timestamptz,
  language_hint text,
  raw           jsonb,
  created_at    timestamptz not null default now(),
  unique (platform, shortcode)
);

-- A user's history entry (their link to a source post)
create table public.user_reels (
  id             bigint generated always as identity primary key,
  user_id        uuid   not null references auth.users(id) on delete cascade,
  source_post_id bigint not null references public.source_posts(id) on delete cascade,
  created_at     timestamptz not null default now(),
  unique (user_id, source_post_id)
);
create index user_reels_user_created_idx on public.user_reels (user_id, created_at desc);

-- One row per deep-cook run
create table public.deep_cooks (
  id             bigint generated always as identity primary key,
  user_reel_id   bigint not null references public.user_reels(id) on delete cascade,
  user_id        uuid   not null references auth.users(id) on delete cascade,
  status         text   not null default 'queued'
                 check (status in ('queued','classifying','extracting','verifying','researching',
                                   'done','not_opportunity','failed')),
  error_code     text,
  classification jsonb,
  extracted      jsonb,
  verification   jsonb,
  report         jsonb,
  tool_calls     int,
  created_at     timestamptz not null default now(),
  finished_at    timestamptz
);
create index deep_cooks_reel_idx on public.deep_cooks (user_reel_id, created_at desc);
create index deep_cooks_user_idx on public.deep_cooks (user_id, created_at desc);

-- Row Level Security (defense in depth; the backend's service-role key bypasses it)
alter table public.source_posts enable row level security;
alter table public.user_reels   enable row level security;
alter table public.deep_cooks   enable row level security;

create policy "users read own reels" on public.user_reels
  for select to authenticated using ((select auth.uid()) = user_id);
create policy "users read own deep cooks" on public.deep_cooks
  for select to authenticated using ((select auth.uid()) = user_id);
-- source_posts: intentionally NO policies -> no direct client access.
-- No insert/update/delete policies anywhere: only the backend writes.
