"""
Schema Parser - Extract structured data from metadata.

Supports:
- JSON-LD (Schema.org)
- Open Graph
- Microdata
- Standard meta tags
"""

from __future__ import annotations
import json
import re
from typing import Any
from bs4 import BeautifulSoup, Tag


class SchemaParser:
    """Extract structured data from page metadata."""
    
    def extract_jsonld(self, soup: BeautifulSoup) -> list[dict]:
        """
        Parse JSON-LD script tags.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of parsed JSON-LD objects
        """
        jsonld_data = []
        
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if data:
                    jsonld_data.append(data)
            except (json.JSONDecodeError, TypeError, AttributeError):
                continue
        
        return jsonld_data
    
    def extract_opengraph(self, soup: BeautifulSoup) -> dict[str, Any]:
        """
        Parse Open Graph meta tags.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dict of Open Graph properties
        """
        og_data = {}
        
        for meta in soup.find_all("meta", property=re.compile(r"^og:")):
            prop = meta.get("property", "")
            content = meta.get("content", "")
            
            if prop and content:
                # Remove og: prefix
                key = prop.replace("og:", "")
                og_data[key] = content
        
        return og_data
    
    def extract_microdata(self, soup: BeautifulSoup) -> dict[str, Any]:
        """
        Parse microdata attributes.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dict of microdata properties
        """
        microdata = {}
        
        # Find elements with itemscope
        for item in soup.find_all(attrs={"itemscope": True}):
            item_type = item.get("itemtype", "")
            
            if item_type:
                # Extract itemprops within this scope
                props = {}
                for prop in item.find_all(attrs={"itemprop": True}):
                    prop_name = prop.get("itemprop", "")
                    
                    # Get content based on tag type
                    if prop.name == "meta":
                        prop_value = prop.get("content", "")
                    elif prop.name == "link":
                        prop_value = prop.get("href", "")
                    elif prop.name == "time":
                        prop_value = prop.get("datetime", prop.get_text(strip=True))
                    else:
                        prop_value = prop.get_text(strip=True)
                    
                    if prop_name and prop_value:
                        props[prop_name] = prop_value
                
                if props:
                    # Extract schema type name (e.g., "Product" from http://schema.org/Product)
                    type_name = item_type.split("/")[-1] if "/" in item_type else item_type
                    microdata[type_name] = props
        
        return microdata
    
    def extract_meta(self, soup: BeautifulSoup) -> dict[str, Any]:
        """
        Parse standard meta tags.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dict of meta properties
        """
        meta_data = {}
        
        # Standard meta tags
        meta_mapping = {
            "description": "description",
            "keywords": "keywords",
            "author": "author",
            "robots": "robots",
            "viewport": "viewport",
            "theme-color": "theme_color",
        }
        
        for meta in soup.find_all("meta"):
            name = meta.get("name", "").lower()
            content = meta.get("content", "")
            
            if name in meta_mapping and content:
                key = meta_mapping[name]
                
                # Parse keywords into list
                if name == "keywords":
                    meta_data[key] = [k.strip() for k in content.split(",") if k.strip()]
                else:
                    meta_data[key] = content
        
        # Article-specific meta tags
        for meta in soup.find_all("meta", property=re.compile(r"^article:")):
            prop = meta.get("property", "")
            content = meta.get("content", "")
            
            if prop and content:
                # article:published_time -> published_time
                key = prop.replace("article:", "")
                meta_data[key] = content
        
        # Product-specific meta tags
        for meta in soup.find_all("meta", property=re.compile(r"^product:")):
            prop = meta.get("property", "")
            content = meta.get("content", "")
            
            if prop and content:
                # product:price -> price
                key = prop.replace("product:", "")
                meta_data[key] = content
        
        return meta_data
    
    def merge(self, soup: BeautifulSoup) -> dict[str, Any]:
        """
        Merge all structured data sources into a single dict.
        
        Priority: JSON-LD > Open Graph > Microdata > Standard Meta
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Merged structured data dict
        """
        merged = {}
        
        # Start with standard meta (lowest priority)
        meta = self.extract_meta(soup)
        merged.update(meta)
        
        # Add microdata
        microdata = self.extract_microdata(soup)
        if microdata:
            merged["microdata"] = microdata
            
            # Flatten common schema types to top level
            for schema_type in ["Product", "Article", "Event", "Organization", "Person"]:
                if schema_type in microdata:
                    merged.update(microdata[schema_type])
        
        # Add Open Graph (higher priority)
        og = self.extract_opengraph(soup)
        merged.update(og)
        
        # Add JSON-LD (highest priority)
        jsonld = self.extract_jsonld(soup)
        if jsonld:
            merged["jsonld"] = jsonld
            
            # Flatten first JSON-LD object to top level
            if jsonld and isinstance(jsonld[0], dict):
                first = jsonld[0]
                
                # Common Schema.org fields
                field_mapping = {
                    "name": "title",
                    "headline": "title",
                    "description": "description",
                    "author": "author",
                    "datePublished": "published_time",
                    "dateModified": "modified_time",
                    "image": "image",
                    "url": "url",
                    "price": "price",
                    "priceCurrency": "currency",
                }
                
                for json_key, merged_key in field_mapping.items():
                    if json_key in first:
                        value = first[json_key]
                        
                        # Handle nested author object
                        if json_key == "author" and isinstance(value, dict):
                            value = value.get("name", value)
                        
                        # Handle image object/array
                        if json_key == "image":
                            if isinstance(value, dict):
                                value = value.get("url", value)
                            elif isinstance(value, list) and value:
                                value = value[0] if isinstance(value[0], str) else value[0].get("url", "")
                        
                        merged[merged_key] = value
        
        return merged
