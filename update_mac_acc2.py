#!/usr/bin/env python3
"""Update Mac Acc URLs, country notes, and CAT_ORDER from 52ad4fe5-macaccimport.csv"""

import csv
import json

CSV_FILE = "/root/.claude/uploads/07039cce-80eb-5721-a836-09956176fa41/52ad4fe5-macaccimport.csv"
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
    all_notes = {}  # code -> set of note parts (from all rows)
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_name = row['Item'].strip()
            if not item_name:
                continue
            urls = {}
            for country_name, code in COUNTRY_MAP.items():
                url_val = row.get(f"URL_{country_name}", '').strip()
                if url_val.startswith('http'):
                    urls[code] = url_val
                note_val = row.get(f"COUNTRY_NOTE_{country_name}", '').strip()
                if note_val:
                    if code not in all_notes:
                        all_notes[code] = []
                    for part in note_val.split(' | '):
                        part = part.strip()
                        if part and part not in all_notes[code]:
                            all_notes[code].append(part)
            products[item_name] = {'urls': urls}
    return products, all_notes

def extract_json_obj(content, const_name):
    idx = content.find(f'const {const_name}=')
    obj_start = content.index('{', idx)
    depth = 0
    for i, c in enumerate(content[obj_start:]):
        if c == '{': depth += 1
        elif c == '}': depth -= 1
        if depth == 0:
            return obj_start, obj_start + i + 1, json.loads(content[obj_start:obj_start+i+1])
    raise ValueError(f"Could not find {const_name}")

def main():
    print("Parsing CSV...")
    products, all_notes = parse_csv()
    for name, data in products.items():
        print(f"  {name}: {len(data['urls'])} URLs")

    print("\nReading index.html...")
    content = open(HTML_FILE, 'r', encoding='utf-8').read()

    # =========================================================
    # 1. UPDATE ACC_IMPORTED_LINKS (replace all Mac Acc URLs)
    # =========================================================
    print("\n--- Updating ACC_IMPORTED_LINKS ---")
    s, e, acc_links = extract_json_obj(content, 'ACC_IMPORTED_LINKS')

    url_count = 0
    for item_name, data in products.items():
        for code, url in data['urls'].items():
            if code not in acc_links:
                acc_links[code] = {}
            old = acc_links[code].get(item_name, '')
            if old != url:
                acc_links[code][item_name] = url
                url_count += 1

    new_links_str = json.dumps(acc_links, ensure_ascii=False, separators=(',', ':'))
    content = content[:s] + new_links_str + content[e:]
    print(f"  Updated {url_count} URLs in ACC_IMPORTED_LINKS")

    # =========================================================
    # 2. UPDATE DEFAULT_COUNTRY_NOTES (merge new notes)
    # =========================================================
    print("\n--- Updating DEFAULT_COUNTRY_NOTES ---")
    notes_idx = content.find('const DEFAULT_COUNTRY_NOTES=')
    if notes_idx < 0:
        print("  WARNING: DEFAULT_COUNTRY_NOTES not found!")
    else:
        notes_s = content.index('{', notes_idx)
        depth = 0
        for i, c in enumerate(content[notes_s:]):
            if c == '{': depth += 1
            elif c == '}': depth -= 1
            if depth == 0:
                notes_e = notes_s + i + 1
                break
        notes_json = json.loads(content[notes_s:notes_e])

        for code, new_parts in all_notes.items():
            existing = notes_json.get(code, [])
            updated = list(existing)
            added = []
            for part in new_parts:
                # Normalize for comparison
                part_norm = part.lower().replace('phillippines', 'philippines').replace('inphillippines', 'in philippines')
                already = any(part_norm in n.lower() or n.lower() in part_norm for n in updated)
                if not already:
                    updated.append(part)
                    added.append(part)
            if added:
                notes_json[code] = updated
                print(f"  {code}: added {added}")
            else:
                notes_json[code] = updated  # ensure it's set even if no change

        new_notes_str = json.dumps(notes_json, ensure_ascii=False, separators=(',', ':'))
        content = content[:notes_s] + new_notes_str + content[notes_e:]
        print("  DEFAULT_COUNTRY_NOTES updated")

    # =========================================================
    # 3. UPDATE CAT_ORDER - reorder MacAcc: USB-C items first
    # =========================================================
    print("\n--- Updating CAT_ORDER ---")
    s, e, cat_order = extract_json_obj(content, 'CAT_ORDER')

    mac_acc = cat_order.get('MacAcc', [])
    # Pull USB-C items to front, keep rest in original order
    usb_first = ["USB-C to USB", "Digital AV Multiport"]
    others = [x for x in mac_acc if x not in usb_first]
    cat_order['MacAcc'] = usb_first + others
    print(f"  MacAcc new order: {cat_order['MacAcc']}")

    new_cat_str = json.dumps(cat_order, ensure_ascii=False, separators=(',', ':'))
    content = content[:s] + new_cat_str + content[e:]
    print("  CAT_ORDER updated")

    # =========================================================
    # Save
    # =========================================================
    print("\nSaving index.html...")
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Done!")

if __name__ == '__main__':
    main()
