#!/bin/bash
SOCKS_PORT=${SOCKS_PORT:-9050}
CONTROL_PORT=${CONTROL_PORT:-9051}

sed "s/\${SOCKS_PORT}/$SOCKS_PORT/g; s/\${CONTROL_PORT}/$CONTROL_PORT/g" \
    /etc/tor/torrc.template > /etc/tor/torrc

su -s /bin/bash debian-tor -c "tor -f /etc/tor/torrc" &
sleep 5
python3 /app/api.py
