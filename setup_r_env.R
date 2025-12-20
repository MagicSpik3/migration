# List of required packages for the Migration Test Harness
required_pkgs <- c("jsonlite", "readr", "devtools", "testthat")

# Install missing packages
new_pkgs <- required_pkgs[!(required_pkgs %in% installed.packages()[,"Package"])]
if(length(new_pkgs)) install.packages(new_pkgs, repos="https://cloud.r-project.org")

print("All R dependencies installed.")