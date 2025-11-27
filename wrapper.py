from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract, ContractDetails
from ibapi.common import TickAttrib, ListOfContractDescription, TickerId
from ibapi.order import Order
import time
import logging
import socket
from typing import Dict, List, Any
import ibapi


socket.setdefaulttimeout(10.0)

logger = logging.getLogger()


class TradeApp(EWrapper, EClient):
    accounts: Dict[str, Dict[str, Any]] = dict()
    portfolios: Dict[str, List[Dict[str, Any]]] = dict()
    currency: Dict[str, float] = dict()
    contract: Dict[int, Any] = dict()
    orders: Dict[int, Dict[str, Any]] = dict()
    reqId: int = -1
    
    
    def __init__(self): 
        EClient.__init__(self, self)
        self.reqId = 3000 + (int(time.time()) % 6999)
        logger.warning(f"ibapi version: {ibapi.__version__} (should be 10.14.1)")



    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str) -> None:
        # print("AccountSummary. ReqId:", reqId, "Account:", account,"Tag: ", tag, "Value:", value, "Currency:", currency)
        self.accounts[account] = dict()
    
    
    def accountSummaryEnd(self, reqId: int) -> None:
        pass
        # print("AccountSummaryEnd. ReqId:", reqId)


    def updateAccountValue(self, key: str, val: str, cur: str, accountName: str) -> None:
        # print("UpdateAccountValue. Key:", key, "Value:", val, "Currency:", cur, "AccountName:", accountName)
        if accountName not in self.accounts.keys():
            self.accounts[accountName] = dict()
        k = key + "." + cur if len(cur) else key
        try:
            valo = float(val)
        except:
            valo = val
            pass
        self.accounts[accountName][k] = valo
        logger.info(f"key:'{key}' val:'{val}' cur:'{cur}' accountName:'{accountName}' --> self.accounts[{accountName}][{k}]={valo} {type(valo)}")
        if len(cur):
            self.currency[cur] = 1
    
    
    def updatePortfolio(self, contract: Contract, position: float, marketPrice: float, marketValue: float, averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str) -> None:
         
        logger.info(f"UpdatePortfolio. Symbol:{contract}, Position:{position}, "
                    f"MarketPrice:{marketPrice}, MarketValue:{marketValue}, "
                    f"AverageCost:{averageCost}, UnrealizedPNL:{unrealizedPNL}, "
                    f"RealizedPNL:{realizedPNL}, AccountName:{accountName}")
         
        if accountName not in self.portfolios.keys():
            self.portfolios[accountName] = []
            
        self.portfolios[accountName].append({
            'symbol': contract.symbol,
            'longName': contract.symbol,
            'secType': contract.secType,
            'primaryExchange': contract.primaryExchange,
            'currency': contract.currency,
            'conId': contract.conId,
            'localSymbol': contract.localSymbol,
            'position': float(position),
            'marketPrice': marketPrice,
            'marketValue': marketValue,
            'averageCost': averageCost,
            'unrealizedPNL': unrealizedPNL,
            'realizedPNL': realizedPNL,
            'orderAct': '',
        })
        # .symbol, "SecType:", secType, "Exchange:",exchange
        
        
    def updateAccountTime(self, timeStamp: str) -> None:
        pass
        # print("UpdateAccountTime. Time:", timeStamp)
      
        
    def accountDownloadEnd(self, accountName: str) -> None:
        pass
        # print("AccountDownloadEnd. Account:", accountName)
    

    def symbolSamples(self, reqId: int, contractDescriptions: ListOfContractDescription) -> None:
        if len(contractDescriptions):
            logger.info(f"Symbol Samples. {contractDescriptions[0]}")
            self.contract[reqId] = contractDescriptions[0].contract
        else:
            self.contract[reqId] = ""


    def contractDetails(self, reqId: int, contractDetails: ContractDetails) -> None:
        logger.info(f"{reqId}, {contractDetails}")
        self.contract[reqId - 2000] = contractDetails


    def contractDetailsEnd(self, reqId: int) -> None:
        logger.info(f"contractDetailsEnd {reqId}")
        pass
      
        
    def headTimestamp(self, reqId: int, headTimestamp: str) -> None:
        # print(reqId, headTimestamp)
        pass


    def tickPrice(self, reqId: int, tickType: int, price: float, attrib: TickAttrib) -> None:
        '''
            TickType values:
            Bid Price	1	Highest priced bid for the contract.
            Ask Price	2	Lowest price offer on the contract.
            Last Price	4	Last price at which the contract traded (does not include some trades in RTVolume).
            High	6	High price for the day.
            Low	7	Low price for the day.
            Close Price	9	The last available closing price for the previous day. 
        '''
        if tickType == 9: 
            if reqId < 1000:
                try:
                    cur = list(self.currency.keys())[reqId]
                    self.currency[cur] = price
                    logger.info(f"{reqId}, {tickType}, {price}, {attrib} -> {cur} {self.currency[cur]}")
                except:
                    ks = list(self.currency.keys())
                    logger.error(f"cannot find currency reqId:{reqId} keys:{ks}")
            else:  
                reqId = reqId - 1000
                try:
                    cur = list(self.currency.keys())[reqId]
                    self.currency[cur] = 1.0 / price
                    logger.info(f"{reqId}, {tickType}, {price}, {attrib} -> {cur} {self.currency[cur]}")
                except:
                    ks = list(self.currency.keys())
                    logger.error(f"cannot find currency reqId:{reqId} keys:{ks}")
        else:
            logger.info(f"Not used Ticktype {tickType}, {reqId}, {price}, {attrib}")
    
    
    def tickSize(self, reqId: int, tickType: int, size: int) -> None:
        pass


    def logRequest(self, fnName: str, fnParams: Any) -> None:
        pass
    
    
    def logAnswer(self, fnName: str, fnParams: Any) -> None:
        pass


    def fundamentalData(self, reqId: int, data: str) -> None:
        pass


    def openOrder(self, orderId: int, contract: Contract, order: Order, orderState: Any) -> None:
        accountName = order.account 
        if accountName not in self.portfolios.keys():
            self.portfolios[accountName] = []
        sign = -1.0 if order.action == "SELL" else 1
<<<<<<< HEAD
        line = {
=======
        line = { # 
            'orderId': orderId,    
            'orderAlgoId': order.algoId,    
            'orderRef': order.orderRef,    
            'orderType': order.orderType,    
>>>>>>> TEMP_BRANCH
            'orderAct': order.action,
            'orderVal': sign * float(order.totalQuantity) * order.lmtPrice,   # TODO / check if priceMagnifier has to be applied
            'orderPos': float(order.totalQuantity),
            'longName': contract.symbol,
            'symbol': contract.symbol,
            'conId': contract.conId,
            'secType': contract.secType,
            'primaryExchange': contract.primaryExchange,
            'currency': contract.currency,
            'localSymbol': contract.localSymbol,
        }
        logger.info(f"openOrder orderId:'{orderId}' contract:'{contract}' order:'{order}' orderState:'{orderState}' {type(order.totalQuantity)} -> {line}")

        self.orders[order.orderId] = { 
            'accountName': accountName,
            'payload': line
        }
        
        
    def orderStatus(self, orderId: int, status: str, filled: float, remaining: float, avgFillPrice: float, permId: int, parentId: int, 
                    lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float) -> None:
        data = self.orders[orderId]
        accountName, line = data['accountName'], data['payload']
        logger.info(line)
        pos = -float(remaining) if line['orderAct'] == "SELL" else float(remaining)
        val = 0.0
        for newPrice in [avgFillPrice, lastFillPrice, mktCapPrice, ]:
            if newPrice > 0.0:
                val = float(newPrice) * pos
        if val == 0.0:
            val = line['orderVal']
        line = {**line, **{
                            'orderPos': pos,
                            'orderVal': val,  # TODO / check if priceMagnifier has to be applied
        }}
        logger.info(f"orderStatus {orderId} {status} {filled} {remaining} {avgFillPrice} {permId} {parentId} {lastFillPrice} {clientId} {whyHeld}  {mktCapPrice} -> {line} ")
<<<<<<< HEAD
        if status in ['Submitted', 'PreSubmitted']:
            self.portfolios[accountName].append(line)
        else:
            logger.warning(f"orderStatus Order  {line['orderAct']} {line['orderPos']} X {line['symbol']} "
                           f"for {line['orderVal']}{line['currency']} has unforseen status '{status}'', "
=======
        if status in ['Submitted', 'PreSubmitted', 'PendingSubmit']:
            self.portfolios[accountName].append(line)
        else:
            logger.warning(f"orderStatus Order  {line['orderAct']} {line['orderPos']} X {line['symbol']} "
                           f"for {line['orderVal']}{line['currency']} has unforseen status '{status}', "
>>>>>>> TEMP_BRANCH
                           f"won't be added to portfolio")


    def openOrderEnd(self) -> None:
        logger.info("OpenOrderEnd")


    def error(self, reqId: TickerId, errorCode: int, errorString: str, advancedOrderRejectJson: str = "") -> None:
        if reqId != -1:
            super().error(reqId, errorCode, errorString)
            logger.error(f"Error. Id:{reqId}, Code:{errorCode}, Msg:{errorString}, AdvancedOrderRejectJson:{advancedOrderRejectJson}")
