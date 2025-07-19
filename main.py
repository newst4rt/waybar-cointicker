#!/usr/bin/env python
import urllib.request
import brotli
import json


total_balance = {}
total_balance["fiat_wallet"] = {}
target_currency = "EUR"
total = 0
debug = False
waybar = True

API_KEY = ""
missing_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "X-Api-Key": API_KEY

}


def create_request(site):
    request_params = urllib.request.Request(
        url=site, 
        headers=missing_headers
    )
    req_url = urllib.request.urlopen(request_params).read()
    decode_data = brotli.decompress(req_url)
    json_data = json.loads(decode_data)
    return json_data


def parse_fiat_wallet(json_data):
    for item in json_data["data"]:
        if float(item["attributes"]["balance"]) != 0.0 and item:
            total_balance["fiat_wallet"][item["attributes"]["fiat_symbol"]] = item["attributes"]["balance"]

def prepare_ticker(json_data):
    ext_currency = ["EUR", "GBP", "CHF", "TRY", "PLN", "HUF", "CZK", "SEK", "DKK", "RON", "BGN"]
    currency = ["CHF", "TRY", "PLN", "HUF", "CZK", "SEK", "DKK", "RON", "BGN"]
    json_ticker["EUR"] = json_ticker["BCPEUR"]
    json_ticker["USD"] = json_ticker["BCPUSD"]
    json_ticker["GBP"] = json_ticker["BCPGBP"]
    for x in currency:
        json_ticker[x] = {}
        value = 1/float(json_ticker["USD"][x])
        json_ticker[x]["USD"] = value
        for y in ext_currency:
            y_value = float(json_ticker["USD"][y])*value
            json_ticker[x][y] = "%.4f" % round(y_value, 4)


    return json_data



    

def parse_asset_wallet(json_data):
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



if __name__ == "__main__":
    json_asset_wallet = create_request("https://api.bitpanda.com/v1/asset-wallets")
    json_fiat_wallet = create_request("https://api.bitpanda.com/v1/fiatwallets")
    json_ticker = create_request("https://api.bitpanda.com/v2/ticker")
    json_ticker = prepare_ticker(json_ticker)
    parse_fiat_wallet(json_fiat_wallet)
    parse_asset_wallet(json_asset_wallet)

    if waybar == True:
        waybar_tooltip = {}
        waybar_count = 0

    for k, v in total_balance.items():
        if v:
            for kx, vx in v.items():
                try:
                    exchange_rate = json_ticker[kx][target_currency]
                    if debug == True:
                        print(f'{kx}:{float(vx) * float(exchange_rate)}')
                    if waybar == True:
                        waybar_tooltip[kx] = "%.2f" % round(float(vx) * float(exchange_rate), 2)
                        if len(kx) > waybar_count:
                            waybar_count = len(kx)
                except:
                    print(f"Error: „{target_currency}\" currency not available.")
                    exit()

                total += float(vx) * float(exchange_rate) 


    if waybar == True:
        wstring_tooltip = ""
        sorted_waybar_tooltip = dict(sorted(waybar_tooltip.items(), key=lambda item: float(item[1]), reverse=True))
        for key, value in sorted_waybar_tooltip.items():
            spaces = (waybar_count - len(key)) * " "
            wstring_tooltip += f'{key}{spaces} : {value} {target_currency}\n'
        output_text = f'₿ : {round(total, 2)} {target_currency}'
        test_dic = {"text":output_text,"tooltip":wstring_tooltip,"class":"bitpanda"}
        print(json.dumps(test_dic))
    else:
        print(f'₿ : {round(total, 2)} {target_currency}')

