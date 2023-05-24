#!bin/bash

# check python scripts:
sleep 5

if pgrep -f "summarize_joins_and_leaves.py" > /dev/null
then
    echo "summarize_joins_and_leaves.py is running."
else
    echo "summarize_joins_and_leaves.py is not running. Starting summarize_joins_and_leaves.py"
    /home/lars/.pyenv/shims/python /home/lars/discord-kpi/scripts/summarize_joins_and_leaves.py &
fi
