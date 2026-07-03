# download_tos_documents.py
import requests
import pandas as pd
import json
import time

def get_documents_for_service(service_id):
    """
    Get documents (ToS, Privacy Policy) for a service
    """
    url = "https://api.tosdr.org/service/v3"
    params = {'id': service_id}
    
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('documents', [])
    return []

def download_tos_text(document_id):
    """
    Get the actual text of a document
    """
    url = "https://api.tosdr.org/document/v2"
    params = {'id': document_id}
    
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('text', '')
    return ''

def collect_tos_for_validation():
    """
    Download ToS text for all services in validation dataset
    """
    # Load your grades
    df = pd.read_csv('tosdr_grades.csv')
    
    # Filter out N/A grades
    df = df[df['Grade'] != 'N/A']
    
    print(f"Downloading ToS for {len(df)} services...\n")
    
    for idx, row in df.iterrows():
        service_id = row['ID']
        service_name = row['Service']
        grade = row['Grade']
        
        print(f"Processing {service_name} (Grade {grade})...")
        
        # Get documents for this service
        documents = get_documents_for_service(service_id)
        
        if not documents:
            print(f"  ⚠️  No documents found")
            continue
        
        # Look for Terms of Service document
        tos_doc = None
        for doc in documents:
            doc_name = doc.get('name', '').lower()
            if 'terms' in doc_name or 'service' in doc_name:
                tos_doc = doc
                break
        
        # If no ToS, use first document
        if not tos_doc and documents:
            tos_doc = documents[0]
        
        if tos_doc:
            doc_id = tos_doc['id']
            doc_name = tos_doc.get('name', 'Unknown')
            
            print(f"  Found: {doc_name} (ID: {doc_id})")
            
            # Download text
            text = download_tos_text(doc_id)
            
            if text:
                # Save to file
                filename = f"data/validation/{service_name.lower().replace(' ', '_')}_tos.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                print(f"  ✅ Saved ({len(text)} chars)")
            else:
                print(f"  ⚠️  No text available")
        
        time.sleep(0.5)  # Be polite
    
    print("\n✅ ToS collection complete!")

if __name__ == "__main__":
    import os
    os.makedirs('data/validation', exist_ok=True)
    
    collect_tos_for_validation()