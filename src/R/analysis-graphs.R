#' Analysis script number two for hypothesis testing CS:GO demo replay data.
#' Focus is always the T-side.
#'
#' Notes: 1) tbd.
#'
#' @author Joschka A. Huellmann <j.huellmann@utwente.nl>
#' @date 2025-12-04
#'

library(dplyr)

main <- function() {
  df <- load.data("data/all-frames.csv")
  df <- preprocess.data(df)

  summary(lm(as.numeric(winningSide) ~ tRoundSpendMoney + tFreezeTimeEndEqVal + tactic_used + bombPlanted, df))

}



#### PREPROCESS DATA FRAME ####

load.data <- function(filename) {
  return(read.csv(filename))
}

preprocess.data <- function(df) {
  df$bombPlanted <- as.factor(df$bombPlanted)
  df$isWarmup <- as.factor(df$isWarmup)
  df$winningSide <- as.factor(df$winningSide)
  df$losingTeam <- as.factor(df$losingTeam)
  df$tactic_used <- as.factor(df$tactic_used)
  df$t0_isAlive <- as.factor(df$t0_isAlive)
  df$t0_isDefusing <- as.factor(df$t0_isDefusing)
  df$t0_isPlanting <- as.factor(df$t0_isPlanting)
  df$t0_isReloading <- as.factor(df$t0_isReloading)
  df$t0_isInBombZone <- as.factor(df$t0_isInBombZone)
  df$t0_isInBuyZone <- as.factor(df$t0_isInBuyZone)
  df$t0_hasHelmet <- as.factor(df$t0_hasHelmet)
  df$t0_hasDefuse <- as.factor(df$t0_hasDefuse)
  df$t0_hasBom <- as.factor(df$t0_hasBom)
  df$t1_isAlive <- as.factor(df$t1_isAlive)
  df$t1_isDefusing <- as.factor(df$t1_isDefusing)
  df$t1_isPlanting <- as.factor(df$t1_isPlanting)
  df$t1_isReloading <- as.factor(df$t1_isReloading)
  df$t1_isInBombZone <- as.factor(df$t1_isInBombZone)
  df$t1_isInBuyZone <- as.factor(df$t1_isInBuyZone)
  df$t1_hasHelmet <- as.factor(df$t1_hasHelmet)
  df$t1_hasDefuse <- as.factor(df$t1_hasDefuse)
  df$t1_hasBomb <- as.factor(df$t1_hasBomb)
  df$t2_isAlive <- as.factor(df$t2_isAlive)
  df$t2_isDefusing <- as.factor(df$t2_isDefusing)
  df$t2_isPlanting <- as.factor(df$t2_isPlanting)
  df$t2_isReloading <- as.factor(df$t2_isReloading)
  df$t2_isInBombZone <- as.factor(df$t2_isInBombZone)
  df$t2_isInBuyZone <- as.factor(df$t2_isInBuyZone)
  df$t2_hasHelmet <- as.factor(df$t2_hasHelmet)
  df$t2_hasDefuse <- as.factor(df$t2_hasDefuse)
  df$t2_hasBomb <- as.factor(df$t2_hasBomb)
  df$t3_isAlive <- as.factor(df$t3_isAlive)
  df$t3_isDefusing <- as.factor(df$t3_isDefusing)
  df$t3_isPlanting <- as.factor(df$t3_isPlanting)
  df$t3_isReloading <- as.factor(df$t3_isReloading)
  df$t3_isInBombZone <- as.factor(df$t3_isInBombZone)
  df$t3_isInBuyZone <- as.factor(df$t3_isInBuyZone)
  df$t3_hasHelmet <- as.factor(df$t3_hasHelmet)
  df$t3_hasDefuse <- as.factor(df$t3_hasDefuse)
  df$t3_hasBomb <- as.factor(df$t3_hasBomb)
  df$t4_isAlive <- as.factor(df$t4_isAlive)
  df$t4_isDefusing <- as.factor(df$t4_isDefusing)
  df$t4_isPlanting <- as.factor(df$t4_isPlanting)
  df$t4_isReloading <- as.factor(df$t4_isReloading)
  df$t4_isInBombZone <- as.factor(df$t4_isInBombZone)
  df$t4_isInBuyZone <- as.factor(df$t4_isInBuyZone)
  df$t4_hasHelmet <- as.factor(df$t4_hasHelmet)
  df$t4_hasDefuse <- as.factor(df$t4_hasDefuse)
  df$t4_hasBomb <- as.factor(df$t4_hasBomb)
  return(df)
}
