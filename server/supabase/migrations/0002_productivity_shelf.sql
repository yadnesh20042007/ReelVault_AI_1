-- Per-user productivity saves. Source posts remain globally cached; these are private bookmarks.
create table public.user_saved_links (
  id           bigint generated always as identity primary key,
  user_id      uuid not null references auth.users(id) on delete cascade,
  user_reel_id bigint not null references public.user_reels(id) on delete cascade,
  label        text not null,
  url          text not null,
  created_at   timestamptz not null default now(),
  unique (user_id, user_reel_id, url)
);
create index user_saved_links_user_created_idx on public.user_saved_links (user_id, created_at desc);

create table public.user_saved_dates (
  id           bigint generated always as identity primary key,
  user_id      uuid not null references auth.users(id) on delete cascade,
  user_reel_id bigint not null references public.user_reels(id) on delete cascade,
  label        text not null,
  event_date   date not null,
  created_at   timestamptz not null default now(),
  unique (user_id, user_reel_id, event_date, label)
);
create index user_saved_dates_user_event_idx on public.user_saved_dates (user_id, event_date);

alter table public.user_saved_links enable row level security;
alter table public.user_saved_dates enable row level security;
create policy "users read own saved links" on public.user_saved_links for select to authenticated using ((select auth.uid()) = user_id);
create policy "users read own saved dates" on public.user_saved_dates for select to authenticated using ((select auth.uid()) = user_id);
