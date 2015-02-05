#!/usr/bin/env python

import argparse, sys, os, struct, io, zipfile, zlib


HEADER = '''
                      __        
__ __ ____ _ _ _  ___/ _|_ __ __
\ V  V / _` | ' \(_-<  _\ V  V /
 \_/\_/\__,_|_||_/__/_|  \_/\_/ 
             by alex kaskasoli
                                     
Pack, Unpack and Check your custom firmware for Wansview IP Cameras

CAUTION: Tested on NCB-541W only, may work on others
'''


# Valid firmware files start with this string
FIRMWARE_HEAD = 'wifi-camera-sys-qetyipadgjlzcbmn'
# Valid firmware files end with this string
FIRMWARE_TAIL = 'wifi-camera-end-nvxkhfsouteqzhpo'



'''

	FUNCTION PACK()

		- First ZIP the target directory to a file-like object

		- Pack the length of the zip as an integer

		- Prepend HEAD + length

		- Append TAIL

		- Save to output file

'''

def pack(t_dir, o_file, verbose=False):

	# File object for holding the packed firmware
	firmware =  open(o_file, 'wb')

	'''
		ZIP TARGET FOLDER
	'''
	if verbose: print '\n [ i ] Zipping target directory...'
	# Temporary in-memory zip file
	zip_file = zipfile.ZipFile(firmware, mode='w')

	# Path length from the scripts directory to the target directory
	t_path_len = len(t_dir) + len(os.sep)

	for root, dirs, files in os.walk(t_dir):
		# We want to include directories
		# zip_file.write(target, destination), so we need to trim out the leading path from current dir
		dir_path = root[t_path_len:]
		if dir_path: zip_file.write(root, dir_path, zipfile.ZIP_DEFLATED)

		for file in files:
			# Full path to target
			file_path = os.path.join(root, file)
			# zip_file.write(target, destination), so we need to trim out the leading path from current dir
			zip_file.write(file_path, file_path[t_path_len:], zipfile.ZIP_DEFLATED)

	zip_file.close()

	firmware.close()

	'''
		PREPEND HEAD + LENGTH AND APPEND TAIL
	'''
	if verbose: print '\n [ i ] Adding file header and footer...'
	length = os.path.getsize(o_file)
	with open(o_file, 'rb') as firmware: contents = firmware.read()
	with open(o_file, 'wb') as firmware: firmware.write(FIRMWARE_HEAD + struct.pack('i', length) + contents + FIRMWARE_TAIL)
	

	# Check o_file is valid firmware
	if not validate_firmware(o_file, verbose):
		if verbose: print '\n [ ! ] Output file is corrupt or is not a firmware'
		return False
	if verbose: print '\n [ OK ] Output file appears to be a valid firmware'

	return True

'''
	### END PACK() ############################################################
'''



'''

	FUNCTION UNPACK()

		- Calls validate_firmware() to make sure the target is valid firmware

		- If target is valid:

			- Read ZIP content (skip first 36 and last 32 bytes)

			- Unzip ZIP content to output directory

		- If unpacking was successful: return True

'''

def unpack(t_file, o_file, verbose=False):

	# Check t_file is valid firmware
	if not validate_firmware(t_file, verbose):
		if verbose: print '\n [ ! ] Input file is corrupt or is not a firmware'
		return False
	if verbose: print '\n [ OK ] Input file appears to be a valid firmware'

	
	t_handle = open(t_file, 'rb')

	# Size to read is ( len(t_file) - 32 HEAD bytes - 4 length bytes - 32 TAIL bytes)
	size = os.path.getsize(t_file) - 68

	# Read contents as file-like object
	if verbose: print '\n [ i ] Fetching and unzipping zip file...'
	t_handle.seek(36)

	# Try to unzip the extracted zip_file
	try:
		with zipfile.ZipFile( io.BytesIO( t_handle.read(size) ) ) as zip_file:
			zip_file.extractall(o_file)
			if verbose: print '\n\t [ i ] Valid zip successfully extracted'
	except zipfile.BadZipfile:
		print '\n [ ! ] Bad Zip File: extracted file system doesn\'t appear to be a valid ZIP'
		return False

	t_handle.close()

	return True

'''
	### END UNPACK() ##########################################################
'''



'''

	FUNCTION VALIDATE_FIRMWARE()

		- Checks that the target file contains the HEAD and TAIL

		- Calculates the length of the contents and checks that it corresponds to
		  the four bytes after HEAD

		- Returns True if file looks like:

			HEAD		32 bytes
			length 		 4 bytes
			contents
			TAIL 		32 bytes

'''

def validate_firmware(t_file, verbose=False):

	if verbose: print '\n [ i ] Checking file ' + str(t_file) + '...'


	# Check the actual size on the system
	t_size = os.path.getsize(t_file)
	if verbose: print '\n\t [ i ] Size on disk ' + str(t_size) + ' bytes'


	t_handle = open(t_file, 'rb')


	# Check 'HEAD' (first 32 bytes)
	t_head = t_handle.read(32)

	if not t_head == FIRMWARE_HEAD:
		if verbose: print '\t [ ! ] Target does not contain a valid head'
		t_handle.close()
		return False
	if verbose: print '\t [ i ] Target contains a valid head'



	# Read the declared length of the contents (bytes 32-36)
	t_length = struct.unpack('i', t_handle.read(4))[0]
	if verbose: print '\t [ i ] Firmware declares size of ' + str(t_length) + ' bytes'

	# Read contents and calulate length
	t_contents = t_handle.read(t_size - 68)
	t_contents_length = len(t_contents)
	if verbose: print '\t [ i ] Calculated size of ' + str(t_contents_length) + ' bytes'

	# Check if lengths match
	if not t_contents_length == t_length:
		if verbose: print '\t [ ! ] Declared size and calculated size do not match!'
		t_handle.close()
		return False
	if verbose: print '\t [ i ] Sizes match'



	# Check the tail of the file (last 32 bytes)
	t_tail = t_handle.read(32)

	if not t_tail == FIRMWARE_TAIL:
		if verbose: print '\t [ ! ] Target does not contain a valid tail'
		t_handle.close()
		return False
	if verbose: print '\t [ i ] Target contains a valid tail'


	t_handle.close()


	return True

'''
	### END VALIDATE_FIRMARE() ################################################
'''



'''

	FUNCTION GET_ARGS()

		- Retrieves and parses command line arguments

		- Checks everything is valid

		- Returns args

'''

def get_args():

	parser = argparse.ArgumentParser(prog='wansfw')

	# Check if we're packing, unpacking or checking
	action = parser.add_mutually_exclusive_group(required=True)
	action.add_argument('-u', '--unpack', action='store_true', help='Unpack input firmware')
	action.add_argument('-p', '--pack', action='store_true', help='Pack input directory')
	action.add_argument('-c', '--check', action='store_true', help='Check validity of input firmware')

	# Input file or directory is mandatory
	parser.add_argument('-i', '--input', required=True, type=str, help='Input file or directory')
	
	# Output file or directory
	parser.add_argument('-o', '--output', type=str, help='Output file or directory')

	# Verbose
	parser.add_argument('-v', '--verbose', action='store_true', help='Output file or directory')

 	# Parse args
	args = parser.parse_args()


	# If we're unpacking, input needs to be a valid file (and set default output if none supplied)
	if args.unpack:
		if not os.path.isfile(args.input):
			parser.error('\n\tWhen unpacking, input needs to be a valid path to the firmware file')

		# When unpacking, if no output has been set, set output directory to 'unpacked_INPUTFILE'
		if not args.output:
			# If input file ends with '.bin', splitext[0] will only contain filename
			args.output = 'unpacked_' + args.input[:-4] if args.input.endswith('.bin') else args.input

	# If we're packing, input needs to be a valid directory (and set default output if none supplied)
	elif args.pack:
		args.input = args.input.rstrip('/')

		if not os.path.isdir(args.input):
			parser.error('\n\tWhen packing, input needs to be a valid directory containing the firmware file system')

		# When packing, if no output has been set, set output file to 'packed_INPUTDIR'
		if not args.output:
			# If the input doesn't end with '.bin', add extension
			args.output = 'packed_' + args.input if args.input.endswith('.bin') else (args.input.rstrip('/') + '.bin')

    # If we're just checking the firmware, we just need to check the input exists and is a file
	elif args.check:
		if not os.path.isfile(args.input):
			parser.error('\n\tWhen checking, input needs to be a valid path to the firmware file')


	return args

'''
	### END GET_ARGS() ########################################################
'''



def main():
	args = get_args()

	if args.check:
		if validate_firmware(args.input, verbose=args.verbose):
			print '\n [ OK ] Input file appears to be a valid firmware'
		else:
			print '\n [ ! ] Input file is corrupt or is not a firmware'
	elif args.unpack:
		if unpack(args.input, args.output, verbose=args.verbose):
			print '\n [ OK ] Input file was successfully extracted to ' + args.output
		else:
			print '\n [ ! ] Could not extract firmware'
	elif args.pack:
		if pack(args.input, args.output, verbose=args.verbose):
			print '\n [ OK ] Input directory was successfully packed to ' + args.output
		else:
			print '\n [ ! ] Could not pack firmware'


if __name__ == "__main__":
	print HEADER
	main()
	print
