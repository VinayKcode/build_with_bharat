-- ===================================================
-- Supabase Schema for Golden Hour (Build with Bharat 4.0)
-- Run this in your Supabase Project -> SQL Editor
-- ===================================================

-- 1. Create Hospitals Table
CREATE TABLE IF NOT EXISTS public.hospitals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    has_trauma BOOLEAN NOT NULL DEFAULT true,
    has_cathlab BOOLEAN NOT NULL DEFAULT false,
    icu_beds INTEGER NOT NULL DEFAULT 0,
    blood_units INTEGER NOT NULL DEFAULT 0,
    rating DOUBLE PRECISION NOT NULL DEFAULT 4.0,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Create Accidents / Emergency Logs Table (for real-time dispatch tracking)
CREATE TABLE IF NOT EXISTS public.accident_logs (
    id BIGSERIAL PRIMARY KEY,
    crash_lat DOUBLE PRECISION NOT NULL,
    crash_lon DOUBLE PRECISION NOT NULL,
    location_method TEXT DEFAULT 'GPS_HIGH_ACCURACY',
    crash_type TEXT DEFAULT 'IMPACT_G_SPIKE',
    speed_drop TEXT,
    allocated_hospital TEXT,
    patient_blood_group TEXT,
    patient_weight_kg DOUBLE PRECISION,
    patient_height_cm DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Enable Row Level Security (RLS) & Allow Public Read/Write for Hackathon Demo
ALTER TABLE public.hospitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accident_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read on hospitals"
ON public.hospitals FOR SELECT
USING (true);

CREATE POLICY "Allow public update on hospitals"
ON public.hospitals FOR UPDATE
USING (true);

CREATE POLICY "Allow public insert on hospitals"
ON public.hospitals FOR INSERT
WITH CHECK (true);

CREATE POLICY "Allow public read on accident_logs"
ON public.accident_logs FOR SELECT
USING (true);

CREATE POLICY "Allow public insert on accident_logs"
ON public.accident_logs FOR INSERT
WITH CHECK (true);

-- 4. Enable Realtime Replication for the tables
ALTER PUBLICATION supabase_realtime ADD TABLE public.hospitals;
ALTER PUBLICATION supabase_realtime ADD TABLE public.accident_logs;

-- 5. Insert Initial Hospital Data (Kannauj / NH-9 Region)
INSERT INTO public.hospitals (id, name, lat, lon, has_trauma, has_cathlab, icu_beds, blood_units, rating, phone, address)
VALUES
    ('H101', 'District Hospital Kannauj (Rajkiya)', 27.0520, 79.9180, true, true, 4, 12, 4.3, '+91 5694 234101', 'Makrand Nagar, Kannauj'),
    ('H102', 'Sanjeevani Trauma & Critical Care', 27.0650, 79.9350, true, true, 6, 18, 4.8, '+91 5694 238202', 'GT Road, Kannauj By-Pass'),
    ('H103', 'City Life Care Clinic', 27.0390, 79.9050, false, false, 0, 2, 3.9, '+91 5694 231303', 'Saraimeera, Kannauj'),
    ('H104', 'Apex Super Specialty & Neuro Trauma', 27.0800, 79.9500, true, true, 8, 24, 4.6, '+91 5694 245404', 'NH-9 Expressway Link, Kannauj'),
    ('H105', 'Highway Emergency First-Aid Center', 27.0250, 79.8850, true, false, 2, 4, 4.1, '+91 5694 222505', 'Tirwa Road Junction, Kannauj')
ON CONFLICT (id) DO UPDATE 
SET 
    name = EXCLUDED.name,
    has_trauma = EXCLUDED.has_trauma,
    has_cathlab = EXCLUDED.has_cathlab,
    icu_beds = EXCLUDED.icu_beds,
    blood_units = EXCLUDED.blood_units,
    rating = EXCLUDED.rating;
