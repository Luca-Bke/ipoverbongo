import random
import math

array = []
for i in range(0, 180*8):
    ran = random.randint(0, 1)
    array.append(ran)

print(array)
print(len(array))
array = array[::-1]


def bytes_to_bits(byte_obj):
    bits = ''
    for byte in byte_obj:
        bits += bin(byte)[2:].zfill(8)  # Binäre Darstellung hinzufügen und auf 8 Bits auffüllen
    return bits

def get_bytes(array):
    if(len(array) >= 8):
        x = int(0)
        for i in range (0, len(array)):
            mask = 1 << i
            x = x | ((array[i] << i) & mask)
        return x.to_bytes(math.ceil(len(array)/8), byteorder='big')

bytes_obj = get_bytes(array)
print(bytes_to_bits(bytes_obj))
print(bytes_obj.hex())