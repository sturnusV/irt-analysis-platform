# ---------------------------------------------------------
# irt_analysis.R - Updated to match Plumber.R logic (Standalone)
# ---------------------------------------------------------

library(mirt)
library(jsonlite)
library(dplyr)
library(tibble)
library(purrr)

# ---------------------------------------------------------
# Enhanced IRT Model Fitting with 3PL and Fallback
# ---------------------------------------------------------

fit_irt_model_standalone <- function(response_matrix) {
  set.seed(12345)
  
  message("Attempting 3PL model fitting...")
  
  # First attempt: 3PL model
  model_3pl <- tryCatch({
    mirt(
      response_matrix, 
      1, 
      itemtype = "3PL", 
      technical = list(
        NCYCLES = 10000,
        theta_lim = c(-6, 6),
        warn = FALSE,
        message = FALSE,
        set.seed = 12345 # Added set.seed here for consistency
      ),
      SE = TRUE,
      verbose = FALSE,
      optimizer = "BFGS" # Added optimizer for consistency
    )
  }, error = function(e) {
    message("3PL model failed: ", e$message)
    NULL
  })
  
  # Check if 3PL converged and has reasonable parameters
  if (!is.null(model_3pl) && model_3pl@OptimInfo$converged) {
    # Validate 3PL parameters
    params_3pl <- coef(model_3pl, simplify = TRUE, IRTpars = TRUE)$items
    
    # Check for problematic parameters
    extreme_params <- any(
      params_3pl[, "a"] > 10 | params_3pl[, "a"] < 0.01 |
      params_3pl[, "b"] > 10 | params_3pl[, "b"] < -10 |
      params_3pl[, "g"] > 0.5 | params_3pl[, "g"] < 0
    )
    
    if (!extreme_params) {
      message("3PL model fitted successfully with reasonable parameters")
      return(list(model = model_3pl, type = "3PL"))
    } else {
      message("3PL model has extreme parameters, falling back to 2PL")
    }
  }
  
  # Fallback: 2PL model
  message("Fitting 2PL model as fallback...")
  model_2pl <- mirt(
    response_matrix, 
    1, 
    itemtype = "2PL", 
    technical = list(
      NCYCLES = 10000,
      theta_lim = c(-6, 6),
      warn = FALSE,
      message = FALSE
    ),
    SE = TRUE,
    verbose = FALSE
  )
  
  return(list(model = model_2pl, type = "2PL"))
}

# ---------------------------------------------------------
# Standard Error Extraction (No Change Needed)
# ---------------------------------------------------------

extract_standard_errors <- function(model, model_type = "3PL") {
  tryCatch({
    # Get parameters with SEs
    params_with_se <- coef(model, SE = TRUE, IRTpars = TRUE, printSE = TRUE)
    
    # Remove the group parameters (last element)
    if ("GroupPars" %in% names(params_with_se)) {
      params_with_se <- params_with_se[-length(params_with_se)]
    }
    
    n_items <- length(params_with_se)
    
    # Create SE matrix
    if (model_type == "3PL") {
      se_matrix <- matrix(NA, nrow = n_items, ncol = 4)
      colnames(se_matrix) <- c("a", "b", "g", "u")
    } else {
      se_matrix <- matrix(NA, nrow = n_items, ncol = 3)
      colnames(se_matrix) <- c("a", "b", "u")
    }
    
    rownames(se_matrix) <- names(params_with_se)
    
    # Extract SEs from the printed output structure
    for (i in 1:n_items) {
      item <- params_with_se[[i]]
      
      # The SEs are in the second row of the matrix
      if (!is.null(item) && nrow(item) >= 2) {
        se_matrix[i, "a"] <- as.numeric(item[2, "a"])
        se_matrix[i, "b"] <- as.numeric(item[2, "b"])
        if (model_type == "3PL" && "g" %in% colnames(item)) {
          se_matrix[i, "g"] <- as.numeric(item[2, "g"])
        }
        if ("u" %in% colnames(item)) {
          se_matrix[i, "u"] <- as.numeric(item[2, "u"])
        }
      }
    }
    
    message("Successfully extracted standard errors")
    return(se_matrix)
    
  }, error = function(e) {
    message("Standard error extraction failed: ", e$message)
    return(NULL)
  })
}

# ---------------------------------------------------------
# Enhanced Parameter Extraction for both 2PL and 3PL (No Change Needed)
# ---------------------------------------------------------

extract_item_params <- function(params_table, params_se_table = NULL, model_type = "2PL") {
  n_items <- nrow(params_table)
  rows <- vector("list", n_items)
  
  for (i in seq_len(n_items)) {
    row <- params_table[i, , drop = TRUE]
    
    # Extract parameters
    a <- as.numeric(row["a"])
    b <- as.numeric(row["b"])
    
    # Guessing parameter handling
    if (model_type == "3PL" && "g" %in% names(row)) {
      g <- as.numeric(row["g"])
    } else {
      g <- 0.0
    }
    
    # Standard errors - with proper extraction
    se_a <- NA_real_
    se_b <- NA_real_
    se_g <- 0.0
    
    if (!is.null(params_se_table) && nrow(params_se_table) >= i) {
      se_row <- params_se_table[i, , drop = TRUE]
      
      if ("a" %in% colnames(params_se_table) && !is.na(se_row["a"])) {
        se_a <- as.numeric(se_row["a"])
      }
      if ("b" %in% colnames(params_se_table) && !is.na(se_row["b"])) {
        se_b <- as.numeric(se_row["b"])
      }
      if (model_type == "3PL" && "g" %in% colnames(params_se_table) && !is.na(se_row["g"])) {
        se_g <- as.numeric(se_row["g"])
      }
    }
    
    rows[[i]] <- tibble(
      item_id = paste0("item_", i),
      discrimination = ifelse(is.na(a), 1.0, round(a, 4)),
      difficulty = ifelse(is.na(b), 0.0, round(b, 4)),
      guessing = round(g, 4),
      se_discrimination = ifelse(is.na(se_a), 0.0, round(se_a, 4)),
      se_difficulty = ifelse(is.na(se_b), 0.0, round(se_b, 4)),
      se_guessing = round(se_g, 4),
      model_type = model_type
    )
  }
  
  bind_rows(rows)
}

# ---------------------------------------------------------
# Enhanced Parameter Cleaning (FIXED TO MATCH Plumber LOGIC)
# ---------------------------------------------------------

clean_parameters <- function(item_params, model_type = "2PL") {
  for (i in seq_len(nrow(item_params))) {
    # Fix negative discrimination (Match Plumber.R: use abs and then cap)
    if (!is.na(item_params$discrimination[i]) && item_params$discrimination[i] < 0) {
      item_params$discrimination[i] <- abs(item_params$discrimination[i]) # Take absolute value
    }
    
    # Fix very high discrimination (Match Plumber.R)
    if (!is.na(item_params$discrimination[i]) && item_params$discrimination[i] > 4.0) {
      item_params$discrimination[i] <- 4.0
    }
    
    # Ensure minimum discrimination (Match Plumber.R)
    if (!is.na(item_params$discrimination[i]) && item_params$discrimination[i] < 0.1) {
      item_params$discrimination[i] <- 0.1
    }
    
    # Fix extreme difficulty values
    if (!is.na(item_params$difficulty[i]) && item_params$difficulty[i] < -4.0) {
      item_params$difficulty[i] <- -4.0
    }
    
    if (!is.na(item_params$difficulty[i]) && item_params$difficulty[i] > 4.0) {
      item_params$difficulty[i] <- 4.0
    }
    
    # For 3PL models, clean guessing parameters
    if (model_type == "3PL") {
      if (!is.na(item_params$guessing[i]) && item_params$guessing[i] < 0) {
        item_params$guessing[i] <- 0.0
      }
      if (!is.na(item_params$guessing[i]) && item_params$guessing[i] > 0.5) {
        item_params$guessing[i] <- 0.5
      }
    }
  }
  
  return(item_params)
}

# ---------------------------------------------------------
# Main Analysis Function (FIXED: Added IIF and TIF)
# ---------------------------------------------------------

perform_irt_analysis <- function(input_file, output_file) {
  # Make deterministic
  set.seed(12345)

  data <- read.csv(input_file, stringsAsFactors = FALSE)
  responses <- as.matrix(data)
  
  # -------------------------------------------------
  # DATA CLEANING AND VALIDATION (Minimal for standalone)
  # NOTE: Full validation should be done outside this script for robustness
  # -------------------------------------------------
  # Remove all-correct or all-wrong rows (impossible to estimate)
  row_sums <- rowSums(responses, na.rm = TRUE)
  valid_rows <- row_sums > 0 & row_sums < ncol(responses)
  responses_clean <- responses[valid_rows, , drop = FALSE]

  if (nrow(responses_clean) < 10) {
    stop("Not enough valid response patterns after filtering (less than 10).")
  }
  
  # Fit model with 3PL fallback to 2PL
  fit_result <- fit_irt_model_standalone(responses_clean)
  model <- fit_result$model
  model_type <- fit_result$type

  message(paste("Model fitted successfully:", model_type))

  # Extract parameters
  params <- coef(model, simplify = TRUE, D = 1, IRTpars = TRUE)$items
  params_se <- extract_standard_errors(model, model_type = model_type)

  if (is.null(params_se)) {
    message("Warning: Standard errors not available")
    # Create empty SE matrix as fallback
    if (model_type == "3PL") {
      params_se <- matrix(0, nrow = nrow(params), ncol = 4)
      colnames(params_se) <- c("a", "b", "g", "u")
    } else {
      params_se <- matrix(0, nrow = nrow(params), ncol = 3)
      colnames(params_se) <- c("a", "b", "u")
    }
    rownames(params_se) <- rownames(params)
  }

  item_params_df <- extract_item_params(params, params_se, model_type)
  item_params_df <- clean_parameters(item_params_df, model_type)

  # -------------------------------------------------
  # Curve Calculations
  # -------------------------------------------------
  theta_grid <- seq(-4, 4, length.out = 101)
  theta_matrix <- matrix(theta_grid)
  
  # 1. ICC calculation
  icc_list <- list()
  for (i in seq_len(ncol(responses_clean))) {
    probs <- probtrace(extract.item(model, i), theta_matrix)
    correct_col <- ncol(probs)
    icc_list[[paste0("item_", i)]] <- list(
      theta = round(theta_grid, 6),
      p = round(as.numeric(probs[, correct_col]), 8)
    )
  }

  # 2. IIF calculation (FIXED)
  iif_list <- list()
  for (i in seq_len(ncol(responses_clean))) {
    tryCatch({
      item_obj <- extract.item(model, i)
      item_info <- iteminfo(item_obj, Theta = theta_matrix)
      iif_list[[paste0("item_", i)]] <- list(
        theta = round(theta_grid, 6),
        info = round(as.numeric(item_info), 8)
      )
    }, error = function(e) {
      message(paste("Warning: Could not compute IIF for item", i, ":", e$message))
      iif_list[[paste0("item_", i)]] <- list(
        theta = round(theta_grid, 6),
        info = rep(NA, length(theta_grid))
      )
    })
  }

  # 3. TIF calculation
  test_info <- tryCatch(
    as.numeric(testinfo(model, Theta = theta_matrix)),
    error = function(e) {
      message("Warning: Could not compute test information")
      rep(NA, length(theta_grid))
    }
  )
  # -------------------------------------------------
  # Model Fit Statistics
  # -------------------------------------------------
  m2stat <- tryCatch(M2(model), error = function(e) NULL)
  m2_value <- NA_real_; m2_df <- NA_integer_; m2_p <- NA_real_
  tli_val <- NA_real_; rmsea_val <- NA_real_
  
  if (!is.null(m2stat) && is.list(m2stat)) {
    m2_value <- as.numeric(m2stat$M2)
    m2_df <- as.integer(m2stat$df)
    m2_p <- as.numeric(m2stat$p)
    tli_val <- if (!is.null(m2stat$TLI)) as.numeric(m2stat$TLI) else NA_real_
    rmsea_val <- if (!is.null(m2stat$RMSEA)) as.numeric(m2stat$RMSEA) else NA_real_
  }

  reliability_val <- tryCatch(marginal_rxx(model), error = function(e) NA_real_)
  ll_val <- tryCatch(as.numeric(logLik(model)), error = function(e) NA_real_)
  aic_val <- tryCatch(AIC(model), error = function(e) NA_real_)
  bic_val <- tryCatch(BIC(model), error = function(e) NA_real_)

  # -------------------------------------------------
  # Final Results Object
  # -------------------------------------------------
  results <- list(
    model_type = model_type,
    items = ncol(responses_clean),
    respondents = nrow(responses_clean),
    parameters = item_params_df,
    model_fit = list(
      m2 = if (!is.na(m2_value)) round(m2_value, 6) else NA_real_,
      m2_df = if (!is.na(m2_df)) m2_df else NA_integer_,
      m2_p = if (!is.na(m2_p)) round(m2_p, 6) else NA_real_,
      tli = if (!is.na(tli_val)) round(as.numeric(tli_val), 6) else NA_real_,
      rmsea = if (!is.na(rmsea_val)) round(as.numeric(rmsea_val), 6) else NA_real_,
      reliability = if (!is.na(reliability_val)) round(as.numeric(reliability_val), 6) else NA_real_,
      log_likelihood = if (!is.na(ll_val)) round(ll_val, 6) else NA_real_,
      aic = if (!is.na(aic_val)) round(aic_val, 6) else NA_real_,
      bic = if (!is.na(bic_val)) round(bic_val, 6) else NA_real_,
      converged = model@OptimInfo$converged
    ),
    icc = icc_list,
    iif = iif_list, # NEW: Item Information Function data
    test_information = list( # NEW: Test Information Function data
        theta = round(theta_grid, 6),
        information = round(test_info, 8)
    )
  )

  # Write JSON and return
  write_json(results, output_file, pretty = TRUE, auto_unbox = TRUE)
  return(results)
}

# CLI execution
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 2) {
  tryCatch({
    perform_irt_analysis(args[1], args[2])
  }, error = function(e) {
    message(paste("CRITICAL ERROR in IRT Analysis:", e$message))
    quit(status = 1)
  })
}