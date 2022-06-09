import pygame
import serial
import numpy as np


stm32 = serial.Serial(
    port = '/dev/ttyTHS1',
    baudrate = 115200,
    # bytesize = serial.EIGHTBITS,
    # parity = serial.PARITY_NONE,
    # stopbits = serial.STOPBITS_ONE,
    timeout = 0,


)

pygame.init()
window = pygame.display.set_mode((300, 300))
pygame.display.set_caption("Pygame Demonstration")

turn=0
speed = 0
mainloop=True
while mainloop:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            mainloop = False

        if event.type == pygame.KEYDOWN:
            turn = np.clip(turn,-40,40)
            speed = np.clip(speed,-140,140)
            print(pygame.key.name(event.key))
            if pygame.key.name(event.key) == 'right':
                turn-=3
                stm32.write("T{0}".format(turn).encode())
            if pygame.key.name(event.key) == 'left':
                turn+=3
                stm32.write("T{0}".format(turn).encode())
            if pygame.key.name(event.key) == 'up':
                speed+=10
                stm32.write("S{0}".format(speed).encode())
            if pygame.key.name(event.key) == 'down':
                speed-=10
                stm32.write("S{0}".format(speed).encode())            
                
pygame.quit()