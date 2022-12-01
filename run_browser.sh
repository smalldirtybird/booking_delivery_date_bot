#!/bin/bash
            firefox -profile "./browser_profile/" --new-tab "https://seller.ozon.ru/app/supply/orders?filter=SupplyPreparation" --headless &
            sleep 10
            kill -9 $!
            kill -9 $!
            