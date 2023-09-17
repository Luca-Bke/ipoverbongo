import socket
import sys
import time
import yaml
import RPi.GPIO as GPIO
import atexit
from bitarray import bitarray 

def on_exit():
    GPIO.output(conifg["READER"]["GPIO_PINS"]["ONE"], 0)
    GPIO.output(conifg["READER"]["GPIO_PINS"]["ZERO"], 0)
    GPIO.output(conifg["READER"]["GPIO_PINS"]["STATUS"], 1)
    if(get_state() == "sending"):        
        set_state("ready")
    print("exiting now, goodbye")



def set_state(state:str):
    print("Setting device to state:", state)
    with open('status.txt', 'w') as f:
        f.write(state)

def get_state():
    with open('status.txt', 'r') as f:
        state = f.read()
        print("Got device state:",state)
        return state



def ip_bytes_to_string(adress_bytes):
    return "{}.{}.{}.{}".format(int.from_bytes(adress_bytes[0:1],"little"),int.from_bytes(adress_bytes[1:2],"little"),int.from_bytes(adress_bytes[2:3],"little"),int.from_bytes(adress_bytes[3:4],"little"))


with open("/home/th-owl/IPoB/config.yaml", "r") as stream:
    try:
        conifg = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        exit()



interface = conifg["READER"]["INTERFACE_NAME"]
transmit_freq = conifg["READER"]["TRANSMIT_FREQUENCY"]
transmit_hold_time = conifg["READER"]["HOLD_TIME"]
transmit_delay= 1/transmit_freq - transmit_hold_time

routing_net_adress = socket.inet_aton(conifg["READER"]["ROUTING"]["IP_NET"])





#Create Subnetmask from CIDR-Suffix
routing_net_mask = 0
routing_net_suffix = conifg["READER"]["ROUTING"]["IP_SUFFIX"]
for i in range(0, routing_net_suffix):
    routing_net_mask = routing_net_mask << 1
    routing_net_mask = routing_net_mask | 1
if(32 - routing_net_suffix > 0):
    routing_net_mask = routing_net_mask << 32 - routing_net_suffix



GPIO.setmode(GPIO.BCM)

GPIO.setup(int(conifg["READER"]["GPIO_PINS"]["STATUS"]), GPIO.OUT)
GPIO.setup(int(conifg["READER"]["GPIO_PINS"]["ONE"]), GPIO.OUT)
GPIO.setup(int(conifg["READER"]["GPIO_PINS"]["ZERO"]), GPIO.OUT)

# GPIO.setup(20, GPIO.IN)
# GPIO.setup(21, GPIO.IN)
atexit.register(on_exit)
GPIO.output(conifg["READER"]["GPIO_PINS"]["STATUS"], 1)


print("Running on Interface: ",interface)
print("Routing Network: ",conifg["READER"]["ROUTING"]["IP_NET"], "/", routing_net_suffix,sep="")

# Create a UDP socket
rawSocket = socket.socket(socket.PF_PACKET, socket.SOCK_DGRAM, socket.htons(0x0800))
rawSocket.bind((interface,0))
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

print("Waiting for packets...\n\n\n")
GPIO.output(conifg["READER"]["GPIO_PINS"]["STATUS"], 0)

while True:
    if("ready" in get_state()):
        # read a packet with recvfrom method
        pkt = rawSocket.recvfrom(65536) # tuple retur

        if(pkt[1][0] == interface):
            rawpaket = pkt[0]
            print("\n\n++++++++++++++++++++++++++++++++++\n")
            print("Paket empfangen:")
            print("Ziel-IP-Adresse:", ip_bytes_to_string(rawpaket[16:20]))
            
            print("Quell-IP-Adresse:", ip_bytes_to_string(rawpaket[12:16]))
            print("\n")

            destination_ip_bytes = rawpaket[16:20]
            clean_routing_net_adress= int.from_bytes(routing_net_adress,"big") & routing_net_mask
            clean_packet_destination_net_adress = int.from_bytes(destination_ip_bytes,"big") & routing_net_mask

            if clean_routing_net_adress == clean_packet_destination_net_adress:
                set_state("sending")
                print("Paket wird genutzt")
                bit_array = bitarray()
                bit_array.frombytes(rawpaket)
                
                print("----------------------")
                print(pkt[1])
                print(rawpaket.hex())
                print("+++++++++++++++++")
                print(bit_array)
                print("")


                version = int.from_bytes(rawpaket[0:1], byteorder='big') >> 4
                print("Version:", version)
                
                header_length = int.from_bytes(rawpaket[0:1], byteorder='big') & 0xF
                print("Headerlänge:", header_length * 32, "bit")
                
                packet_length = int.from_bytes(rawpaket[2:4], byteorder='big')
                print("Packetlänge:", packet_length)
                
                identifier = int.from_bytes(rawpaket[4:6], byteorder='big')
                print("Kennung:", identifier)
                
                protocol = int.from_bytes(rawpaket[9:10], byteorder='big')
                print("Protokoll:", protocol)

                print("\n")

                packet_converterd = int.from_bytes(rawpaket, byteorder='big')

                for i in range(0,len(bit_array)):
                    print(i,bit_array[i])
                    if(bit_array[i] == 1):
                        GPIO.output(conifg["READER"]["GPIO_PINS"]["ONE"], 1)
                        time.sleep(transmit_hold_time)
                        GPIO.output(conifg["READER"]["GPIO_PINS"]["ONE"], 0)
                        
                    else:
                        GPIO.output(conifg["READER"]["GPIO_PINS"]["ZERO"], 1)
                        time.sleep(transmit_hold_time)
                        GPIO.output(conifg["READER"]["GPIO_PINS"]["ZERO"], 0)
                    time.sleep(transmit_delay)

                print("\n----------------------")
                set_state("ready")
                time.sleep(5)
            else:
                print("Paket wird verworfen")
    else:
        time.sleep(1)