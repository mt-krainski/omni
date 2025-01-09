import xml.etree.ElementTree as ET
from time import sleep

import requests
from airflow.decorators import task

MAX_RESULTS = 10


@task.python
def search_papers(params):
    search_term = params["search_term"]
    page = 1

    if not search_term:
        raise ValueError("Search term is required")

    # Construct the PubMed API URL with the search term and page
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": search_term,
        "retmode": "json",
        "retstart": (page - 1) * MAX_RESULTS,
        "retmax": MAX_RESULTS,
    }

    # Make the request to the PubMed API to get the PubMed IDs
    response = requests.get(base_url, params=params)
    response.raise_for_status()

    # Extract the PubMed IDs from the API response
    data = response.json()
    pubmed_ids = data["esearchresult"]["idlist"]
    total_results = int(data["esearchresult"]["count"])
    total_pages = (total_results // MAX_RESULTS) + 1

    article_details = []

    # Retrieve article details using the PubMed API's esummary endpoint
    total_count = len(pubmed_ids)
    for index, pubmed_id in enumerate(pubmed_ids):
        print(f"Processing article {index + 1} / {total_count}")
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {"db": "pubmed", "id": pubmed_id, "retmode": "json"}
        summary_response = requests.get(summary_url, params=summary_params)
        summary_response.raise_for_status()

        summary_data = summary_response.json()
        article_title = summary_data["result"][pubmed_id]["title"]
        article_url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/"

        # Get the authors' information
        authors = summary_data["result"][pubmed_id]["authors"]
        author_names = [author["name"] for author in authors]
        publication_date = summary_data["result"][pubmed_id]["epubdate"]
        journal_name = summary_data["result"][pubmed_id]["source"]
        doi = next(
            (
                item["value"]
                for item in summary_data["result"][pubmed_id]["articleids"]
                if item["idtype"] == "doi"
            ),
            "DOI Not Found",
        )

        abstract = get_abstract(pubmed_id)["abstract"]

        article_details.append(
            {
                "abstract": abstract,
                "authors": author_names,
                "doi": f"https://doi.org/{doi}",
                "journal": journal_name,
                "publication_date": publication_date,
                "pubmed_id": pubmed_id,
                "title": article_title,
                "url": article_url,
            }
        )
        sleep(1)

    return {
        "articles": article_details,
        "page": page,
        "total_pages": total_pages,
    }


def get_abstract(pubmed_id):
    if not pubmed_id:
        raise ValueError("PubMed ID is required")

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "pubmed", "id": pubmed_id, "retmode": "xml"}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return parse_abstract(response.text)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request error: {str(e)}")
    except ET.ParseError:
        raise RuntimeError("Error parsing XML response")


def parse_abstract(xml_data):
    root = ET.fromstring(xml_data)
    abstract_elements = root.findall(".//AbstractText")

    if abstract_elements:
        abstract = "\n".join(
            abstract_element.text.strip()
            for abstract_element in abstract_elements
            if abstract_element.text
        )
        return {"abstract": abstract}
    else:
        return {"abstract": "Abstract Not Found"}
