# wansfw
Tool for packing, unpacking and validating firmware files for Wansview IP Cameras.

### CAUTION
Tested on model NCB-541W firmwares only, it may work on others

### Unpacking
`./wansfw.py --unpack -i 51.3.0.152.bin`

Will unpack the target firmware's file system into `unpacked_51.3.0.152/`

### Packing
`./wansfw.py --pack -i custom_firmware/`

Will pack the target directory into `custom_firmware.bin`

### Check
`./wansfw.py --check -i firmware.bin`

Checks that the target firmware contains a valid head, tail and 4 byte length "check".
