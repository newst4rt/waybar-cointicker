#!/usr/bin/env python
import urllib.request
import brotli
import json
import configparser
import os
import sys

total_balance = {}
total = 0
debug = False
currencies = ["USD", "EUR", "GBP", "CHF", "TRY", "PLN", "HUF", "CZK", "SEK", "DKK", "RON", "BGN"]
header = {
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    }

def startup():

    ram_access = False
    config = configparser.ConfigParser()
    config_path = os.getcwd() + "/config_bitpanda.ini"
    if os.path.isfile("/dev/shm/config_bitpanda.ini") == True:
        ram_access = True
    else:
        if os.path.isfile(config_path) == False:
            import shutil
            print("Setup Bitpanda Configuration\n")
            API_KEY = str(input("API-KEY: "))
            if not API_KEY:
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
            
            config['DEFAULT'] = {"API_KEY": API_KEY,
                            "target_currency": target_currency,
                            "waybar": waybar}
            with open('config_bitpanda.ini', 'w') as configfile:
                config.write(configfile)
                print(f"Configuration file has been written to: {os.getcwd()}/config_bitpanda.ini")
            try:
                shutil.copy(os.getcwd() + "/config_bitpanda.ini", "/dev/shm/config_bitpanda.ini")
            except:
                pass

    if ram_access == True:
        config.read("/dev/shm/config_bitpanda.ini")
    else:
        config.read(config_path)
        
    API_KEY = config['DEFAULT']['API_KEY']
    target_currency = config['DEFAULT']['target_currency']
    waybar = config['DEFAULT']['waybar']
    header["X-Api-Key"] = API_KEY
    
    return [str(API_KEY), str(target_currency), bool(waybar)]

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


def create_request(site):
    request_params = urllib.request.Request(
        url=site, 
        headers=header
    )
    req_url = urllib.request.urlopen(request_params).read()
    decode_data = brotli.decompress(req_url)
    json_data = json.loads(decode_data)
    return json_data

def parse_fiat_wallet(json_data):
    total_balance["fiat_wallet"] = {}
    for item in json_data["data"]:
        if float(item["attributes"]["balance"]) != 0.0 and item:
            total_balance["fiat_wallet"][item["attributes"]["fiat_symbol"]] = item["attributes"]["balance"]

def prepare_ticker(json_data):
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


    return json_data

def parse_asset_wallet(json_data):
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


if __name__ == "__main__":

    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "reset":
            reset()
        elif sys.argv[1].lower() == "udate":
            update()

    API_KEY, target_currency, waybar = startup()

    json_asset_wallet = create_request("https://api.bitpanda.com/v1/asset-wallets")
    json_fiat_wallet = create_request("https://api.bitpanda.com/v1/fiatwallets")
    json_ticker = create_request("https://api.bitpanda.com/v2/ticker")
    json_ticker = prepare_ticker(json_ticker)
    parse_fiat_wallet(json_fiat_wallet)
    parse_asset_wallet(json_asset_wallet)

    if waybar == True:
        waybar_tooltip = {}
        wcs_space = 0
        wvar_space = 0

    for k, v in total_balance.items():
        if v:
            for kx, vx in v.items():
                try:
                    exchange_rate = json_ticker[kx][target_currency]
                    if debug == True:
                        print(f'{kx}:{float(vx) * float(exchange_rate)}')
                    if waybar == True:
                        waybar_tooltip[kx] = ["%.2f" % round(float(vx) * float(exchange_rate), 2), exchange_rate]
                        if len(kx) > wcs_space:
                            wcs_space = len(kx)
                        if len(waybar_tooltip[kx][0]) > wvar_space:
                            wvar_space = len(waybar_tooltip[kx][0])
                        
                except:
                    print(f"Error: „{target_currency}\" currency not available.")
                    exit()

                total += float(vx) * float(exchange_rate) 

    if waybar == True:
        wstring_tooltip = ""
        sorted_waybar_tooltip = dict(sorted(waybar_tooltip.items(), key=lambda item: float(item[1][0]), reverse=True))
        for key, value in sorted_waybar_tooltip.items():
            cs_spaces = (wcs_space - len(key)) * " "
            var_spaces = (wvar_space - len(value[0])) * " "
            wstring_tooltip += f'{key}{cs_spaces} : {value[0]} {target_currency}{var_spaces} <span color=\'GreenYellow\' font-family=\'OpenSymbol\'>@</span> {value[1]}\n'
        output_text = f'₿ : {round(total, 2)} {target_currency}'
        test_dic = {"text":output_text,"tooltip":wstring_tooltip,"class":"bitpanda"}
        print(json.dumps(test_dic))
    else:
        print(f'₿ : {round(total, 2)} {target_currency}')

