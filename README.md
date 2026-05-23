# Flash-Race

Using python 3.14

It need the libraries below to run:

import pygame #may need to pip install, not built-in (python -m pip install pygame)

import random

import sys

import csv

import os

from collections

Please download the whole 9001Asign3 folder,resource file are required.
To run the game just directly run flash-race.py.

Game Window will be 1200*900pixel

At lease a 1920*1080pixel screen device required,and pls turn windows Scale to 100% for a 1080p device

otherwise the display may be incomplete.

Thank you for reading!

Have Fun ^^!

To adjust difficulty, we can change line 427 of flash-race.py

            # self.base_speed = 8 + int((self.score ** 1.2) // 20)
            
the constant 8 is the init speed when game start, higher will be harder.

the formula after + is the increasing difficulty by score growing

# Control:

# A D or < > to control car go left or right

# SPACE bar for using nitro


# All game visual sprites (car, rock, coin, shield, background) were generated using gemini.photo generater.

# For Easier Code Reading, I also translated my Chinese annotations into English.
