# Pewpi Infinity Research Portal

A research token management and visualization system with color-coded category buttons and dynamic view modes.

## Features

### 1. JSON-Backed Token Hash Reading (`pewpi_login.py`)

- **Category Token Configuration** (`category_tokens.json`): Stores token hashes linked to research categories
- **Categories**: engineering (green), CEO (orange), import (blue), investigate (pink), routes (red), data (yellow), assimilation (purple)
- **Dynamic Association**: Tokens are automatically categorized based on keyword matching

### 2. Color-Coded Buttons

- Dynamic button generation based on categories from JSON/token data
- Each button displays research article links grouped by category
- Visual feedback with category-specific colors for quick identification

### 3. Toggle View Modes

The portal supports three view modes for displaying research content:

- **Plain Text**: Default mode, displays unformatted content
- **Word Mode**: Highlights individual keywords in their category colors
- **Sentence Mode**: Highlights entire sentences based on the most relevant category

### 4. Error Handling & Logging

- Comprehensive error handling for missing/invalid data
- Detailed logging for debugging and development
- Graceful fallbacks when data is unavailable

## Files

| File | Description |
|------|-------------|
| `pewpi_login.py` | Main module with token management, button generation, and view modes |
| `category_tokens.json` | Category configuration with token hashes and keywords |
| `research_index.json` | Research article index linked to categories |
| `index.html` | Web portal with color-coded buttons and toggle view modes |
| `test_pewpi_login.py` | Integration tests for the module |

## Usage

### Command Line

```bash
# Show status
python pewpi_login.py

# Sync tokens with research index
python pewpi_login.py --sync

# Validate configuration
python pewpi_login.py --validate

# List all categories
python pewpi_login.py --categories

# Output button data JSON
python pewpi_login.py --button-data

# Enable verbose logging
python pewpi_login.py --verbose
```

### Python API

```python
from pewpi_login import PewpiLogin

# Initialize
pewpi = PewpiLogin()

# Get all categories
categories = pewpi.get_categories()

# Sync tokens to research index
records = pewpi.sync()

# Get button data for frontend
button_data = pewpi.get_button_data()

# Generate HTML components
components = pewpi.generate_html_components()
# Returns: toggle_html, toggle_styles, toggle_script

# Validate configuration
result = pewpi.validate()
```

### Web Portal

Open `index.html` in a browser to access the research portal:

1. **Select a Category**: Click any role button to filter research by category
2. **Toggle View Mode**: Use the view mode toggle to switch between Plain Text, Word, and Sentence highlighting
3. **Open Research**: Click "Open research file" to view the full token data

## Configuration

### category_tokens.json

```json
{
  "categories": {
    "engineering": {
      "color": "green",
      "display_name": "Engineering",
      "description": "Engineering and technical research",
      "token_hashes": ["abc123..."],
      "keywords": ["quantum", "physics", "algorithm"]
    }
  },
  "color_map": {
    "green": "#22c55e",
    "orange": "#f97316"
  }
}
```

### Adding New Categories

1. Edit `category_tokens.json`
2. Add a new entry under `categories` with:
   - `color`: Color name (must be in `color_map`)
   - `display_name`: Human-readable name
   - `description`: Category description
   - `token_hashes`: Array of token hashes (can be empty)
   - `keywords`: Array of keywords for automatic categorization

## Testing

Run all tests:

```bash
python -m unittest test_pewpi_login -v
```

## Integration with Existing Scripts

- `build_research_index.py` - Builds research index from tokens
- `cart077_infinity_research_scraper.py` - Scrapes research sources
- `cart080_infinity_research_router.py` - Routes research content
- `cart082_infinity_token_valuator.py` - Values tokens
- `cart083_frontend_router_patch.py` - Updates frontend pages

## License

Pewpi Infinity Research Portal - Part of the Infinity Research System.
