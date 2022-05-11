#!/usr/bin/env Rscript
# --- (BOBA_CONFIG)
{
  "decisions": [
    {"var": "dataset_outcome_var", "options": ["TF_count", "all_mig_count"]},
    {
        "var": "dataset_population_vars", 
        "options": ["+ log_ACS_pop_i + log_ACS_pop_j", "+ log_allpop_i + log_allpop_j"]
    },
    {"var": "log_distance", "options": ["+ log_distance_ij", ""]},
    {"var": "contiguous", "options": ["+ contiguous", ""]},
    {"var": "sales_tax", "options": ["+ state_sales_ij", ""]},
    {"var": "property_tax", "options": ["+ prop_tax_ij", ""]},
    {"var": "mean_income", "options": ["+ meaninc_ij", ""]},
    {"var": "winter_temperature", "options": ["+ wint_temp_ij", ""]},
    {"var": "sunshine", "options": ["+ sun_ij", ""]},
    {"var": "humid", "options": ["+ humid_ij", ""]},
    {"var": "temperature", "options": ["+ temp_dif_ij", ""]},
    {"var": "landscape", "options": ["+ topog_ij", ""]},
    {"var": "water", "options": ["+ water_ij", ""]},
    {"var": "unemployment_rate", "options": ["+ unemp_ij", ""]},
    {"var": "back_transform", "options": [
      "exp(mu + sigma^2/2)",
      "mu",
      "mu"
    ]},
    {"var": "df", "options": [
        "pred$df",
        "df.residual(model)",
        "df.residual(model)"
    ]}
  ],
  "constraints":[
      {"link": ["dataset_outcome_var", "dataset_population_vars"]},
      {"link": ["back_transform", "Model", "df"]}
  ],
  "before_execute": "cp ../../tax_induced_migration.csv ./ && rm -rf results && mkdir results",
  "after_execute": "cd .. && sh after_execute.sh",
  "visualizer": "visualizer_config.json"
}
# --- (END)

suppressPackageStartupMessages(library(MASS))
suppressPackageStartupMessages(library(readr))
suppressPackageStartupMessages(library(tidyverse))
suppressPackageStartupMessages(library(broom.mixed))
source("../../boba_util.R")

# a function for post-processing predicted means and standard deviations into expected number of deaths
pred2expectation <- function(mu, sigma) {
    return({{back_transform}})
}


# a custom function for cross validation
cross <- function (df, func, fml, folds = 5) {
  l = nrow(df) %/% folds
  mse = 0
  for (i in c(1:folds)) {
    # properly splitting train/test
    i1 = l*(i-1)+1
    i2 = l*i
    d_test = df[i1:i2, ]
    if (i1 > 1) {
      if (i2+1 < nrow(df)) {
        d_train = rbind(df[1:(i1-1), ], df[(i2+1):nrow(df), ])
      } else {
        d_train = df[1:(i1-1), ]
      }
    } else {
      d_train = df[(i2+1):nrow(df), ]
    }

    model <- func(fml, data = d_train)
    mu <- predict(model, d_test, type = "response")
    sigma <- sigma(model)
    expected_outcome <- pred2expectation(mu, sigma)

    mse = mse + sum((d_test${{dataset_outcome_var}} - expected_outcome)^2)
  }

  mse = sqrt(mse / nrow(df))
  return(mse)
}


df <- read_csv("../tax_induced_migration.csv") %>%
    drop_na()
df <- transform(df,
    TF_count = as.integer(TF_count),
    all_mig_count = as.integer(all_mig_count)
)


# --- (Model) ols_regression
formula <- paste("log({{dataset_outcome_var}})", "~ all_trate100_ij", "{{dataset_population_vars}}",
    "{{log_distance}}", "{{contiguous}}", "{{sales_tax}}", "{{property_tax}}", "{{mean_income}}", "{{winter_temperature}}",
     "{{sunshine}}", "{{humid}}", "{{temperature}}", "{{landscape}}", "{{water}}", "{{unemployment_rate}}"
    )
model <- lm(as.formula(formula), data = df)
fit = cross(df, lm, as.formula(formula)) # cross validation

# --- (Model) poisson_model
formula <- paste("{{dataset_outcome_var}}", "~ all_trate100_ij", "{{dataset_population_vars}}",
    "{{log_distance}}", "{{contiguous}}", "{{sales_tax}}", "{{property_tax}}", "{{mean_income}}", "{{winter_temperature}}",
     "{{sunshine}}", "{{humid}}", "{{temperature}}", "{{landscape}}", "{{water}}", "{{unemployment_rate}}"
    )
model <- glm(as.formula(formula), data = df, family = "poisson")
fit = cross(df, glm, as.formula(formula)) # cross validation

# --- (Model) negative_binomial
formula <- paste("{{dataset_outcome_var}}", "~ all_trate100_ij","{{dataset_population_vars}}",
    "{{log_distance}}", "{{contiguous}}", "{{sales_tax}}", "{{property_tax}}", "{{mean_income}}", "{{winter_temperature}}",
     "{{sunshine}}", "{{humid}}", "{{temperature}}", "{{landscape}}", "{{water}}", "{{unemployment_rate}}"
    )
model <- glm.nb(formula, data = df)
fit <- cross(df, glm.nb, as.formula(formula)) # cross validation

# --- (O)
smr <- summary(model)
smr

nrmse <- fit / (max(df${{dataset_outcome_var}}) - min(df${{dataset_outcome_var}}))

result <- tidy(model, conf.int = TRUE) %>%
    filter(term == "all_trate100_ij") %>%
    add_column(
        NRMSE = nrmse
    )

pred <- predict(model, se.fit = TRUE, type = "response")
disagg_fit <- df  %>%
    mutate(
        fit = pred$fit,                                     # add fitted predictions and standard errors to dataframe
        se.fit = pred$se.fit,
        df = {{df}},                                        # get degrees of freedom
        sigma = sigma(model),                               # get residual standard deviation
        se.residual = sqrt(sum(residuals(model)^2) / df)    # get residual standard errors
    )

disagg_fit <- disagg_fit %>%
    mutate(expected = pred2expectation(fit, sigma)) %>%
    dplyr::select(
        observed = {{dataset_outcome_var}},
        expected = expected
    )


uncertainty <- sampling_distribution(model, "all_trate100_ij") %>%
    dplyr::select(estimate = coef)

# output
write_csv(result, '../results/estimate_{{_n}}.csv')
write_csv(disagg_fit, '../results/disagg_fit_{{_n}}.csv')
write_csv(uncertainty, '../results/uncertainty_{{_n}}.csv')