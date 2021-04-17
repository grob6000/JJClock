# JJ Clock
# Lots of love from George 2021

## INCLUDES ##
import pygame
import datetime
import os
import random
import math

## GLOBALS ##
pleasequit = False

## FUNCTIONS ##

## SCRIPT ##

pygame.init()
 
# Set the width and height of the screen [width, height]
screensize = (1448, 1072)

screen = pygame.display.set_mode(screensize)
 
pygame.display.set_caption("My Game")
 
# Loop until the user clicks the close button.
done = False
 
# Used to manage how fast the screen updates
clock = pygame.time.Clock()

localdir = os.path.dirname(os.path.realpath(__file__))
print(localdir)

while not pleasequit:
  	# handle events
	if pygame.event.peek(pygame.QUIT):
		pleasequit = True
	if pygame.event.peek(pygame.VIDEOEXPOSE) or pygame.event.peek(pygame.VIDEORESIZE):
		rerender = True
	pygame.event.clear()
    
    # --- Limit to 5 frames per second
	clock.tick(12)
    
# Close the window and quit.
pygame.quit()