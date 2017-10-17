import sys

numArgs = len(sys.argv)
print("Got " + str(numArgs) + " argument(s):");
for index, arg in enumerate(sys.argv):
	print("[" + str(index) + "] \"" + arg + "\"");

class Range(object):
	def __init__(self, start, end):
		self._start = start;
		self._end = end;
	
	@property
	def start(self):
		return self._start;
	
	@property
	def end(self):
		return self._end;
		
	@property
	def size(self):
		return self._end - self._start;

class HexFile(object):
	def __init__(self):
		self.minAddress = 0;
		self.maxAddress = 0;
		self.numDataBytes = 0;
		self.binaryImage = {};
		self.filledMin = False;
	
	def FindNextFilledAddressAbove(self, baseAddress):
		found = False;
		result = 0;
		for key in self.binaryImage:
			# print("Checking 0x%08X" % key);
			if (key > baseAddress and (found == False or key < result)):
				# print("Found!");
				result = key;
				found = True;
		
		if (not found):
			return 0;
		else:
			return result;
	
	def GetAddressRanges(self):
		rangeStart = self.minAddress;
		address = self.minAddress;
		ranges = [];
		
		while (address <= self.maxAddress):
			if (address in self.binaryImage):
				pass; # print("0x%08X exists" % address);
			else:
				if (address > rangeStart):
					ranges.append(Range(rangeStart, address))
				
				rangeStart = self.FindNextFilledAddressAbove(address);
				if (rangeStart == 0): break;
				address = rangeStart-1;
			
			address += 1;
		
		return ranges;
	
	def OpenHexFile(self, hexFileName):
		with open(hexFileName, 'r') as hexFile:
			lineNum = 0;
			upperAddress = 0x0000;
			
			for line in hexFile:
				lineStr = line.strip();
				if (len(lineStr) == 0):
					print("Empty line");
				elif (lineStr[0] != ':'):
					print("No colon on line " + str(lineNum));
				elif (len(lineStr) < 11):
					print("Line " + str(lineNum) + " was too short");
				else:
					lineStr = lineStr[1:];
					# print("[" + str(lineNum) + "] = \"" + lineStr + "\"");
					numBytesStr = lineStr[0:2];
					numBytes = int(numBytesStr, 16);
					addressStr = lineStr[2:6];
					address = int(addressStr, 16);
					address += (upperAddress << 16);
					commandStr = lineStr[6:8];
					command = int(commandStr, 16);
					dataStr = lineStr[8:-2];
					# print("\t" + str(numBytes) + " bytes, address %08X: CMD %02X" % (address, command));
					
					if (command == 0x00):
						# print((str(numBytes) + " bytes 0x%08X: [" + dataStr + "]") % address);
						self.numDataBytes += len(dataStr)/2;
						if (len(dataStr)/2 == numBytes):
							for bIndex in range(numBytes):
								valueAddr = address+bIndex;
								value = int(dataStr[bIndex*2:bIndex*2+2], 16);
								
								if (valueAddr in self.binaryImage):
									print("!!!!!!!! Conflict at 0x%08X !!!!!!!!" % valueAddr);
								
								# print("[0x%08X] = 0x%02X" % (valueAddr, value))
								self.binaryImage[valueAddr] = value;
								if (self.filledMin == False or valueAddr < self.minAddress):
									self.minAddress = valueAddr;
									self.filledMin = True;
								if (valueAddr >= self.maxAddress):
									self.maxAddress = valueAddr+1;
						else:
							print("Data length didn't match actual data string.");
							print(str(len(dataStr)/2) + " != " + str(numBytes));
							return;
					elif (command == 0x04):
						upperAddress = int(dataStr, 16);
						# print("Upper address changed to %04X" % upperAddress);
					elif (command == 0x01):
						print("End of file!");
						break;
					else:
						pass;
						# print("Unknown command %02X" % command);
						# print("line " + str(lineNum) + ": \"" + lineStr + "\"");
				
				lineNum += 1;
			
			print("Current Filled " + str(self.numDataBytes) + " bytes.");
			print("Current Address Range: 0x%08X-0x%08X [%u bytes]" % (self.minAddress, self.maxAddress, self.maxAddress-self.minAddress ));
	
	def GetLineChecksum(self, lineString):
		result = 0;
		
		# print("CRC on \"" + lineString + "\" " + str(len(lineString)));
		if (((len(lineString)) % 2) != 0):
			print("Line was not a multiple of 2 for GetLineChecksum!");
			print("Line: \"" + lineString + "\" " + str(len(lineString)));
			return 0x00;
		
		for bIndex in range(len(lineString)/2):
			result += int(lineString[bIndex*2:bIndex*2 + 2], 16);
		result = 0xFF & ((~result) + 1);
		
		return result;
	
	def SaveToHexFile(self, outputFileName):
		with open(outputFileName, 'w') as hexFile:
			upperAddress = 0;
			ranges = self.GetAddressRanges();
			for r in ranges:
				rangeOffset = 0;
				while (rangeOffset < r.size):
					address = r.start + rangeOffset;
					lowerAddress = 0xFFFF & address;
					numBytes = min(16, r.size - rangeOffset);
					
					# Write the upper address change if we need to
					if (upperAddress != (0xFFFF & (address >> 16))):
						upperAddress = (0xFFFF & (address >> 16));
						addressLine = ":02000004%04X" % upperAddress;
						addressLineChecksum = self.GetLineChecksum(addressLine[1:]);
						addressLine += "%02X" % addressLineChecksum;
						hexFile.write(addressLine + "\n");
					
					newLine = ":";
					newLine += "%02X" % numBytes;
					newLine += "%04X" % lowerAddress;
					newLine += "00"; # Data Command
					for offset in range(numBytes):
						newLine += "%02X" % self.binaryImage[address+offset];
					newLineChecksum = self.GetLineChecksum(newLine[1:]);
					newLine += "%02X" % newLineChecksum;
					hexFile.write(newLine + "\n");
					
					rangeOffset += numBytes;
	
	def BluetoothModifications(self):
		ranges = self.GetAddressRanges();
		applicationRange = None;
		for r in ranges:
			if (r.start == 0x1F000):
				applicationRange = r;
				break;
		
		if (applicationRange == None):
			print("Couldn't find application range.");
			return;
		
		print("Application is %u bytes" % applicationRange.size);
		
		# NOTE: See nrf_dfu_types.h and nrf_dfu_settings.c
		bootloaderSettingsAddress = 0x0007F000;
		u32Size = 4;
		bank0InfoAddress = bootloaderSettingsAddress + u32Size*6;
		applicationSize     = applicationRange.size;
		applicationCrc      = 0x00000000;# NOTE: Disables the CRC check
		applicationBankCode = 0x00000001;# NOTE: Indicates a valid application
		
		self.binaryImage[bank0InfoAddress + 0]  = 0xFF & (applicationBankCode >> 0);
		self.binaryImage[bank0InfoAddress + 1]  = 0xFF & (applicationBankCode >> 8);
		self.binaryImage[bank0InfoAddress + 2]  = 0xFF & (applicationBankCode >> 16);
		self.binaryImage[bank0InfoAddress + 3]  = 0xFF & (applicationBankCode >> 24);
		
		self.binaryImage[bank0InfoAddress + 4]  = 0xFF & (applicationCrc >> 0);
		self.binaryImage[bank0InfoAddress + 5]  = 0xFF & (applicationCrc >> 8);
		self.binaryImage[bank0InfoAddress + 6]  = 0xFF & (applicationCrc >> 16);
		self.binaryImage[bank0InfoAddress + 7]  = 0xFF & (applicationCrc >> 24);
		
		self.binaryImage[bank0InfoAddress + 8]  = 0xFF & (applicationSize >> 0);
		self.binaryImage[bank0InfoAddress + 9]  = 0xFF & (applicationSize >> 8);
		self.binaryImage[bank0InfoAddress + 10] = 0xFF & (applicationSize >> 16);
		self.binaryImage[bank0InfoAddress + 11] = 0xFF & (applicationSize >> 24);
		
		for bIndex in range(12):
			print("[%08X] = 0x%02X" % (bank0InfoAddress + bIndex, self.binaryImage[bank0InfoAddress + bIndex]));

if (numArgs < 3):
	print("No file specified");
else:
	# print("Opening file \"" + sys.argv[1] + "\"");
	hexFile = HexFile();
	for index, arg in enumerate(sys.argv):
		if (index >= 1 and index < numArgs-1):
			print("\n\nAdding Hex file \"" + arg + "\"")
			hexFile.OpenHexFile(arg);
	
	# hexFile.BluetoothModifications();
	
	ranges = hexFile.GetAddressRanges();
	print("Final Address Ranges:");
	for current in ranges:
		print("\t0x%08X-0x%08X [%u bytes]" % (current.start, current.end, current.size));
		if (current.size <= 16):
			sys.stdout.write("\t\t[");
			for bIndex in range(current.size):
				sys.stdout.write("%02X" % hexFile.binaryImage[current.start + bIndex]);
			print("]");
	
	outputFileName = sys.argv[numArgs-1];
	print("Outputting File: \"" + outputFileName + "\"");
	hexFile.SaveToHexFile(outputFileName);
	

# while (1):
# 	dontDoAnything = 1;
		