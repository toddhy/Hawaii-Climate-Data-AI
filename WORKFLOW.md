# HCDP Project Workflow Visualization

This document visualizes the architecture and operational flow of the Hawaii Climate Data Portal (HCDP) AI Assistant.

## System Architecture

The following diagram illustrates how the Gemini-powered agent interacts with the HCDP API, the high-performance TileDB database, and local raster data to serve user requests.

```mermaid
graph TD
    %% Entities
    User([User])
    
    subgraph "Interaction & Orchestration"
        Agent[Gemini 2.0 Flash Agent]
        Tools{LangChain Tool Layer}
    end

    subgraph "Functional Tools (Python Scripts)"
        G[geocode_placename]
        F[find_nearby_stations]
        M[generate_gridded_map]
        Q[query_historical_climate_data]
    end

    subgraph "External & Local APIs"
        Geo[Nominatim Geocoder]
        Finder[station_finder.py]
        Vis[map_visualizer.py]
        TileAPI[tiledb_access.py]
    end

    subgraph "Data Storage"
        CSV[Station CSV/Metadata]
        TIFFs[(Local TIFF Rasters)]
        TDB[(TileDB Arrays<br/>Rainfall/Temp/SPI)]
    end

    %% Flow: Input
    User -- "Natural Language Request" --> Agent
    Agent -- "Chains Tool Calls" --> Tools
    
    %% Flow: Tools
    Tools --> G
    Tools --> F
    Tools --> M
    Tools --> Q

    %% Flow: Tool -> Logic
    G --> Geo
    F --> Finder
    M --> Vis
    Q --> TileAPI

    %% Flow: Logic -> Data
    Finder --> CSV
    Vis -- "Aggregates" --> TIFFs
    Vis -- "Markers" --> CSV
    TileAPI -- "Slices/Queries" --> TDB

    %% Flow: Output
    Vis -- "Folium Render" --> HTML[interactive_map.html]
    TileAPI -- "Data Values" --> Q
    
    HTML -- "Display" --> User
    Q --> Agent
    Agent -- "Text Explanation" --> User

    %% Styling
    style User fill:#f9f,stroke:#333,stroke-width:2px
    style Agent fill:#bbf,stroke:#333,stroke-width:2px
    style TDB fill:#bfb,stroke:#333,stroke-width:2px
    style TIFFs fill:#bfb,stroke:#333,stroke-width:1px
```

## Data Ingestion & Optimization Flow

The project also includes a specialized workflow for optimizing storage efficiency by converting raw TIFFs into compressed TileDB arrays.

```mermaid
graph LR
    Raw[Raw HCDP TIFFs] --> Opt[optimize_stations_data.py]
    Opt -- "Re-ingestion" --> TDB_New[(Optimized TileDB)]
    TDB_New -- "Zstd Compression" --> Storage[25GB -> Reduced Size]
    TDB_New -- "Optimized Dimensions" --> Agent
```

> [!TIP]
> **TileDB Efficiency**: The TileDB arrays allow the agent to query a single "pixel" across 30+ years of data without loading entire TIFF files into memory, enabling near-instant response times for historical climate queries.
