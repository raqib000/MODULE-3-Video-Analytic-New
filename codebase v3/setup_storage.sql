-- Create the storage bucket 'videos' if it doesn't exist
insert into storage.buckets (id, name, public)
values ('videos', 'videos', false)
on conflict (id) do nothing;

-- Enable RLS on objects
alter table storage.objects enable row level security;

-- Create permissive policies for storage (development only)
create policy "Give me access to own video 1337" on storage.objects for all using ( bucket_id = 'videos' ) with check ( bucket_id = 'videos' );
