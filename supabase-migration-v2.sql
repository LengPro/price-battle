-- Price Battle · Migration v2
-- Run this if you already ran supabase-setup.sql (adds site_id support)

ALTER TABLE pb_events ADD COLUMN IF NOT EXISTS site_id TEXT;

CREATE INDEX IF NOT EXISTS pb_events_site ON pb_events (site_id);

-- Updated get_dashboard with optional site_id filter
CREATE OR REPLACE FUNCTION get_dashboard(
  since_ts   TIMESTAMPTZ DEFAULT NOW() - INTERVAL '1 day',
  until_ts   TIMESTAMPTZ DEFAULT NULL,
  p_site_id  TEXT        DEFAULT NULL
)
RETURNS JSON LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  result JSON;
  _until TIMESTAMPTZ;
BEGIN
  _until := COALESCE(until_ts, NOW());

  SELECT json_build_object(
    'total_opens', (
      SELECT COUNT(*) FROM pb_events
      WHERE event_type = 'page_open'
        AND created_at >= since_ts AND created_at <= _until
        AND (p_site_id IS NULL OR site_id = p_site_id)
    ),
    'active_now', (
      SELECT COUNT(*) FROM pb_sessions
      WHERE last_seen >= NOW() - INTERVAL '2 minutes'
    ),
    'trade_toggles', (
      SELECT COUNT(*) FROM pb_events
      WHERE event_type = 'trade_toggle'
        AND created_at >= since_ts AND created_at <= _until
        AND (p_site_id IS NULL OR site_id = p_site_id)
    ),
    'bundle_adds', (
      SELECT COUNT(*) FROM pb_events
      WHERE event_type = 'bundle_add'
        AND created_at >= since_ts AND created_at <= _until
        AND (p_site_id IS NULL OR site_id = p_site_id)
    ),
    'top_zones', (
      SELECT COALESCE(json_agg(z ORDER BY z.cnt DESC), '[]'::json)
      FROM (
        SELECT country_zone AS zone, COUNT(*) AS cnt
        FROM pb_events
        WHERE event_type = 'country_select'
          AND created_at >= since_ts AND created_at <= _until
          AND country_zone IS NOT NULL
          AND (p_site_id IS NULL OR site_id = p_site_id)
        GROUP BY country_zone ORDER BY cnt DESC LIMIT 5
      ) z
    ),
    'top_countries', (
      SELECT COALESCE(json_agg(c ORDER BY c.cnt DESC), '[]'::json)
      FROM (
        SELECT country_code, country_name, COUNT(*) AS cnt
        FROM pb_events
        WHERE event_type = 'country_select'
          AND created_at >= since_ts AND created_at <= _until
          AND country_code IS NOT NULL
          AND (p_site_id IS NULL OR site_id = p_site_id)
        GROUP BY country_code, country_name ORDER BY cnt DESC LIMIT 10
      ) c
    ),
    'top_products', (
      SELECT COALESCE(json_agg(p ORDER BY p.cnt DESC), '[]'::json)
      FROM (
        SELECT product_name, category, COUNT(*) AS cnt
        FROM pb_events
        WHERE event_type = 'product_select'
          AND created_at >= since_ts AND created_at <= _until
          AND product_name IS NOT NULL
          AND (p_site_id IS NULL OR site_id = p_site_id)
        GROUP BY product_name, category ORDER BY cnt DESC LIMIT 10
      ) p
    ),
    'site_ids', (
      SELECT COALESCE(json_agg(DISTINCT site_id), '[]'::json)
      FROM pb_events WHERE site_id IS NOT NULL
    )
  ) INTO result;
  RETURN result;
END;
$$;

GRANT EXECUTE ON FUNCTION get_dashboard TO anon;
