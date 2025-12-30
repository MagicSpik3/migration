# Documentation: summarize_deaths

## 1. Executive Summary
### Objective:
Summarize the number of deaths by month.

### Key Steps:
- Extracts the month from the `date_death` variable.
- Groups the data by the extracted month.
- Counts the total number of deaths for each month.

### Outcome:
The final dataset will show the total number of deaths for each month, allowing you to see trends over time.

## 2. Process Flowchart
```mermaid
graph TD;
    classDef script fill:#f9f,stroke:#333,stroke-width:2px;
    classDef data fill:#bbf,stroke:#333,stroke-width:2px;
    classDef logic fill:#dfd,stroke:#333,stroke-width:2px;
    LoadData[("Load Patient CSV")];
    FilterDeath["Filter by Date of Death"];
    CalcMonth["Calculate Death Month"];
    AggregateDeaths["Aggregate Deaths by Month"];
    SaveOutput("Save to Output File");
    LoadData --> FilterDeath
    FilterDeath --> CalcMonth
    CalcMonth --> AggregateDeaths
    AggregateDeaths --> SaveOutput
    class LoadData data;
    class FilterDeath logic;
    class CalcMonth logic;
    class AggregateDeaths logic;
    class SaveOutput script;
```

## 3. Original Source
* **File:** `02_summarize_deaths.sps`
* **Migrated To:** `summarize_deaths.R`
