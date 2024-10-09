
library(png)
library(dplyr)

setwd("D:\\dev\\csgo-demo-visualizer\\src")
df <- read.csv("testdemo.csv")


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
df$side = factor(df$side)
par(mfrow=c(2,2))
df.test <- df %>% group_by(seconds) %>% summarise(ctHP = sum(hp[side=="T"]), tHP = sum(hp[side=="CT"]), bombDistance = min(BombDistance), mapControl = min(MapControl))
plot(df.test$seconds, df.test$ctHP, ylim=c(0,500))
plot(df.test$seconds, df.test$tHP, ylim=c(0,500))
plot(df.test$seconds, df.test$bombDistance)
plot(df.test$seconds, df.test$mapControl, ylim=c(-1,1))
par(mfrow=c(1,1))
