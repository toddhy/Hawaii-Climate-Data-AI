# Project Utilities

This directory contains specialized tools and helper scripts used for data acquisition, processing, and legacy Gemini API interactions.

## Subdirectories

### 1. `gemini_txtfile_interaction/`
Legacy interaction layer for the Gemini **File API** (separate from the current LangChain agent).
- `fileAPI_uploader.py`: Uploads local text files/datasets to Gemini's long-term context storage.
- `chatbot.py`: Interactive chat session using all currently active uploaded files.
- `fileAPI_deleter.py`: Clean up tool to remove files from the Gemini cloud storage.

### 2. `HCDP_PublicationScraper/`
Automated tools for building the HCDP research corpus.
- `robust_downloader.py`: Headless browser-based scraper to download research PDFs from HCDP and Google Scholar.
- `url_extractor.py`: Extracts and validates publication links from raw text sources.

### 3. `pdfImageExtractor/` & `pdfTextExtractor/`
Advanced PDF processing pipeline for extracting structured data from academic papers.
- `extractImages.py`: Separates figures, charts, and maps from climate publications.
- `pdfTextExtractor.py`: High-fidelity text extraction using `PyMuPDF`.
- `run_marker.py`: Orchestrates deep document analysis (requires `marker-pdf`).

### 4. `misc/`
General-purpose scripts for codebase and data maintenance.
- `optimize_stations_data.py`: Prunes and reformats station metadata for faster UI loading.
- `print_duplicate_files.py`: Identifies redundant TIFFs or PDFs across directories.
- `compare_pdf_txt.py`: Validates the integrity of text extraction against original source PDFs.

---
*Note: These tools are intended for internal developers and researchers. Most end-user functionality is accessed via the root `start_app.cmd` or `gemini_chat/langchain_agent.py`.*
