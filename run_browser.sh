#!/bin/bash
            firefox -profile "/home/drew/.mozilla/firefox/0q26uo9f.default/" --new-tab "https://seller.ozon.ru/app/supply/orders?filter=SupplyPreparation" --headless &
            sleep 10
            kill -9 $!
            kill -9 $!
            