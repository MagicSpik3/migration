# Documentation: demo_complex_logic

## 1. Executive Summary
Calculates tax based on Region and Income tiers (North=15%, South=10%, Others=5%).

## 2. Process Flowchart
```mermaid
graph TD;
    classDef script fill:#f9f,stroke:#333,stroke-width:2px;
    classDef data fill:#bbf,stroke:#333,stroke-width:2px;
    classDef logic fill:#dfd,stroke:#333,stroke-width:2px;
    Start[("Start Process")];
    CheckRegion["Check Region (North/South)"];
    NorthBranch["Set Tax 15%"];
    HighIncomeCheck["Check Income > 50k"];
    SouthBranch["Set Tax 10%"];
    DefaultBranch["Set Tax 5%"];
    End("Save Data");
    Start --> CheckRegion
    CheckRegion --> NorthBranch
    NorthBranch --> HighIncomeCheck
    HighIncomeCheck --> SouthBranch
    SouthBranch --> DefaultBranch
    DefaultBranch --> End
    class Start data;
    class CheckRegion logic;
    class NorthBranch logic;
    class HighIncomeCheck logic;
    class SouthBranch logic;
    class DefaultBranch logic;
    class End script;
```

## 3. Original Source
* **File:** `demo_script.sps`
* **Migrated To:** `demo_script.R`
