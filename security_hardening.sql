-- security_hardening.sql

-- ==============================================================================
-- SECURITY HARDENING SCRIPT
-- ==============================================================================
-- This script enables Row Level Security (RLS) on custom voting tables
-- and implements policies to enforce least privilege.

-- 1. Enable RLS on all custom application tables.
-- Idempotency: ALTER TABLE does not fail if RLS is already enabled.
-- Note: This assumes tables are in the 'public' schema, which is standard for Django/Supabase.
ALTER TABLE IF EXISTS voting_election ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS voting_candidate ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS voting_vote ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS voting_securitylog ENABLE ROW LEVEL SECURITY;

-- 2. Public Read Policies for non-sensitive tables.
-- These tables are deemed safe for public reading (e.g., list of elections/candidates).
-- 'TO public' in PostgreSQL covers all database roles (including API users).

-- Election Table: Allow anyone to view election details.
DROP POLICY IF EXISTS "Allow public read-only access to Elections" ON voting_election;
CREATE POLICY "Allow public read-only access to Elections" ON voting_election
FOR SELECT TO public USING (TRUE);

-- Candidate Table: Allow anyone to view candidate details.
DROP POLICY IF EXISTS "Allow public read-only access to Candidates" ON voting_candidate;
CREATE POLICY "Allow public read-only access to Candidates" ON voting_candidate
FOR SELECT TO public USING (TRUE);

-- 3. Total Restriction for sensitive tables.
-- By enabling RLS and NOT defining any ALLOW policies, we enforce
-- a "deny-all" access policy by default. This effectively secures
-- sensitive columns (encrypted_vote, voter_ip, ip_address, etc.)
-- from all Supabase Data API access.

-- Explicitly drop any existing policies to ensure a clean slate.
DROP POLICY IF EXISTS "Restrict all access to Votes" ON voting_vote;
DROP POLICY IF EXISTS "Restrict all access to SecurityLogs" ON voting_securitylog;

-- ==============================================================================
-- END OF SCRIPT
-- ==============================================================================
