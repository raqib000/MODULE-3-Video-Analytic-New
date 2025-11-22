-- Enable RLS on all tables
alter table candidates enable row level security;
alter table videos enable row level security;
alter table analysis_results enable row level security;

-- Create permissive policies for development (allows all operations)
-- WARNING: For production, you should restrict these policies!

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
