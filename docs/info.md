<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

Listens to ascii 'MARCO' and once detected, with 10us delay (mega fast) replies with '\n\rPOLO!\n\r'

## How to test

Connect with with your favourite UART gizmo, i used my PC and FTDI FT2232HQ USB-UART bridge builtin my ArtyS7 evaluation board.

with default putty serial settings 9600 bauds 
8 data bits 
1 stop bit 
parity NONE 

and type uppercase 'MARCO' trough UART RX pin
you should receive a '\n\rPOLO!\n\r' on UART TX pin

More meta signals exposed in order to perform the testing are
- baud_tick_rx (9600*8 bauds) and baud_tick_tx (9600bauds) 
- trigger_send active for one clck cycle on 'MARCO' match, and uartTxbusy active during the '\n\rPOLO!\n\r' transmission

## External hardware

probably a USB to TTL dongle like CP2102
