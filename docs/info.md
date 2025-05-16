<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

Listens to ascii 'MARCO\n' and once detected, it replies with 'POLO! :D\n\r'

## How to test

Connect with default putty serial settings 115200bauds 
8 data bits 
1 stop bit 
parity NONE 

and type uppercase 'MARCO'+ press enter (which sends an extra '\n') trough UART RX
you should receive a 'POLO! :D\n\r' on UART TX

## External hardware

List external hardware used in your project (e.g. PMOD, LED display, etc), if any
