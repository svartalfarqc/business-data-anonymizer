# Business Data Anonymizer

A Python tool for anonymizing business data in CSV files while preserving specified columns and maintaining full traceability through mapping files.
Created by Luc Mercier using Claude (Anthropic AI). Provided AS IS.

## Overview

This tool is designed to anonymize business data (marketing campaigns, UTM parameters, product IDs, etc.) in CSV files before sharing with public LLMs. It maintains a mapping file that allows you to reverse the anonymization when needed.

**Key Features:**
- Configurable column preservation (metrics, dates, etc. remain unchanged)
- Smart anonymization based on data patterns (UTMs, IDs, categories)
- Full traceability with JSON mapping file
- Reverse lookup functionality
- No external dependencies (uses Python standard library only)

## Quick Start

1. **Setup your configuration** (`config.json`):
```json
{
  "source_file": "your_data.csv",
  "destination_file": "anonymized_data.csv",
  "mapping_file": "anonymization_mappings.json",
  "encoding": "auto",
  "preserve_columns": ["date", "revenue", "clicks", "conversions"]
}
```

2. **Run the anonymizer**:
```bash
python anonymize.py
```

3. **Use the anonymized data** with your LLM for analysis

4. **Reverse lookup** when needed:
```bash
python anonymize.py -r "UTM_a3f2c8d9" utm_source
```

## Installation

No installation required! Just ensure you have Python 3.6+ and copy the script.

```bash
# Clone or download the script
git clone <repository>
cd business-data-anonymizer

# Create your config file
cp config.example.json config.json
# Edit config.json with your settings
```

## Configuration

The `config.json` file controls the anonymization process:

```json
{
  "source_file": "path/to/input.csv",
  "destination_file": "path/to/output.csv",
  "mapping_file": "anonymization_mappings.json",
  "encoding": "auto",
  "preserve_columns": [
    "date",
    "revenue",
    "cost",
    "impressions",
    "clicks",
    "conversions"
  ]
}
```

### Configuration Options

- **source_file**: Path to your input CSV file
- **destination_file**: Path where anonymized CSV will be saved
- **mapping_file**: Path to store the anonymization mappings (default: `anonymization_mappings.json`)
- **encoding**: Character encoding for reading the CSV file
  - `"auto"` - Automatically detect encoding (default)
  - `"utf-8"`, `"latin-1"`, `"windows-1252"`, etc. - Specify encoding manually
- **preserve_columns**: List of column names that should NOT be anonymized (typically metrics and dates)

## Usage Examples

### Basic Anonymization

```bash
# Using default config.json
python anonymize.py

# Using custom config file
python anonymize.py -c my_config.json

# Override encoding from command line
python anonymize.py -e windows-1252
```

### Reverse Lookup

```bash
# Look up original value in specific column
python anonymize.py -r "CAT_001" campaign_type

# Search all columns
python anonymize.py -r "UTM_a3f2c8d9" any
```

### Export Mapping Summary

```bash
# Anonymize and create a readable summary
python anonymize.py -s
```

## Anonymization Patterns

The tool intelligently anonymizes based on detected patterns:

### UTM-Style Parameters
- Original: `social_facebook_summer2024`
- Anonymized: `social_a3f2c8d9`

### IDs and Identifiers
- Original: `CAMP-2024-SUMMER-PROMO`
- Anonymized: `CAMP-a3f2-c8d9-e5b1`

### Categories
- Original: `premium_tier`
- Anonymized: `CAT_001`

### Generic Values
- Original: `complex_business_data_string`
- Anonymized: `ANON_b2d4e6_0001`

## Example Workflow

1. **Prepare your data**:
```csv
date,utm_source,utm_campaign,product_id,revenue,conversions
2024-01-15,google,spring_sale_2024,PROD-12345,5000,25
2024-01-15,facebook,spring_sale_2024,PROD-67890,3000,15
```

2. **Configure preservation** (config.json):
```json
{
  "preserve_columns": ["date", "revenue", "conversions"],
  "encoding": "auto"
}
```

3. **Run anonymization**:
```bash
python anonymize.py
```

Output:
```
Detected encoding: windows-1252
Processing: your_data.csv
Preserving columns: conversions, date, revenue
Anonymizing 5 columns: utm_source, utm_campaign, product_id...
  Processed 1000 rows...

Anonymization complete!
  Rows processed: 2500
  Output file: anonymized_data.csv
  Mapping file: anonymization_mappings.json
```

4. **Result**:
```csv
date,utm_source,utm_campaign,product_id,revenue,conversions
2024-01-15,UTM_a3f2c8,UTM_d9e5f1,IDa3f2c8d9e5b1,5000,25
2024-01-15,UTM_b4d3e9,UTM_d9e5f1,IDb4d3e9f2a1c5,3000,15
```

5. **Use with LLM**: The anonymized data is now safe to share with public LLMs for analysis

6. **Interpret results**: When the LLM references "UTM_a3f2c8", use reverse lookup to find it means "google"

## Security Best Practices

1. **Never commit real data or mapping files to version control**
   - The `.gitignore` file is configured to exclude CSV files and mapping files
   - Always use `.example` files for sharing configurations

2. **Protect your mapping file**
   - The mapping file (`anonymization_mappings.json`) is your key to the original data
   - Store it securely and limit access
   - Consider encrypting it at rest

3. **Use separate mapping files for different security levels**
   ```bash
   python anonymize.py -c config_public.json    # Less sensitive data
   python anonymize.py -c config_internal.json  # More sensitive data
   ```

4. **Regular backups**
   - Backup your mapping files regularly
   - Store backups securely, separate from the anonymized data

## Limitations

- Designed for business data, not PII (assumes PII already removed)
- Date values are preserved by default (configure if needed)
- Memory-based processing (very large files may require chunking)
- Anonymization is deterministic (same input = same output)

## Troubleshooting

### "Source file not found"
- Check the path in your config.json
- Ensure the file exists and is readable

### "CSV file appears to be empty"
- Verify the CSV has headers
- Check file encoding (UTF-8 expected)

### Encoding errors (UnicodeDecodeError)
- The tool automatically detects encoding when set to `"auto"`
- The error "can't decode byte 0xe9" typically indicates Latin-1 or Windows-1252 encoding (the byte represents 'é')
- If auto-detection fails, specify encoding manually in config.json:
  ```json
  "encoding": "latin-1"  // or "windows-1252", "iso-8859-1", etc.
  ```
- Common encodings for business data:
  - `utf-8` - Standard encoding (default for most modern files)
  - `latin-1` or `iso-8859-1` - Western European characters
  - `windows-1252` or `cp1252` - Windows encoding
  - `utf-16` - Sometimes used by Excel exports

### Reverse lookup returns "No mapping found"
- Ensure you're using the correct mapping file
- Check if the value was actually anonymized (not in preserve_columns)

## Advanced Usage

### Programmatic Usage

```python
from anonymize import BusinessDataAnonymizer

# Initialize with custom config
anonymizer = BusinessDataAnonymizer("my_config.json")

# Anonymize
anonymizer.anonymize_csv()

# Reverse lookup
original = anonymizer.reverse_lookup("UTM_a3f2c8", "utm_source")
print(f"Original value: {original}")
```

### Handling Different File Encodings

The tool automatically detects file encoding, but you can specify it manually:

```json
{
  "encoding": "windows-1252"  // For files with European characters
}
```

Common scenarios:
- Excel exports: Often `windows-1252` or `utf-16`
- Files with accented characters: `latin-1` or `iso-8859-1`
- Modern CSV exports: Usually `utf-8`

### Custom Anonymization Patterns

You can extend the anonymization logic by modifying the pattern detection methods:
- `_looks_like_utm()` - Detect UTM-style parameters
- `_looks_like_id()` - Detect ID patterns
- `_looks_like_category()` - Detect category values

## License

This tool is provided as-is for business data anonymization. Ensure compliance with your organization's data handling policies.
