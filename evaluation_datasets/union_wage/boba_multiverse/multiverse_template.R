#!/usr/bin/env Rscript
# --- (BOBA_CONFIG)
{
  "decisions": [
    {"var": "age", "options": ["+ age", ""]},
    {"var": "hours", "options": ["+ hours", ""]},
    {"var": "grade", "options": ["+ grade", ""]},
    {"var": "collgrad", "options": ["+ collgrad", ""]},
    {"var": "married", "options": ["+ married", ""]},
    {"var": "south", "options": ["+ south", ""]},
    {"var": "smsa", "options": ["+ smsa", ""]},
    {"var": "c_city", "options": ["+ c_city", ""]},
    {"var": "ttl_exp", "options": ["+ ttl_exp", ""]},
    {"var": "tenure", "options": ["+ tenure", ""]}

  ],
  "before_execute": "cp ../../../union_wage.csv ./ && rm -rf results && mkdir results",
  "after_execute": "cd ../.. && sh after_execute.sh",
  "visualizer": "visualizer_config.json"
}
# --- (END)

suppressPackageStartupMessages(library(readr))
suppressPackageStartupMessages(library(tidyverse))
suppressPackageStartupMessages(library(broom.mixed))
source('../../../boba_util.R') #fixme


# a function for post-processing predicted means and standard deviations into expected number of deaths
pred2expectation <- function(mu, sigma) {
    return(exp(mu / 100 + (sigma / 100)^2 / 2))
}

# a custom function for cross validation
cross <- function(df, func, fml, folds = 5) {
    l <- nrow(df) %/% folds
    mse <- 0
    for (i in c(1:folds)) {
        # properly splitting train/test
        i1 <- l * (i - 1) + 1
        i2 <- l * i
        d_test <- df[i1:i2, ]
        if (i1 > 1) {
            if (i2 + 1 < nrow(df)) {
                d_train <- rbind(df[1:(i1 - 1), ], df[(i2 + 1):nrow(df), ])
            } else {
                d_train <- df[1:(i1 - 1), ]
            }
        } else {
            d_train <- df[(i2 + 1):nrow(df), ]
        }

        model <- func(fml, data = d_train)
        mu <- predict(model, d_test, type = "response")
        sigma <- sigma(model)
        expected_outcome <- pred2expectation(mu, sigma)

        mse <- mse + sum((d_test$wage - expected_outcome)^2)
    }

    mse <- sqrt(mse / nrow(df))
    return(mse)
}


# read data
df <- read_csv('../union_wage.csv') %>%
    drop_na()

model <- lm(log(wage)*100 ~ union {{age}} {{hours}} {{grade}} {{collgrad}} {{married}} {{south}}
            {{smsa}} {{c_city}} {{ttl_exp}} {{tenure}}, data = df)


smr <- summary(model)
smr

fit <- cross(df, lm, log(wage)*100 ~ union {{age}} {{hours}} {{grade}} {{collgrad}} {{married}} {{south}}
            {{smsa}} {{c_city}} {{ttl_exp}} {{tenure}}) # cross validation
            
nrmse <- fit / (max(df$wage) - min(df$wage))

result <- tidy(model, conf.int = TRUE) %>%
    filter(term == "unionunion") %>%
    add_column(
        NRMSE = nrmse,
        R2_flipped = 1 - pmax(pmin(smr$adj.r.squared, 1), 0)
    )
pred <- predict(model, se.fit = TRUE, type = "response")
disagg_fit <- df %>%
    mutate(
        fit = pred$fit, # add fitted predictions and standard errors to dataframe
        se.fit = pred$se.fit,
        df = df.residual(model), # get degrees of freedom
        sigma = sigma(model), # get residual standard deviation
        se.residual = sqrt(sum(residuals(model)^2) / df) # get residual standard errors
    )

disagg_fit <- disagg_fit %>%
    mutate(expected = pred2expectation(fit, sigma)) %>%
    dplyr::select(
        observed = wage,
        expected = expected
    )

# get uncertainty in coefficient for unionunion as draws from sampling distribution
uncertainty <- sampling_distribution(model, "unionunion") %>%
    dplyr::select(estimate = coef)

# output
write_csv(result, '../results/estimate_{{_n}}.csv')
write_csv(disagg_fit, '../results/disagg_fit_{{_n}}.csv')
write_csv(uncertainty, '../results/uncertainty_{{_n}}.csv')