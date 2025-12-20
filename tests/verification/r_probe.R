# tests/verification/r_probe.R
# Usage: Rscript r_probe.R <function_name> <output_json_path>

# tests/verification/r_probe.R

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {
  stop("Usage: Rscript r_probe.R <func_name> <output_json> <package_path>")
}

func_name <- args[1]
output_path <- args[2]
pkg_path <- args[3]  # <--- NEW ARGUMENT

# Load the package from the specific path provided
if (!dir.exists(pkg_path)) {
  stop(paste("Package path does not exist:", pkg_path))
}

suppressPackageStartupMessages(devtools::load_all(pkg_path))

# Check if function exists
if (!exists(func_name)) {
  stop(paste("Function", func_name, "not found in package."))
}

# Run the function
result <- do.call(func_name, list())

# Export to JSON
if (!requireNamespace("jsonlite", quietly = TRUE)) {
  install.packages("jsonlite", repos = "https://cloud.r-project.org")
}

jsonlite::write_json(result, output_path, auto_unbox = TRUE, pretty = TRUE)
cat(paste("Successfully exported", func_name, "to", output_path, "\n"))
