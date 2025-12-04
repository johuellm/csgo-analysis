#' Analysis script number two for hypothesis testing CS:GO demo replay data.
#' Focus is always the T-side.
#'
#' Notes: 1) tbd.
#'
#' @author Joschka A. Huellmann <j.huellmann@utwente.nl>
#' @date 2025-12-04
#'

library(dplyr)

#### PREPROCESS DATA FRAME ####
df <- read.csv("data/output.csv")
