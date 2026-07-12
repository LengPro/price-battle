# Price Battle — Project Knowledge

## Overview
**Price Battle** is a single-file web app (`index.html`) that compares Apple product prices between Thailand (base) and other supported Apple Store countries/regions. Users can quickly find where to buy their next Apple device at the best price, compare multiple items as a bundle, and add suggested accessories.

---

## Tech Stack
- Single HTML file — no framework, no build tool
- Vanilla JS + CSS (CSS variables for theming)
- Data stored in `localStorage`
- Exchange rates fetched live from external API
- Deployed / shared as a standalone `.html` file

---

## Core Features

### 1. Price Comparison
- Select country → category → model → storage size
- Shows Thailand price vs selected country price side-by-side
- Prices stored in `CSV_PRICES` constant (keyed by product key e.g. `"iPhone - iPhone 17 Pro - 256GB"`)
- Exchange rate converts prices between THB and foreign currency

### 2. Price Difference Display
- Shows savings in foreign currency amount (e.g. "Save ¥173")
- Shows savings as percentage: formula = `(foreign - thailand) / foreign × 100`
- Green = Thailand is cheaper, Red = foreign is cheaper
- Thumbs up 👍 shown on winning side

### 3. VAT Refund (Thailand)
- Toggle on/off
- Deducts VAT refund amount from Thailand price
- Shows breakdown: base price − VAT refund = effective price
- Official Thai Tourist VAT Refund table used

### 4. Sales Tax (USA & Canada only)
- Appears below price columns when USA or Canada is selected
- User enters ZIP code (USA) or postal code prefix (Canada)
- **USA**: Looks up combined rate (state + county + city) from 922 ZIP prefixes hardcoded table. Falls back to state-only rate if prefix not found
- **Canada**: Looks up province from first letter of postal code → combined GST/HST/PST rate
- Shows: state/province name, base price, tax rate (combined or state-only), tax amount, total with tax
- Toggle "Include tax in comparison" → updates price display and diff calculation
- No external API used — fully offline/hardcoded

### 5. Store Links
- "View on Apple Store [Country]" button with direct URL
- URLs stored in `DEFAULT_PRODUCT_LINKS` (keyed by country code → product key)
- Two link buttons shown (main + alternate)

### 6. Country Notes
- Shown below comparison as bullet points
- Stored in `DEFAULT_COUNTRY_MODEL_NOTES` (keyed by country code → model key)
- Examples: "eSIM only", "Dual physical SIM (no eSIM)", "Can't turn off shutter sound"
- Notes are per model (not per storage size)

### 7. Bundle Cart / Bundle Comparison
- Users can add more than one selected product to a bundle cart
- Bundle mode compares the total Thailand price vs selected country total
- Bundle result keeps the same core comparison behaviours: exchange conversion, VAT refund, sales tax where supported, and difference display
- Bundle header shows selected bundle items and bundle breakdown rows for Thailand and the foreign country
- Cart state is saved in `localStorage` using `apc_compare_cart`

### 8. Suggested Accessories
- Accessory suggestion strip appears below the comparison card when the selected product category has mapped accessories
- Suggested accessory pills can add an accessory directly into the bundle cart
- If an accessory needs a storage/spec choice, the app jumps to that accessory category/model for selection
- Used to encourage natural bundles such as device + compatible accessory

### 9. Trade-in
- Trade-in toggle appears in the comparison result when a product is selected
- User selects device type → model → storage/spec to subtract trade-in value from the Thailand price
- Trade-in values are stored in `TRADE_IN_DATA`
- Supported trade-in device families: `iPhone`, `iPad`, `Apple Watch`
- Trade-in affects the effective Thailand-side price and can be included in normal comparison and bundle comparison
- Trade-in value date is shown in the UI (e.g. `Trade-in value · 26/05/2026`)
- Separate **Trade-in value overview** mode lets users browse trade-in values by device family

### 10. Repair / Buy New Comparison
- App includes a Repair mode (`gb`) that compares repair cost vs buying a new Apple product
- Supports repair category/model/issue selection and buy-new product selection
- Repair comparison can also apply VAT refund and trade-in to the buy-new side

### 11. Analytics / Dashboard Data Collection
- Sends lightweight usage events for dashboard/analytics using `sbTrack(...)`
- Backend endpoint uses Supabase tables such as `pb_events` and `pb_sessions`
- Tracks events such as page open, country select, product select, trade-in toggle, bundle add, and suggested accessory bundle add
- Each analytics session gets a `pb_sid` stored in `sessionStorage`
- Sends heartbeat updates to keep `pb_sessions.last_seen` current
- Uses browser geolocation, when permission is granted, to assign nearest Thai Apple Store branch/site (`iconsiam`, `centralworld`, or `unknown`) and saves it as `apc_branch`
- Event payloads can include selected country location fields such as `country_code`, `country_name`, and `country_zone` from `ZONE_MAP`

---

## Data Structure

### Product Key Format
```
"[Category] - [Model] - [Spec]"
```
Examples:
- `"iPhone - iPhone 17 Pro - 256GB"`
- `"Mac - MacBook Pro 14" - M4 Pro 12C"`
- `"AirPods - AirPods Pro 3"` (no spec for some AirPods)

### Categories
`iPhone`, `iPad`, `Mac`, `Watch`, `AirPods`

### Countries / Regions
Supported country/region codes currently include:

AU, AT, BE, BR, CA, CL, CN, CZ, DK, FI, FR, DE, HK, HU, IN, IE, IT, JP, LU, MY, MX, NL, NZ, NO, PH, PL, PT, SA, SG, KR, ES, SE, CH, TW, TH, TR, AE, GB, US, VN, MO

### Key JS Constants
| Constant | Description |
|---|---|
| `CSV_PRICES` | `{ productKey: { countryCode: price } }` |
| `MODEL_GROUPS` | Category → model → specs/icon/displayName |
| `DEFAULT_PRODUCT_LINKS` | `{ countryCode: { productKey: url } }` |
| `DEFAULT_COUNTRY_MODEL_NOTES` | `{ countryCode: { modelKey: [note, ...] } }` |
| `CAT_ORDER` | Display order of categories |
| `ZIP_COMBINED_RATES` | `{ "zipPrefix3": combinedRate }` — 922 entries |
| `US_STATE_TAX` | State-level fallback rates |
| `CA_PROVINCE_TAX` | Canada province combined rates |
| `ACC_CAT_MAP` | Maps a main product category to its suggested accessory category |
| `TRADE_IN_DATA` | Trade-in values by device family → model → storage/spec |
| `TRADE_IN_TYPES` | Supported trade-in families (`iPhone`, `iPad`, `Apple Watch`) |
| `GB_REPAIR_PRICE_DATA` | Repair prices used by Repair mode |
| `ZONE_MAP` | Maps country codes to dashboard geography zones |

---

## UI Structure

### Navigation Bar
- Logo + "Price Battle · Thailand Base"
- EN / TH / 中文 language toggle
- ⚙️ Settings/Manage button
- `?` Info button (below rate bar, top-right)

### Rate Bar
- Shows live exchange rates: 1 THB = X USD / EUR / JPY etc.
- Auto-refreshes, shows "live" indicator

### Step 1 — Select Country
- Dropdown with 39 countries + flag

### Step 2 — Select Category
- Grid of category icons (iPhone, iPad, Mac, Watch, AirPods)

### Step 3 — Select Model & Storage
- Model grid with product images
- Storage/size pills below

### Result Card
- Header: product image + name + VAT Refund toggle
- Trade-in toggle and inline trade-in selectors when available
- Bundle item row when bundle mode is active
- Sub-header: country + storage + exchange rate
- Price columns: Thailand (left) vs Foreign (right)
- Bundle breakdown under each price column when comparing multiple selected items
- Sales Tax widget (US/CA only)
- Price Difference chips
- VAT Refund chip (if VAT on)
- Trade-in deduction can be shown in the Thailand price breakdown
- Bundle cart controls: add current selection, clear cart, selected item count
- Suggested accessories strip when accessory mappings are available
- Notes section
- Send Feedback link

### Mode Switcher
- **Compare**: standard international Apple price comparison
- **Repair**: compare repair price vs buying new, with optional VAT refund/trade-in on buy-new side
- **Trade-in value**: table-style overview of trade-in values by device family/model/spec

### Settings Panel (⚙️)
- **Prices & Rates tab**: Edit exchange rates, edit individual prices per country
- **Add Product tab**: Add custom products
- **Export/Import tab**: Export to CSV, import from CSV, Reset All
- Version stamp shown (e.g. `v 25.04.2026 00:01`)

---

## Localisation
- EN / TH / 中文 toggle
- All UI strings stored in `TR.en`, `TR.th`, and `TR.zh` objects
- `tr(key)` function returns current language string
- `setLang(l)` switches language and updates all UI elements
- `apc_lang` can store `en`, `th`, or `zh`

---

## localStorage Keys
| Key | Content |
|---|---|
| `apc_app_version` | Version string — triggers auto-clear on update |
| `apc_prices` | User-overridden prices |
| `apc_custom` | Custom added products |
| `apc_product_links` | User-overridden store URLs |
| `apc_country_model_notes` | User-edited notes |
| `apc_hidden_products` | Hidden/removed products |
| `apc_model_order` | Custom model sort order |
| `apc_spec_order` | Custom spec sort order |
| `apc_lang` | Last selected language (`en`/`th`/`zh`) |
| `apc_compare_cart` | Bundle cart selections |
| `apc_mode` | Last selected app mode/section |
| `apc_branch` | Nearest Thai Apple Store branch/site selected from browser geolocation |

> **Auto-clear**: On app load, if `apc_app_version` doesn't match the current version string, all data keys above are cleared and the new version is stored. This ensures fresh data when a new HTML file is deployed.

---

## Data Source
- Prices imported from `Master_Template_numbers.csv`
- CSV columns: product key, 40 country prices, 40 URLs, 40 country notes
- Import script (Python) parses CSV and replaces JS constants in HTML
- Notes use `|` as separator between bullet points

---

## Known Behaviours / Notes
- USA/Canada tax is **estimate only** — combined rate by 3-digit ZIP prefix, may differ slightly from Apple.com (which uses exact address-level rate)
- "State rate only" label shown when ZIP prefix not in combined table
- Percentage formula changed to `(foreign - thai) / foreign` to avoid misleadingly high numbers
- VAT Refund only applies to Thailand side
- Trade-in only reduces the Thailand-side effective price
- Trade-in pricing is for full-value, undamaged devices and store trade-in with purchase
- Bundle comparison requires at least two selected cart items before rendering the bundle total view
- Suggested accessories are category-mapped; if no mapping or accessory models exist, the strip is hidden
- Analytics geolocation is optional and depends on browser permission; if unavailable or denied, dashboard site defaults to `unknown`
- Send Feedback → opens mail to `leng_pp2@icloud.com` with subject "Feedback: Price battle"

---

## Build Rules
- **Every new build of `index.html` must include a current date+time stamp** in the version string (e.g. `v 26.06.2025 14:30`). Update the `APP_VERSION` constant and the visible version stamp in the Settings panel each time a new file is generated.
- **Always use Thailand timezone (UTC+7)** for the timestamp. The build server runs UTC, so always run `TZ=Asia/Bangkok date` to get the correct Bangkok time before setting the stamp.
- **Every version change or meaningful feature change must also update this `price-battle.md` file** so the project knowledge stays current with the shipped `index.html`.
