# Movies Recommendation

A web-based application that provides movie and OTT release recommendations with search functionality.

## Project Structure

```
├── app.js                 # Main JavaScript application
├── index.html            # HTML interface
├── styles.css            # Styling
├── excel_to_json.py      # Python script to convert Excel to JSON
├── movies.json           # Movie data
├── movies.xlsx           # Excel source data
├── data/                 # Data directory
│   ├── best-india.json
│   ├── ott-releases.json
│   ├── upcoming-ott.json
│   ├── upcoming-theatrical.json
│   ├── search-index.json
│   └── index.html
└── Readme.md            # This file
```

## Features

- Browse upcoming OTT releases
- View new OTT releases
- Explore best Indian movies/shows
- Search movies by title
- Pagination support
- Language-based sorting

## How to Run

### Option 1: Using Python's Built-in Server (Recommended)

1. Navigate to the project directory:
   ```bash
   cd /workspaces/MoviesRecommendation
   ```

2. Start a local server using Python:
   ```bash
   # For Python 3
   python -m http.server 8000
   
   # Or for Python 2
   python -m SimpleHTTPServer 8000
   ```

3. Open your browser and visit:
   ```
   http://localhost:8000
   ```

### Option 2: Using Node.js/npm

If you have Node.js installed, you can use `http-server`:

1. Install http-server globally (if not already installed):
   ```bash
   npm install -g http-server
   ```

2. Start the server:
   ```bash
   http-server
   ```

3. Open your browser and visit the URL shown in the terminal (typically `http://localhost:8080`)

### Option 3: Direct File Opening

Simply open `index.html` in your web browser by double-clicking it, though some features may work better with a server.

## Data Preparation

If you need to update the movie data from Excel:

1. Ensure you have Python 3 installed
2. Run the Excel to JSON converter:
   ```bash
   python excel_to_json.py
   ```

This will convert `movies.xlsx` to JSON format and update the data files.

## Requirements

- **Browser**: Any modern web browser (Chrome, Firefox, Safari, Edge)
- **Python** (optional): For running the local server or converting Excel data
- **Node.js** (optional): If using http-server

## Usage

1. **Search**: Use the search bar to find movies by title
2. **Browse**: Navigate through different categories using tabs
3. **Pagination**: Use pagination controls to view more movies
4. **Filter**: Movies are automatically sorted by language priority (Hindi → Telugu → Tamil → Malayalam)

## Browser Support

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Notes

- Make sure to serve the files through a web server (not just opening as `file://`) to avoid CORS issues
- All data is loaded from JSON files in the `data/` directory
- The application uses vanilla JavaScript with no external dependencies


====

Run Locally using cmd --> python -m http.server 8000
