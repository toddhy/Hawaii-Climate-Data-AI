# System Architecture

The following diagram illustrates the interaction between the React frontend, FastAPI backend, LangChain AI agent, and the TileDB climate database.

```mermaid
graph TD
    subgraph "Frontend (React / Vite)"
        UI["Chat Interface (App.tsx)"]
        Map["Map Viewer (Iframe)"]
        Client["API Client (api.ts)"]
    end

    subgraph "Backend (FastAPI)"
        Srv["Server (server.py)"]
        DB_Sess[("Session Store (Memory)")]
    end

    subgraph "AI Agent (LangChain)"
        Agent["LangChain Agent (langchain_agent.py)"]
        LLM["Gemini 2.0 Flash"]
    end

    subgraph "Tools & Utilities (HCDP API)"
        Finder["Station Finder"]
        Mapper["Map Visualizer"]
    end

    subgraph "Data Layer (TileDB)"
        TDB_Access["TileDB Access (tiledb_access.py)"]
        Rainfall[("Rainfall Array")]
        Temp[("Temperature Arrays (Mean/Max/Min)")]
        SPI[("SPI Array")]
    end

    %% Interactions
    UI --> Client
    Client -- "POST /chat" --> Srv
    Srv --> DB_Sess
    Srv -- "Invoke" --> Agent
    Agent -- "Prompts" --> LLM
    Agent -- "Calls" --> Finder
    Agent -- "Calls" --> Mapper
    
    Finder -- "Queries" --> TDB_Access
    Mapper -- "Queries" --> TDB_Access
    Agent -- "Queries" --> TDB_Access

    TDB_Access --> Rainfall
    TDB_Access --> Temp
    TDB_Access --> SPI

    Mapper -- "Generates" --> MapHTML["gridded_map.html"]
    Srv -- "Serves" --> MapHTML
    MapHTML --> Map
```

## Component Breakdown

1.  **React Frontend**: Provides a premium chat interface where users can ask natural language questions. It displays the assistant's text responses and renders generated interactive maps in an iframe.
2.  **FastAPI Backend**: Acts as the bridge between the frontend and the AI. It manages conversation sessions and serves the generated HTML map files.
3.  **LangChain Agent**: The "brain" of the application. It uses Gemini 2.0 Flash to understand intent and decides which local tools to call (geocoding, data querying, or mapping).
4.  **HCDP API Tools**: Specialized Python scripts that perform heavy lifting like coordinate resolution, spatial searches, and raster map generation using `folium` and `rasterio`.
5.  **TileDB Data Layer**: A high-performance spatial database storing over 30 years of monthly climate data for Hawaii, optimized for sub-second retrieval.
