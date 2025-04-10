import requests
import re
from core.config import config
from typing import Union, Dict, Optional


NCBI_API_KEY = config.NCBI_API_KEY



def fetch_pmc_id(pmid, api_key):
    """Check if a given PubMed ID (PMID) has a corresponding PMC ID."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    params = {
        "dbfrom": "pubmed",
        "db": "pmc",
        "id": pmid,
        "retmode": "json",
        "api_key": api_key
    }
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        linksets = data.get("linksets", [])
        if linksets and "linksetdbs" in linksets[0]:
            for link in linksets[0]["linksetdbs"]:
                if link["dbto"] == "pmc":
                    return link["links"][0]  # Return first PMC ID found
    return None

def fetch_pmc_pdf(pmc_id):
    pdf_url = f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_id}/pdf/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }  # Replace with your actual User-Agent
    try:
        response = requests.get(pdf_url, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PDF for PMC{pmc_id}: {e}")
        return None

def fetch_abstract(pmid, api_key):
    """Retrieve only the abstract of a PubMed article."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "text",
        "rettype": "medline",
        "api_key": api_key
    }
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        text_data = response.text
        abstract_match = re.search(r"AB  - (.+)", text_data, re.DOTALL)
        if abstract_match:
            return abstract_match.group(1).strip()  # Extract abstract
        return "No abstract available."
    else:
        return f"Error: {response.status_code}, {response.text}"


def fetch_full_text_or_abstract(pmid, api_key: Optional[str] = NCBI_API_KEY):
    """Check PMC for full-text availability, otherwise return the abstract."""
    pmc_id = fetch_pmc_id(pmid, api_key)
    
    if pmc_id:
        pdf_content = fetch_pmc_pdf(pmc_id)
        if pdf_content:
            print(f"Successfully fetched PDF for PMC ID: {pmc_id}")
            return pdf_content  # Return the PDF as binary data
    
    # If no full text is found, return abstract
    return fetch_abstract(pmid, api_key)



##### Test case for the above the methods

# pmid = "30092180"  # Example PubMed ID
# result = fetch_full_text_or_abstract(pmid)
# if isinstance(result, bytes):
#     print("PDF downloaded successfully (binary data).")
# else:
#     print("Abstract:", result)


def fetch_gse_entry(gse_id: str, api_key: Optional[str] = NCBI_API_KEY) -> Union[str, Dict[str, str]]:
   
    if not gse_id or not isinstance(gse_id, str):
        return {"error": "invalid_input", "message": "GSE ID must be a non-empty string"}
        
    if not re.match(r'^GSE\d+$', gse_id):
        return {"error": "invalid_id", "message": f"Invalid GSE ID format: {gse_id}"}
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    headers = {"User-Agent": "GSE_Fetcher/1.0"}
    
    search_params = {
            "db": "gds",
            "term": f"{gse_id}[Accession]",
            "api_key": api_key,
            "retmode": "json"
        }
        
    search_response = requests.get(
            f"{base_url}esearch.fcgi",
            params=search_params,
            headers=headers,
            timeout=15
        )
    search_response.raise_for_status()
    search_data = search_response.json()
        
    id_list = search_data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
            return {"error": "not_found", "message": f"{gse_id} not found in GEO database"}
            
    uid = id_list[0]

    summary_params = {
                "db": "gds",
                "id": uid,
                "retmode": "json",
                "api_key": api_key
            }
    summary_response = requests.get(
                f"{base_url}esummary.fcgi",
                params=summary_params,
                headers=headers,
                timeout=15
            )
    summary_response.raise_for_status()
    summary_data = summary_response.json()
    return summary_data

                    

    
##### Test case for the above the method

# result = fetch_gse_entry("GSE13517")
# import json
# print(json.dumps(result, indent=2)) 