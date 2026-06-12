-- Price Battle · Supabase Analytics Setup
-- Run this in the Supabase SQL Editor

-- ── TABLES ────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS pb_events (
  id          BIGSERIAL PRIMARY KEY,
  event_type  TEXT NOT NULL,
  country_code TEXT,
  country_name TEXT,
  country_zone TEXT,
  product_name TEXT,
  category    TEXT,
  session_id  TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pb_sessions (
  session_id  TEXT PRIMARY KEY,
  last_seen   TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for dashboard queries
CREATE INDEX IF NOT EXISTS pb_events_type_time ON pb_events (event_type, created_at);
CREATE INDEX IF NOT EXISTS pb_sessions_last_seen ON pb_sessions (last_seen);

-- ── RLS ───────────────────────────────────────────────────────────────────────

ALTER TABLE pb_events  ENABLE ROW LEVEL SECURITY;
ALTER TABLE pb_sessions ENABLE ROW LEVEL SECURITY;

-- Anon can insert events
CREATE POLICY "anon_insert_events" ON pb_events
  FOR INSERT TO anon WITH CHECK (true);

-- Anon can upsert sessions
CREATE POLICY "anon_insert_sessions" ON pb_sessions
  FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "anon_update_sessions" ON pb_sessions
  FOR UPDATE TO anon USING (true);

-- ── RPC: get_dashboard ────────────────────────────────────────────────────────
-- Returns aggregated stats for a given time window.
-- Usage: POST /rest/v1/rpc/get_dashboard  body: {"since_ts": "2026-06-06T00:00:00Z"}

CREATE OR REPLACE FUNCTION get_dashboard(since_ts TIMESTAMPTZ DEFAULT NOW() - INTERVAL '1 day')
RETURNS JSON LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'total_opens', (
      SELECT COUNT(*) FROM pb_events
      WHERE event_type = 'page_open' AND created_at >= since_ts
    ),
    'active_now', (
      SELECT COUNT(*) FROM pb_sessions
      WHERE last_seen >= NOW() - INTERVAL '2 minutes'
    ),
    'trade_toggles', (
      SELECT COUNT(*) FROM pb_events
      WHERE event_type = 'trade_toggle' AND created_at >= since_ts
    ),
    'bundle_adds', (
      SELECT COUNT(*) FROM pb_events
      WHERE event_type = 'bundle_add' AND created_at >= since_ts
    ),
    'top_zones', (
      SELECT COALESCE(json_agg(z ORDER BY z.cnt DESC), '[]'::json)
      FROM (
        SELECT country_zone AS zone, COUNT(*) AS cnt
        FROM pb_events
        WHERE event_type = 'country_select' AND created_at >= since_ts
          AND country_zone IS NOT NULL
        GROUP BY country_zone
        ORDER BY cnt DESC LIMIT 5
      ) z
    ),
    'top_countries', (
      SELECT COALESCE(json_agg(c ORDER BY c.cnt DESC), '[]'::json)
      FROM (
        SELECT country_code, country_name, COUNT(*) AS cnt
        FROM pb_events
        WHERE event_type = 'country_select' AND created_at >= since_ts
          AND country_code IS NOT NULL
        GROUP BY country_code, country_name
        ORDER BY cnt DESC LIMIT 5
      ) c
    ),
    'top_products', (
      SELECT COALESCE(json_agg(p ORDER BY p.cnt DESC), '[]'::json)
      FROM (
        SELECT product_name, category, COUNT(*) AS cnt
        FROM pb_events
        WHERE event_type = 'product_select' AND created_at >= since_ts
          AND product_name IS NOT NULL
        GROUP BY product_name, category
        ORDER BY cnt DESC LIMIT 5
      ) p
    )
  ) INTO result;
  RETURN result;
END;
$$;

GRANT EXECUTE ON FUNCTION get_dashboard TO anon;
