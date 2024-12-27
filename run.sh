#!/usr/bin/with-contenv bashio
echo "##############################################"
echo "##       "`date`"       ##"
echo "##############################################"

nginx

echo "{" > /plc_network/mqtt.json
echo '  "mqttserver": "'`bashio::services mqtt "host"`'",' >> /plc_network/mqtt.json
echo '  "mqttport": '`bashio::services mqtt "port"`',' >> /plc_network/mqtt.json
echo '  "mqttusername": "'`bashio::services mqtt "username"`'",' >> /plc_network/mqtt.json
echo '  "mqttpassword": "'`bashio::services mqtt "password"`'"' >> /plc_network/mqtt.json
echo "}" >> /plc_network/mqtt.json

DEBUG=$(bashio::config 'debug')
if [ $DEBUG == "true" ]
then
    echo `date +[%Y-%m-%d\ %H:%M:%S]`' DEBUG run.sh: Generated mqtt.json'
    ls -la /plc_network/mqtt.json
    cat /plc_network/mqtt.json
    echo `date +[%Y-%m-%d\ %H:%M:%S]`' DEBUG run.sh: Executing plc_network.py'
fi

python3 /plc_network/plc_network.py
