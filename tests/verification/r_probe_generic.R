# tests/verification/r_probe_generic.R
library(jsonlite)
library(readr)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 4) {
  stop("Usage: Rscript r_probe_generic.R <func_name> <args_map_json> <output_json> <package_path>")
}

func_name <- args[1]
args_map_json <- args[2] 
output_path <- args[3]
pkg_path <- args[4]

# 1. Load Package
if (!dir.exists(pkg_path)) {
  stop(paste("Package path does not exist:", pkg_path))
}

# Use 'export_all=TRUE' to ensure even internal functions are visible
suppressPackageStartupMessages(devtools::load_all(pkg_path, export_all = TRUE))

# 2. Parse Arguments
raw_args <- fromJSON(args_map_json)
final_args <- list()

for (arg_name in names(raw_args)) {
  val <- raw_args[[arg_name]]
  
  if (is.character(val) && grepl("\\.csv$", val)) {
    if(file.exists(val)) {
        # Check if readr is available
        if (!requireNamespace("readr", quietly = TRUE)) stop("Package 'readr' needed.")
        df <- readr::read_csv(val, show_col_types = FALSE)
        final_args[[arg_name]] <- df
    } else {
        final_args[[arg_name]] <- val 
    }
  } else {
    final_args[[arg_name]] <- val
  }
}

# 3. Execute with Debugging
if (!exists(func_name)) {
  # --- DEBUG BLOCK ---
  cat("------------------------------------------------\n")
  cat(paste("ERROR: Function '", func_name, "' not found.\n", sep=""))
  cat("Listing visible functions in the loaded package:\n")
  
  # List all objects in the package environment
  pkg_env_name <- paste0("package:", devtools::as.package(pkg_path)$package)
  if (pkg_env_name %in% search()) {
      print(ls(pkg_env_name))
  } else {
      cat("Package environment not found in search path.\n")
      # Try to list internal functions
      print(ls(envir = devtools::dev_env(pkg_path)))
  }
  cat("------------------------------------------------\n")
  stop("Function not found (see list above).")
}

result <- do.call(func_name, final_args)

# 4. Export Result
jsonlite::write_json(result, output_path, auto_unbox = TRUE, pretty = TRUE)