#!/usr/bin/env python3
"""Add Mac Acc products from 1a9de736-macaccimport.csv to index.html"""

import csv
import json
import re

CSV_FILE = "/root/.claude/uploads/07039cce-80eb-5721-a836-09956176fa41/1a9de736-macaccimport.csv"
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
            for country_name, code in COUNTRY_MAP.items():
                price_str = row.get(country_name, '').strip()
                if price_str:
                    try:
                        val = float(price_str)
                        prices[code] = int(val) if val == int(val) else val
                    except ValueError:
                        pass
                url_val = row.get(f"URL_{country_name}", '').strip()
                if url_val.startswith('http'):
                    urls[code] = url_val
            products[item_name] = {'prices': prices, 'urls': urls}
    return products

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
    products = parse_csv()
    for name, data in products.items():
        print(f"  {name}: {len(data['prices'])} prices, {len(data['urls'])} URLs")

    print("\nReading index.html...")
    content = open(HTML_FILE, 'r', encoding='utf-8').read()

    # =========================================================
    # 1. UPDATE ACC_IMPORTED_PRICES
    # =========================================================
    print("\n--- Updating ACC_IMPORTED_PRICES ---")
    s, e, acc_prices = extract_json_obj(content, 'ACC_IMPORTED_PRICES')

    for item_name, data in products.items():
        acc_prices[item_name] = data['prices']
        print(f"  Added: {item_name}")

    new_acc_str = json.dumps(acc_prices, ensure_ascii=False, separators=(',', ':'))
    content = content[:s] + new_acc_str + content[e:]
    print(f"  ACC_IMPORTED_PRICES updated")

    # =========================================================
    # 2. UPDATE ACC_IMPORTED_LINKS
    # =========================================================
    print("\n--- Updating ACC_IMPORTED_LINKS ---")
    # Need to re-extract positions after content change
    s, e, acc_links = extract_json_obj(content, 'ACC_IMPORTED_LINKS')

    url_count = 0
    for item_name, data in products.items():
        for code, url in data['urls'].items():
            if code not in acc_links:
                acc_links[code] = {}
            acc_links[code][item_name] = url
            url_count += 1

    new_links_str = json.dumps(acc_links, ensure_ascii=False, separators=(',', ':'))
    content = content[:s] + new_links_str + content[e:]
    print(f"  Added {url_count} URLs to ACC_IMPORTED_LINKS")

    # =========================================================
    # 3. UPDATE CAT_ORDER - add MacAcc
    # =========================================================
    print("\n--- Updating CAT_ORDER ---")
    s, e, cat_order = extract_json_obj(content, 'CAT_ORDER')

    # Existing Mac Acc products (suffix after "Mac Acc - ")
    existing_mac_acc = ["Magic Mouse White", "Magic Mouse Black", "Magic Trackpad White", "Magic Trackpad Black"]
    # New products from CSV (suffix)
    new_mac_acc = [name.replace("Mac Acc - ", "") for name in products.keys()]

    mac_acc_order = existing_mac_acc + new_mac_acc
    cat_order['MacAcc'] = mac_acc_order
    print(f"  MacAcc order: {mac_acc_order}")

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
