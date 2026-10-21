-- Hackathon Five-Stage Verification Workflow:
-- 1. Extracted -> 2. Claims -> 3. Evidence -> 4. Verdict -> 5. Card
--
-- Note: Created for review. Do not apply directly to shared live DB without team review.

create table if not exists public.verification_runs (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references auth.users(id) on delete cascade,
  user_reel_id   bigint references public.user_reels(id) on delete set null,
  input_type     text not null default 'rvpack' check (input_type in ('rvpack', 'url', 'text')),
  raw_input      text not null,
  status         text not null default 'in_progress'
                 check (status in ('in_progress', 'completed', 'failed')),
  current_stage  text not null default 'extracted'
                 check (current_stage in ('extracted', 'claims', 'evidence', 'verdict', 'card', 'completed')),
  error_message  text,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create index if not exists verification_runs_user_idx
  on public.verification_runs (user_id, created_at desc);

create table if not exists public.verification_stages (
  id             uuid primary key default gen_random_uuid(),
  run_id         uuid not null references public.verification_runs(id) on delete cascade,
  stage_name     text not null
                 check (stage_name in ('extracted', 'claims', 'evidence', 'verdict', 'card')),
  stage_order    int not null
                 check (stage_order between 1 and 5),
  status         text not null default 'completed'
                 check (status in ('completed', 'failed', 'in_progress')),
  payload        jsonb not null default '{}'::jsonb,
  created_at     timestamptz not null default now(),
  unique (run_id, stage_name),
  unique (run_id, stage_order)
);

create index if not exists verification_stages_run_order_idx
  on public.verification_stages (run_id, stage_order asc);

-- Row Level Security
alter table public.verification_runs enable row level security;
alter table public.verification_stages enable row level security;

create policy "users read own verification runs"
  on public.verification_runs for select to authenticated
  using ((select auth.uid()) = user_id);

create policy "users read own verification stages"
  on public.verification_stages for select to authenticated
  using (
    exists (
      select 1 from public.verification_runs vr
      where vr.id = verification_stages.run_id and vr.user_id = (select auth.uid())
    )
  );
