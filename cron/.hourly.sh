#!bin/bash

# check python scripts:
sleep 5

if pgrep -f "summarize_channels.py" > /dev/null
then
    echo "summarize_channels.py is running."
else
    echo "summarize_channels.py is not running. Starting summarize_channels.py"
    /home/$USER/.pyenv/shims/python /home/$USER/discord-kpi/scripts/summarize_channels.py &
fi

if pgrep -f "summarize_user_activity.py" > /dev/null
then
    echo "summarize_user_activity.py is running."
else
    echo "summarize_user_activity.py is not running. Starting summarize_user_activity.py"
    /home/$USER/.pyenv/shims/python /home/$USER/discord-kpi/scripts/summarize_user_activity.py &
fi
