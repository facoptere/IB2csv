import logging
import polars as pl
import locale
import os
import sys
from utils import SetupLogger, ibConnect, getAccounts, getOpenOrders, getCurrencies, getAssetDetails, ibDisconnect, computeThings


logger = SetupLogger()
logging.getLogger().setLevel(logging.DEBUG)

ipaddr = os.getenv("IPADDR", "127.0.0.1")
BaseCur = ['USD', 'CHF', 'EUR'] 

app = ibConnect(ipaddr)

if app is None:
    print("Cannot reach instance. Please check the IP address to use and your Trader Workstation configuration.\n"
          "See https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#remote-connection\n"
          "    https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#tws-config-api"
          "    https://www.interactivebrokers.com/campus/trading-lessons/installing-configuring-tws-for-the-api/\n\n"
          "Check also the python module ibapi version, should be 10.14.1 or better.", file=sys.stderr)
    sys.exit(-2)
else:
    try:
        getAccounts(app)
        getOpenOrders(app)
        getCurrencies(app, BaseCur)  # a little help to convert malaysian currency... , {"MYR":0.2372}
        getAssetDetails(app)

        ibDisconnect(app)

        computeThings(app, BaseCur)
        
        for account in app.accounts:
            df = pl.DataFrame(app.portfolios[account])
            with pl.Config(
                tbl_cell_numeric_alignment="RIGHT",
                thousands_separator="",
                decimal_separator=locale.localeconv()["decimal_point"],
                float_precision=4,
                set_tbl_column_data_type_inline=False,
            ):
                filename = f"{account}.csv"
                logger.warning(f"Writing CSV file '{filename}'...") 
                df.write_csv(file=filename, separator='\t', float_precision=4, null_value="")
                
    except Exception as exe:
        logger.fatal(type(exe)) 
        sys.exit(-1)
