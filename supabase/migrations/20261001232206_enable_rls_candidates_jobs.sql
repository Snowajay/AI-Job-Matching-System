-- Enable RLS on public.candidates and public.jobs.
--
-- Neither table is queried through Supabase's client-side API (PostgREST) —
-- the codebase has no supabase-js usage and no anon/service key anywhere;
-- the FastAPI backend is the only consumer, connecting directly via
-- SQLAlchemy/psycopg2 as the postgres role, which bypasses RLS. So this
-- enables RLS with no policies, which only changes behavior for the
-- anon/authenticated roles used by Supabase's REST API, locking them out.
ALTER TABLE public.candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
