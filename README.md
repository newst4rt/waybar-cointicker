<table align="center"><tr><td align="center" width="9999">
<img src="/img/logo.png" align="center" width="250">

# CoinTicker for Waybar
CoinTicker is an asset tracker, written in Python, developed for Waybar, and it can be used with other applications that support stdout output as a display.
<br></br>
</td></tr></table>

<p align="center">
<img src="/img/example_1.png" width="250">&nbsp;
<img src="/img/example_2.png" width="250"></p>

<p align="center"><b>Works only with Bitpanda and Kucoin for now.</b></p>




</div></td></tr></table>

## Requirment
- `requests`

## Getting Started


1. Start the setup and complete the prompts with the required information.
   
   ```
   python3 main.py init
   ```
   
2. Add the module to the Waybar configuration file and align it in the desired direction.
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

CoinTicker creates by itself a configuration file at start up after finishing the execution with the `init` parameter. For Linux it's necessary after changing the configuration manually to execute the `update` parameter to apply the settings. Use `reset` for deleting the current configuration.   

## Credits

It's one of my first programs, and it can definitely be written better. I created this tool for educational and personal purposes; feel free to use it under the GPLv3 license.

