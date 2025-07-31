#!/usr/bin/env python
import base64
import hashlib
import time
import requests
import json
import configparser
import os
import sys
import re
from urllib.parse import urlencode
import hmac


debug = False
currencies = ["USD", "EUR", "GBP", "CHF", "TRY", "PLN", "HUF", "CZK", "SEK", "DKK", "RON", "BGN"]
stablecoins = [["USDT", "USD"], ["USDC", "USD"], ["DAI", "USD"], ["TUSD", "USD"], ["BUSD", "USD"], ["USDP", "USD"], ["GUSD", "USD"], ["FDUSD", "USD"], ["PYUSD", "USD"], ["EURC", "EUR"], ["EURS", "EUR"], ["sUSD", "USD"], ["FRAX", "USD"], ["FRAXUSD", "USD"], ["USDS", "USD"], ["USDE", "USD"], ["DJED", "USD"], ["RSV", "USD"], ["USD1", "USD"], ["XAUt", "Gold"], ["PAXG", "Gold"], ["aUSD", "USD"], ["nUSD", "USD"], ["CUSD", "USD"], ["LUSD", "USD"], ["MIM", "USD"], ["HUSD", "USD"], ["AGEUR", "EUR"], ["SDAI", "USD"], ["MUSD", "USD"], ["VAI", "USD"], ["USDN", "USD"], ["ALUSD", "USD"], ["XUSD", "USD"]]
header = {
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    }

w_space = [0, 0]

def initialize():
    config = configparser.ConfigParser()
    config_path = os.path.dirname(os.path.realpath(__file__)) + "/config_cointicker.ini"
    if os.path.isfile("/dev/shm/config_cointicker.ini") == True:
        config.read("/dev/shm/config_cointicker.ini")
    else:
        if os.path.isfile(config_path) == True:
            config.read(config_path)
            ram_access = config["Global"]["ram_access"]
            if ram_access == True:
                import shutil
                shutil.copy(config_path, "/dev/shm/config_cointicker.ini")
        else:
            print("You should set up Cointicker with init at first.")
            exit()

    #Load Bitpanda API Credentials
    bp_cred = []
    bp_cred.append(config['Bitpanda']['active'])
    if bp_cred[0].lower() == "true":
        bp_cred.append(config['Bitpanda']['api_key'])

    
    ku_cred = []
    ku_cred.append(config['KuCoin']['active'])
    if ku_cred[0].lower() == "true":
    # Load KuCoin API Credentials
        ku_cred.append(config['KuCoin']['api_key'])
        ku_cred.append(config['KuCoin']['secret_key'])
        ku_cred.append(config['KuCoin']['passphrase'])
    

    target_currency = config['Global']['target_currency']
    show_total = config['Waybar']['show_total']
    waybar_text = config['Waybar']['text']

    waybar = config['Global']['waybar']

    return [bp_cred, ku_cred, target_currency, bool(waybar), waybar_text, show_total]


def qinput(text, count):
    for x in range(0, count):
        out = input(text)
        if "yes" in out.lower():
            return True
        elif "no" in out.lower():
            return False
        else:
            print("Try it again with Yes or No.")
    else:
        print("Try it next time ~ bye")
        exit()

def configure():
    
    config = configparser.ConfigParser()

    print("Welcome to CoinTicker !")
    print("(For the best experience, use it with Waybar.)\n")
    ask_bp = qinput("Do you want to set up Bitpanda? [Yes/No] ", 3) 
    if ask_bp == True:
        bt_api_key = str(input("API-KEY: "))

    ask_ku = qinput("Do you want to set up KuCoin? [Yes/No] ", 3) 
    if ask_ku == True:
        ku_api_key = str(input("API-KEY: "))
        ku_secret = str(input("Secret: "))
        ku_pass = str(input("Passphrase: "))

    print(f"Available currencies: {currencies}")        
    for x in range(0, 3):
        target_currency = str(input("Chose your currency: ").upper())
        if target_currency in currencies:
            break
        else:
            print("Invalid currency. Please try again.")
    else:
        exit()

    waybar = qinput("Enable Waybar specific json output? [Yes/No]: " , 3)
    if waybar == True:
        print("Print total of your Portfolio in you Waybar? [Yes/No] \n(The total amount appears when you hover the course over the module)")
        show_total = qinput("", 3)
    
        config['Bitpanda'] = {"api_key": bt_api_key,}
        config['KuCoin'] = {"api_key": ku_api_key, "secret_key": ku_secret, "passphrase": ku_pass}
        config["Global"] = {"waybar": waybar, "target_currency": target_currency}
        config['Waybar'] = {"text": " ₿ ", "show_total": show_total}

        if os.path.isdir("/dev/shm/") == True:
            import shutil
            config["Global"] = {"ram_access": True}
            shutil.copy(os.getcwd() + "/config_cointicker.ini", "/dev/shm/config_cointicker.ini")
        else:
            config["Global"] = {"ram_access": False}

        with open('config_cointicker.ini', 'w') as configfile:
            config.write(configfile)
            print(f"Configuration written to: {os.getcwd()}/config_cointicker.ini")
            print("(Reuse this file for future changes or run init again.)")   

def reset():
    if os.path.isfile("/dev/shm/config_cointicker.ini") == True:
        os.remove("/dev/shm/config_cointicker.ini")
    if os.path.isfile(os.getcwd() + "/config_cointicker.ini") == True:
        os.remove(os.getcwd() + "/config_cointicker.ini")        

    print("Done")
    exit()

def update():
    import shutil
    shutil.copy(os.getcwd() + "/config_cointicker.ini", "/dev/shm/config_cointicker.ini")
    print("Done")
    exit()

def prepare_waybar_tooltip(name, total, waybar_tooltip, waybar, w_space):
    if waybar == True:
        title_space = 2 * " "
        wstring_tooltip = "<b>" + name + "</b>" + title_space + "<i><span color=\'gray\' rise=\'-1000\'>Total: " + str(round(total, 2)) + " " + target_currency + "</span></i>\n\n"
        sorted_waybar_tooltip = dict(sorted(waybar_tooltip.items(), key=lambda item: float(item[1][0]), reverse=True))
        for key, value in sorted_waybar_tooltip.items():
            cs_spaces = (w_space[0] - len(key)) * " "
            var_spaces = (w_space[1] - len(value[0])) * " "
            wstring_tooltip += f'{key}{cs_spaces} : {value[0]} {target_currency}{var_spaces} <span color=\'GreenYellow\' font-family=\'OpenSymbol\'>@</span> {value[1]}\n'
        return total, wstring_tooltip + "\n"
    else:
        return total, " "
        print(f'₿ : {round(total, 2)} {target_currency}')

def print_waybar_tooltip(ex_data, waybar_text, show_total):
    total = 0
    text = ""
    exs_data = sorted(ex_data, key=lambda x: float(x[0]), reverse=True)
    for x in exs_data:
        total += x[0]
        text += x[1] 

    if show_total.lower() == "true":
        output_text = f'{waybar_text} {round(total, 2)} {target_currency}'
    else:
        output_text = waybar_text
        text += "<b>Total </b>:: <span color=\'gold\'><b>" + str("%.2f" % round(total, 2)) + " " + target_currency + "</b></span>"
    output_dic = {"text":output_text,"tooltip":text, "class":"Coin_Tracker"}
    print(json.dumps(output_dic))


def create_request(session, endpoint, path, method, exchanger):
    full_path = f"{endpoint}{path}"
    raw_url = f"{path}"
    request = requests.Request(method=method, url=full_path).prepare()
    
    if isinstance(exchanger, Bitpanda):
        headers = exchanger.headers()

    if isinstance(exchanger, KuCoin):
        payload = method + raw_url
        headers = exchanger.headers(payload)

    if exchanger == True:
        headers = {"Accept-Encoding": "gzip, deflate, br, zstd"}

    request.headers.update(headers)
    send_request = session.send(request)
    json_data = json.loads(send_request.content)
    return json_data

class Bitpanda:
    def __init__(self, session, api_key, target_currency, waybar):
        global json_ticker, w_space
        self.bp_total = 0
        total_balance = {}
        self.api_key = api_key
        json_asset_wallet, json_fiat_wallet, json_ticker = self.request("/v1/asset-wallets"), self.request("/v1/fiatwallets"), self.request("/v2/ticker")
        json_ticker = self.prepare_ticker(json_ticker)
        self.parse_fiat_wallet(json_fiat_wallet, total_balance)
        self.parse_asset_wallet(json_asset_wallet, total_balance)
        
        self.waybar_tooltip = {}

        for k, v in total_balance.items():
            if v:
                for kx, vx in v.items():
                    try:
                        exchange_rate = json_ticker[kx][target_currency]
                        self.bp_total += float(vx) * float(exchange_rate) 
                        if debug == True:
                            print(f'{kx}:{float(vx) * float(exchange_rate)}')
                        if waybar == True:
                            self.waybar_tooltip[kx] = ["%.2f" % round(float(vx) * float(exchange_rate), 2), exchange_rate]
                            if len(kx) > w_space[0]:
                                w_space[0] = len(kx)
                            if len(self.waybar_tooltip[kx][0]) > w_space[1]:
                                w_space[1] = len(self.waybar_tooltip[kx][0])
                    except:
                        print(f"Error: „{target_currency}\" currency not available.")
                        exit()

    def headers(self) -> dict:
        return {
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "X-Api-Key": self.api_key
        } 
    
    def request(self, path: str):
        return create_request(session, "https://api.bitpanda.com", path, "GET", self)

    def parse_fiat_wallet(self, json_data, total_balance):
        total_balance["fiat_wallet"] = {}
        for item in json_data["data"]:
            if float(item["attributes"]["balance"]) != 0.0 and item:
                total_balance["fiat_wallet"][item["attributes"]["fiat_symbol"]] = item["attributes"]["balance"]

    def prepare_ticker(self, json_ticker):        
        json_ticker["EUR"] = json_ticker["BCPEUR"]
        json_ticker["USD"] = json_ticker["BCPUSD"]
        json_ticker["GBP"] = json_ticker["BCPGBP"]
        for x in currencies[3:]:
            json_ticker[x] = {}
            value = 1/float(json_ticker["USD"][x])
            json_ticker[x]["USD"] = value
            for y in currencies[1:]:
                y_value = float(json_ticker["USD"][y])*value
                json_ticker[x][y] = "%.4f" % round(y_value, 4)

        return json_ticker
    
    def parse_asset_wallet(self, json_data, total_balance):
        for k, v in json_data["data"]["attributes"].items():
            total_balance[k] = {}
            if k == "cryptocoin":
                for x in v["attributes"]["wallets"]:
                    if float(x["attributes"]["balance"]) != 0.0 and v:
                        total_balance[k][x["attributes"]["cryptocoin_symbol"]] = x["attributes"]["balance"]
            if k == "commodity":
                for x in v["metal"]["attributes"]["wallets"]:
                    if float(x["attributes"]["balance"]) != 0.0 and v:
                        total_balance[k][x["attributes"]["cryptocoin_symbol"]] = x["attributes"]["balance"]
            if k == "index":
                for x in v["index"]["attributes"]["wallets"]:
                    if float(x["attributes"]["balance"]) != 0.0 and v:
                        total_balance[k][x["attributes"]["cryptocoin_symbol"]] = x["attributes"]["balance"]
            if k == "security" or k == "equity_security":
                for y in v.keys():
                    for x in v[y]["attributes"]["wallets"]:
                        if float(x["attributes"]["balance"]) != 0.0 and v:
                            total_balance[k][x["attributes"]["cryptocoin_symbol"]] = x["attributes"]["balance"]

class KuCoin:
    def __init__(self, session, api_key: str, api_secret: str, api_passphrase: str):
        # ref https://www.kucoin.com/docs-new/authentication
        self.session = session or ""
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""
        self.api_passphrase = api_passphrase or ""
        self.ku_spot_balance = {}
        self.ku_future_balance = {}
        self.ku_waybar_tooltip = {}

        if "json_ticker" not in globals():
            global json_ticker
            json_ticker = create_request(session, "https://api.bitpanda.com", "/v2/ticker", "GET", True) 
            Bitpanda.prepare_ticker("Bitpanda", json_ticker)

        if api_passphrase and api_secret:
            self.api_passphrase = self.sign(api_passphrase.encode('utf-8'), api_secret.encode('utf-8'))
            self.fetch_account_balance()
            self.compare_tickers_with_account_balance()

        if not all([api_key, api_secret, api_passphrase]):
            print("API token is empty. Access is restricted to public interfaces only.")

    def fetch_account_balance(self):
        json_spot_data = self.request("/api/v1/accounts/")
        json_future_data = self.request("/api/v1/orders", "https://api-futures.kucoin.com")
        for x in json_spot_data["data"]:
            if float(x["balance"]) > 0:
                self.ku_spot_balance[x["currency"]] = [x["balance"]]

        if int(json_future_data["data"]["totalNum"]) > 0:
            for x in range(0, len(json_future_data["data"]["items"])):
                if "done" not in json_future_data["data"]["items"][x]["status"]:
                    future_symbol = json_future_data["data"]["items"][x]["symbol"]
                    if self.ku_future_balance.get(future_symbol) == None:
                        future_details = self.request('/api/v1/position?' + urlencode({"symbol":future_symbol}), "https://api-futures.kucoin.com")
                        future_total = float(future_details["data"]["posInit"]) - float(future_details["data"]["unrealisedPnl"])*-1 - float(future_details["data"]["posMaint"])
                        self.ku_future_balance[future_symbol] = [future_total, "x" + str(future_details["data"]["leverage"]), future_details["data"]["markPrice"]]
                    
    def compare_tickers_with_account_balance(self):
        self.ku_waybar_tooltip = {}
        self.ku_total = 0

        if self.ku_spot_balance:
            self.compare_tickers_with_spot_balance()

        if self.ku_future_balance:    
            self.compare_tickers_with_future_balance()

    def compare_tickers_with_future_balance(self):
        for key, value in self.ku_future_balance.items():
            self.ku_waybar_tooltip[key] = [str(round(float(value[0])*float(json_ticker["USD"][target_currency]), 2)), round(float(value[2])*float(json_ticker["USD"][target_currency]), 6)]
            if len(key) > w_space[0]:
                w_space[0] = len(key)
            if len(self.ku_waybar_tooltip[key][0]) > w_space[1]:
                w_space[1] = len(self.ku_waybar_tooltip[key][0])

    def compare_tickers_with_spot_balance(self):
        json_spot_tickers = self.request("/api/v1/market/allTickers")
        for y in self.ku_spot_balance.keys():
            sc_found = False
            for yx in stablecoins:
                if y in yx[0]:
                    self.ku_spot_balance[y].append(["STABLECOIN", yx[1]])
                    sc_found = True 
                    break
            
            if sc_found == True:
                target_ticker = float(json_ticker[x[1]][target_currency])
                target_total = float(self.ku_spot_balance[y][0])*float(target_ticker)
                self.ku_waybar_tooltip[y] = [str("%.2f" % round(target_total, 2)), str(target_ticker)]
                self.ku_total += target_total
                continue

            ku_asset_volume = 0
            for x in json_spot_tickers["data"]["ticker"]:
                if re.match(rf"^{y}-", x["symbol"]):
                    for z in currencies:
                        if z in x["symbol"]:
                            currency = z
                    if currency:
                        tmp_volume = float(float(x["sell"])*float(x["vol"]))
                        self.ku_spot_balance[y].append([x["symbol"], currency, x["sell"], x["vol"], tmp_volume])
                        if tmp_volume > ku_asset_volume:
                            ku_asset_volume = float(float(x["sell"])*float(x["vol"]))
            
            if 0 != ku_asset_volume:
                for x in self.ku_spot_balance[y][1:]:
                    if x[4] == ku_asset_volume:
                        len_ticker = len(x[2])
                        target_ticker = float(x[2])*float(json_ticker[x[1]][target_currency])
                        target_total = float(self.ku_spot_balance[y][0])*float(target_ticker)
                        self.ku_waybar_tooltip[y] = [str("%.2f" % round(target_total, 2)) ,str(round(target_ticker, len_ticker-2))] 
                        if len(y) > w_space[0]:
                            w_space[0] = len(y)
                        if len(self.ku_waybar_tooltip[y][0]) > w_space[1]:
                            w_space[1] = len(self.ku_waybar_tooltip[y][0])
                        self.ku_total += target_total

    def request(self, path: str, endpoint = "https://api.kucoin.com"):
        return create_request(session, endpoint, path, "GET", self)

    def sign(self, plain: bytes, key: bytes) -> str:
        hm = hmac.new(key, plain, hashlib.sha256)
        return base64.b64encode(hm.digest()).decode()

    def headers(self, plain: str) -> dict:
        timestamp = str(int(time.time() * 1000))
        signature = self.sign((timestamp + plain).encode('utf-8'), self.api_secret.encode('utf-8'))

        return {
            "Content-Type": "application/json",
            "KC-API-KEY": self.api_key,
            "KC-API-PASSPHRASE": self.api_passphrase,
            "KC-API-TIMESTAMP": timestamp,
            "KC-API-SIGN": signature,
            "KC-API-KEY-VERSION": "2"
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "reset":
            reset()
        elif sys.argv[1].lower() == "update":
            update()
        elif sys.argv[1].lower() == "init":
            configure()

    ex_data = []
    session = requests.Session()
    bp_cred, ku_cred, target_currency, waybar, waybar_text, show_total = initialize()
    
    if bp_cred[0].lower() == "true":
        bp_data = Bitpanda(session, bp_cred[1], target_currency, waybar)
        bp_total, bp_tooltip = prepare_waybar_tooltip("Bitpanda", bp_data.bp_total, bp_data.waybar_tooltip, waybar, w_space)
        ex_data.append((bp_total, bp_tooltip))


    if ku_cred[0].lower() == "true":
        ku_data = KuCoin(session, ku_cred[1], ku_cred[2], ku_cred[3])
        ku_total, ku_tooltip = prepare_waybar_tooltip("KuCoin", round(ku_data.ku_total, 2), ku_data.ku_waybar_tooltip, waybar, w_space)
        ex_data.append((ku_total, ku_tooltip))


    if waybar == True:
        print_waybar_tooltip(ex_data, waybar_text, show_total)

