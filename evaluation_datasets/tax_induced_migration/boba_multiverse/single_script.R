#!/usr/bin/env Rscript

library(MASS)
suppressPackageStartupMessages(library(readr))
suppressPackageStartupMessages(library(tidyverse))
suppressPackageStartupMessages(library(broom.mixed))
source("./boba_util.R")

df <- read_csv("../tax_induced_migration.csv") %>%
    drop_na()
df <- transform(df,
    TF_count = as.integer(TF_count),
    all_mig_count = as.integer(all_mig_count)
)

model <- lm(log(TF_count) ~ all_trate100_ij +
    log_ACS_pop_i + log_ACS_pop_j, data = df)

model <- glm(TF_count ~ all_trate100_ij +
    log_ACS_pop_i + log_ACS_pop_j, data = df, family = "poisson")

model <- glm.nb(TF_count ~ all_trate100_ij +
    log_ACS_pop_i + log_ACS_pop_j, data = df)

smr <- summary(model)
smr

fit <- cross_validation(df, model, "TF_count")
nrmse <- fit / (max(df$TF_count) - min(df$TF_count))

result <- tidy(model, conf.int = TRUE) %>%
    filter(term == "all_trate100_ij") %>%
    add_column(
        NRMSE = nrmse
    )
# get predictions
disagg_fit <- pointwise_predict(model, df) %>%
    dplyr::select(
        observed = TF_count,
        expected = fit
    )

# get uncertainty in coefficient for female as draws from sampling distribution
uncertainty <- sampling_distribution(model, "all_trate100_ij") %>%
    dplyr::select(estimate = coef)