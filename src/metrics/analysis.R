
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