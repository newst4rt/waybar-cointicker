# CoinTicker for Waybar

CoinTicker is an open-source asset tracker and written in Python and developed for Waybar. Cointicker can be used as Waybar module or for other application supporting stdout output as display. 

`It works only with Bitpanda and Kucoin for now.`

## Requirment
- `requests`

## Getting Started


1. Initialize the set up and fill the prompts with the required data.
   
   ```
   python3 main.py init
   ```
   
2. Add the module in the Waybar configuration file and allign it to the desired direction.
   ```
   "custom/cointicker": {
        "exec": "python3 <path>/main.py",
        "on-click": "python3 <path>/main.py",
        "interval": 60,
        "return-type": "json",
        "format": "   {}"
   },
   ```

## Configuration

CoinTicker creates by itself a configuration file at start up after finishing the execution with the `init` parameter. For Linux it's necessary after changing the configuration manually to execute the `update` parameter to apply the settings.   

## Credits

It's one of my first programs, and it can definitely be written better. I created this tool for educational and personal purposes; feel free to use it under the GPLv3 license.

