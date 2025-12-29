                    # Documentation: complex_logic

                    ## 1. Executive Summary
                    ### Objective:
The system categorizes participants into age groups and calculates the average delay days by region.

### Key Steps:
- **Recode Age:** Converts numerical age values into categorical age groups (Minor, Adult, Senior).
- **Filter Data:** Removes any records where the delay days are negative.
- **Aggregate Data:** Groups the remaining data by region and calculates the average delay days and maximum age within each region.

### Outcome:
The final dataset will include the following information for each region:
- The average number of delay days
- The maximum age of participants in that region

This helps stakeholders understand how delays vary across different regions based on participant age groups.

                    ## 2. Process Flowchart
                    ```mermaid
                    graph TD;
    classDef script fill:#f9f,stroke:#333,stroke-width:2px;
    classDef data fill:#bbf,stroke:#333,stroke-width:2px;
    classDef logic fill:#dfd,stroke:#333,stroke-width:2px;
    LoadData[("Load Patient Data")];
    FilterDelay["Filter Non-negative Delays"];
    RecodeAge["Recode Age into Groups"];
    AggregateData["Aggregate by Region"];
    SaveResult("Save to Output");
    LoadData --> FilterDelay
    FilterDelay --> RecodeAge
    RecodeAge --> AggregateData
    AggregateData --> SaveResult
    class LoadData data;
    class FilterDelay logic;
    class RecodeAge logic;
    class AggregateData logic;
    class SaveResult script;
                    ```

                    ## 3. Original Source
                    * **File:** `03_complex_logic.sps`
                    * **Migrated To:** `complex_logic.R`
