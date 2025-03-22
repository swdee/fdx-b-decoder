##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2024 https://github.com/swdee
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd

# constants
HEADER = "10000000000"
DATA_BLOCK_FLAG_POSITION = 66
ANIMAL_APP_FLAG_POSITION = 82
LOGIC_BIT_POSITIONS = [11,20,29,38,47,56,65,74,83,92,101,110,119]
CRC_CHECKSUM_START_POSITION = 84
CRC_CHECKSUM_END_POSITION = CRC_CHECKSUM_START_POSITION + 16
EXTRA_DATA_START_POSITION = 102
EXTRA_DATA_END_POSITION = EXTRA_DATA_START_POSITION + 25
NATIONAL_CODE_START_POSITION = 12
NATIONAL_CODE_END_POSITION = NATIONAL_CODE_START_POSITION + 41
COUNTRY_CODE_START_POSITION = 54
COUNTRY_CODE_END_POSITION = COUNTRY_CODE_START_POSITION + 10

# The Transponder sends data back at a bit rate of 4194 bit/sec which results
# in a modulation width of 0.23845ms.  We use a cut off of 200 (0.200ms) to determine
# if we have a bit "1" or "0".
MODULATION_WIDTH = 200

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'fdx-b'
    name = 'FDX-B'
    longname = 'FDX-B ISO 11784/11785'
    desc = 'FDX-B 134.2kHz RFID protocol.'
    license = 'gplv3+'
    inputs = ['logic']
    outputs = []
    tags = ['IC', 'RFID']
    channels = (
        {'id': 'data', 'name': 'Data', 'desc': 'Data line', 'idn':'dec_fdxb_chan_data'},
    )
    options = (
    )
    annotations = (
        ('bit', 'Bit'),                             # 0
        ('header', 'Header'),                       # 1
        ('logic-seperator', 'Logic Seperator'),     # 2
        ('data-block-flag', 'Data Block Flag'),     # 3
        ('animal-app-flag', 'Animal Application Flag'),  # 4
        ('crc-checksum', 'CRC16 Checksum'),         # 5
        ('application-data', 'Application Data'),   # 6
        ('national-code', 'National Code'),         # 7
        ('country-code', 'Country Code'),           # 8
        ('id', 'ID'),                               # 9
        ('extra-data-true', 'Extra Data'),          # 10
        ('extra-data-false', 'No Extra Data'),      # 11
        ('valid-checksum', 'Valid Checksum'),       # 12
        ('invalid-checksum', 'Invalid Checksum'),   # 13
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('fields', 'Fields', (1, 2, 3, 4, 5, 6, 7, 8,)),
        ('values', 'Values', (9,10,11,12,13)),
    )

    def __init__(self):
        self.reset()

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def reset(self):
        self.samplerate = None
        self.telegram = []
        self.hasHeader = False
        self.hasExtraData = False
        self.endTelegram = False
        self.tagID = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    # clear telegram buffered data
    def clearTelegram(self):
        self.telegram = []
        self.hasHeader = False
        self.hasExtraData = False
        self.endTelegram = False
        self.tagID = None

    def set_data_block_flag(self, bit):
        if bit == "1":
            self.hasExtraData = True
        else:
            self.hasExtraData = False

    # draw the transponder ID code (number)
    def drawID(self):
        # get bits from telegram used for calculating national code
        segment = self.telegram[NATIONAL_CODE_START_POSITION:NATIONAL_CODE_END_POSITION+1]
        # remove logic bits from this segment: 8, 17, 26, 35.  make sure its done in desc order as the index numbers
        # change as the array is shrunk
        segment.pop(35)
        segment.pop(26)
        segment.pop(17)
        segment.pop(8)

        segment.reverse()
        # get binary bits
        bits = ""
        for idx, data in enumerate(segment):
            bits += data[0]

        nationalCode = int(bits, base=2)

        # get bits for calculating country code
        segment = self.telegram[COUNTRY_CODE_START_POSITION:COUNTRY_CODE_END_POSITION+1]
        # remove logic bits from segment
        segment.pop(2)

        segment.reverse()
        bits = ""
        for idx, data in enumerate(segment):
            bits += data[0]

        countryCode = int(bits, base=2)

        self.tagID = "%d%d" % (countryCode , nationalCode)

        self.put(self.telegram[NATIONAL_CODE_START_POSITION][1], self.telegram[COUNTRY_CODE_END_POSITION][2],self.out_ann,
                 [9,["Tag ID: %s" % self.tagID, "ID: %s" % self.tagID]])


    # calculate data checksum which is CRC16/Kermit
    def calc_checksum(self):
        # first get the checksum provided in the telegram
        segment = self.telegram[CRC_CHECKSUM_START_POSITION:CRC_CHECKSUM_END_POSITION+1]
        # remove logic bits from segment
        segment.pop(8)
        segment.reverse()

        bits = ""
        for idx, data in enumerate(segment):
            bits += data[0]

        checkSum = int(bits, base=2)

        # calculate our own checksum across national and country code data
        segment = self.telegram[NATIONAL_CODE_START_POSITION:ANIMAL_APP_FLAG_POSITION+1]
        # remove logic bits from this segment: 8, 17, 26, 35.  make sure its done in desc order as the index numbers
        # change as the array is shrunk
        segment.pop(62)
        segment.pop(53)
        segment.pop(44)
        segment.pop(35)
        segment.pop(26)
        segment.pop(17)
        segment.pop(8)

        segment.reverse()
        bits = ""
        for idx, data in enumerate(segment):
            bits += data[0]

        # then reverse the 8 bit block order
        orderedBits = bits[56:]+bits[48:56]+bits[40:48]+bits[32:40]+bits[24:32]+bits[16:24]+bits[8:16]+bits[:8]

        myBytes = int(orderedBits, 2).to_bytes(len(orderedBits) // 8, byteorder='big')
        myCheckSum = self.crc16(myBytes,0,8)

        if myCheckSum == checkSum:
            self.put(self.telegram[CRC_CHECKSUM_START_POSITION][1], self.telegram[CRC_CHECKSUM_END_POSITION][2],
                     self.out_ann,
                     [12, ["Valid Checksum: %s" % hex(checkSum), "Valid CRC", "V"]])
        else:
            self.put(self.telegram[CRC_CHECKSUM_START_POSITION][1], self.telegram[CRC_CHECKSUM_END_POSITION][2],
                     self.out_ann,
                     [13, ["Invalid Checksum: Got %s, wanted %s" % (hex(myCheckSum), hex(checkSum)), "Invalid CRC", "E"]])

    # CRC16 CCITT Kermit implementation
    def crc16(self, data: bytearray, offset, length):
        if data is None or offset < 0 or offset > len(data) - 1 or offset + length > len(data):
            return 0
        crc = 0
        for i in range(0, length):
            crc ^= data[offset + i]
            for j in range(0, 8):
                if (crc & 1) > 0:
                    crc = (crc >> 1) ^ 0x8408
                else:
                    crc = crc >> 1
        return crc

    # check the telegram buffer state
    def check_telegram(self):
        if self.hasHeader:
            # get most recent bit in telegram
            teleIdx = len(self.telegram) - 1

            # draw logic bit field
            if teleIdx in LOGIC_BIT_POSITIONS:
                self.put(self.telegram[teleIdx][1],self.telegram[teleIdx][2],self.out_ann,
                         [2,["Logic Seperator","Logic","L"]])

            # draw data block flag
            if teleIdx == DATA_BLOCK_FLAG_POSITION:
                self.put(self.telegram[teleIdx][1], self.telegram[teleIdx][2], self.out_ann,
                         [3, ["Data Block Flag", "Data Flag", "D"]])
                self.set_data_block_flag(self.telegram[teleIdx][0])
                if self.hasExtraData:
                    self.put(self.telegram[teleIdx][1], self.telegram[teleIdx][2], self.out_ann,
                             [10, ["Contains Extra Data", "Extra True", "E"]])
                else:
                    self.put(self.telegram[teleIdx][1], self.telegram[teleIdx][2], self.out_ann,
                             [11, ["No Extra Data", "Extra False", "X"]])

            # draw animal application flag
            if teleIdx == ANIMAL_APP_FLAG_POSITION:
                self.put(self.telegram[teleIdx][1], self.telegram[teleIdx][2], self.out_ann,
                         [4, ["Animal Application Flag", "Animal Flag", "A"]])

            # draw crc16 checksum block
            if teleIdx == CRC_CHECKSUM_END_POSITION:
                self.put(self.telegram[CRC_CHECKSUM_START_POSITION][1], self.telegram[CRC_CHECKSUM_START_POSITION+8][1], self.out_ann,
                         [5, ["CRC16 Checksum", "CRC", "C"]])
                self.put(self.telegram[CRC_CHECKSUM_START_POSITION+9][1], self.telegram[teleIdx][2], self.out_ann,
                         [5, ["CRC16 Checksum", "CRC", "C"]])
                self.calc_checksum()

            # draw extra data block
            if teleIdx == EXTRA_DATA_END_POSITION and self.hasExtraData:
                self.put(self.telegram[EXTRA_DATA_START_POSITION][1], self.telegram[EXTRA_DATA_START_POSITION+8][1], self.out_ann,
                         [6, ["Application Data", "App Data", "X"]])
                self.put(self.telegram[EXTRA_DATA_START_POSITION+9][1], self.telegram[EXTRA_DATA_START_POSITION+17][1], self.out_ann,
                         [6, ["Application Data", "App Data", "X"]])
                self.put(self.telegram[EXTRA_DATA_START_POSITION+18][1], self.telegram[teleIdx][2], self.out_ann,
                         [6, ["Application Data", "App Data", "X"]])
                self.endTelegram = True

            # draw national code block
            if teleIdx == NATIONAL_CODE_END_POSITION:
                self.put(self.telegram[NATIONAL_CODE_START_POSITION][1], self.telegram[NATIONAL_CODE_START_POSITION+8][1], self.out_ann,
                         [6, ["National Code", "Code", "N"]])
                self.put(self.telegram[NATIONAL_CODE_START_POSITION+9][1], self.telegram[NATIONAL_CODE_START_POSITION+17][1], self.out_ann,
                         [6, ["National Code", "Code", "N"]])
                self.put(self.telegram[NATIONAL_CODE_START_POSITION+18][1], self.telegram[NATIONAL_CODE_START_POSITION+26][1], self.out_ann,
                         [6, ["National Code", "Code", "N"]])
                self.put(self.telegram[NATIONAL_CODE_START_POSITION+27][1], self.telegram[NATIONAL_CODE_START_POSITION+35][1], self.out_ann,
                         [6, ["National Code", "Code", "N"]])
                self.put(self.telegram[NATIONAL_CODE_START_POSITION+36][1], self.telegram[teleIdx][2], self.out_ann,
                         [6, ["National Code", "Code", "N"]])

            # draw country code block
            if teleIdx == COUNTRY_CODE_END_POSITION:
                self.put(self.telegram[COUNTRY_CODE_START_POSITION][1], self.telegram[COUNTRY_CODE_START_POSITION+2][1], self.out_ann,
                         [7, ["Country Code", "Country", "C"]])
                self.put(self.telegram[COUNTRY_CODE_START_POSITION+3][1], self.telegram[teleIdx][2], self.out_ann,
                         [7, ["Country Code", "Country", "C"]])
                self.drawID()

        else:
            self.find_header()


    def find_header(self):
        if len(self.telegram) < len(HEADER):
            # we don't have enough data yet to match the length of the header
            return

        for idx, data in enumerate(self.telegram):
            if HEADER[idx] != data[0]:
                return

        # has header
        self.hasHeader = True
        self.put( self.telegram[0][1],self.telegram[len(HEADER)-1][2],self.out_ann,[1,["Header"]])


    # adds the next bit to the telegram data buffer
    def add_to_telegram(self, bit, startPos, endPos):
        if len(self.telegram) >= len(HEADER) and not self.hasHeader:
            # remove first element from array
            self.telegram.pop(0)

        self.telegram.append([bit, startPos, endPos])


    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')

        self.lastSamplenum = 0
        self.lastLastSampleNum = 0
        self.lastState = 0
        self.lastWidth = 0
        self.foundFirstOne = False
        counter = 0

        # Enter loop to keep getting samples
        while True:
            # Ignore identical samples, only process edges.
            (state,) = self.wait({0: 'e'})

            counter += 1

            # Calculate pulse width in samples
            width_samples = self.samplenum - self.lastSamplenum

            # Convert width to time in microseconds
            width = (width_samples / self.samplerate) * 1e6

            # ignore the first edge as it could be partial
            if counter > 1:
                if width > MODULATION_WIDTH:
                   self.foundFirstOne = True
                   self.put(self.lastSamplenum, self.samplenum, self.out_ann, [0, ["1"]])
                   self.add_to_telegram("1", self.lastSamplenum, self.samplenum)
                   self.lastWidth = 0
                elif (width + self.lastWidth) > MODULATION_WIDTH and self.foundFirstOne:
                    self.put(self.lastLastSampleNum, self.samplenum, self.out_ann, [0, ["0"]])
                    self.add_to_telegram("0", self.lastLastSampleNum, self.samplenum)
                    self.lastWidth = 0
                else:
                    self.lastWidth = width

            self.check_telegram()

            if self.endTelegram:
                self.clearTelegram()

            self.lastLastSampleNum = self.lastSamplenum
            self.lastSamplenum = self.samplenum