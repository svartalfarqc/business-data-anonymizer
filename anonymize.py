#!/usr/bin/env python3
"""
Business Data Anonymizer (anonymize.py)
Anonymizes business data in CSV files while preserving specified columns.
Maintains a mapping file for traceability.
Automatically detects file encoding or accepts manual specification.
"""

import csv
import json
import hashlib
import os
import sys
from datetime import datetime
from typing import Dict, List, Set, Any


class BusinessDataAnonymizer:
    """Anonymizes business data in CSV files with configurable column preservation."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize with configuration file."""
        self.config = self._load_config(config_path)
        self.mapping_file = self.config.get("mapping_file", "anonymization_mappings.json")
        self.mappings = self._load_mappings()
        self.preserved_columns = set(self.config.get("preserve_columns", []))
        self.anonymization_counter = 0
        self.encoding = self.config.get("encoding", "auto")  # auto-detect by default
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ["source_file", "destination_file"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")
        
        return config
    
    def _load_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load existing mappings from file."""
        if os.path.exists(self.mapping_file):
            with open(self.mapping_file, 'r') as f:
                return json.load(f)
        return {"_metadata": {"created": datetime.now().isoformat()}}
    
    def _save_mappings(self):
        """Save mappings to file."""
        self.mappings["_metadata"]["last_updated"] = datetime.now().isoformat()
        self.mappings["_metadata"]["total_mappings"] = sum(
            len(v) for k, v in self.mappings.items() if k != "_metadata"
        )
        
        with open(self.mapping_file, 'w') as f:
            json.dump(self.mappings, f, indent=2, sort_keys=True)
    
    def _create_anonymized_value(self, original_value: str, column_name: str) -> str:
        """Create an anonymized value for the given original value."""
        # Create a composite key from column name and value
        composite_key = f"{column_name}::{original_value}"
        
        # Check if we already have a mapping
        if column_name not in self.mappings:
            self.mappings[column_name] = {}
        
        if original_value in self.mappings[column_name]:
            return self.mappings[column_name][original_value]
        
        # Determine the type of value and create appropriate anonymization
        if self._looks_like_utm(column_name, original_value):
            anon_value = self._anonymize_utm_style(original_value, column_name)
        elif self._looks_like_id(original_value):
            anon_value = self._anonymize_id_style(original_value, column_name)
        elif self._looks_like_category(original_value):
            anon_value = self._anonymize_category_style(original_value, column_name)
        else:
            anon_value = self._anonymize_generic(original_value, column_name)
        
        # Store the mapping
        self.mappings[column_name][original_value] = anon_value
        return anon_value
    
    def _looks_like_utm(self, column_name: str, value: str) -> bool:
        """Check if the value looks like a UTM parameter or marketing identifier."""
        utm_indicators = ['utm_', 'campaign', 'source', 'medium', 'term', 'content']
        column_lower = column_name.lower()
        return any(indicator in column_lower for indicator in utm_indicators)
    
    def _looks_like_id(self, value: str) -> bool:
        """Check if the value looks like an ID."""
        # Check for common ID patterns
        if len(value) > 20:  # Long strings often IDs
            return True
        if value.count('-') >= 2:  # UUID-like patterns
            return True
        if value.count('_') >= 2 and any(c.isdigit() for c in value):  # ID patterns
            return True
        return False
    
    def _looks_like_category(self, value: str) -> bool:
        """Check if the value looks like a category or enumerated value."""
        # Short values without special characters are often categories
        return len(value) <= 50 and value.replace(' ', '').replace('-', '').replace('_', '').isalnum()
    
    def _anonymize_utm_style(self, value: str, column_name: str) -> str:
        """Anonymize UTM-style parameters maintaining structure."""
        # Extract prefix if exists (e.g., "social_" from "social_facebook")
        parts = value.split('_', 1)
        if len(parts) == 2 and len(parts[0]) < 15:
            prefix = parts[0]
            # Generate consistent hash for the meaningful part
            hash_input = f"{column_name}:{parts[1]}"
            hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            return f"{prefix}_{hash_value}"
        else:
            # No clear prefix, use column-based prefix
            col_prefix = column_name.split('_')[0][:3].upper()
            hash_value = hashlib.md5(f"{column_name}:{value}".encode()).hexdigest()[:8]
            return f"{col_prefix}_{hash_value}"
    
    def _anonymize_id_style(self, value: str, column_name: str) -> str:
        """Anonymize ID-style values maintaining format hints."""
        # Preserve general structure (dashes, underscores)
        if '-' in value:
            parts = value.split('-')
            # Keep first part if it's a prefix (like "CAMP-")
            if len(parts[0]) <= 6 and parts[0].isalpha():
                prefix = parts[0]
                hash_value = hashlib.md5(f"{column_name}:{value}".encode()).hexdigest()[:12]
                return f"{prefix}-{hash_value[:4]}-{hash_value[4:8]}-{hash_value[8:12]}"
            else:
                hash_value = hashlib.md5(f"{column_name}:{value}".encode()).hexdigest()[:16]
                return f"{hash_value[:4]}-{hash_value[4:8]}-{hash_value[8:12]}-{hash_value[12:16]}"
        else:
            # Simple ID format
            hash_value = hashlib.md5(f"{column_name}:{value}".encode()).hexdigest()[:12].upper()
            return f"ID{hash_value}"
    
    def _anonymize_category_style(self, value: str, column_name: str) -> str:
        """Anonymize category-style values."""
        # Create readable category names
        col_prefix = ''.join(word[0].upper() for word in column_name.split('_'))[:3]
        if not col_prefix:
            col_prefix = "CAT"
        
        # Use consistent numbering within each column
        existing_values = len(self.mappings.get(column_name, {}))
        return f"{col_prefix}_{existing_values + 1:03d}"
    
    def _anonymize_generic(self, value: str, column_name: str) -> str:
        """Generic anonymization for unrecognized patterns."""
        # Create a readable generic value
        self.anonymization_counter += 1
        hash_suffix = hashlib.md5(f"{column_name}:{value}".encode()).hexdigest()[:6]
        return f"ANON_{hash_suffix}_{self.anonymization_counter:04d}"
    
    def _detect_encoding(self, file_path: str) -> str:
        """Detect the encoding of a file by trying common encodings."""
        # Common encodings to try (in order of likelihood for business data)
        # utf-8: Standard modern encoding
        # latin-1/iso-8859-1: Western European (é, ñ, etc.)
        # windows-1252/cp1252: Windows Western European
        # utf-16: Sometimes used by Excel
        encodings = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1', 'cp1252', 'utf-16']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # Try to read the first 10000 characters
                    f.read(10000)
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # If all else fails, use latin-1 which accepts all byte values
        return 'latin-1'
    
    def anonymize_csv(self):
        """Process the CSV file according to configuration."""
        source_file = self.config["source_file"]
        dest_file = self.config["destination_file"]
        
        if not os.path.exists(source_file):
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        # Determine encoding
        if self.encoding == "auto":
            detected_encoding = self._detect_encoding(source_file)
            print(f"Detected encoding: {detected_encoding}")
            file_encoding = detected_encoding
        else:
            file_encoding = self.encoding
            print(f"Using specified encoding: {file_encoding}")
        
        print(f"Processing: {source_file}")
        print(f"Preserving columns: {', '.join(sorted(self.preserved_columns)) if self.preserved_columns else 'None'}")
        
        # Read and process the CSV
        with open(source_file, 'r', newline='', encoding=file_encoding) as infile, \
             open(dest_file, 'w', newline='', encoding='utf-8') as outfile:
            
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            
            if not fieldnames:
                raise ValueError("CSV file appears to be empty or invalid")
            
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Identify columns to anonymize
            columns_to_anonymize = [col for col in fieldnames if col not in self.preserved_columns]
            print(f"Anonymizing {len(columns_to_anonymize)} columns: {', '.join(columns_to_anonymize[:5])}")
            if len(columns_to_anonymize) > 5:
                print(f"  ... and {len(columns_to_anonymize) - 5} more")
            
            # Process each row
            row_count = 0
            for row in reader:
                anonymized_row = {}
                
                for column, value in row.items():
                    if column in self.preserved_columns or not value:
                        # Preserve the original value
                        anonymized_row[column] = value
                    else:
                        # Anonymize the value
                        anonymized_row[column] = self._create_anonymized_value(value, column)
                
                writer.writerow(anonymized_row)
                row_count += 1
                
                if row_count % 1000 == 0:
                    print(f"  Processed {row_count} rows...")
        
        # Save mappings
        self._save_mappings()
        
        print(f"\nAnonymization complete!")
        print(f"  Rows processed: {row_count}")
        print(f"  Output file: {dest_file}")
        print(f"  Mapping file: {self.mapping_file}")
        
        # Print statistics
        self._print_statistics()
    
    def _print_statistics(self):
        """Print anonymization statistics."""
        print("\nAnonymization Statistics:")
        total_mappings = 0
        for column, mappings in self.mappings.items():
            if column != "_metadata":
                count = len(mappings)
                total_mappings += count
                print(f"  {column}: {count} unique values anonymized")
        
        print(f"\nTotal unique values anonymized: {total_mappings}")
    
    def reverse_lookup(self, anonymized_value: str, column_name: str = None) -> str:
        """Look up the original value for an anonymized value."""
        if column_name:
            # Search in specific column
            if column_name in self.mappings:
                for original, anonymous in self.mappings[column_name].items():
                    if anonymous == anonymized_value:
                        return original
        else:
            # Search all columns
            for col, mappings in self.mappings.items():
                if col != "_metadata":
                    for original, anonymous in mappings.items():
                        if anonymous == anonymized_value:
                            return f"{original} (from column: {col})"
        
        return f"No mapping found for: {anonymized_value}"
    
    def export_mapping_summary(self, output_file: str = "mapping_summary.txt"):
        """Export a human-readable summary of mappings."""
        with open(output_file, 'w') as f:
            f.write("Business Data Anonymization Mapping Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Mapping file: {self.mapping_file}\n\n")
            
            for column, mappings in sorted(self.mappings.items()):
                if column != "_metadata":
                    f.write(f"\nColumn: {column}\n")
                    f.write("-" * 30 + "\n")
                    
                    # Sort by anonymized value for easier reference
                    sorted_mappings = sorted(mappings.items(), key=lambda x: x[1])
                    for original, anonymized in sorted_mappings[:10]:  # First 10 examples
                        f.write(f"  {original:<40} -> {anonymized}\n")
                    
                    if len(mappings) > 10:
                        f.write(f"  ... and {len(mappings) - 10} more mappings\n")
        
        print(f"\nMapping summary exported to: {output_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Anonymize business data in CSV files")
    parser.add_argument("-c", "--config", default="config.json",
                        help="Path to configuration file (default: config.json)")
    parser.add_argument("-r", "--reverse-lookup", nargs=2, metavar=("VALUE", "COLUMN"),
                        help="Reverse lookup an anonymized value (optionally specify column)")
    parser.add_argument("-s", "--summary", action="store_true",
                        help="Export a mapping summary after anonymization")
    parser.add_argument("-e", "--encoding", 
                        help="Override file encoding (e.g., utf-8, latin-1, windows-1252)")
    
    args = parser.parse_args()
    
    try:
        anonymizer = BusinessDataAnonymizer(args.config)
        
        # Override encoding if specified
        if args.encoding:
            anonymizer.encoding = args.encoding
        
        if args.reverse_lookup:
            value = args.reverse_lookup[0]
            column = args.reverse_lookup[1] if args.reverse_lookup[1] != "any" else None
            result = anonymizer.reverse_lookup(value, column)
            print(f"Reverse lookup: {value} -> {result}")
        else:
            anonymizer.anonymize_csv()
            
            if args.summary:
                anonymizer.export_mapping_summary()
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()