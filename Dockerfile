ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache \
    python3 \
    open-plc-utils \
    py3-paho-mqtt \
    nginx

COPY run.sh /
RUN chmod a+x /run.sh

COPY ingress.conf /etc/nginx/http.d

COPY content /plc_network

WORKDIR /data
CMD [ "/run.sh" ]