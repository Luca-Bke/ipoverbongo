import pyaudio
import numpy as np
import time
import wave
from bitarray import bitarray
import socket
import atexit



# open stream
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

CHUNK = 8192 # RATE / number of updates per second

# use a Blackman window
window = np.blackman(CHUNK)


x = 0
started = True
detected = False
freq_array = []
vol_array = []
counter = 0
bit_array = bitarray()
packet_length = 6
last_volume = 0
max_volume = 0


def on_exit():
    if(get_state() == "listening"):        
        set_state("ready")
    print("exiting now, goodbye")


def set_state(state:str):
    print("Setting device to state:", state)
    with open('status.txt', 'w') as f:
        f.write(state)

def get_state():
    with open('status.txt', 'r') as f:
        state = f.read()
        # print("Got device state:",state)
        return state


atexit.register(on_exit)

s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

def ip_bytes_to_string(adress_bytes):
    return "{}.{}.{}.{}".format(int.from_bytes(adress_bytes[0:1],"little"),int.from_bytes(adress_bytes[1:2],"little"),int.from_bytes(adress_bytes[2:3],"little"),int.from_bytes(adress_bytes[3:4],"little"))


def analyse_sound(stream):
    global detected,counter,freq_array,vol_array,packet_length,last_volume,max_volume,started
    t1=time.time()
    data = stream.read(CHUNK, exception_on_overflow=False)
    waveData = wave.struct.unpack("%dh"%(CHUNK), data)
    npArrayData = np.array(waveData)
    indata = npArrayData*window

    fftData=np.abs(np.fft.rfft(indata))
    which = fftData[1:].argmax() + 1

    if which != len(fftData)-1:
        y0,y1,y2 = np.log(fftData[which-1:which+2:])
        x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)

        thefreq = (which+x1)*RATE/CHUNK
        #print(max(fftData),max(fftData) - last_volume)

        #
        # print(max(fftData) - last_volume)
        if(started):
            started = False
            last_volume = max(fftData)
        print(max(fftData), (max(fftData) - last_volume), last_volume)
        if(max(fftData) > 15000 and (max(fftData) - last_volume) > 20000 and detected == False):
            detected = True
#            print("Ton Beginn", max(fftData))
            freq_array.append(thefreq)
            vol_array.append(max(fftData))
            #print(max(fftData))

            if(max_volume < max(fftData)):
                max_volume = max(fftData)
            
        elif((max_volume - max(fftData)) > 35000 and detected == True):
#            print("Ton Ende",  max(fftData))

            if(np.mean(freq_array) < 290):
                bit_array.append(0)
                print(len(bit_array),"0", np.mean(freq_array),freq_array,vol_array ,bit_array)
            else: 
                bit_array.append(1)
                print(len(bit_array),"1", np.mean(freq_array),freq_array,vol_array ,bit_array)





            # resetting and counting
            detected = False
            freq_array.clear()
            vol_array.clear()
            max_volume = 0
            counter += 1
            
            

            # archievemnts based on transmit progress

            if(len(bit_array) == 1):
                set_state("listening")
            if(len(bit_array) == 32):
            
                packet_length = int.from_bytes(bit_array.tobytes()[2:4], byteorder='big')
                print("Packetlänge:", packet_length)
                print("Lenght of Paket:",bit_array.tobytes().hex())
                print(bit_array)
            elif(len(bit_array) == 160):
                print("Ziel-IP-Adresse:", ip_bytes_to_string(bit_array.tobytes()[16:20]))
            elif(len(bit_array) == packet_length*8):
                print("Paketende", bit_array.tobytes().hex())

                s.sendto(bit_array.tobytes(), (ip_bytes_to_string(bit_array.tobytes()[16:20]), 0))
                bit_array.clear()
                set_state("ready")
                time.sleep(1)

        elif(detected == True):
            # print(max_volume - max(fftData),  max(fftData))
            freq_array.append(thefreq)
            vol_array.append(max(fftData))

            if(max_volume < max(fftData)):
                max_volume = max(fftData)


        last_volume = max(fftData)


        # if(max(fftData) >15000 and ("ready" in get_state() or "listening" in get_state()) and detected == False):
        #     if(max_volume < max(fftData)):
        #         max_volume = max(fftData)
        #         print("new max volume",max_volume)
        #     if(thefreq < 400):
        #         freq_array.append(thefreq)
        #         # print(max(fftData),thefreq)
        #     if detected == False:
        #         detected = True
        #         print("Start of Tone")
        #     print("dif to max",(max_volume - max(fftData)))
        # elif((max_volume - max(fftData)) > 30000 and detected == True):
        #     # print(max(fftData))
        #     detected = False
        #     # print(np.mean(freq_array))
        #     # print(freq_array)
        #     max_volume = 0
        #     if(np.mean(freq_array) < 290):
        #         bit_array.append(0)
        #         print(len(bit_array),"0",bit_array)
        #     else: 
        #         bit_array.append(1)
        #         print(len(bit_array),"1",bit_array)
            
        #     freq_array.clear()
        #     if(len(bit_array) == 1):
        #         set_state("listening")
        #     if(len(bit_array) == 32):
            
        #         packet_length = int.from_bytes(bit_array.tobytes()[2:4], byteorder='big')
        #         print("Packetlänge:", packet_length)
        #         print("Lenght of Paket:",bit_array.tobytes().hex())
        #         print(bit_array)
        #     elif(len(bit_array) == 160):
        #         print("Ziel-IP-Adresse:", ip_bytes_to_string(bit_array.tobytes()[16:20]))
        #     elif(len(bit_array) == packet_length*8):
        #         print("Paketende", bit_array.tobytes().hex())

        #         s.sendto(bit_array.tobytes(), (ip_bytes_to_string(bit_array.tobytes()[16:20]), 0))
        #         bit_array.clear()
        #         set_state("ready")
        #         time.sleep(1)

    else:
        thefreq = which*RATE/CHUNK
        print("The freq is %f Hz." % (thefreq))




if __name__=="__main__":
    print("A1")
    p=pyaudio.PyAudio()
    print("A2")
    for i in range(p.get_device_count()):
        print(p.get_device_info_by_index(i))
    stream=p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True,
                  frames_per_buffer=CHUNK,input_device_index=1)

    print("Listening...")
    while True:
        analyse_sound(stream)

    stream.stop_stream()
    stream.close()
    p.terminate()