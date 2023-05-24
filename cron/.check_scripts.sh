#!bin/bash

# check python scripts:
sleep 5

if pgrep -f "discord_main.py" > /dev/null
then
    echo "discord_main.py is running."
else
    echo "discord_main.py is not running. Starting discord_main.py"
    /home/$USER/.pyenv/shims/python /home/$USER/discord-kpi/scripts/discord_main.py &
fi
