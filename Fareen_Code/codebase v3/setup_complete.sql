-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Candidates Table
create table if not exists candidates (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  email text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Videos Table
create table if not exists videos (
  id uuid primary key default uuid_generate_v4(),
  candidate_id uuid references candidates(id) not null,
  storage_path text not null,
  status text not null default 'processing', -- 'processing', 'completed', 'failed'
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Analysis Results Table
create table if not exists analysis_results (
  id uuid primary key default uuid_generate_v4(),
  video_id uuid references videos(id) not null,
  transcript text,
  speaking_rate float,
  pause_count integer,
  filler_count integer,
  loudness_db float,
  score float,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on all tables
alter table candidates enable row level security;
alter table videos enable row level security;
alter table analysis_results enable row level security;

-- Create permissive policies for development (allows all operations)
-- Drop existing policies if they exist to avoid errors on re-run
drop policy if exists "Enable all access for candidates" on candidates;
drop policy if exists "Enable all access for videos" on videos;
drop policy if exists "Enable all access for analysis_results" on analysis_results;

-- Candidates
create policy "Enable all access for candidates" 
on candidates for all 
using (true) 
with check (true);

-- Videos
create policy "Enable all access for videos" 
on videos for all 
using (true) 
with check (true);

-- Analysis Results
create policy "Enable all access for analysis_results" 
on analysis_results for all 
using (true) 
with check (true);
