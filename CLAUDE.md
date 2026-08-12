# Price Battle — Project Reference

## What is Price Battle?

Price Battle is a web app for comparing Apple product prices across countries that have an Apple Store or Apple Store Online. Staff at Apple Store Iconsiam and Apple Store Central World use it on-site.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Main app — THB base currency, `apc_*` localStorage keys |
| `price-battle-one.html` | Copy of the app for a second site (one-shortcuts.github.io). Snapshot — does not yet have the tabs added in index.html. Trade-in data is kept in sync with index.html |
| `Japan-based.html` | Japan variant — JPY base currency, `jpb_*` localStorage keys (may be deleted from main; lives in feature branch) |
| `dashboard.html` | Analytics dashboard — reads from Supabase |

## Tabs

The app has four tabs (`switchMode()`, order as shown). The mode switcher was hidden for a long time; the last selected tab is remembered in `apc_mode`.

| Tab | Mode key | Purpose |
|-----|----------|---------|
| **Battle** | `pz` | The original country-vs-Thailand comparison |
| **List** | `ls` | Every model ranked by how much cheaper Thailand is |
| **AppleCare+** | `ac` | AppleCare+ price as a % of device price, and vs repair costs |
| **Repair** | `gb` | Out-of-warranty repair cost vs buying new |

> Each `mode-view` must be a **sibling** of the others. A missing `</div>` once nested Repair/Trade-in/AppleCare+ inside the Battle view, which silently hid them all (a parent with `display:none` hides its whole subtree regardless of the child's own `show` class).

## Battle tab

1. User selects a **comparison country**
2. User selects a **product category**: iPhone, iPad, Mac, Apple Watch, AirPods, Apple TV, HomePod, Beats, AirTag, and iPhone/iPad/Mac/Watch Accessories
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

Notes are the country-level list **concatenated with** the per-model list. The seeding CSV wrote identical text into both, so every note rendered twice for 15 countries — `renderCountryNotes()` now de-duplicates case/whitespace-insensitively at render time, which also protects against a future CSV repeating the mistake.

#### AppleCare+ bundle toggle
A third inline toggle (order: VAT Refund → AppleCare+ → Trade-in) that adds the model's AppleCare+ price to **both** sides of the comparison, each using that country's own AppleCare+ price — unlike VAT Refund/Trade-in, which only reduce the Thailand side. Shown only for categories that have AppleCare+ pricing, and it applies to every eligible item when a bundle is in the cart.

**AppleCare+ is not VAT-refundable**, so the VAT bracket is looked up on the device price alone, not the AppleCare+-inclusive total.

## List tab

Shows **every model and storage tier at once**, ranked by how much cheaper Thailand is than the comparison country — the answer to "which items are worth buying here?"

**Flow:** pick a comparison country → pick a category pill → the ranked list appears.

- **Country carries over from Battle** (and back). Both tabs share one selection so switching tabs never asks for the country again. `applyLsCountry()` is the pure state/UI update used for syncing and rebuilds; `pickLsCountry()` is the user action and is the only path that reports the `country_select` analytics event.
- **Category pills** match Battle exactly (`LS_CATS = CAT_KEYS`), plus an **All** pill selected by default that merges every category and re-sorts globally (~181 items).
- **VAT Refund toggle, on by default** — independent of Battle's own VAT toggle. Recomputes the Thailand price and re-sorts live; items can flip from "foreign cheaper" to "Thailand cheaper" once the refund applies.
- **Both price columns show native + converted currency**, so a row reads in either direction.
- **The cheaper side is printed in green** (both its lines), explained by a "🟢 is great price" legend.
- **Tap the SAVE header to flip the sort**: `Save ↑` = biggest Thailand saving first (default), `Save ↓` = smallest first. The direction persists across category and country changes.
- The column header row is **sticky**, pinned below the 44px sticky nav.

AppleCare+ entries are skipped here — a service, not a device, and it has its own tab.

### Data updates
All product prices, trade-in values, URL links, and country notes come from **CSV files supplied by the user** when there is a price update. No automatic scraping.

### Exchange rates
Live exchange rate API already in place and working well. Rates update automatically on app load with an 8-second fetch timeout fallback to default rates.

## AppleCare+ tab

Category → model → storage. Shows a table of **every storage tier at once** (Storage | Price | AppleCare+ | Ratio), because AppleCare+ costs the same regardless of storage — so the ratio falls as capacity rises (iPhone 17 Pro Max: 256GB 15.9% → 2TB 9.6%).

Below it, **AppleCare+ Ratio with Repair** lists each repair issue as full repair cost → AppleCare+ service fee → ratio, ordered Battery service → Screen damage → Back glass → Other damage (`AC_ISSUE_ORDER`).

AppleCare+ prices live in `CSV_PRICES` under keys like `iPhone - AppleCare+ - 17 Pro Max`; `acRowFor(cat, rawName)` maps a device model to its key (strips the "iPhone "/"Apple Watch " prefix, collapses all Apple TV variants to one).

`GB_APPLECARE_FEE` holds the AppleCare+ **service fees** (what you pay per repair when covered). Currently iPhone only — battery ฿0, screen ฿1,000, back glass ฿1,000, other damage ฿3,300. Other categories need their fee schedules before those rows will show.

## Repair tab

Out-of-warranty repair pricing (`GB_REPAIR_FAMILIES` / `GB_REPAIR_ISSUES` / `GB_REPAIR_PRICE_DATA`, keyed by Apple's own `TAG_…` product ids) compared against buying new.

**Repair prices are updated by hand from CSV/screenshots, not scraped.** Live scraping isn't possible from the browser (CORS blocks calling support.apple.com from a static GitHub Pages site). A scheduled GitHub Action that scrapes and opens a PR would work, but hasn't been built.

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

## Layout gotchas worth remembering

- **Scope selectors per tab.** The Battle and List dropdowns share the `.ddo`/`.ddrl` classes. Document-wide queries in `filterDd()` and `pickCountry()` were reaching into the other tab and clearing its options/checkmark — both are now scoped to `#ddopts` / `#ls-ddopts`.
- **`G()` caches elements by id.** Anything rebuilt at runtime (the List dropdown is rebuilt on language switch) must be re-queried, or `G()` hands back a stale detached node.
- **`position:sticky` needs a non-clipping ancestor.** The List card had to drop `overflow:hidden`, with the rounded top corners moved onto the header row instead.
- **`1fr` is `minmax(auto,1fr)`** — its min-content floor pushed the Save pill outside the card at large accessibility text sizes. Use `minmax(0,…)` for tracks that should shrink, and `minmax(max-content,…)` for one that must never clip its contents.
- **`align-items:baseline`** on the List rows keeps a wrapped product name on the same line as its price; `align-items:center` floated it above.
