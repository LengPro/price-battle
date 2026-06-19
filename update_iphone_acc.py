#!/usr/bin/env python3
"""
Replace iPhone Acc prices, URLs, and country notes in index.html
using exact data from 23d7c1d5-iphoneaccnew.csv
"""

import csv
import json
import re

CSV_FILE = "/root/.claude/uploads/07039cce-80eb-5721-a836-09956176fa41/23d7c1d5-iphoneaccnew.csv"
HTML_FILE = "/home/user/price-battle/index.html"

COUNTRY_MAP = {
    "Australia": "AU", "Austria": "AT", "Belgium": "BE", "Brazil": "BR",
    "Canada": "CA", "Chile": "CL", "China": "CN", "Czechia": "CZ",
    "Denmark": "DK", "Finland": "FI", "France": "FR", "Germany": "DE",
    "Hong Kong": "HK", "Hungary": "HU", "India": "IN", "Ireland": "IE",
    "Italy": "IT", "Japan": "JP", "Luxembourg": "LU", "Macau": "MO",
    "Malaysia": "MY", "Mexico": "MX", "Netherlands": "NL", "New Zealand": "NZ",
    "Norway": "NO", "Philippines": "PH", "Poland": "PL", "Portugal": "PT",
    "Saudi Arabia": "SA", "Singapore": "SG", "South Korea": "KR",
    "Spain": "ES", "Sweden": "SE", "Switzerland": "CH", "Taiwan": "TW",
    "Thailand": "TH", "Turkey": "TR", "UAE": "AE", "UK": "GB",
    "USA": "US", "Vietnam": "VN"
}

def parse_csv():
    products = {}
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_name = row['Item'].strip()
            if not item_name:
                continue
            prices = {}
            urls = {}
            notes = {}
            for country_name, code in COUNTRY_MAP.items():
                # Price
                price_str = row.get(country_name, '').strip()
                if price_str:
                    try:
                        val = float(price_str)
                        prices[code] = int(val) if val == int(val) else val
                    except ValueError:
                        pass
                # URL (only real URLs)
                url_val = row.get(f"URL_{country_name}", '').strip()
                if url_val.startswith('http'):
                    urls[code] = url_val
                # Country note
                note_val = row.get(f"COUNTRY_NOTE_{country_name}", '').strip()
                if note_val:
                    notes[code] = note_val
            products[item_name] = {'prices': prices, 'urls': urls, 'notes': notes}
    return products

def build_price_str(prices):
    parts = []
    for code, price in prices.items():
        parts.append(f'"{code}":{price}')
    return '{' + ','.join(parts) + '}'

def main():
    print("Parsing CSV...")
    products = parse_csv()
    for name, data in products.items():
        print(f"  {name}: {len(data['prices'])} prices, {len(data['urls'])} URLs")

    print("\nReading index.html...")
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # =========================================================
    # 1. UPDATE CSV_PRICES
    # =========================================================
    print("\n--- Updating CSV_PRICES ---")
    for item_name, data in products.items():
        new_price_str = build_price_str(data['prices'])
        escaped = re.escape(item_name)
        pattern = rf'"{escaped}":\{{[^}}]*\}}'
        new_entry = f'"{item_name}":{new_price_str}'
        if re.search(pattern, content):
            content = re.sub(pattern, new_entry, content, count=1)
            print(f"  Updated prices: {item_name}")
        else:
            print(f"  WARNING not found: {item_name}")

    # =========================================================
    # 2. UPDATE DEFAULT_PRODUCT_LINKS (parse JSON, update, reserialize)
    # =========================================================
    print("\n--- Updating DEFAULT_PRODUCT_LINKS ---")
    idx = content.find('const DEFAULT_PRODUCT_LINKS=')
    obj_start = content.index('{', idx)
    depth = 0
    for i, c in enumerate(content[obj_start:]):
        if c == '{': depth += 1
        elif c == '}': depth -= 1
        if depth == 0:
            obj_end = obj_start + i + 1
            break

    links_json = json.loads(content[obj_start:obj_end])

    update_count = 0
    for item_name, data in products.items():
        for code, new_url in data['urls'].items():
            if code in links_json:
                old_url = links_json[code].get(item_name, '')
                if old_url != new_url:
                    links_json[code][item_name] = new_url
                    update_count += 1

    print(f"  Updated {update_count} URL entries")

    new_links_str = json.dumps(links_json, ensure_ascii=False, separators=(',', ':'))
    content = content[:obj_start] + new_links_str + content[obj_end:]
    print("  DEFAULT_PRODUCT_LINKS replaced")

    # =========================================================
    # 3. UPDATE DEFAULT_COUNTRY_NOTES for IN and PH
    # =========================================================
    print("\n--- Updating DEFAULT_COUNTRY_NOTES ---")

    # Collect notes from all CSV rows - use first row (Crossbody) as it has full notes
    # The CSV has notes for IN and PH in all rows, they should be the same
    csv_notes = {}
    for item_name, data in products.items():
        for code, note in data['notes'].items():
            if code not in csv_notes:
                csv_notes[code] = note

    print(f"  Notes from CSV: {list(csv_notes.keys())}")

    # Find DEFAULT_COUNTRY_NOTES
    notes_idx = content.find('const DEFAULT_COUNTRY_NOTES=')
    if notes_idx < 0:
        print("  WARNING: DEFAULT_COUNTRY_NOTES not found!")
    else:
        notes_obj_start = content.index('{', notes_idx)
        depth = 0
        for i, c in enumerate(content[notes_obj_start:]):
            if c == '{': depth += 1
            elif c == '}': depth -= 1
            if depth == 0:
                notes_obj_end = notes_obj_start + i + 1
                break

        notes_json = json.loads(content[notes_obj_start:notes_obj_end])
        print(f"  Current countries in notes: {list(notes_json.keys())}")

        # Process IN (India) notes
        india_csv_note = csv_notes.get('IN', '')
        if india_csv_note:
            india_parts = [p.strip() for p in india_csv_note.split(' | ')]
            existing_in = notes_json.get('IN', [])
            updated_in = list(existing_in)
            for part in india_parts:
                already_there = any(part.lower() in n.lower() for n in updated_in)
                if not already_there:
                    updated_in.append(part)
            if updated_in != existing_in:
                notes_json['IN'] = updated_in
                print(f"  Updated IN notes: {updated_in}")
            else:
                print(f"  IN notes already up to date: {existing_in}")

        # Process PH (Philippines) notes
        ph_csv_note = csv_notes.get('PH', '')
        if ph_csv_note:
            ph_parts = [p.strip() for p in ph_csv_note.split(' | ')]
            existing_ph = notes_json.get('PH', [])
            updated_ph = list(existing_ph)
            for part in ph_parts:
                # Fix typo: "Phillippines" -> "Philippines"
                part = part.replace('Phillippines', 'Philippines').replace('inPhillippines', 'in Philippines')
                already_there = any('belkin' in n.lower() for n in updated_ph) if 'belkin' in part.lower() else any(part.lower() in n.lower() for n in updated_ph)
                if not already_there:
                    updated_ph.append(part)
            if updated_ph != existing_ph:
                notes_json['PH'] = updated_ph
                print(f"  Updated PH notes: {updated_ph}")
            else:
                print(f"  PH notes already up to date: {existing_ph}")

        new_notes_str = json.dumps(notes_json, ensure_ascii=False, separators=(',', ':'))
        content = content[:notes_obj_start] + new_notes_str + content[notes_obj_end:]
        print("  DEFAULT_COUNTRY_NOTES replaced")

    # =========================================================
    # Save
    # =========================================================
    print("\nSaving index.html...")
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Done!")

if __name__ == '__main__':
    main()
