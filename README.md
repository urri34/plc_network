# plc_network

Home assistant addon under development

# **<<<This addon has some <ins>physical</ins> restrictions>>>**. 

PLC have no ip, so we need to talk to them thru the mac address. And that means that the computer where we are executing plc_network addon needs to be physically connected to the PLC (in case you run plc_network addon in a virtual machine, the host needs to be connected to the PLC).

<p align="center">
  <img src="https://github.com/urri34/MyPLCNetwork/blob/main/Diagram.jpg#01" />
</p>

<p align="center">
  <img src="https://github.com/urri34/MyPLCNetwork/blob/main/Devolo.jpg" />
</p>

I'm using this devolo 550+ as my PLC standard. If I connect one ethernet coming from the router to one of those ports, and the access to my HA to the other one ... I will have internet access in the HA thru the router, access to LAN elements (Wi-Fi or wired) thru the router and access to LAN elements behind other PLCs thru the PLC.

This is the only diagram that will work. plc_network addon executed connected to a PLC.
