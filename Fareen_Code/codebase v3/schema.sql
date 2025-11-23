-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Candidates Table
create table candidates (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  email text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Videos Table
create table videos (
  id uuid primary key default uuid_generate_v4(),
  candidate_id uuid references candidates(id) not null,
  storage_path text not null,
  status text not null default 'processing', -- 'processing', 'completed', 'failed'
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Analysis Results Table
create table analysis_results (
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
