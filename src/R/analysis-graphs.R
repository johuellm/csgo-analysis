#' Analysis script number two for hypothesis testing CS:GO demo replay data.
#' Focus is always the T-side.
#'
#' Notes: 1) tbd.
#'
#' @author Joschka A. Huellmann <j.huellmann@utwente.nl>
#' @date 2025-12-09
#'

library(dplyr)
library(ggplot2)

main <- function() {


  # TODO:
  # dependent variables:
  #  - distance bomb to bombspot (done)
  #  - roundWin (done)
  #  - DamageTaken (done)
  #  - matchWin
  #  - DamageInflicted
  #  - areaControl
  # nice timeseries visuals


  setwd("M:\\dev\\csgo-analysis")
  source("src\\R\\analysis-graphs.R")

  df <- load.data("data/all-frames.csv")
  df <- preprocess.data(df)

  describe.data(df)

  analyse.tick.level(df)
  analyse.round.level(df)
  analyse.sequence.level(df)

  df.merged <- preprocess.merge.tactics(df)
  analyse.sequence.level(df)
}







describe.data(df) <- function(df) {

  nrow(df)
  length(unique(df$demoName))
  df %>% group_by(demoName) %>% summarize(n=n_distinct(roundIdx),n()) %>% rename("Rounds" = n, "Observations" = `n()`)
  unique(df$losingTeam)
  plot(df$tactic_used)
}




#### SEQUENCE-LEVEL ANALYSIS ####

analyse.sequence.level <- function(df) {
  # Define the slice size
  # 2 ticks are 1 second, so a slice of 10 rows is 5 seconds
  slice_size <- 10

  # First: slice each demo and game round, creating sequences
  df.sliced <- df %>%
    group_by(demoName, roundIdx) %>%
    mutate(slice = (row_number() - 1) %/% slice_size + 1) %>%
    as.data.frame()

  # Second: rowwise aggregations
  df.sliced <- df.sliced %>%
    rowwise() %>%
    mutate(
      hpTotal = sum(t0_hp,t1_hp,t2_hp,t3_hp,t4_hp),
      distBombplace = min(dist67,dist68)
    ) %>%
    as.data.frame()

  # Third: columnwise aggregations
  df.sliced <- df.sliced %>%
    group_by(demoName, roundIdx, slice) %>%
    summarize(
      tickLast = last(tick),
      hpDiff = last(hpTotal) - first(hpTotal),
      hpFirst = first(hpTotal),
      hpLast = last(hpTotal),
      distBombplaceDiff = last(distBombplace) - first(distBombplace),
      distBombplaceFirst = first(distBombplace),
      distBombplaceLast = last(distBombplace),
      tRoundSpendMoney = first(tRoundSpendMoney),
      tFreezeTimeEndEqVal = first(tFreezeTimeEndEqVal),
      tacticFirst = first(tactic_used),
      tacticLast = first(tactic_used),
      tacticCount = n_distinct(tactic_used),
      winningSide = first(winningSide)
    ) %>%
    as.data.frame()


  # Run regressions
  ## (a) HP DIFFERENCE
  fit <- lm(hpDiff ~ demoName + roundIdx + slice + distBombplaceDiff + tRoundSpendMoney + tFreezeTimeEndEqVal + tacticLast, data=df.sliced)
  summary(fit)
  
  par(mar = c(10, 4.1, 4.1, 2.1) + 0.1)
  plot(df.sliced$tacticLast, df.sliced$hpDiff, las = 2)
  lines(predict(fit,
        newdata = data.frame(
            tacticLast = factor(levels(df.sliced$tacticLast), levels = levels(df.sliced$tacticLast)),
            demoName = df.sliced$demoName[1],
            roundIdx = mean(df.sliced$roundIdx),
            slice = mean(df.sliced$slice),
            distBombplaceDiff = mean(df.sliced$distBombplaceDiff),
            tRoundSpendMoney = mean(df.sliced$tRoundSpendMoney),
            tFreezeTimeEndEqVal = mean(df.sliced$tFreezeTimeEndEqVal)
        )), col = "red", lwd = 2, add = TRUE)
  par(mar = c(5.1, 4.1, 4.1, 2.1))


  ## (b) BOMB DISTANCE DIFFERENCE
  fit <- lm(distBombplaceDiff ~ demoName + roundIdx + slice + hpDiff + tRoundSpendMoney + tFreezeTimeEndEqVal + tacticLast, data=df.sliced)
  summary(fit)

  par(mar = c(10, 4.1, 4.1, 2.1) + 0.1)
  plot(df.sliced$tacticLast, df.sliced$distBombplaceDiff, las = 2)
  lines(predict(fit,
        newdata = data.frame(
            tacticLast = factor(levels(df.sliced$tacticLast), levels = levels(df.sliced$tacticLast)),
            demoName = df.sliced$demoName[1],
            roundIdx = mean(df.sliced$roundIdx),
            slice = mean(df.sliced$slice),
            hpDiff = mean(df.sliced$hpDiff),
            tRoundSpendMoney = mean(df.sliced$tRoundSpendMoney),
            tFreezeTimeEndEqVal = mean(df.sliced$tFreezeTimeEndEqVal)
        )), col = "red", lwd = 2, add = TRUE)
  par(mar = c(5.1, 4.1, 4.1, 2.1))


  ## (c) WINNING ROUND
  fit <- lm(as.numeric(winningSide) ~ demoName + roundIdx + slice + hpDiff + distBombplaceDiff + tRoundSpendMoney + tFreezeTimeEndEqVal + tacticLast, data=df.sliced, family=binomial)
  summary(fit)
  

  # with glm and plotting winning Side
  fit <- glm(winningSide ~ demoName + roundIdx + slice + hpDiff + distBombplaceDiff + tRoundSpendMoney + tFreezeTimeEndEqVal + tacticLast, data=df.sliced, family=binomial)
  summary(fit)
  ggplot(df.sliced, aes(x = tacticLast, y = 1, fill=winningSide)) + 
    geom_col(position="fill", stat="identity") + 
    scale_y_continuous(labels = scales::percent) +        # Format y-axis as percentages
    labs(
      title = "Factor Level Shares", 
      x = "", 
      y = "Proportion (%)"
    ) +
    theme_minimal() +
    theme(
      legend.position = "none",
      axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1)
    )


  # with lags
  fit <- lm(hpDiff ~ lag(hpDiff, 1) + demoName + roundIdx + slice + distBombplaceDiff + tRoundSpendMoney + tFreezeTimeEndEqVal + tacticLast, data=df.sliced)
  summary(fit)
  fit <- lm(distBombplaceDiff ~ lag(distBombplaceDiff, 1) + demoName + roundIdx + slice + hpDiff + tRoundSpendMoney + tFreezeTimeEndEqVal + tacticLast, data=df.sliced)
  summary(fit)


  # Plot different demos
  ## (a) Plot demos with different intercepts
  fit <- lm(distBombplaceDiff ~ demoName + roundIdx + slice + hpDiff + tRoundSpendMoney + tFreezeTimeEndEqVal + tacticLast, data=df.sliced)
  summary(fit)
  par(mar = c(10, 4.1, 4.1, 2.1) + 0.1)
  plot(df.sliced$tacticLast, df.sliced$hpDiff, las = 2)
  for (demo in unique(df.sliced$demoName)[1:8]) {
    lines(predict(fit,
          newdata = data.frame(
              tacticLast = factor(levels(df.sliced$tacticLast), levels = levels(df.sliced$tacticLast)),
              demoName = demo,
              roundIdx = mean(df.sliced$roundIdx),
              slice = mean(df.sliced$slice),
              hpDiff = mean(df.sliced$hpDiff),
              tRoundSpendMoney = mean(df.sliced$tRoundSpendMoney),
              tFreezeTimeEndEqVal = mean(df.sliced$tFreezeTimeEndEqVal)
          )), col = rainbow(4), lwd = 2)
  }
  par(mar = c(5.1, 4.1, 4.1, 2.1))


  ## (b) Plot demos with different fits
  par(mfrow=c(2,4))
  for (demo in unique(df.sliced$demoName)[1:8]) {
    df.sliced.filtered <- df.sliced %>% filter(demoName == demo)
    df.sliced.filtered$tacticLast <- droplevels(df.sliced.filtered$tacticLast) # lm drops levels, so we need to do it before, otherwise predict fails
    fit <- lm(distBombplaceDiff ~ roundIdx + slice + hpDiff + tRoundSpendMoney + tFreezeTimeEndEqVal + tacticLast, data=df.sliced.filtered)
    plot(df.sliced.filtered$tacticLast, df.sliced.filtered$hpDiff, las = 2)
    lines(predict(fit,
      newdata = data.frame(
          tacticLast = factor(levels(df.sliced.filtered$tacticLast), levels = levels(df.sliced.filtered$tacticLast)),
          roundIdx = mean(df.sliced.filtered$roundIdx),
          slice = mean(df.sliced.filtered$slice),
          hpDiff = mean(df.sliced.filtered$hpDiff),
          tRoundSpendMoney = mean(df.sliced.filtered$tRoundSpendMoney),
          tFreezeTimeEndEqVal = mean(df.sliced.filtered$tFreezeTimeEndEqVal)
      )), col = "red", lwd = 2)
  }
  par(mfrow=c(1,1))


  ## (c) overlay lines of different fits
  par(mar = c(10, 4.1, 4.1, 2.1) + 0.1)
  plot(df.sliced.filtered$tacticLast, df.sliced.filtered$hpDiff,
    las = 2,
    ylim=c(0, -500))
  colors = rainbow(8)
  demos = unique(df.sliced$demoName)[1:8]
  for (i in 1:8) {
    demo = demos[i]
    df.sliced.filtered <- df.sliced %>% filter(demoName == demo)
    df.sliced.filtered$tacticLast <- droplevels(df.sliced.filtered$tacticLast) # lm drops levels, so we need to do it before, otherwise predict fails
    fit <- lm(distBombplaceDiff ~ roundIdx + slice + hpDiff + tRoundSpendMoney + tFreezeTimeEndEqVal + tacticLast, data=df.sliced.filtered)
    lines(predict(fit,
      newdata = data.frame(
          tacticLast = factor(levels(df.sliced.filtered$tacticLast), levels = levels(df.sliced.filtered$tacticLast)),
          roundIdx = mean(df.sliced.filtered$roundIdx),
          slice = mean(df.sliced.filtered$slice),
          hpDiff = mean(df.sliced.filtered$hpDiff),
          tRoundSpendMoney = mean(df.sliced.filtered$tRoundSpendMoney),
          tFreezeTimeEndEqVal = mean(df.sliced.filtered$tFreezeTimeEndEqVal)
      )), col = colors[i], lwd = 2)
  }
  par(mar = c(5.1, 4.1, 4.1, 2.1))

}





#### TICK-LEVEL ANALYSIS ####

analyse.tick.level <- function(df) {
  # most simple regressions
  summary(glm(winningSide ~ tactic_used, data=df, family=binomial))
  summary(glm(winningSide ~ tRoundSpendMoney + tFreezeTimeEndEqVal + tactic_used, data=df, family=binomial))
  df.grouped <- df %>%
    rowwise() %>%
    mutate(totalHp = sum(t0_hp,t1_hp,t2_hp,t3_hp,t4_hp), distBombplace = min(dist67,dist68)) %>%
    as.data.frame()
  summary(glm(winningSide ~ tRoundSpendMoney + tFreezeTimeEndEqVal + tactic_used + totalHp + distBombplace, data=df.grouped, family=binomial))
  summary(glm(winningSide ~ demoName + roundIdx + tRoundSpendMoney + tFreezeTimeEndEqVal + tactic_used + totalHp + distBombplace, data=df.grouped, family=binomial))
}





#### ROUND-LEVEL ANALYSIS ####

analyse.round.level <- function(df) {
  df.grouped <- df %>% group_by(demoName, roundIdx) %>%
    summarise(
      tactics = n_distinct(tactic_used),
      winningSide = last(winningSide) == "T",
      totalHp = sum(last(t0_hp),last(t1_hp),last(t2_hp),last(t3_hp),last(t4_hp)),
      distBombplace = min(last(dist67),last(dist68)),
      equipmentVal = first(tFreezeTimeEndEqVal)
    )

  df.grouped <- as.data.frame(df.grouped)

  # Everything matters, except number of tactics for roundwin
  fit <- glm(as.numeric(winningSide) ~ tactics + totalHp + distBombplace + equipmentVal, data=df.grouped, family=binomial)
  summary(fit)
  fit <- glm(as.numeric(winningSide) ~ tactics + I(tactics^2) + totalHp + distBombplace + equipmentVal, data=df.grouped, family=binomial)
  summary(fit)
  fit <- glm(as.numeric(winningSide) ~ tactics + I(1/tactics) + totalHp + distBombplace + equipmentVal, data=df.grouped, family=binomial)
  summary(fit)

  # Explanation can be seen visually:
  data_counted <- df.grouped %>% group_by(winningSide, tactics) %>% summarize(count = n()) %>% ungroup()

  # Scatterplot with size based on count
  ggplot(data_counted, aes(x = tactics, y = winningSide, size = count)) +
    geom_point(alpha = 0.7) +  # Transparency for better visualization
    scale_size_continuous(range = c(2, 10)) +  # Scale the point sizes
    scale_x_continuous(breaks = 1:7) +
    labs(size = "Count", title = "Scatterplot with Point Sizes Based on Count") +
    theme_minimal()


  # Relationships between number of tactics and (a) distance to bombplace, (b) totalHp
  # (a) For distance: negative coefficients are better!
  fit <- lm(distBombplace ~ tactics, data=df.grouped)
  summary(fit)
  fit <- lm(distBombplace ~ tactics + I(tactics^2), data=df.grouped)
  summary(fit)
  fit <- lm(distBombplace ~ tactics + I(tactics^2) + totalHp + equipmentVal, data=df.grouped)
  summary(fit)
  plot(df.grouped$tactics, df.grouped$distBombplace)
  curve(predict(fit,
    newdata = data.frame(tactics = x, totalHp = mean(df.grouped$totalHp), equipmentVal = mean(df.grouped$equipmentVal))),
    col = "red", lwd = 2, add = TRUE)

  # (b) TotalHp
  fit <- lm(totalHp ~ tactics, data=df.grouped)
  summary(fit)
  fit <- lm(totalHp ~ tactics + I(tactics^2), data=df.grouped)
  summary(fit)
  fit <- lm(totalHp ~ tactics + I(tactics^2) + distBombplace + equipmentVal, data=df.grouped)
  summary(fit)
  plot(df.grouped$tactics, df.grouped$totalHp)
  curve(predict(fit,
    newdata = data.frame(tactics = x, distBombplace = mean(df.grouped$distBombplace), equipmentVal = mean(df.grouped$equipmentVal))),
    col = "red", lwd = 2, add = TRUE)







  ## only firstTactic and roundWin
  df.grouped <- df %>% group_by(demoName, roundIdx) %>%
    summarise(
      tactic = first(tactic_used),
      winningSide = last(winningSide) == "T",
      equipmentVal = first(tFreezeTimeEndEqVal)
    ) %>% as.data.frame()
  
  summary(lm(as.numeric(winningSide) ~ tactic + equipmentVal + demoName + roundIdx, data = df.grouped))


  ## only lastTactic and roundWin
  df.grouped <- df %>% group_by(demoName, roundIdx) %>%
    summarise(
      tactic = last(tactic_used),
      winningSide = last(winningSide) == "T",
      equipmentVal = first(tFreezeTimeEndEqVal)
    ) %>% as.data.frame()
  
  summary(lm(as.numeric(winningSide) ~ tactic + equipmentVal + demoName + roundIdx, data = df.grouped))
}



#### PREPROCESS DATA FRAME ####

load.data <- function(filename) {
  return(read.csv(filename))
}

preprocess.data <- function(df) {
  df$demoName <- as.factor(df$demoName)
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

preprocess.merge.tactics <- function(df)  {
  df <- df %>% mutate(
    tactic_used = case_when(
      tactic_used == "t_setup_a" ~ 'control',
      tactic_used == "t_setup_b" ~ 'control',
      tactic_used == "t_execute_b" ~ 'aggressive',
      tactic_used == "t_execute_a_long" ~ 'aggressive',
      tactic_used == "t_execute_a_short" ~ 'aggressive',
      tactic_used == "t_execute_mid_to_b" ~ 'aggressive',
      tactic_used == "t_control_b_lower_tunnels" ~ 'control',
      tactic_used == "t_control_a_long" ~ 'control',
      tactic_used == "t_control_mid" ~ 'control',
      tactic_used == "t_rush_b" ~ 'rush',
      tactic_used == "t_rush_a_short" ~ 'rush',
      tactic_used == "t_rush_a_long" ~ 'rush',
      tactic_used == "t_rush_mid_to_b" ~ 'rush',
      tactic_used == "t_fake_a" ~ 'other',
      tactic_used == "t_fake_b" ~ 'other',
      tactic_used == "unknown" ~ 'other'
      #.default = NA
    )
  )

  # put other first, for dummy regression load it into intercept
  df$tactic_used <- factor(df$tactic_used, levels = c('other', 'control', 'aggressive', 'rush'))
  return(df)
}