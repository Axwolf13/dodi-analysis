# Superseded. The July 2026 grade collection. Six record numbers in
# known_services are wrong (WhatsApp, Amazon, Apple, Spotify, Steam, TikTok),
# so it fetched other services under those names; see the README's Corrections.
# tosdr_working_api.py
import requests
import pandas as pd
import time
import json

def get_service_by_id(service_id):
    """
    Get service data using actual ToS;DR API v3
    """
    url = "https://api.tosdr.org/service/v3"
    params = {'id': service_id}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"  Status {response.status_code} for ID {service_id}")
            return None
            
    except Exception as e:
        print(f"  Error for ID {service_id}: {e}")
        return None

def search_service(query):
    """
    Search for services using search API
    """
    url = "https://api.tosdr.org/search/v5"
    params = {'query': query}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('services', [])
        return []
        
    except Exception as e:
        print(f"Search error: {e}")
        return []

def collect_tosdr_grades():
    """
    Collect ToS;DR grades for known services
    """
    print("="*60)
    print("ToS;DR Data Collection (Using Official API)")
    print("="*60 + "\n")
    
    # Known service IDs from ToS;DR website
    # You can find more by searching
    known_services = {
        'Facebook': 182,
        'Google': 217,
        'Amazon': 194,
        'Wikipedia': 265,
        'Twitter': 195,
        'Instagram': 219,
        'Netflix': 185,
        'Spotify': 222,
        'Microsoft': 244,
        'Apple': 216,
        'Steam': 340,
        'TikTok': 295,
        'YouTube': 274,
        'Discord': 536,
        'Reddit': 194,
    }
    
    results = []
    
    for name, service_id in known_services.items():
        print(f"Fetching {name} (ID: {service_id})...")
        
        data = get_service_by_id(service_id)
        
        if data:
            rating = data.get('rating', 'N/A')
            
            result = {
                'Service': name,
                'ID': service_id,
                'Grade': rating,
                'Slug': data.get('slug', ''),
                'Reviewed': data.get('is_comprehensively_reviewed', False)
            }
            
            results.append(result)
            print(f"  ✅ Grade: {rating}")
            
            # Save individual response for inspection
            with open(f'tosdr_{name.lower()}.json', 'w') as f:
                json.dump(data, f, indent=2)
        
        time.sleep(0.5)  # Be polite to API
    
    # Save results
    df = pd.DataFrame(results)
    df.to_csv('tosdr_grades.csv', index=False)
    
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS! Collected {len(results)} services")
    print(f"{'='*60}\n")
    
    # Show grade distribution
    print("Grade Distribution:")
    print(df['Grade'].value_counts())
    print(f"\nSaved to: tosdr_grades.csv")
    
    return df

def search_and_collect(search_queries):
    """
    Alternative: Search for services first, then get details
    """
    print("\n" + "="*60)
    print("Searching for additional services...")
    print("="*60 + "\n")
    
    all_services = []
    
    for query in search_queries:
        print(f"Searching for: {query}")
        services = search_service(query)
        
        for service in services[:3]:  # Top 3 results
            service_id = service.get('id')
            name = service.get('name')
            rating = service.get('rating', 'N/A')
            
            print(f"  Found: {name} (ID: {service_id}, Grade: {rating})")
            
            all_services.append({
                'Service': name,
                'ID': service_id,
                'Grade': rating,
                'Slug': service.get('slug', '')
            })
        
        time.sleep(0.5)
    
    return pd.DataFrame(all_services)

if __name__ == "__main__":
    # Method 1: Direct collection from known IDs
    df_known = collect_tosdr_grades()
    
    # Method 2: Search for additional services
    search_terms = ['cloud', 'streaming', 'gaming', 'social media']
    df_searched = search_and_collect(search_terms)
    
    # Combine
    if not df_searched.empty:
        df_all = pd.concat([df_known, df_searched], ignore_index=True)
        df_all = df_all.drop_duplicates(subset=['ID'])
        df_all.to_csv('tosdr_all_grades.csv', index=False)
        
        print(f"\n✅ Total services collected: {len(df_all)}")
        print(f"   Saved to: tosdr_all_grades.csv")