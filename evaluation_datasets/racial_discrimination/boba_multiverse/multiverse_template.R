#!/usr/bin/env Rscript
# --- (BOBA_CONFIG)
{
  "decisions": [

    {
        "var": "quality", 
        "options": ["h", 
                    "sumq_med",
                    "qall_med",
                    "qallxb_med",
                    "qblack_med",
                    "qblackxb_med",
                    "qwhite_med",
                    "qwhitexb_med",
                    "sumq", 
                    "qall",
                    "qallxb", 
                    "qblack",
                    "qblackxb",
                    "qwhite",
                    "qwhitexb"
                    ]
    },

    { "var": "subsample", "options": ["", "female == 1", "female == 0"]}
  ],
  "before_execute": "cp ../../processed_racial_discrimination.csv ./ && rm -rf results && mkdir results",
  "after_execute": "cd .. && sh after_execute.sh",
  "visualizer": "visualizer_config.json"
}
# --- (END)
suppressPackageStartupMessages(library(readr))
suppressPackageStartupMessages(library(tidyverse))
suppressPackageStartupMessages(library(broom.mixed))
library(miceadds)
library(margins)


formula <- paste("call",  " ~ ", "{{quality}}:black + black + {{quality}}")
formula2 <- as.formula(paste(" ~ ", "{{quality}}:black + black + {{quality}}"))

df <- read_csv("../processed_racial_discrimination.csv")
df <- df %>% filter({{subsample}}) 



# --- (Model) regression
model <- lm.cluster(formula, data=df, cluster ="adid")
m1 <- summary(margins::margins(model$lm_res, data=df))
m2 <- summary(margins::margins(model$lm_res, data = df, 
              at = list(black = unique(df$black))))
m <- model.matrix(formula2, data = df)[,]
predictions <- coef(model) %*% t(m)
predictions <- drop(predictions)

# --- (Model) probit
model <- glm.cluster(formula, family = binomial(link = "probit"), 
    data = df, cluster = "adid")
m1 <- summary(margins::margins(model$glm_res, data = df))
m2 <- summary(margins::margins(model$glm_res, data = df, 
              at = list(black = unique(df$black))))
m <- model.matrix(formula2, data = df)[,]
predictions <- coef(model) %*% t(m)
predictions <- drop(plogis(predictions))

# --- (Output_Model)
smr <- summary(model)
pinter <- smr[4, 4]
eblack <- m1$AME[1]
pblack <- m1$p[1]
qual_black <- m2$AME[4]
qual_white <- m2$AME[3]
einter <- qual_black - qual_white

# --- (Adjust_Effect_Size_Model) median_split @if quality.index >= 9
model <- lm({{quality}} ~ {{quality}}_med, data=df)
qual_dx <- summary(model)$coefficients[2, 1]
einter <- qual_dx * einter

# --- (Adjust_Effect_Size_Model) none @if quality.index < 9

# --- (O)
df <- df %>% add_column(pred = predictions)
rho <- cor(df$call, df$pred)

result <- data.frame (rho = rho,
                      eblack = eblack,
                      pblack = pblack,
                      einter = einter,
                      pinter = pinter
                      )

write_csv(result, '../results/estimate_{{_n}}.csv')
