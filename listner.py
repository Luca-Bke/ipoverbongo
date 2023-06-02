import socket
import sys
import time
import argparse






def get_bytes(array):
    if(len(array) >= 8):
        x = int(0)
        for i in range (0, len(array)):
            mask = 1 << i
            x = x | ((array[i] << i) & mask)
        return x.to_bytes(math.ceil(len(array)/8), byteorder='big')





parser = argparse.ArgumentParser()
parser.add_argument("-i", "--interface", help="Name of Network Interface")
parser.add_argument("-rn1", "--routingNet1", help="Adress of Net to be routed")
parser.add_argument("-rn2", "--routingNet2", help="Adress of Net to be routed")
parser.add_argument("-rn3", "--routingNet3", help="Adress of Net to be routed")
parser.add_argument("-rn4", "--routingNet4", help="Adress of Net to be routed")
args = parser.parse_args()




interface = args.interface
routing_net = [int(args.routingNet1), int(args.routingNet2), int(args.routingNet3), int(args.routingNet4)]
print(interface)
print(routing_net)

# Create a UDP socket
rawSocket = socket.socket(socket.PF_PACKET, socket.SOCK_DGRAM, socket.htons(0x0800))
rawSocket.bind((interface,0))
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

while True:

    # read a packet with recvfrom method
    pkt = rawSocket.recvfrom(65536) # tuple retur
    if(pkt[1][0] == interface):
        rawpaket = pkt[0]

        destination_ip = [0, 0, 0, 0]
        destination_ip[0] = int.from_bytes(rawpaket[16:17], byteorder='big')
        destination_ip[1] = int.from_bytes(rawpaket[17:18], byteorder='big')
        destination_ip[2] = int.from_bytes(rawpaket[18:19], byteorder='big')
        destination_ip[3] = int.from_bytes(rawpaket[19:20], byteorder='big')


        if(destination_ip[0] == routing_net[0] and destination_ip[1] == routing_net[1] and destination_ip[2] == routing_net[2] and destination_ip[3] >= routing_net[3]):
            
            source_ip = [0, 0, 0, 0]
            source_ip[0] = int.from_bytes(rawpaket[12:13], byteorder='big')
            source_ip[1] = int.from_bytes(rawpaket[13:14], byteorder='big')
            source_ip[2] = int.from_bytes(rawpaket[14:15], byteorder='big')
            source_ip[3] = int.from_bytes(rawpaket[15:16], byteorder='big')
            
            print("----------------------")
            print(pkt[1])
            print(rawpaket.hex())
            print("")
            print("Ziel-IP-Adresse:", destination_ip)
            print("Quell-IP-Adresse:", source_ip)


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

            print("")

            packet_converterd = int.from_bytes(rawpaket, byteorder='big')

            bit_array = []
            for i in range(0, len(rawpaket)*8-1):
                # Shift-Operator, um das gewünschte Bit an die niedrigste Position zu bringen
                shifted_value = packet_converterd >> i

                # Bitmaske, um nur das niedrigste Bit zu behalten
                result = shifted_value & 1
                
                print(i,result)
                bit_array.append(int(result))
                time.sleep(0.5)
            send_bytes = get_bytes(bit_array)

            print("----------------------")
            time.sleep(0)
            destination = '{}.{}.{}.{}'.format(destination_ip[0],destination_ip[1],destination_ip[2],destination_ip[3])
            s.sendto(send_bytes, (destination, 0))


