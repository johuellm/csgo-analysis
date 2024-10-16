#' Analysis script for hypothesis testing CS:GO demo replay data.
#' Focus is always the T-side.
#' 
#' Notes: 1) seconds and clocktime are resetted after bomb plant.
#'        2) tbd.
#' 
#' @author Joschka A. Huellmann <j.huellmann@utwente.nl>
#' @date 2024-10-15
#'

library(dplyr)

setwd("..\\src\\")

#### PREPROCESS DATA FRAME ####
df <- read.csv("testdemo.csv")
df$afterAdverseEvent = df$t_alivePlayers < 5
df$bombPlanted = as.logical(df$bombPlanted)



#### DESCRIPTIVE ANALYSIS ####

# round lengths
barplot(maxRoundLength ~ roundNum, df %>% group_by(roundNum) %>% summarise(maxRoundLength = max(secondsCalculated)) %>% data.frame)

# minimum equipment both teams per round
barplot(minEq ~ roundNum, df %>% group_by(roundNum) %>% summarise(minEq = min(t_teamEqVal, ct_teamEqVal)) %>% data.frame)

# ratio of rounds with bomb planted
df %>% group_by(roundNum) %>% count(bombPlanted)

# plot positions
df.test <- df %>% filter(roundNum == 1)
plot(c(df.test$t1_x,df.test$t2_x,df.test$t3_x,df.test$t4_x,df.test$t5_x), c(df.test$t1_y,df.test$t2_y,df.test$t3_y,df.test$t4_y,df.test$t5_y))

# plot bombdistance, mapcontrol, hp, playeralive, velocityDeviation
df.test <- df %>% filter(roundNum == 3) %>%
	select(velocityDeviation,tHp,ctHp,bombDistance,mapControl,deltaDistance,totalDistance,secondsCalculated,afterAdverseEvent,bombPlanted,bombSeconds)
timeAdverseEvent <- df %>% filter(roundNum == 3, afterAdverseEvent == TRUE) %>% pull(secondsCalculated) %>% first()
par(mfrow=c(2,3))
plot(df.test$secondsCalculated, df.test$tHp, ylim=c(0,500), col = rgb(df.test$afterAdverseEvent,0,df.test$bombPlanted))
abline(v = df.test$bombSeconds, lty="dashed")
abline(v = timeAdverseEvent)
plot(df.test$secondsCalculated, df.test$mapControl, ylim=c(-1,1), col = rgb(df.test$afterAdverseEvent,0,df.test$bombPlanted))
abline(v = df.test$bombSeconds, lty="dashed")
abline(v = timeAdverseEvent)
plot(df.test$secondsCalculated, df.test$bombDistance, col = rgb(df.test$afterAdverseEvent,0,df.test$bombPlanted))
abline(v = df.test$bombSeconds, lty="dashed")
abline(v = timeAdverseEvent)
plot(df.test$secondsCalculated, df.test$deltaDistance, col = rgb(df.test$afterAdverseEvent,0,df.test$bombPlanted))
abline(v = df.test$bombSeconds, lty="dashed")
abline(v = timeAdverseEvent)
plot(df.test$secondsCalculated, df.test$totalDistance, col = rgb(df.test$afterAdverseEvent,0,df.test$bombPlanted))
abline(v = df.test$bombSeconds, lty="dashed")
abline(v = timeAdverseEvent)
plot(df.test$secondsCalculated, df.test$velocityDeviation, col = rgb(df.test$afterAdverseEvent,0,df.test$bombPlanted))
abline(v = df.test$bombSeconds, lty="dashed")
abline(v = timeAdverseEvent)
par(mfrow=c(1,1))



#### TESTING ####

# Test that estimated times are correct
df.test <- df %>% filter(roundNum == 5) %>% mutate(secondsDiff = secondsCalculated - seconds) %>% select(tick, seconds, secondsCalculated, secondsDiff)


