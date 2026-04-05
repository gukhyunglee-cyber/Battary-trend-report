# Battery Trend Reporter

A Python-based tool to automatically collect battery industry trends from the web and YouTube, and upload them to Google NotebookLM for analysis.

## Features
- **Data Collection**: Scrapes search results from DuckDuckGo and YouTube using `duckduckgo-search`.
- **Automated Upload**: Uses Playwright to navigate NotebookLM and upload collected data as a text source.
- **Robust Automation**: Handles Korean interface quirks and persistent Google authentication.

## Prerequisites
- Python 3.8+
- Google Account (for NotebookLM)

## Installation

1. Clone the repository and navigate to the project folder:
   ```bash
   cd battery-trend-reporter
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
   (Note: `requirements.txt` should include `playwright`, `duckduckgo-search`, `beautifulsoup4`)

## Configuration

Edit `settings.py` to configure:
- `NOTEBOOK_ID`: The ID of your target NotebookLM notebook (optional, will create new if empty).
- `USER_DATA_DIR`: Path to store persistent browser session (default: `./user_data`).

## Usage

### 1. First Run (Authentication)
Run the orchestrator. If not logged in, a browser window will open. Log in to your Google account manually.
```bash
python orchestrator.py
```
Once logged in, the script will proceed (or you might need to restart it if it times out during login). The session cookies will be saved.

### 2. Standard Run
```bash
python orchestrator.py
```
This will:
1. Collect latest trends for "2차전지 이슈" and "배터리 기술 동향".
2. Save them to `trend_data.txt`.
3. Upload the text to NotebookLM.

### 3. Collection Only (Testing)
To verify data collection without uploading:
```bash
python orchestrator.py --collect-only
```

## Troubleshooting
- **Upload Failures**: If the "Add source" button isn't found, ensure the interface language is English or Korean (supported).
- **Login Issues**: Delete the `user_data` directory to reset authentication.

## License
MIT
