#' Analysis script for hypothesis testing CS:GO demo replay data.
#' 
#' Notes: 1) seconds and clocktime are resetted after bomb plant.
#'        2) tbd.
#' 
#' @author Joschka A. Huellmann <j.huellmann@utwente.nl>
#' @date 2024-10-15
#'

library(dplyr)

setwd("..\\src")
df <- read.csv("testdemo3.csv")

# preprocess dataframe
df$side = factor(df$side)
df$afterAdverseEvent = df$alivePlayers < 5

# round lengths
barplot(max ~ roundNum, df %>% group_by(roundNum) %>% summarise(max = max(seconds)) %>% data.frame)
# minimum equipment both teams per round
barplot(max ~ roundNum, df %>% group_by(roundNum) %>% summarise(max = min(teamEqVal)) %>% data.frame)
# ratio of rounds with bomb planted
sum(is.na(df$bombPlantTick)) / nrow(df)

# plot positions
test <- df %>% filter(side == "T", roundNum == 3)
plot(test$x, test$y, col=as.factor(test$name))


# plot bombdistance, mapcontrol, hp, playeralive



df.test <- df %>% filter(roundNum == 3) %>% group_by(tick) %>% summarise(
	ctHP = sum(hp[side=="T"]),
	tHP = sum(hp[side=="CT"]),
	bombDistance = min(bombDistance),
	mapControl = min(mapControl),
	deltaDistance = min(deltaDistance),
	totalDistance = min(totalDistance),
	velocitySync = sd(abs(velocityX)+abs(velocityY)),
	seconds = min(seconds))
par(mfrow=c(2,3))
plot(df.test$seconds, df.test$ctHP, ylim=c(0,500))
plot(df.test$seconds, df.test$tHP, ylim=c(0,500))
plot(df.test$seconds, df.test$mapControl, ylim=c(-1,1))
plot(df.test$seconds, df.test$bombDistance)
plot(df.test$seconds, df.test$deltaDistance)
plot(df.test$seconds, df.test$totalDistance)
par(mfrow=c(1,1))


# velocity synchronization

df.test <- df %>% filter(side == "T") %>% select(velocityX, velocityY) %>% mutate(velocityAbs = abs(velocityX)+abs(velocityY))
hist(df.test$velocityAbs)

df.test <- df %>% filter(roundNum == 3, side == "T") %>% group_by(tick) %>% summarise(
	tHP = sum(hp),
	bombDistance = min(bombDistance),
	mapControl = min(mapControl),
	deltaDistance = min(deltaDistance),
	totalDistance = min(totalDistance),
	velocitySync = sd(abs(velocityX)+abs(velocityY)),
	afterAdverseEvent = first(afterAdverseEvent),
	seconds = min(seconds))
plot(df.test$seconds, df.test$velocitySync, col=df.test$afterAdverseEvent, pch=1)




# filter first kill

df.test <- df %>% filter(side == "T", roundNum == 3) %>% mutate(afterAdverseEvent = df.test$alivePlayers < 5)
plot()



# estimate correct ingame seconds without restarting at zero after plant
# TODO: didnt test if this actually work
# TODO: perhaps do it in data preparation
df.test %>% group_by(roundNum == 3) %>% mutate(secondsCalc = seconds + min(seconds[bombPlanted == True) * bombPlanted) %>% ungroup()



# testing

df.test$secondsCalc = (df.test$tick-df.test$freezeTimeEndTick)/128

df.test <- df %>% filter(roundNum == 3) %>% select(tick, seconds, totalDistance, roundNum, side, clockTime, startTick)
df.test$clockTime = as.factor(df.test$clockTime)
par(mfrow=c(1,2))
plot(df.test$tick, df.test$seconds)
plot(df.test$tick, df.test$clockTime)
par(mfrow=c(1,1))

