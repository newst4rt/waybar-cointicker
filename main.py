#!/usr/bin/env python
import base64
import hashlib
import time
import requests
import brotli
import json
import configparser
import os
import sys
from urllib.parse import urlencode
import hmac


total_balance = {}
total = 0
debug = False
currencies = ["USD", "EUR", "GBP", "CHF", "TRY", "PLN", "HUF", "CZK", "SEK", "DKK", "RON", "BGN"]
header = {
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    }

def __init__():
    ram_access = False
    config = configparser.ConfigParser()
    config_path = os.getcwd() + "/config_bitpanda.ini"
    if os.path.isfile("/dev/shm/config_bitpanda.ini") == True:
        ram_access = True
    else:
        import shutil
        if os.path.isfile(config_path) == False: 
            print("Setup Bitpanda Configuration\n")
            api_key = str(input("API-KEY: "))
            if not api_key:
                print("Error: Invalid input.")
                exit()
            count = 1
            for x in range(0, 3):
                print(f"Available currencies: {currencies}")
                target_currency = str(input("Set your target currency: ").upper())
                if target_currency in currencies:
                    break
                else:
                    print("Invalid currency. Please try again.")
            else:
                exit()
    
            for x in range(0, 3):
                waybar_ask = str(input("Enable Waybar specific json output? [Yes/No]: "))
                if "yes" in waybar_ask.lower():
                    waybar = True
                    break
                elif "no" in waybar_ask.lower():
                    waybar = False
                    break
                else:
                    print("Invalid input. Please try again.")
            else:
                exit()
            
            config['DEFAULT'] = {"api_key": api_key,
                            "target_currency": target_currency,
                            "waybar": waybar}
            with open('config_bitpanda.ini', 'w') as configfile:
                config.write(configfile)
                print(f"Configuration file has been written to: {os.getcwd()}/config_bitpanda.ini")
            try:
                shutil.copy(os.getcwd() + "/config_bitpanda.ini", "/dev/shm/config_bitpanda.ini")
            except:
                pass
        
        else:
            shutil.copy(config_path, "/dev/shm/config_bitpanda.ini")

    if ram_access == True:
        config.read("/dev/shm/config_bitpanda.ini")
    else:
        config.read(config_path)
        
    api_key = config['DEFAULT']['api_key']
    target_currency = config['DEFAULT']['target_currency']
    waybar = config['DEFAULT']['waybar']
    header["X-Api-Key"] = api_key
    
    return [str(api_key), str(target_currency), bool(waybar)]

def reset():
    if os.path.isfile("/dev/shm/config_bitpanda.ini") == True:
        os.remove("/dev/shm/config_bitpanda.ini")
    if os.path.isfile(os.getcwd() + "/config_bitpanda.ini") == True:
        os.remove(os.getcwd() + "/config_bitpanda.ini")        

    print("Done")
    exit()

def update():
    import shutil
    shutil.copy(os.getcwd() + "/config_bitpanda.ini", "/dev/shm/config_bitpanda.ini")
    print("Done")
    exit()


def create_request(session, endpoint, path, method, exchanger = ""):
    full_path = f"{endpoint}{path}?{urlencode}"
    raw_url = f"{path}?{urlencode}"
    request = requests.Request(method=method, url=full_path).prepare()
    
    if isinstance(exchanger, str) and "Bitpanda" in exchanger:
        request.headers.update(header)

    elif isinstance(exchanger, KuCoin):
        payload = method + raw_url
        headers = exchanger.headers(payload)
        request.headers.update(headers)

    send_request = session.send(request)
    json_data = json.loads(send_request.content)
    return json_data

class Bitpanda:
    def __init__(self, session, api_key, target_currency, waybar):
        global json_ticker
        total_balance = {}
        self.total = 0
        json_asset_wallet = create_request(session, "https://api.bitpanda.com", "/v1/asset-wallets", "GET", "Bitpanda")
        json_fiat_wallet = create_request(session, "https://api.bitpanda.com", "/v1/fiatwallets", "GET", "Bitpanda")
        json_ticker = create_request(session, "https://api.bitpanda.com", "/v2/ticker", "GET", "Bitpanda")
        json_ticker = self.prepare_ticker(json_ticker)
        self.parse_fiat_wallet(json_fiat_wallet, total_balance)
        self.parse_asset_wallet(json_asset_wallet, total_balance)
        
        self.waybar_tooltip = {}
        self.wcs_space = 0
        self.wvar_space = 0

        for k, v in total_balance.items():
            if v:
                for kx, vx in v.items():
                    try:
                        exchange_rate = json_ticker[kx][target_currency]
                        self.total += float(vx) * float(exchange_rate) 
                        if debug == True:
                            print(f'{kx}:{float(vx) * float(exchange_rate)}')
                        if waybar == True:
                            self.waybar_tooltip[kx] = ["%.2f" % round(float(vx) * float(exchange_rate), 2), exchange_rate]
                            if len(kx) > self.wcs_space:
                                self.wcs_space = len(kx)
                            if len(self.waybar_tooltip[kx][0]) > self.wvar_space:
                                self.wvar_space = len(self.waybar_tooltip[kx][0])
                    except:
                        print(f"Error: „{target_currency}\" currency not available.")
                        exit()

                    

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
                        #print(float(x["attributes"]["balance"]))
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


def prepare_waybar_tooltip(name, total, waybar_tooltip, waybar, wcs_space, wvar_space):
    if waybar == True:
        title_space = (int(wcs_space) + int(wvar_space) - 10) * " "
        wstring_tooltip = "<b>" + name + "</b>" + title_space + "<i><span color=\'gray\' rise=\'-1000\'>Total: " + str(round(total, 2)) + " " + target_currency + "</span></i>\n\n"
        sorted_waybar_tooltip = dict(sorted(waybar_tooltip.items(), key=lambda item: float(item[1][0]), reverse=True))
        for key, value in sorted_waybar_tooltip.items():
            cs_spaces = (wcs_space - len(key)) * " "
            var_spaces = (wvar_space - len(value[0])) * " "
            wstring_tooltip += f'{key}{cs_spaces} : {value[0]} {target_currency}{var_spaces} <span color=\'GreenYellow\' font-family=\'OpenSymbol\'>@</span> {value[1]}\n'
        output_text = f'₿ : {round(total, 2)} {target_currency}'
        output_dic = {"text":output_text,"tooltip":wstring_tooltip, "class":name}
        print(json.dumps(output_dic))
    else:
        print(f'₿ : {round(total, 2)} {target_currency}')

class KuCoin:
    def __init__(self, session, api_key: str, api_secret: str, api_passphrase: str):
        # ref https://www.kucoin.com/docs-new/authentication
        self.session = session or ""
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""
        self.api_passphrase = api_passphrase or ""
        self.ku_account_balance = {}
        self.ku_waybar_tooltip = {}

        if api_passphrase and api_secret:
            self.api_passphrase = self.sign(api_passphrase.encode('utf-8'), api_secret.encode('utf-8'))
            #self.json_data = create_request(session, "https://api.kucoin.com", "/api/v1/accounts/", "GET", self)
            self.fetch_account_balance()
            self.compare_ticker_with_account_balance()

        if not all([api_key, api_secret, api_passphrase]):
            print("API token is empty. Access is restricted to public interfaces only.")
    
    def fetch_account_balance(self):
        json_account_data = self.request("/api/v1/accounts/")
        for x in json_account_data["data"]:
            if int(x["balance"]) > 0:
                self.ku_account_balance[x["currency"]] = [x["balance"]]

    def compare_ticker_with_account_balance(self):
        json_ticker_data = self.request("/api/v1/market/allTickers")
        for y in self.ku_account_balance.keys():
            for x in json_ticker_data["data"]["ticker"]:
                if y in x["symbol"]:
                    for z in currencies:
                        if z in x["symbol"]:
                            currency = z
                    else:
                        if "BTC" in x["symbol"]:
                            currency = "BTC"
                    if currency:
                        self.ku_account_balance[y].append(f'[{x["symbol"]}, {currency}, {x["sell"]}, {x["vol"]}]')
        
        #There are multiple tickers; we fetch those with the highest volume. Initially, we convert the ticker currency using the fiat cover rate from Bitpanda.

                        #testa = float(self.ku_account_balance[y][0])*(float(x["sell"])*float(json_ticker[currency][target_currency]))
                        #self.ku_waybar_tooltip[y] = [testa]
                    #print(self.ku_account_balance["DCK"][1])

    def request(self, path):
        return create_request(session, "https://api.kucoin.com", path, "GET", self)

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

    api_key, target_currency, waybar = __init__()
    
    #print(signer)
    session = requests.Session()
    bp_data = Bitpanda(session, api_key, target_currency, waybar)
    ku_data = KuCoin(session, "", "", "")
    #print(ku_data.json_data)
    #ku_data = create_request(session, "https://api.kucoin.com", "/api/v1/accounts/", "GET", signer)
    #print(test)
    if waybar == True:
        prepare_waybar_tooltip("Bitpanda", bp_data.total, bp_data.waybar_tooltip, waybar, bp_data.wcs_space, bp_data.wvar_space)

