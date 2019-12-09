#!/usr/bin/python3

import sys
from pprint import pprint

def debug(data):
	if dbg == 1:
		print(data)

# get user input
def get_input():
	input_value = input("Provide input: ")
	try:
		userinput = int(input_value)
	except:
		print("Error: input must be an integer")
		exit(0)
	return userinput

# help function for managing parameter modes
# create parameter mode list with zeroes if not matching number of parameters and reverse list to match order of parameters
def parmode(raw_parmode,pnum):
	pm = raw_parmode
	while len(pm) < pnum:
		pm.insert(0,0)
	return pm[::-1]

# get input parameter values - supporting different parameter modes
def get_arg_values(instr, raw_parmode, iargs):
	global ebp
	pm = parmode(raw_parmode,len(instr)-1)
	debug("parmode: "+str(pm)+", iargs: "+str(iargs))
	argvals = [instr[0]]
	for i in range(1,iargs+1):
		if pm[i-1] == 0:
			# positional mode
			val = getmem(instr[i])
		elif pm[i-1] == 1:
			# immediate mode
			val = instr[i]
		elif pm[i-1] == 2:
			# relative mode
			val = getmem(ebp + instr[i])
		else: # non-existent mode
			print("Warning: non-existent parameter mode: "+str(pm[i-1]))
			return argvals
		argvals.append(val)
	# treat output parameters differently, return memory index
	if len(instr) > iargs:
		# if not all parameters are input parameters, the last parameter is output
		if pm[-1] == 0:
			# positional mode			
			val = instr[-1]
		elif pm[-1] == 2:
			# relative mode
			val = ebp + instr[-1]
		argvals.append(val)
	return argvals


# execute instruction
# inputs:
#   instr - instruction (opcode + parameters)
#   iargs - number of input arguments
# return error code
#   0 - no error 
#   1 - jump taken, do not increment eip
#   99 - exit instruction
#   -2 - non-existent opcode   
def execi(instr):
	global eip, mem, ebp, opcode_table

	debug(instr)
	op = instr[0]
	# pick out last two digits, which is the opcode
	opcode = abs(op) % 100
	debug("opcode: "+str(opcode)+" - "+opcode_table[opcode][2])
	# pick out parameter modes
	raw_parmode = [int(x) for x in str(op)][:-2]
	# get input argument values
	iargs = opcode_table[opcode][1] # number of input arguments
	argvals = get_arg_values(instr,raw_parmode,iargs)
	debug("argvals:"),
	debug(argvals)

	# execute instruction
	if opcode == 1:
		# add
		checkmem(argvals[3])
		mem[argvals[3]] = argvals[1] + argvals[2]
		return 0
	elif opcode == 2:
		# multiply
		checkmem(argvals[3])
		mem[argvals[3]] = argvals[1] * argvals[2]
		return 0
	elif opcode == 3:
		# user input operation
		arg = get_input()
		print(arg)
		checkmem(argvals[1])
		mem[argvals[1]] = arg
		return 0
	elif opcode == 4:
		# output operation
		arg = argvals[1]
		print("Output: "+str(arg))
		return 0
	elif opcode == 5:
		# jump-if-true
		if argvals[1] != 0:
			eip = argvals[2]
			return 1
		return 0
	elif opcode == 6:
		# jump-if-false
		if argvals[1] == 0:
			eip = argvals[2]
			return 1
		return 0
	elif opcode == 7:
		# less than
		checkmem(argvals[3])
		if argvals[1] < argvals[2]:
			mem[argvals[3]] = 1
		else:
			mem[argvals[3]] = 0
		return 0
	elif opcode == 8:
		# equals
		checkmem(argvals[3])
		if argvals[1] == argvals[2]:
			mem[argvals[3]] = 1
		else:
			mem[argvals[3]] = 0
		return 0
	elif opcode == 9:
		# change relative base pointer
		ebp += argvals[1]
		if ebp < 0:
			print("Warning: relative base pointer is negative. ebp: "+str(ebp))
		return 0
	elif opcode == 99:
		return 99
	else:
		# wrong opcode
		return -1

# execute program
def execute():
	global eip
	eip = 0
	while(True):
		debug("")
		debug("eip: "+str(eip)+" , ebp: "+str(ebp))
		# return if instruction is exit
		if getmem(eip) == 99:
			return 0
		# execute instruction
		ilen = instrlen(getmem(eip))
		if ilen == 0:
			print("Error, invalid opcode: "+str(getmem(eip)))
			return -1
		# check if ilen is within program len
		#if eip + ilen > len(text):
		#	print("Error, instruction is longer than what is left of memory"+str(text[eip:]))
		#	return -2
		# get instruction
		instr = []
		for i in range(ilen):
			instr.append(getmem(eip+i))
		ret = execi(instr)

		debug("Debug - program memory: "),
		if dbg == 1:
			printmem()
		# move instruction pointer to next instruction (if not jump taken)
		if ret != 1:
			eip += ilen
		if ret == -1:
			print("Error, invalid opcode: "+str(getmem(eip)))
			return -1
		elif ret == -2:
			print("Error, parameter out of memory range")
			return -2
		# check if we are at end of memory
		#if eip >= len(text):
		#	return 0
	return 0

# memory debugging and management functions
def printmem():	
	print("Memory state:")
	pprint(mem)

def getmem(pos):
	global mem
	val = 0 # default memory value
	checkmem(pos)
	if pos in mem:
		return mem[pos]
	else:
		print("Warning: accessing memory position which has not been set, pos: "+str(pos))
		return 0

def checkmem(pos):
	if pos < 0:
		print("Error: Segfault. Out of memory access accessing pos: "+str(pos))
		# exit program if trying to access out of memory
		sys.exit(1)
	return 0

# look up instruction len and number of input arguments
def instrlen(op):
	global opcode_table
	# pick out last two digits
	opcode = abs(op) % 100 
	#debug("instrlen: opcode = " + str(opcode))
	data = opcode_table.get(opcode)
	if data:
		instrlen = data[0]
		return instrlen
	else:
		print("Error: Invalid opcode: "+str(opcode))
		return 0

def create_opcode_table():
	# opcode table is a dictionary for looking up instruction len, number of input arguments, and instruction name
	opcodes = {}
	opcodes[1] = (4,2,"add")
	opcodes[2] = (4,2,"mul")
	opcodes[3] = (2,0,"input")
	opcodes[4] = (2,1,"output")
	opcodes[5] = (3,2,"jump-if-true")
	opcodes[6] = (3,2,"jump-if-false")
	opcodes[7] = (4,2,"less-than")
	opcodes[8] = (4,2,"equals")
	opcodes[9] = (2,1,"change-ebp")
	opcodes[99] = (1,0,"exit")
	return opcodes

### main ###

# set dbg flag to 1 for debug printouts
dbg = 0

### read program from file
filename = "input"
f = open(filename,'r')
prog = list(map(int,(f.read().rstrip()).split(',')))
f.close()

# testprog
#prog = [109,1,204,-1,1001,100,1,100,1008,100,16,101,1006,101,0,99]
#prog = [1102,34915192,34915192,7,4,7,99,0]
#prog = [104,1125899906842624,99]

debug("prog = "),
debug(prog)
debug("prog length = " + str(len(prog)))

# create opcode table
opcode_table = create_opcode_table()

# set memory and registers
# text segment contains program
#text = list(prog)
# instruction pointer
eip = 0
# relative base address - for relative parameters
ebp = 0
# memory is a dictionary
mem = {}

# copy program to memory
for i in range(len(prog)):
	mem[i] = prog[i]


### run program
ret = execute()
debug("Stderr: "+str(ret))

