#
# Buy 50 shares of a stock when its 50-day moving average goes above the 200-day moving average.
# (A moving average is an average of past data points that smooths out day-to-day price fluctuations and thereby identifies trends.)
# Sell shares of the stock when its 50-day moving average goes below the 200-day moving average.
#
#
# Trend-following Strategies
# The most common algorithmic trading strategies follow trends in
# moving averages, channel breakouts, price level movements, and related technical indicators.
#
# Arbitrage Opportunities
# Buying a dual-listed stock at a lower price in one market and simultaneously selling it at a higher price in another
# market offers the price differential as risk-free profit or arbitrage.


import alpaca_trade_api as tradeapi
import datetime, os
import pandas as pd
import pickle
from datetime import date
from datetime import timedelta
import time
import decimal

# The rate limit is 200 requests per every minute per API key
api = tradeapi.REST('PKOFBC8IS8VMMP69347V', 'F8vTz0JIAsJsUW3MvImHcIFiVfuoJzcgYoiecWBm',
                    'https://paper-api.alpaca.markets', api_version='v2')  # or use ENV Vars shown below
account = api.get_account()
positions = api.list_positions()


def downloadHistoricalData(unit, symbol, startDate, endDate):
    loopDate = startDate
    priceData = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    totalMinuteLoops = int((endDate - startDate).days)
    while loopDate < endDate:
        if loopDate.isoweekday() == 7:
            loopDate += datetime.timedelta(days=1)
            continue
        elif loopDate.isoweekday() == 6:
            loopDate += datetime.timedelta(days=1)
            continue
        elif unit == "minute":
            strLoopDate = loopDate.strftime('%Y-%m-%d')
            priceData = priceData.append(
                (api.polygon.historic_agg_v2(symbol, 1, unit, _from=strLoopDate, to=strLoopDate).df))
            time.sleep(7)
            loopDate += datetime.timedelta(days=1)
            requestsLeft = ((totalMinuteLoops - int((endDate - loopDate).days)) / float(totalMinuteLoops)) * 100
            print(symbol + " data " + str(round(requestsLeft, 2)) + "% downloaded")
        else:
            strLoopDate = loopDate.strftime('%Y-%m-%d')
            strEndDate = endDate.strftime('%Y-%m-%d')
            priceData = priceData.append(
                (api.polygon.historic_agg_v2(symbol, 1, unit, _from=strLoopDate, to=strEndDate).df))
            loopDate = endDate
    return priceData


# Should make it look for existing data first
def SMACalculator(symbol, days):
    startDate = ((datetime.date.today()) - datetime.timedelta(days=days))
    endDate = datetime.date.today()
    if endDate.isoweekday() == 7:
        endDate -= datetime.timedelta(days=2)
    elif endDate.isoweekday() == 6:
        endDate -= datetime.timedelta(days=1)
        time.sleep(2)
    stockData = downloadHistoricalData("day", symbol, startDate, endDate)
    closingValues = stockData['close'].tolist()
    currentMovingAverage = sum(closingValues) / float(len(closingValues))
    return currentMovingAverage


def loadHistoricalData(symbol, startDate, endDate):
    strStartDate = startDate.strftime("%Y-%m-%d")
    strEndDate = endDate.strftime("%Y-%m-%d")
    try:
        with open(symbol + ".pickle", "rb") as fp:
            data = pickle.load(fp)
            fp.close()
        data = data[
            (data.index.get_level_values(0) >= strStartDate)
            & (data.index.get_level_values(0) <= strEndDate)]
    except:
        print("Data loading failed!")
    data = data['close'].tolist()
    dataSum = sum(data)
    dataLen = len(data)
    dataAvg = float(dataSum / dataLen)
    return [data, dataSum, dataLen, dataAvg]


class tradeTemplate:
    def __init__(self):
        self.symbol = None
        self.tradePlaced = False
        self.purchasePrice = 0


def SMABacktester(symbol, stopLossPercent, longSMADays, shortSMADays, startDate, endDate):
    tradeProfile = tradeTemplate()
    loopDate = startDate
    net = 0
    while loopDate != endDate:
        if loopDate.isoweekday() == 6:
            loopDate += timedelta(days=1)
            continue
        elif loopDate.isoweekday() == 7:
            loopDate += timedelta(days=1)
            continue
        try:
            longSMAData = loadHistoricalData(symbol, (loopDate - timedelta(days=longSMADays)), loopDate)
            shortSMAData = loadHistoricalData(symbol, (loopDate - timedelta(days=shortSMADays)), loopDate)
            loopData = loadHistoricalData(symbol, loopDate, (loopDate + timedelta(days=1)))
            todaysPriceSum = 0
        except:
            loopDate += timedelta(days=1)
            continue





        for i in range(len(loopData[0])):
            loopPrices =+ loopData[0][i]
            shortSMA = float((loopPrices + shortSMAData[1])/(shortSMAData[2] + i + 1))
            longSMA = float((loopPrices + longSMAData[1]) / (longSMAData[2] + i + 1))


            if tradeProfile.purchasePrice != 0:
                lossPercent = (loopData[0][i]/tradeProfile.purchasePrice)*100 - 100
                lossPercent = (tradeProfile.purchasePrice / loopData[0][i]) * 100 - 100
                if lossPercent >= stopLossPercent and tradeProfile.tradePlaced == True:
                    print("\n\n\nshlitt")
                    print("Current Price:",str(loopData[0][i]))
                    print("Bought at:",str(tradeProfile.purchasePrice))

                    tradeProfile.tradePlaced = False
                    gross = loopData[0][i] - tradeProfile.purchasePrice
                    # print("Sold at:", str(loopData[0][i]))
                    print("Profit:", gross)
                    net += gross

            if shortSMA >= longSMA and tradeProfile.tradePlaced == False:
                tradeProfile.tradePlaced = True
                tradeProfile.purchasePrice = loopData[0][i]
                # print("Bought at:",str(loopData[0][i]))


            elif shortSMA <= longSMA and tradeProfile.tradePlaced == True:
                tradeProfile.tradePlaced = False
                gross = loopData[0][i] - tradeProfile.purchasePrice
                print("\n\n\nBought at:",str(tradeProfile.purchasePrice))
                print("Sold at:",str(loopData[0][i]))
                print("Profit:",gross)
                net += gross



        loopDate += timedelta(days=1)

    print(net)




#151.7
# f_date = date(2019, 3, 30)
# l_date = date(2020, 3, 30)
# SMABacktester("TSLA", 50, 5, f_date, l_date)


f_date = date(2019, 11, 30)
l_date = date(2020, 3, 30)
SMABacktester("TSLA", .5, 50, 5, f_date, l_date)




