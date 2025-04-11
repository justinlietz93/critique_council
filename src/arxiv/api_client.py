"""
ArXiv API Client Module

This module provides functionality to interact with the arXiv API,
handling request formation, rate limiting, and response parsing.
"""

import time
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

class ArxivApiClient:
    """
    Client for interacting with the arXiv API.
    
    This class handles:
    1. Making API requests with rate limiting
    2. Parsing XML responses
    3. Converting API data to a structured format
    """
    
    # arXiv API configuration
    API_BASE_URL = "http://export.arxiv.org/api/query"
    
    # Rate limiting to be respectful to arXiv API (3 second delay)
    REQUEST_DELAY = 3.0  # seconds
    
    def __init__(self):
        """Initialize the ArXiv API client."""
        self._last_request_time = 0
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting to API requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.REQUEST_DELAY:
            sleep_time = self.REQUEST_DELAY - time_since_last
            logger.debug(f"Rate limiting: Sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
            
        self._last_request_time = time.time()
    
    def make_request(self, params: Dict[str, str]) -> str:
        """
        Make a request to the arXiv API with rate limiting.
        
        Args:
            params: Dictionary of query parameters
            
        Returns:
            API response as a string
        """
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Construct the URL
        query_string = urllib.parse.urlencode(params)
        url = f"{self.API_BASE_URL}?{query_string}"
        
        logger.debug(f"Making arXiv API request: {url}")
        
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
                return content
        except Exception as e:
            logger.error(f"Error calling arXiv API: {e}")
            raise
    
    def parse_response(self, response_xml: str) -> List[Dict[str, Any]]:
        """
        Parse the XML response from arXiv API.
        
        Args:
            response_xml: XML response from arXiv API
            
        Returns:
            List of paper metadata dictionaries
        """
        results = []
        try:
            # Parse XML and extract namespaces
            root = ET.fromstring(response_xml)
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # Extract each entry
            for entry in root.findall('.//atom:entry', namespaces):
                paper = {}
                
                # Extract basic data
                title_elem = entry.find('atom:title', namespaces)
                paper['title'] = title_elem.text.strip() if title_elem is not None else "Unknown Title"
                
                id_elem = entry.find('atom:id', namespaces)
                if id_elem is not None:
                    # Extract arXiv ID from the URL
                    id_url = id_elem.text
                    arxiv_id = id_url.split('/')[-1]
                    paper['id'] = arxiv_id
                
                summary_elem = entry.find('atom:summary', namespaces)
                paper['abstract'] = summary_elem.text.strip() if summary_elem is not None else ""
                
                # Authors
                authors = []
                for author_elem in entry.findall('.//atom:author/atom:name', namespaces):
                    authors.append(author_elem.text.strip())
                paper['authors'] = authors
                
                # Published/Updated dates
                published_elem = entry.find('atom:published', namespaces)
                updated_elem = entry.find('atom:updated', namespaces)
                paper['published'] = published_elem.text if published_elem is not None else ""
                paper['updated'] = updated_elem.text if updated_elem is not None else ""
                
                # ArXiv-specific fields
                primary_category = entry.find('arxiv:primary_category', namespaces)
                if primary_category is not None:
                    paper['primary_category'] = primary_category.attrib.get('term', "")
                
                comment_elem = entry.find('arxiv:comment', namespaces)
                if comment_elem is not None and comment_elem.text:
                    paper['comment'] = comment_elem.text.strip()
                
                journal_ref_elem = entry.find('arxiv:journal_ref', namespaces)
                if journal_ref_elem is not None and journal_ref_elem.text:
                    paper['journal_ref'] = journal_ref_elem.text.strip()
                
                doi_elem = entry.find('arxiv:doi', namespaces)
                if doi_elem is not None and doi_elem.text:
                    paper['doi'] = doi_elem.text.strip()
                
                # Categories (subjects)
                categories = []
                for category_elem in entry.findall('atom:category', namespaces):
                    if 'term' in category_elem.attrib:
                        categories.append(category_elem.attrib['term'])
                paper['categories'] = categories
                
                # Links
                links = {}
                for link_elem in entry.findall('atom:link', namespaces):
                    link_title = link_elem.attrib.get('title', '')
                    href = link_elem.attrib.get('href', '')
                    rel = link_elem.attrib.get('rel', '')
                    
                    if link_title == 'pdf' and href:
                        links['pdf'] = href
                    elif rel == 'alternate' and href:
                        links['abstract_page'] = href
                    elif link_title == 'doi' and href:
                        links['doi'] = href
                
                paper['links'] = links
                results.append(paper)
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing arXiv API response: {e}")
            return []
    
    def search(self, 
               search_query: str, 
               max_results: int = 10, 
               sort_by: str = "relevance",
               sort_order: str = "descending") -> List[Dict[str, Any]]:
        """
        Search arXiv for papers matching the given query.
        
        Args:
            search_query: The search query string
            max_results: Maximum number of results to return
            sort_by: Sort field ("relevance", "lastUpdatedDate", "submittedDate")
            sort_order: Sort direction ("ascending" or "descending")
            
        Returns:
            List of paper metadata
        """
        # Prepare query parameters
        params = {
            'search_query': search_query,
            'max_results': str(min(max_results, 100)),  # Limit to 100 for reasonable responses
            'sortBy': sort_by,
            'sortOrder': sort_order
        }
        
        try:
            response = self.make_request(params)
            return self.parse_response(response)
        except Exception as e:
            logger.error(f"Failed to search arXiv: {e}")
            return []
    
    def fetch_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for a specific arXiv paper by ID.
        
        Args:
            arxiv_id: The arXiv ID of the paper
            
        Returns:
            Paper metadata or None if not found
        """
        # Prepare query parameters
        params = {
            'id_list': arxiv_id
        }
        
        try:
            response = self.make_request(params)
            results = self.parse_response(response)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to fetch arXiv paper: {e}")
            return None
