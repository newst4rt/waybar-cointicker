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
import re
from urllib.parse import urlencode
import hmac


total_balance = {}
total = 0
debug = False
currencies = ["USD", "EUR", "GBP", "CHF", "TRY", "PLN", "HUF", "CZK", "SEK", "DKK", "RON", "BGN"]
stablecoins = [["USDT", "USD"], ["USDC", "USD"], ["DAI", "USD"], ["TUSD", "USD"], ["BUSD", "USD"], ["USDP", "USD"], ["GUSD", "USD"], ["FDUSD", "USD"], ["PYUSD", "USD"], ["EURC", "EUR"], ["EURS", "EUR"], ["sUSD", "USD"], ["FRAX", "USD"], ["FRAXUSD", "USD"], ["USDS", "USD"], ["USDE", "USD"], ["DJED", "USD"], ["RSV", "USD"], ["USD1", "USD"], ["XAUt", "Gold"], ["PAXG", "Gold"], ["aUSD", "USD"], ["nUSD", "USD"], ["CUSD", "USD"], ["LUSD", "USD"], ["MIM", "USD"], ["HUSD", "USD"], ["AGEUR", "EUR"], ["SDAI", "USD"], ["MUSD", "USD"], ["VAI", "USD"], ["USDN", "USD"], ["ALUSD", "USD"], ["XUSD", "USD"]]
blacklisted_coins = []
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
        #output_text = f'₿ : {round(total, 2)} {target_currency}'
        return total, wstring_tooltip + "\n"
        #output_dic = {"text":output_text,"tooltip":wstring_tooltip, "class":name}
        #print(json.dumps(output_dic))
    else:
        print(f'₿ : {round(total, 2)} {target_currency}')

def print_waybar_tooltip(total, text):
    output_text = f'₿ : {round(total, 2)} {target_currency}'
    output_dic = {"text":output_text,"tooltip":text, "class":"Coin_Tracker"}
    print(json.dumps(output_dic))


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
            if float(x["balance"]) > 0:
                self.ku_account_balance[x["currency"]] = [x["balance"]]

    def compare_ticker_with_account_balance(self):
        json_ticker_data = self.request("/api/v1/market/allTickers")
        self.ku_waybar_tooltip = {}
        self.ku_total = 0
        for y in self.ku_account_balance.keys():
            sc_found = False
            for yx in stablecoins:
                if y in yx[0]:
                    self.ku_account_balance[y].append(["STABLECOIN", yx[1]])
                    sc_found = True 
                    break
            
            if sc_found == True:
                target_ticker = float(json_ticker[x[1]][target_currency])
                target_total = float(self.ku_account_balance[y][0])*float(target_ticker)
                self.ku_waybar_tooltip[y] = [str("%.2f" % round(target_total, 2)), str(target_ticker)]
                self.ku_total += target_total
                continue

            ku_asset_volume = 0
            for x in json_ticker_data["data"]["ticker"]:
                if re.match(rf"^{y}-", x["symbol"]):
                    for z in currencies:
                        if z in x["symbol"]:
                            currency = z
                    if currency:
                        tmp_volume = float(float(x["sell"])*float(x["vol"]))
                        self.ku_account_balance[y].append([x["symbol"], currency, x["sell"], x["vol"], tmp_volume])
                        if tmp_volume > ku_asset_volume:
                            ku_asset_volume = float(float(x["sell"])*float(x["vol"]))
            
            
            if 0 != ku_asset_volume:
                for x in self.ku_account_balance[y][1:]:
                    if x[4] == ku_asset_volume:
                        target_ticker = float(x[2])*float(json_ticker[x[1]][target_currency])
                        target_total = float(self.ku_account_balance[y][0])*float(target_ticker)
                        self.ku_waybar_tooltip[y] = [str("%.2f" % round(target_total, 2)) ,str(round(target_ticker, 4))] 
                        self.ku_total += target_total
                        #print(x)

        #self.convert_account_balance = {}
        #for key, value in self.ku_account_balance.items():
        #    print(value[1][2])
        #    print(json_ticker[value[1][1]][target_currency])
        #    self.ku_account_balance[key] = float(value[1][2])*float(json_ticker[value[1][1]][target_currency])

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
    
    #signer = KuCoin("687ff1a9dffe710001e65ce3", "35106d0f-02ec-4356-b840-532b4cd0e7b2", "Ue.E$\\gT)\\i&vS[os\\ln")
    #print(signer)
    session = requests.Session()
    bp_data = Bitpanda(session, api_key, target_currency, waybar)
    ku_data = KuCoin(session, "", "", "")
    #print(ku_data.json_data)
    #ku_data = create_request(session, "https://api.kucoin.com", "/api/v1/accounts/", "GET", signer)
    #print(test)
    if waybar == True:
        bit_total, bitpanda_tooltip = prepare_waybar_tooltip("Bitpanda", bp_data.total, bp_data.waybar_tooltip, waybar, bp_data.wcs_space, bp_data.wvar_space)
        ku_total, kucoin_tooltip = prepare_waybar_tooltip("KuCoin", round(ku_data.ku_total, 2), ku_data.ku_waybar_tooltip, waybar, bp_data.wcs_space, bp_data.wvar_space)
        print_waybar_tooltip(bit_total + ku_total, bitpanda_tooltip + kucoin_tooltip)

