import sys
import logging
from wrapper import TradeApp
import threading
import time
from ibapi.contract import Contract
from typing import Dict, List, Optional, Any 
# import os


logger = logging.getLogger()


def SetupLogger() -> logging.Logger:
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)],
                        level=logging.DEBUG,
                        format="%(asctime)s - %(name)s:%(filename)s:%(funcName)s:%(lineno)d - %(levelname)s - %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",)
    logger = logging.getLogger()

    return logger


def ibConnect(ipaddr: str) -> Optional[TradeApp]:
    '''
        see https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#remote-connection
    '''   
    app = TradeApp()
    app.connect(ipaddr, 7496, clientId=app.reqId)
    time.sleep(1)
    api_thread = threading.Thread(target=app.run)
    time.sleep(.1)
    api_thread.start()
    time.sleep(1)
    if app.isConnected():
        return app
    logger.warning("Could not connect to TWS!")
    return None


def getAccounts(app: TradeApp) -> Dict[str, Dict[str, Any]]:
    app.reqMarketDataType(4)
    time.sleep(.1)
    app.reqAccountSummary(0, "All", "AccountType")
    time.sleep(1)

    logger.warning(f"Found the following accounts: {app.accounts}")

    for account in app.accounts.keys():
        app.reqAccountUpdates(True, account)
        time.sleep(1)

    numLines = 0
    for account in app.accounts.keys():
        # print(app.accounts[account])
        app.reqAccountUpdates(False, account)
        time.sleep(.1)
        numLines += len(app.portfolios[account])

    logger.warning(f"Found {numLines} lines in all portfolios")

    return app.accounts


def getOpenOrders(app: TradeApp) -> Dict[int, Dict[str, Any]]:
    app.reqAllOpenOrders()
    time.sleep(1)
    numLines = 0
    for account in app.accounts.keys():
        numLines += len(app.portfolios[account])
    logger.warning(f"Found {numLines} lines including live orders")
    return app.orders


def getCurrencies(app: TradeApp, BaseCur: List[str], cooked: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    app.reqMarketDataType(4)
    time.sleep(.1)

    # preparing data for currency conversion
    BaseCur = ['USD', 'CHF', 'EUR'] 
    otherCur = set()
    otherCur.update(BaseCur)
    
    for account in app.portfolios.keys():
        for line in app.portfolios[account]:
            otherCur.add(line['currency'])
            
    app.currency = dict()
    for cur in list(otherCur):
        if len(cur) == 3:  # forbid "BASE" fake currency
            app.currency[cur] = -1 if cur != "USD" else 1

    query2Cancel = list()

    # trying to convert 1 USD in local currency
    for cur in app.currency.keys():
        if cur != 'USD':
            c = Contract()
            c.symbol = 'USD'
            c.secType = 'CASH'
            c.exchange = "IDEALPRO"
            c.primaryExchange = "IDEALPRO"
            c.currency = cur
            id = list(app.currency.keys()).index(cur)
            query2Cancel.append(id)
            logger.debug(f"Trying to convert USD in {cur} (reqID:{id})")
            app.reqMktData(id, c, "", True, False, [])
            time.sleep(.1)
    time.sleep(.5)

    # in case of failure, trying to convert local currency to USD
    for cur in app.currency.keys():
        if cur != 'USD' and app.currency[cur] < 0:
            c = Contract()
            c.currency = 'USD'
            c.secType = 'CASH'
            c.exchange = "IDEALPRO"
            c.primaryExchange = "IDEALPRO"
            c.symbol = cur
            id = 1000 + list(app.currency.keys()).index(cur)
            query2Cancel.append(id)
            logger.debug(f"Trying to convert {cur} in USD (reqID:{id})")
            app.reqMktData(id, c, "", True, False, [])
            time.sleep(.1)
    time.sleep(.5)

    for q in query2Cancel:
        app.cancelAccountSummary(q)
        time.sleep(.1)

    if cooked:
        app.currency = {**app.currency, **cooked}
        
    for cur in app.currency.keys():
        if app.currency[cur] < 0:
            logger.error(f"Could not manage to get currency {cur}.USD -- assessement may be wrong")
            
    logger.warning(f"Managed to get following currencies (base 1=USD): {app.currency}")
        
    return app.currency  


def getAssetDetails(app: TradeApp) -> None:
    for account in app.portfolios.keys():
        logger.info("GETTING STOCK DETAILS AND PRICE MAGNIFIER")
        app.contract = dict()
        for idx, line in enumerate(app.portfolios[account]):
            c = Contract()
            c.conId =           line['conId']
            c.secType =         line['secType']
            c.exchange =        line['primaryExchange']
            c.primaryExchange = line['primaryExchange']
            c.symbol =          line['symbol']
            c.currency =        line['currency']
            c.localSymbol =     line['localSymbol']
            app.reqContractDetails(2000 + idx, c)
            time.sleep(.1)


        time.sleep(2)

        for idx, line in enumerate(app.portfolios[account]):
            if idx in app.contract.keys():
                contractDetails = app.contract[idx]
                app.portfolios[account][idx]['longName'] =       getattr(contractDetails, 'longName', "")
                app.portfolios[account][idx]['industry'] =       getattr(contractDetails, 'industry', "")
                app.portfolios[account][idx]['category'] =       getattr(contractDetails, 'category', "")
                app.portfolios[account][idx]['subcategory'] =    getattr(contractDetails, 'subcategory', "")
                app.portfolios[account][idx]['priceMagnifier'] = int(getattr(contractDetails, 'priceMagnifier', 1.0))
                app.portfolios[account][idx]['stockType'] =      getattr(contractDetails, 'stockType', "")
                app.portfolios[account][idx]['minSize'] =        float(getattr(contractDetails, 'minSize', 0.0001))
                app.portfolios[account][idx]['sizeIncrement'] =  float(getattr(contractDetails, 'sizeIncrement', 1.0))
                app.portfolios[account][idx]['minTick'] =        float(getattr(contractDetails, 'minTick', 0.0001))
            else:
                logger.error(f"Missing contract {app.portfolios[account][idx]['localSymbol']}")


def ibDisconnect(app: TradeApp) -> None:
    app.disconnect()
    

def computeThings(app: TradeApp, BaseCur: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    for account in app.portfolios.keys():
        
        for k in app.accounts[account].keys():
            if k.startswith('NetLiquidation.'):
                logger.info(f"NetLiquidation  k:'{k}'  val:'{app.accounts[account][k]}'  ")
                grandtotalCur = k[len(k) - 3:]
                grandtotalVal = app.accounts[account][k] 
                app.portfolios[account].append({
                    'orderAct': '',
                    'secType': "TOTAL",
                    'currency': grandtotalCur,
                    'marketValue': grandtotalVal,
                })
                break

        totalAsset = dict(zip(BaseCur, [0] * len(BaseCur)))
        usd = BaseCur[0]
        marketValueUSD = f"marketValue.{usd}"
        
        for idx, line in enumerate(app.portfolios[account]):
            # action = line['orderAct']
            # if action != "":  # line from the order book
            #    try:
            #        # applying magnifier for ongoing orders only (for example prices expressed in penny /100p -> 1£)
            #        line['orderVal'] /= app.portfolios[account][idx]['priceMagnifier']
            #    except:
            #        logger.info(f"cannot apply magnifier for {app.portfolios[account][idx]['symbol']} current order")
            
            for column in ['marketPrice', 'marketValue', 'averageCost',  'unrealizedPNL', 'realizedPNL', 'orderVal']:
                for currency in BaseCur:
                    if column in line:
                        cur = line['currency']
                        if app.currency[cur] > 0: # value is neg if conversion is unknown
                            val = line[column]
                            valCur = val / app.currency[cur] * app.currency[currency]
                            # valCur /= magnifier if column in ['marketPrice', 'averageCost'] else 1.0
                            # app.portfolios[account][idx][f"{column}.{currency}"] = valCur
                            line[f"{column}.{currency}"] = valCur
                        if column == 'marketValue' and line['secType'] not in ['TOTAL', 'CASH']:
                            totalAsset[currency] += valCur

        if len(app.portfolios[account]) > 0 and marketValueUSD in app.portfolios[account][-1]:
            for idx, line in enumerate(app.portfolios[account]):
                action = line['orderAct']
                if line['secType'] != "TOTAL" and action == "" and marketValueUSD in line:  # line from the portfolio
                    line['pct'] = line[marketValueUSD] / app.portfolios[account][-1][marketValueUSD] * 100.0
                # else:
                #     logger.warning(f"missing computation for asset id {idx} - won't compute percentages")
        # else:
        #    logger.warning(f"missing grand total in usd - won't compute percentages")
        
        app.portfolios[account].append({'orderAct': '', 'secType': "CASH"})
        logger.debug(f"-1 {app.portfolios[account][-1]}")  # CASH line
        logger.debug(f"-2 {app.portfolios[account][-2]}")  # TOTAL line
        logger.debug(f"totalAsset {totalAsset}")           # value of all assets
        
        for currency in BaseCur:
            app.portfolios[account][-1][f"marketValue.{currency}"] = app.portfolios[account][-2][f"marketValue.{currency}"] - totalAsset[currency]
            
        app.portfolios[account][-1]['pct'] = 100.0 * (app.portfolios[account][-2][marketValueUSD] - totalAsset[usd]) / app.portfolios[account][-2][marketValueUSD]
    
    return app.portfolios
