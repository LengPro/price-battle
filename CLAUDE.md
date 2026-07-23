# Price Battle — Project Reference

## What is Price Battle?

Price Battle is a web app for comparing Apple product prices across countries that have an Apple Store or Apple Store Online. Staff at Apple Store Iconsiam and Apple Store Central World use it on-site.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Main app — THB base currency, `apc_*` localStorage keys |
| `Japan-based.html` | Japan variant — JPY base currency, `jpb_*` localStorage keys (may be deleted from main; lives in feature branch) |
| `dashboard.html` | Analytics dashboard — reads from Supabase |

## How the app works

1. User selects a **comparison country**
2. User selects a **product category**: iPhone, iPad, Mac, Apple Watch, AirPods, iPhone Accessories, iPad Accessories, Mac Accessories
3. Prices display side-by-side; the cheaper country gets a **green background + 👍 emoji**
4. A **summary** shows how much cheaper and the % saving

### Key features

#### VAT Refund toggle
When enabled, recalculates prices after deducting the local VAT refund. Shows the VAT refund value separately.

#### Trade-In
User selects a device to trade in. Trade-in value is deducted from the comparison. Trade-in values come from CSV data supplied by the user.

#### Bundle Adds (Add to Bundle)
Select **multiple products at once** (no quantity limit). When a main device (iPhone, iPad, Mac, Apple Watch) is selected, **suggested accessories** appear below. The bundle total price is compared across countries in real time. Works with VAT Refund and Trade-In.

#### URL Links
Each product has a direct link to the Apple website page for that country. Links come from the CSV data file.

#### Country Notes
Per-country notes that describe limitations or differences (e.g. stock availability, model differences). Data comes from CSV.

### Data updates
All product prices, trade-in values, URL links, and country notes come from **CSV files supplied by the user** when there is a price update. No automatic scraping.

### Exchange rates
Live exchange rate API already in place and working well. Rates update automatically on app load with an 8-second fetch timeout fallback to default rates.

## Analytics (dashboard.html)

Tracked at two physical locations:
- **Apple Store Iconsiam** (`iconsiam`)
- **Apple Store Central World** (`centralworld`)

### Events tracked
| Metric | Description |
|--------|-------------|
| Active Now | Live sessions in the last 2 minutes |
| Total Opens | Page load count |
| Trade-In Toggles | Toggle on/off events |
| Bundle Adds | "Add to Bundle" button presses |

### Dashboard display
- Top 5 Regions selected most
- Top 10 Countries compared most
- Top 10 Products compared most
- Period filters: Today, Yesterday, 7 Days, 30 Days, Custom
- Site filter: All / ICON / CTW
- Trend charts (line + dot) for Opens / Trade-In / Bundle Adds on 7-day+ views — requires Supabase RPC `get_dashboard_daily` returning `[{day, total_opens, trade_toggles, bundle_adds}]`

### Supabase
- URL: `https://pclutmwvjdkcctlsrhuc.supabase.co`
- RPC `get_dashboard` — aggregate stats
- RPC `get_dashboard_daily` — daily time-series for trend charts
- Auto-refresh every 30 seconds

## APP_VERSION

`index.html` (and `Japan-based.html` when active) has an `APP_VERSION` constant used for cache-busting localStorage on version change.

**Always update it on every code change** using Bangkok time:
```bash
TZ=Asia/Bangkok date +"%d.%m.%Y-%H:%M"
```

Format: `"DD.MM.YYYY-HH:MM"` for index.html, `"DD.MM.YYYY-HH:MM-JP"` for Japan-based.html.

The version is visible inside the Gear (admin) panel in the UI — currently hidden from users.

## localStorage key namespacing

| Prefix | App |
|--------|-----|
| `apc_*` | index.html (THB base) |
| `jpb_*` | Japan-based.html (JPY base) |

Contamination protection in `initApp()` detects cross-prefix keys and clears them.

## Git workflow

- Feature branch: `claude/price-battle-fqaf9r`
- Always commit + push to feature branch, then merge to `main`
- Validate JS before committing:
```bash
node -e "var fs=require('fs');var html=fs.readFileSync('index.html','utf8');var m=html.match(/<script>([\s\S]*?)<\/script>/g);var ok=true;m.forEach(function(s,i){var js=s.replace(/<\/?script>/g,'');try{new Function(js);}catch(e){console.error('Block '+i+': '+e.message);ok=false;}});if(ok)console.log('JS OK');"
```

## iOS Safari notes

- `touch-action: manipulation` (not `pan-y`) on dropdown option buttons — `pan-y` suppresses click in scrollable containers
- Direct `touchstart`/`touchend` listeners on `.ddo` buttons bypass iOS click suppression in `overflow-y:auto` containers
- Tap detection: movement < 10px AND duration < 600ms = confirmed tap
