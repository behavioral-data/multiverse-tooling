#!/usr/bin/env Rscript
suppressPackageStartupMessages(library(readr))
suppressPackageStartupMessages(library(tidyverse))
suppressPackageStartupMessages(library(broom.mixed))
library(miceadds)
library("margins")

# source("./boba_util.R")

df <- read_csv("/projects/bdata/kenqgu/Research/MultiverseProject/multiverse_tooling/data/racial_discrimination/processed_racial_discrimination.csv")

model_sumqdx <- lm(sumq ~ sumq_med, data = df)

sumq_dx <- summary(model_sumqdx)$coefficients[2, 1]

model1 <- lm(call ~ sumq:black + black + sumq, data = df)

model <- glm.cluster(call ~ sumq:black + black + sumq,
    family = binomial(link = "probit"),
    data = df, cluster="adid"
)

m <- model.matrix(~ ~ sumq:black + black + sumq, data = df)[,]
p2 <- coef(model) %*% t(m)
p2 <- drop(plogis(p2))

smr <- summary(model)
pinter <- smr$coefficients[4, 4]

m1 <- summary(margins::margins(model))
eblack <- m1$AME[1]
pblack <- m1$p[1]
m2 <- summary(margins::margins(model, at = list(black = unique(df$black))))
qual_black <- m1$AME[4]
qual_white <- m2$AME[3]
einter <- qual_black - qual_white
einter <- sumq_dx * einter

predictions <- predict(model, df)
df <- df %>% add_column(pred = predictions)
))

rho_female <- cor(df_female$call, df_female$pred)
rho_male <- cor(df_male$call, df_male$pred)
