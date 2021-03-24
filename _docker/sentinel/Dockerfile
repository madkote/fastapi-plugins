FROM redis:5
LABEL maintainer="madkote(at)bluewin.ch"
EXPOSE 26379

ENV SENTINEL_QUORUM 2
ENV SENTINEL_DOWN_AFTER 5000
ENV SENTINEL_FAILOVER 10000
# ENV SENTINEL_MASTER mymaster

ADD sentinel.conf /etc/redis/sentinel.conf
RUN chown redis:redis /etc/redis/sentinel.conf

ADD entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]

# ENV SENTINEL_PORT 26000
