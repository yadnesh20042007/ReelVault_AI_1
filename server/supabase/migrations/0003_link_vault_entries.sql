-- A focused resource bundle: all useful links and search prompts from one reel.
create table public.user_link_vault_entries (
  id           bigint generated always as identity primary key,
  user_id      uuid not null references auth.users(id) on delete cascade,
  user_reel_id bigint not null references public.user_reels(id) on delete cascade,
  title        text not null,
  links        jsonb not null default '[]'::jsonb,
  topics       jsonb not null default '[]'::jsonb,
  created_at   timestamptz not null default now(),
  unique (user_id, user_reel_id)
);
create index user_link_vault_entries_user_created_idx
  on public.user_link_vault_entries (user_id, created_at desc);

alter table public.user_link_vault_entries enable row level security;
create policy "users read own link vault entries"
  on public.user_link_vault_entries for select to authenticated
  using ((select auth.uid()) = user_id);
