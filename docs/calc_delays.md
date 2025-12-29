                    # Documentation: calc_delays

                    ## 1. Executive Summary
                    ### Objective:
The system loads data from a CSV file and calculates the delays between two dates, storing the results in a new dataset.

### Key Steps:
- **Load Data:** The system reads data from a CSV file named `input_data.csv`.
- **Convert Dates:** It converts the date strings into numeric formats for easier calculation.
- **Calculate Delay:**
  - Extracts year, month, and day from both dates.
  - Converts these parts into actual date values using the MDY function.
  - Calculates the delay in seconds between the registration date (`date_reg`) and the death date (`date_death`).
  - Converts the delay from seconds to days.
- **Filter Data:** Only records with a non-negative delay (i.e., delays that are not negative) are kept.

### Outcome:
The final dataset contains the original data along with an additional column indicating the delay in days between the registration and death dates. This allows stakeholders to understand how long it took for individuals to register after their deaths, which can be useful for various analyses or reports.

                    ## 2. Process Flowchart
                    ```mermaid
                    graph TD;
    classDef script fill:#f9f,stroke:#333,stroke-width:2px;
    classDef data fill:#bbf,stroke:#333,stroke-width:2px;
    classDef logic fill:#dfd,stroke:#333,stroke-width:2px;
    LoadData[("Load Patient CSV")];
    ConvertData["Convert and Calculate Dates"];
    FilterDelay["Filter Delay Days"];
    SaveResult("Save to SQL");
    LoadData --> ConvertData
    ConvertData --> FilterDelay
    FilterDelay --> SaveResult
    class LoadData data;
    class ConvertData logic;
    class FilterDelay logic;
    class SaveResult script;
                    ```

                    ## 3. Original Source
                    * **File:** `01_calc_delays.sps`
                    * **Migrated To:** `calc_delays.R`
