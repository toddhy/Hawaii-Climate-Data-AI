# HCDP-data-for-AI
Analyzing data from the Hawaii Climate Data Portal.

## Project Highlights

### Gemini Chatbot Automation
We've integrated a Gemini 2.0 Flash powered chatbot that can:
- **Execute Local Scripts**: Trigger data fetching and mapping directly from natural language.
- **Inferred Geolocation**: Understand place names (like "Honolulu") and automatically provide coordinates to data scripts.
- **Batch Processing**: Handle complex workflows like "fetch data for Hilo and then map it".

### HCDP API Tools
A suite of tools located in `HCDP_API/` for:
- Finding weather stations within a specific radius.
- Fetching historical rainfall timeseries data.
- Batch downloading rainfall TIFF rasters.
- Creating unified maps with both station points and gridded rainfall overlays.
- Creating interactive rainfall distribution maps.

## Useful Links
- [HCDP Publication List](https://www.hawaii.edu/climate-data-portal/publications-list/)
- [Additional Works Cited (Scholar)](https://scholar.google.com/scholar?oi=bibs&hl=en&cites=15630183130413266936&as_sdt=5)