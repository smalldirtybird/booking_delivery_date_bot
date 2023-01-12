#!/bin/bash
firefox --new-tab "$1" --profile "$2" --headless &
sleep 5
kill -9 $!
kill -9 $!
            