#!python3
# -*- coding: utf-8 -*-
from datetime import datetime
from json import dumps, load, dump
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from os import path
import paho.mqtt.client as mqtt
from pathlib import Path
from subprocess import run
from sys import _getframe
from time import sleep

LogFile=path.join(path.dirname(path.realpath(__file__)), path.splitext(path.basename(__file__))[0]+'.log')
LogLevel=INFO #.DEBUG .INFO .WARNING .ERROR .CRITICAL
if not path.isfile('/data/options.json'):
    LogLevel=DEBUG
with open('/data/options.json') as JsonFile:
    Data = load(JsonFile)
    if str(Data['debug']).lower() == "true":
        LogLevel=DEBUG
CLEAN_SESSION=True
QOS=0

def AvailableNetworkInterfaces():
    DefName=_getframe( ).f_code.co_name
    CommandArguments=['/sbin/ip', 'a']
    logger.debug(DefName+'(): CommandArguments='+str(CommandArguments))
    CommandExecution=run(CommandArguments, capture_output=True, text=True)
    StdOut=CommandExecution.stdout.strip()
    StdError=CommandExecution.stderr.strip()
    if StdError != '':
        logger.critical(DefName+'(): StdError=\n'+str(StdError))
        exit()
    logger.debug(DefName+'(): Looking for interfaces ...')
    Interfaces=[]
    InterfaceName=''

    for Line in StdOut.splitlines():
        #logger.debug(DefName+'(): Line='+str(Line))
        if 'mtu' in Line:
            if InterfaceName != '':
                Interfaces.append(InterfaceName)
                InterfaceName=''
            InterfaceName=Line.split(' ')[1].replace(':','')
            #logger.debug(DefName+'(): interface detected '+InterfaceName)
            
    if InterfaceName != '':
        Interfaces.append(InterfaceName)
    logger.debug(DefName+'(): Interfaces='+str(Interfaces))
    return Interfaces

def GenerateJsonFile(Elements):
    DefName=_getframe( ).f_code.co_name
    Nodes=[]
    NodeNumber=1
    NodeCentral=''
    for Element in Elements:
        Nodes.append({"id": Element['sensor_name'], "group": str(NodeNumber)})
        NodeNumber=NodeNumber+1
        if Element['rx'] == 0 and Element['tx'] == 0:
            NodeCentral=Element['sensor_name']
    if NodeCentral == '':
        print('ERROR empty NodeCentral')

    Links=[]
    for Element in Elements:
        if Element['sensor_name'] != NodeCentral:
            Links.append({'source': NodeCentral, 'target': Element['sensor_name'], 'tx': Element['tx'], 'rx': Element['rx']})

    with open('/plc_network/web.json', 'w', encoding='utf-8') as f:
        dump({'reload': MainSleep,'nodes': Nodes, 'links': Links}, f, ensure_ascii=False, indent=4)

def GetElementsFromPLCStats(InforFromPLCStat):
    DefName=_getframe( ).f_code.co_name
    Elements=[]
    for Line in InforFromPLCStat.splitlines():
        if 'P/L NET TEI ------ MAC ------ ------ BDA ------  TX  RX CHIPSET FIRMWARE' not in Line:
            Components=' '.join(Line.split()).split(' ')
            #logger.debug(DefName+'(): Components='+str(Components))
            Element={}
            Element['mac']=Components[3]
            Element['sensor_name']='PLC-'+Element['mac'].replace(':','')
            Element['role']=Components[1]
            try:
                Element['sw_version']=Components[8]
            except:
                Element['sw_version']='Unknown'
            try:
                Element['hw_version']=Components[7]
            except:
                Element['hw_version']='Unknown'
            if Components[5] == 'n/a':
                Element['tx']=0
            else:
                Element['tx']=int(Components[5])
            if Components[6] == 'n/a':
                Element['rx']=0
            else:
                Element['rx']=int(Components[6])
            if Element['sw_version']=='Unknown' and Element['hw_version']=='Unknown':
                Element['status']='off'   
            else:
                Element['status']='on'   
            logger.debug(DefName+'(): Element from OS='+str(Element))
            Elements.append(Element)
    return Elements

def GetInfoFromPLCStat():
    DefName=_getframe( ).f_code.co_name
    CommandArguments=['/usr/bin/plcstat', '-t', '-i', Interface]
    logger.debug(DefName+'(): CommandArguments='+str(CommandArguments))
    CommandExecution=run(CommandArguments, capture_output=True, text=True)
    StdOut=CommandExecution.stdout.strip()
    StdError=CommandExecution.stderr.strip()
    if StdError != '':
        logger.critical(DefName+'(): StdError=\n'+str(StdError))
        exit()
    return StdOut

def GetPayLoadData(Element):
    PayLoadData={
        "rx":int(Element['rx']),
        "tx":int(Element['tx']),
        "role":Element['role']
    }
    return PayLoadData

def GetPayLoadDeviceAndTx(Element):
    DefName=_getframe( ).f_code.co_name
    PayLoadDeviceAndTx={
        "name": "Tx",
        "device_class":"data_rate",
        "state_topic":"homeassistant/sensor/"+Element['sensor_name']+"/state",
        "unit_of_measurement":"MB/s",
        "value_template":"{{ value_json.tx }}",
        "unique_id": "PLC_"+str(Element['mac']).replace(':','')+"_tx",
        "icon": "mdi:transmission-tower-import",
        "device":{
            "identifiers": [ "PLC_"+str(Element['mac']).replace(':','') ],
            "name": Element['sensor_name'],
            "serial_number": str(Element['mac']).replace(':',''),
            "hw_version": Element['hw_version'],
            "sw_version": Element['sw_version'],
            "configuration_url": "https://github.com/urri34/MyPLCNetwork",
            "manufacturer": "plcstat",
            "model": "MyPLCNetwork"
        }
    }
    return PayLoadDeviceAndTx

def GetPayLoadRole(Element):
    PayLoadRole={
        "name": "Role",
        "device_class":"enum",
        "state_topic":"homeassistant/sensor/"+Element['sensor_name']+"/state",
        "value_template":"{{ value_json.role }}",
        "unique_id": "PLC_"+str(Element['mac']).replace(':','')+"_role",
        "options": ["CCO", "STA", "Unknown"],
        "device":{
            "identifiers":[ "PLC_"+str(Element['mac']).replace(':','') ]
        }
    }
    return PayLoadRole

def GetPayLoadRx(Element):
    DefName=_getframe( ).f_code.co_name
    PayLoadRx={
        "name": "Rx",
        "device_class":"data_rate",
        "state_topic":"homeassistant/sensor/"+Element['sensor_name']+"/state",
        "unit_of_measurement":"MB/s",
        "value_template":"{{ value_json.rx }}",
        "unique_id": "PLC_"+str(Element['mac']).replace(':','')+"_rx",
        "icon": "mdi:transmission-tower-export",
        "device":{
            "identifiers":[ "PLC_"+str(Element['mac']).replace(':','') ]
        }
    }
    return PayLoadRx

def LoadVarsFromAddonConfig():
    DefName=_getframe( ).f_code.co_name
    global Broker, Port, UserName, Password, MainSleep, Interface

    if not path.isfile('/data/options.json'):
        logger.critical(DefName+'(): /data/options.json not present')
        exit()
    with open('/data/options.json') as JsonFile:
        try:
            Data = load(JsonFile)
            logger.debug(DefName+'(): /data/options.json is json valid')
        except:
            logger.critical(DefName+'(): /data/options.json has not a valid json structure')
            exit()
        try:
            MainSleep=Data['refresh']
            logger.debug(DefName+'(): MainSleep='+str(MainSleep))
        except:
            logger.critical(DefName+'(): /data/options.json has not entry for refresh')
            exit()
        try:
            Interface=str(Data['interface'])
        except:
            Interface='auto'
        logger.debug(DefName+'(): Interface='+str(Interface))

    if not path.isfile('/plc_network/mqtt.json'):
        logger.critical(DefName+'(): /data/mqtt.json not present')
        exit()
    with open('/plc_network/mqtt.json') as JsonFile:
        try:
            Data = load(JsonFile)
            logger.debug(DefName+'(): /plc_network/mqtt.json is json valid')
        except:
            logger.critical(DefName+'(): /plc_network/mqtt.json has not a valid json structure')
            exit()
        try:
            Broker=str(Data['mqttserver'])
            logger.debug(DefName+'(): Broker='+str(Broker))
        except:
            logger.critical(DefName+'(): /plc_network/mqtt.json has not entry for mpttserver')
            exit()
        try:
            Port=Data['mqttport']
            logger.debug(DefName+'(): Port='+str(Port))
        except:
            logger.critical(DefName+'(): /plc_network/mqtt.json has not entry for port')
            exit()
        try:
            UserName=str(Data['mqttusername'])
            logger.debug(DefName+'(): UserName='+str(UserName))
        except:
            logger.critical(DefName+'(): /plc_network/mqtt.json has not entry for mqttusername')
            exit()
        try:
            Password=str(Data['mqttpassword'])
            logger.debug(DefName+'(): Password='+str(Password))
        except:
            logger.critical(DefName+'(): /plc_network/mqtt.json has not entry for mqttpassword')
            exit()

        logger.info(DefName+'(): Vars from addon config file succesfully loaded.')
   
def MQTTOnConnect(client, userdata, flags, reason_code, properties=None):
    DefName=_getframe( ).f_code.co_name
    '''
    0: Connection successful
    1: Connection refused incorrect protocol version
    2: Connection refused invalid client identifier
    3: Connection refused server unavailable
    4: Connection refused bad username or password
    5: Connection refused not authorised
    6-255: Currently unused.
    '''
    logger.info(DefName+'(): Succesfully connected to MQTT with code='+str(reason_code))

def MQTTOnDisconnect(client, userdata, rc):
    DefName=_getframe( ).f_code.co_name
    logger.info(DefName+'(): Disconnected with result code '+str(str(rc).rsplit()))
    while True:
        try:
            client.reconnect()
            logger.info(DefName+'(): Reconnected successfully.')
            return
        except Exception as err:
            logger.info(DefName+'(): Reconnect failed with error="'+str(err)+'"')
        sleep(5)

def SendPayLoadToMQTTTopic(PayLoad, Topic, client):
    DefName=_getframe( ).f_code.co_name
    logger.debug(DefName+'(): PayLoad='+dumps(PayLoad, indent=1))
    logger.debug(DefName+'(): Topic='+str(Topic))
    logger.debug(DefName+'(): Return:'+str(client.publish(Topic,
                                    dumps(PayLoad),
                                    QOS)))

def SetInterface():
    DefName=_getframe( ).f_code.co_name
    MayBePhisycalInterfaces=[]
    for MayBePhisycalInterface in AvailableNetworkInterfaces():
        if MayBePhisycalInterface == 'lo':
            next
        elif MayBePhisycalInterface == 'hassio':
            next
        elif MayBePhisycalInterface.startswith('docker'):
            next
        elif MayBePhisycalInterface.startswith('veth'):
            next
        else:
            MayBePhisycalInterfaces.append(MayBePhisycalInterface)
    logger.debug(DefName+'(): MayBePhisycalInterfaces='+str(MayBePhisycalInterfaces))
    MayBePLCInterfaces=[]
    for MayBePLCInterface in MayBePhisycalInterfaces:
        CommandArguments=['/usr/bin/plcstat', '-t', '-i', MayBePLCInterface]
        logger.debug(DefName+'(): CommandArguments='+str(CommandArguments))
        CommandExecution=run(CommandArguments, capture_output=True, text=True)
        StdOut=CommandExecution.stdout.strip()
        if StdOut != '':
            logger.debug(DefName+'(): MayBeInterface='+str(MayBePLCInterface)+' with '+str(StdOut.count('\n'))+' elements.')
            MayBePLCInterfaces.append([str(MayBePLCInterface), StdOut.count('\n')])
        else:
            logger.debug(DefName+'(): MayBeInterface='+str(MayBePLCInterface)+' with no elements.')
    logger.debug(DefName+'(): MayBePLCInterfaces='+str(MayBePLCInterfaces))
    Interface=''
    InterfacePLCElements=0
    for MayBePLCInterface in MayBePLCInterfaces:
        if MayBePLCInterface[1] > InterfacePLCElements:
            Interface=MayBePLCInterface[0]
    if Interface=='':
        logger.critical(DefName+'():Unable to find a valid interface with PLC elements.')
        exit()
    return Interface

def SetMyLogger():
    from logging import getLogger, Formatter, StreamHandler
    from logging.handlers import RotatingFileHandler

    logger = getLogger()
    logger.setLevel(LogLevel)
    LogFormat = ('[%(asctime)s] %(levelname)-4s %(message)s')
    formatter = Formatter(LogFormat)

    file_handler = RotatingFileHandler(LogFile, mode="a", encoding="utf-8", maxBytes=1*1024*1024, backupCount=2)
    file_handler.setLevel(LogLevel)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stdout_handler = StreamHandler()
    stdout_handler.setLevel(LogLevel)
    stdout_handler.setFormatter(formatter)       
    logger.addHandler(stdout_handler)

    return logger

def ShowSendResume(Elements):
    DefName=_getframe( ).f_code.co_name
    Temp=[]
    for Element in Elements:
        Temp.append([Element['mac'].replace(':',''), Element['tx'],Element['rx']])
    logger.info(DefName+'(): Sending '+str(len(Elements))+' elements: '+str(Temp))
    del(Temp)

def main():
    DefName=_getframe( ).f_code.co_name
    global logger, Interface
    logger = SetMyLogger()
    logger.debug(DefName+'(): Logging active for me: '+str(Path(__file__).stem))

    logger.info(DefName+'(): Loading vars from addon config file ...')
    LoadVarsFromAddonConfig()

    if Interface == 'auto':
        Interface=SetInterface()
    else:
        Interface=Interface

    logger.info(DefName+'(): Connecting to MQTT ...')
    client = mqtt.Client(path.splitext(path.basename(__file__))[0]+'_'+str(datetime.now().strftime("%Y%m%d%H%M%S")), clean_session=CLEAN_SESSION)
    client.username_pw_set(UserName, Password)
    client.on_connect = MQTTOnConnect
    client.on_disconnect = MQTTOnDisconnect
    client.connect(Broker, Port)
    client.loop_start()

    while True:
        InforFromPLCStat=GetInfoFromPLCStat()
        logger.debug(DefName+'(): Loading elements from plcstat ...')
        Elements=GetElementsFromPLCStats(InforFromPLCStat)

        ShowSendResume(Elements)
        GenerateJsonFile(Elements)
        for Element in Elements:
            PayLoadDeviceAndTx=GetPayLoadDeviceAndTx(Element)
            Topic="homeassistant/sensor/"+Element['sensor_name']+"/tx/config"
            SendPayLoadToMQTTTopic(PayLoadDeviceAndTx, Topic, client)
            del(PayLoadDeviceAndTx)

            PayLoadRx=GetPayLoadRx(Element)
            Topic="homeassistant/sensor/"+Element['sensor_name']+"/rx/config"
            SendPayLoadToMQTTTopic(PayLoadRx, Topic, client)
            del(PayLoadRx)

            PayLoadRole=GetPayLoadRole(Element)
            Topic="homeassistant/sensor/"+Element['sensor_name']+"/role/config"
            SendPayLoadToMQTTTopic(PayLoadRole, Topic, client)
            del(PayLoadRole)
            PayLoadData=GetPayLoadData(Element)
            Topic="homeassistant/sensor/"+Element['sensor_name']+"/state"
            SendPayLoadToMQTTTopic(PayLoadData, Topic, client)
            del(PayLoadData)

        sleep(MainSleep)
    client.loop_stop()
    client.disconnect()

if __name__ == '__main__':
    main()
