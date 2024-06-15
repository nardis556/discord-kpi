#!bin/bash

# check python scripts:
sleep 5

if pgrep -f "get_channel.py" > /dev/null
then
    echo "get_channel.py is running."
else
    echo "get_channel.py is not running. Starting get_channel.py"
    /home/lars/.pyenv/shims/python /home/lars/discord-kpi/scripts/get_channel.py &
fi