# ---------------------------------------------------------
# R IRT Analysis Service (Plumber API)
# ---------------------------------------------------------

library(plumber)
library(jsonlite)
library(mirt)
library(dplyr)
library(purrr)
library(tibble)

# ---------------------------------------------------------
# GLOBAL CACHE FOR FITTED MODELS 💾
# ---------------------------------------------------------

# A simple environment to store fitted models: key=data_path, value=fitted_model_list
irt_model_cache <- new.env(parent = emptyenv())

# ---------------------------------------------------------
# Enhanced IRT Model Fitting with 3PL and Fallback
# ---------------------------------------------------------

fit_irt_model <- function(response_matrix) {
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
        set.seed = 12345
      ),
      SE = TRUE,
      verbose = FALSE,
      optimizer = "BFGS"
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
      params_3pl[, "a"] > 10 | params_3pl[, "a"] < 0.01 |   # Extreme discrimination
      params_3pl[, "b"] > 10 | params_3pl[, "b"] < -10 |   # Extreme difficulty
      params_3pl[, "g"] > 0.5 | params_3pl[, "g"] < 0      # Unreasonable guessing
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
# CACHING WRAPPER FUNCTION 📦
# ---------------------------------------------------------

get_or_fit_model <- function(data_path, resp_clean) {
    if (exists(data_path, envir = irt_model_cache)) {
        message(paste("Model found in cache for:", data_path))
        return(get(data_path, envir = irt_model_cache))
    }
    
    message(paste("Model not in cache, fitting now for:", data_path))
    fit_result <- fit_irt_model(resp_clean)
    
    # Store only the necessary info (model object + type)
    assign(data_path, fit_result, envir = irt_model_cache) 
    
    return(fit_result)
}


# ---------------------------------------------------------
# Standard Error Extraction
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
# Enhanced Parameter Extraction for both 2PL and 3PL
# ---------------------------------------------------------

extract_item_params <- function(params_table, params_se_table = NULL, model_type = "3PL") {
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
# Enhanced Parameter Cleaning
# ---------------------------------------------------------

clean_parameters <- function(item_params, model_type = "3PL") {
  for (i in seq_len(nrow(item_params))) {
    # Fix negative discrimination
    if (!is.na(item_params$discrimination[i]) && item_params$discrimination[i] < 0) {
      original_val <- item_params$discrimination[i]
      item_params$discrimination[i] <- abs(original_val)
      message(paste("Fixed negative discrimination for item", i, "from", original_val, "to", abs(original_val)))
    }
    
    # Cap extreme discrimination values
    if (!is.na(item_params$discrimination[i]) && item_params$discrimination[i] > 4.0) {
      original_val <- item_params$discrimination[i]
      item_params$discrimination[i] <- 4.0
      message(paste("Capped discrimination for item", i, "from", original_val, "to 4.0"))
    }
    
    # Ensure minimum discrimination
    if (!is.na(item_params$discrimination[i]) && item_params$discrimination[i] < 0.1) {
      item_params$discrimination[i] <- 0.1
    }
    
    # Cap extreme difficulty values
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
# UTILITY FUNCTION: DATA VALIDATION AND CLEANING 🧹
# ---------------------------------------------------------

validate_and_clean_data <- function(data_path, res) {
    if (is.null(data_path)) {
      res$status <- 400
      stop(list(status = "error", error = "data_path required"))
    }
    
    df <- read.csv(data_path)
    resp <- as.matrix(df)

    # Ensure binary (0/1) response matrix
    unique_vals <- unique(as.vector(resp))
    if (!all(unique_vals %in% c(0, 1, NA))) {
      res$status <- 400
      stop(list(
        status = "error",
        error = sprintf("Responses must be 0/1. Found: %s",
                        paste(sort(unique_vals), collapse = ", "))
      ))
    }

    # Remove all-correct or all-wrong rows (impossible to estimate)
    row_sums <- rowSums(resp, na.rm = TRUE)
    valid_rows <- row_sums > 0 & row_sums < ncol(resp)
    
    if (sum(valid_rows) < 10) {
      res$status <- 400
      stop(list(
        status = "error",
        error = "Not enough valid response patterns after filtering"
      ))
    }
    
    resp_clean <- resp[valid_rows, , drop = FALSE]
    
    return(list(resp_clean = resp_clean, original_resp = resp))
}

# ---------------------------------------------------------
# API Title
# ---------------------------------------------------------

#* @apiTitle IRT Analysis R Service
#* @apiDescription Backend for IRT analysis with ICC and IIF curves, using model caching.

# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

#* @get /health
function() {
  list(status = "healthy", version = "1.2.0")
}

# ---------------------------------------------------------
# MAIN ANALYSIS ENDPOINT - WITH CACHING
# ---------------------------------------------------------

#* @post /analyze
function(req, res) {
  tryCatch({
    # Extract data_path and clean data
    data_path <- req$body$data_path
    data_list <- validate_and_clean_data(data_path, res)
    resp_clean <- data_list$resp_clean
    resp <- data_list$original_resp
    
    message(paste("After filtering:", nrow(resp_clean), "valid rows"))

    # Fit model with 3PL fallback to 2PL (uses cache if available)
    fit_result <- get_or_fit_model(data_path, resp_clean)
    model <- fit_result$model
    model_type <- fit_result$type

    # Check model convergence
    if (!model@OptimInfo$converged) {
      message("WARNING: Model did not converge properly")
    }

    message(paste("Model successfully retrieved/fitted:", model_type))

    # Extract item parameters and SEs
    params <- coef(model, simplify = TRUE, D = 1, IRTpars = TRUE)$items
    params_se <- extract_standard_errors(model, model_type = model_type)

    if (is.null(params_se)) {
      message("Warning: Standard errors not available")
      # Create empty SE matrix as fallback (same logic as before)
      if (model_type == "3PL") {
        params_se <- matrix(0, nrow = nrow(params), ncol = 4)
        colnames(params_se) <- c("a", "b", "g", "u")
      } else {
        params_se <- matrix(0, nrow = nrow(params), ncol = 3)
        colnames(params_se) <- c("a", "b", "u")
      }
      rownames(params_se) <- rownames(params)
    }

    # Extract and clean parameters with model type
    item_params <- extract_item_params(params, params_se, model_type = model_type)
    item_params <- clean_parameters(item_params, model_type = model_type)

    # Fit statistics
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

    # Additional fit stats
    reliability_val <- tryCatch(marginal_rxx(model), error = function(e) NA_real_)
    ll_val <- tryCatch(as.numeric(logLik(model)), error = function(e) NA_real_)
    aic_val <- tryCatch(AIC(model), error = function(e) NA_real_)
    bic_val <- tryCatch(BIC(model), error = function(e) NA_real_)

    # Test information (replicated from previous logic)
    theta <- seq(-4, 4, length.out = 101)
    test_info <- tryCatch(
      as.numeric(testinfo(model, Theta = matrix(theta))),
      error = function(e) rep(NA, length(theta))
    )
    test_info <- round(test_info, 8)

    # Return results
    return(list(
      status = "success",
      analysis_type = fit_result$type,
      model_info = list(
        type = fit_result$type,
        converged = model@OptimInfo$converged,
        iterations = model@OptimInfo$iter,
        log_likelihood = as.numeric(logLik(model))
      ),
      data_summary = list(
        n_students = nrow(resp_clean), 
        n_items = ncol(resp_clean),
        original_students = nrow(resp),
        response_rate = mean(resp_clean, na.rm = TRUE)
      ),
      item_parameters = item_params,
      model_fit = list(
        m2 = ifelse(!is.na(m2_value), round(m2_value, 6), NA_real_),
        m2_df = ifelse(!is.na(m2_df), m2_df, NA_integer_),
        m2_p = ifelse(!is.na(m2_p), round(m2_p, 6), NA_real_),
        tli = ifelse(!is.na(tli_val), round(as.numeric(tli_val), 6), NA_real_),
        rmsea = ifelse(!is.na(rmsea_val), round(as.numeric(rmsea_val), 6), NA_real_),
        reliability = ifelse(!is.na(reliability_val), round(as.numeric(reliability_val), 6), NA_real_),
        log_likelihood = ifelse(!is.na(ll_val), round(ll_val, 6), NA_real_),
        aic = ifelse(!is.na(aic_val), round(aic_val, 6), NA_real_),
        bic = ifelse(!is.na(bic_val), round(bic_val, 6), NA_real_),
        converged = model@OptimInfo$converged
      ),
      test_information = list(
        theta = round(theta, 6),
        information = test_info
      )
    ))

  }, error = function(e) {
    error_msg <- paste("R ANALYSIS ERROR:", e$message)
    message(error_msg)
    
    res$status <- 500
    return(list(status = "error", error = e$message$error)) # Pass the extracted error
  })
}

# ---------------------------------------------------------
# ICC ENDPOINT (GLOBAL OR SINGLE ITEM) - WITH CACHING
# ---------------------------------------------------------

#* @post /icc
function(req, res) {
  tryCatch({
    data_path <- req$body$data_path
    item_id <- req$body$item_id

    # Read data and get model (uses cache)
    data_list <- validate_and_clean_data(data_path, res)
    resp_clean <- data_list$resp_clean
    fit_result <- get_or_fit_model(data_path, resp_clean)
    model <- fit_result$model

    theta <- seq(-4, 4, length.out = 101)

    # SINGLE ITEM (Optimized)
    if (!is.null(item_id)) {
      idx <- as.numeric(gsub("item_", "", item_id))
      probs <- probtrace(extract.item(model, idx), matrix(theta))
      correct_col <- ncol(probs)
      return(list(
        status = "success",
        theta = round(theta, 6),
        probability = round(as.numeric(probs[, correct_col]), 8),
        item_id = item_id
      ))
    }

    # ALL ITEMS - return long format (theta, probability, item_id)
    full <- bind_rows(lapply(1:ncol(resp_clean), function(i) { # Use resp_clean for n items
      probs <- probtrace(extract.item(model, i), matrix(theta))
      correct_col <- ncol(probs)
      data.frame(
        theta = round(theta, 6),
        probability = round(as.numeric(probs[, correct_col]), 8),
        item_id = paste0("item_", i),
        stringsAsFactors = FALSE
      )
    }))

    list(status = "success", icc_data = full)

  }, error = function(e) {
    res$status <- 500
    list(status = "error", error = e$message)
  })
}

# ---------------------------------------------------------
# ITEM INFORMATION ENDPOINT (IIF) - NEW & CACHED 📈
# ---------------------------------------------------------

#* @post /iif
function(req, res) {
  tryCatch({
    data_path <- req$body$data_path
    
    # Enhanced debugging
    message("=== IIF ENDPOINT STARTED ===")
    message(paste("Data path:", data_path))
    
    # Read data and get model (uses cache)
    data_list <- validate_and_clean_data(data_path, res)
    resp_clean <- data_list$resp_clean
    message(paste("Data cleaned:", nrow(resp_clean), "rows,", ncol(resp_clean), "items"))
    
    fit_result <- get_or_fit_model(data_path, resp_clean)
    model <- fit_result$model
    message(paste("Model retrieved:", fit_result$type))
    
    theta <- seq(-4, 4, length.out = 101)
    message(paste("Theta grid created:", length(theta), "points"))
    
    # Enhanced IIF calculation with detailed error handling
    message("Starting IIF calculation for each item...")
    
    full_iif <- bind_rows(lapply(1:ncol(resp_clean), function(i) {
      tryCatch({
        message(paste("  Processing item", i))
        
        # Step 1: Extract item
        item_obj <- tryCatch({
          extracted <- extract.item(model, i)
          message(paste("    ✓ extract.item successful for item", i))
          extracted
        }, error = function(e) {
          message(paste("    ✗ extract.item FAILED for item", i, ":", e$message))
          stop(e) # Re-throw to outer catch
        })
        
        # Step 2: Calculate IIF
        item_info <- tryCatch({
          info <- iteminfo(item_obj, Theta = matrix(theta))
          message(paste("    ✓ iteminfo successful for item", i))
          info
        }, error = function(e) {
          message(paste("    ✗ iteminfo FAILED for item", i, ":", e$message))
          stop(e) # Re-throw to outer catch
        })
        
        # Step 3: Create data frame
        result_df <- data.frame(
          theta = round(theta, 6),
          iif = round(as.numeric(item_info), 8),
          item_id = paste0("item_", i),
          stringsAsFactors = FALSE
        )
        
        message(paste("    ✓ Data frame created for item", i, "dimensions:", nrow(result_df), "x", ncol(result_df)))
        
        result_df
        
      }, error = function(e) {
        message(paste("  ✗ COMPLETE FAILURE for item", i, ":", e$message))
        # Return NA values for this item
        data.frame(
          theta = round(theta, 6),
          iif = rep(NA, length(theta)),
          item_id = paste0("item_", i),
          stringsAsFactors = FALSE
        )
      })
    }))

    message("=== IIF CALCULATION COMPLETED ===")
    message(paste("Final result dimensions:", nrow(full_iif), "rows"))
    
    # Check for any failures
    na_count <- sum(is.na(full_iif$iif))
    if (na_count > 0) {
      message(paste("WARNING:", na_count, "NA values in IIF results"))
    }
    
    list(status = "success", iif_data = full_iif)

  }, error = function(e) {
    message(paste("=== FATAL ERROR IN IIF ENDPOINT:", e$message, "==="))
    res$status <- 500
    return(list(status = "error", error = paste("IIF calculation failed:", e$message)))
  })
}

# ---------------------------------------------------------
# TEST INFORMATION ENDPOINT - WITH CACHING
# ---------------------------------------------------------

#* @post /testinfo
function(req, res) {
  tryCatch({
    data_path <- req$body$data_path
    
    # Read data and get model (uses cache)
    data_list <- validate_and_clean_data(data_path, res)
    resp_clean <- data_list$resp_clean
    fit_result <- get_or_fit_model(data_path, resp_clean)
    model <- fit_result$model

    theta <- seq(-4, 4, length.out = 101)
    info <- tryCatch(
      testinfo(model, Theta = matrix(theta)), 
      error = function(e) rep(NA, length(theta))
    )
    
    list(
      status = "success",
      theta = round(theta, 6),
      information = round(as.numeric(info), 8)
    )

  }, error = function(e) {
    res$status <- 500
    list(status = "error", error = e$message)
  })
}
