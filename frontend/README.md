# Frontend Process Flow - Sequence Diagram

This diagram shows the complete process flow of the frontend application, from startup to simulation execution and results viewing.

## Mermaid Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant A as App (main)
    participant SC as StatusCheckUI
    participant ST as Simulation Tab
    participant GD as GridDesignerUI
    participant SI as SimulationInputUI
    participant SP as SimulationPreparationUI
    participant SIM as Simulator
    participant RT as Result Tab
    participant RU as ResultUI
    participant DB as SimulationDatabase
    participant TC as TC Server
    participant SM as SM Server
    participant BE as Backend Server

    Note over U, BE: Application Startup & Status Check
    U->>A: Launch application
    A->>A: Configure Streamlit app
    A->>SC: Initialize StatusCheckUI
    SC->>TC: Check server 1 status
    SC->>SM: Check server 1 status
    SC->>BE: Check server 1 status
    SC->>TC: Check server 2 status
    SC->>SM: Check server 2 status
    SC->>BE: Check server 2 status
    SC->>U: Display server status & controls

    Note over U, BE: Grid Design Phase
    U->>ST: Switch to Simulation tab
    ST->>GD: Initialize GridDesignerUI
    GD->>U: Request grid Excel file upload
    U->>GD: Upload grid Excel file
    GD->>GD: Validate grid data and stations
    GD->>GD: Calculate buffer ratios
    GD->>U: Display grid visualization
    GD->>U: Request desired skycar directions
    U->>GD: Input skycar directions
    GD->>U: Request linked stations configuration
    U->>GD: Configure linked stations

    Note over U, BE: Simulation Input Phase
    ST->>SI: Initialize SimulationInputUI
    SI->>U: Request simulation parameters<br/>(name, duration, bins per order, etc.)
    U->>SI: Input simulation parameters
    SI->>SI: Validate inputs and calculate recommendations
    SI->>U: Display bin distribution plots
    SI->>U: Show recommended number of skycars

    Note over U, BE: Simulation Preparation Phase
    ST->>SP: Initialize SimulationPreparationUI
    SP->>U: Request server selection
    U->>SP: Select server (1 or 2)
    SP->>SP: Create input objects:<br/>- InputZonesAndStations<br/>- InputSMObstacles<br/>- InputBuffer<br/>- InputSkyCarSetup<br/>- InputTCObstacles<br/>- InputSkyCarConstraints<br/>- InputAutostore<br/>- InputSimulation<br/>- InputDatabase
    SP->>U: Display prepared JSON files (optional)

    Note over U, BE: Simulation Execution Phase
    U->>ST: Click "Start Simulation"
    ST->>SIM: Initialize Simulator
    SIM->>TC: Check server health
    SIM->>SM: Check server health
    SIM->>BE: Check server health
    
    alt Server healthy and no simulation running
        SIM->>SM: Reset layout (/v3/initialize/reset)
        SIM->>SM: Initialize setup (/v3/initialize)
        SIM->>SM: Configure SM obstacles (/v3/obstacles)
        SIM->>SM: Configure storage layout (/v3/initialize/storage)
        SIM->>TC: Configure TC obstacles (/wcs/obstacle)
        SIM->>TC: Configure skycar setup (/simulation/seed-skycars)
        SIM->>TC: Configure skycar constraints (/operation/cube/constraints)
        SIM->>TC: Start cube (/operation/cube)
        SIM->>SM: Disable autostore (/v3/settings/auto-store)
        SIM->>DB: Create simulation run record
        SIM->>BE: Start simulation (/jobs/create)
        SIM->>DB: Save simulation parameters
        SIM->>U: Display success message
    else Server unhealthy or simulation running
        SIM->>U: Display warning message
    end

    Note over U, BE: Results Viewing Phase
    U->>RT: Switch to Result tab
    RT->>RU: Initialize ResultUI
    RU->>U: Request date range for simulations
    U->>RU: Select date range
    RU->>DB: Get simulation runs by timestamp range
    RU->>U: Display available simulations
    U->>RU: Select simulation
    
    alt Cached data available
        RU->>RU: Load from session cache
    else No cached data
        RU->>DB: Get logs by simulation run
        RU->>TC: Get movement data from MongoDB
        RU->>RU: Cache data in session state
    end
    
    RU->>RU: Process and analyze data:<br/>- Parse stations from string<br/>- Calculate operation ranges<br/>- Filter normal vs advance operations
    RU->>U: Display simulation duration metrics
    RU->>U: Display bin presentation over time chart
    RU->>U: Display bin presentation rate by station
    RU->>U: Display bin handling rate by skycar
    
    opt Animation requested
        U->>RU: Upload grid file for animation
        U->>RU: Specify time range
        U->>RU: Click "Animate"
        RU->>RU: Generate animation video
        RU->>U: Provide download link for animation
    end
```

## Process Overview

The frontend application follows a structured workflow:

### 1. Application Startup & Status Check
- Streamlit app initialization
- Server health checks for TC, SM, and Backend servers
- Status display and control interface

### 2. Grid Design Phase
- Grid Excel file upload and validation
- Station configuration and validation
- Skycar direction preferences
- Linked station setup

### 3. Simulation Input Phase
- Simulation parameter configuration
- Bin distribution setup using Pareto distribution
- Skycar count recommendations
- Input validation and visualization

### 4. Simulation Preparation Phase
- Server selection (1 or 2)
- Creation of input objects for all simulation components
- JSON configuration file preparation

### 5. Simulation Execution Phase
- Health checks and conflict detection
- Sequential API calls to configure servers:
  - SM (Storage Manager) configuration
  - TC (Traffic Controller) setup
  - Backend simulation initiation
- Database record creation

### 6. Results Viewing Phase
- Simulation run selection
- Data retrieval and caching
- Comprehensive analytics and visualization
- Optional animation generation

## Components

- **GridDesignerUI**: Grid layout design and validation
- **SimulationInputUI**: Parameter input and validation
- **SimulationPreparationUI**: Configuration preparation
- **Simulator**: Orchestrates simulation startup
- **ResultUI**: Results analysis and visualization
- **StatusCheckUI**: Server monitoring and control

## External Systems

- **TC Server**: Traffic control and skycar management
- **SM Server**: Storage management
- **Backend Server**: Simulation execution engine
- **SimulationDatabase**: Local data persistence
- **MongoDB**: Movement data storage
