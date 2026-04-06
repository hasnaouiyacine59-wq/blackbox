FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y tor python3 python3-pip --no-install-recommends \
    && pip3 install flask requests[socks] --break-system-packages \
    && rm -rf /var/lib/apt/lists/*

COPY torrc.template /etc/tor/torrc.template
COPY api.py /app/api.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV SOCKS_PORT=9050
ENV CONTROL_PORT=9051

EXPOSE ${SOCKS_PORT} ${CONTROL_PORT}

CMD ["/start.sh"]
