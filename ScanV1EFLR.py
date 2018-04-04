#!/usr/bin/env python
# Part of TotalDepth: Petrophysical data processing and presentation
# Copyright (C) 1999-2012 Paul Ross
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Paul Ross: apaulross@gmail.com
"""Does...

Created on Oct 27, 2011

@author: paulross
"""

__author__ = 'Paul Ross'
__date__ = '2011-08-03'
__version__ = '0.1.0'
__rights__ = 'Copyright (c) 2011 Paul Ross.'

import sys
import io
import time
import collections
from TotalDepth.util import FileBuffer
import Commitar.AttrComp_V2 as AttrComp





def writeLog(file,s):
    with open(file, "a") as f:
        f.write(s+"\n")

"""From Appendix A of the spec:
Code    Type    Description    Allowable Set Types
0    FHLR    File Header    FILE-HEADER
1    OLR    Origin    ORIGIN
WELL-REFERENCE
2    AXIS    Coordinate Axis    AXIS
3    CHANNL    Channel-related information    CHANNEL
4    FRAME    Frame Data    FRAME
PATH
5    STATIC    Static Data    CALIBRATION
CALIBRATION-COEFFICIENT
CALIBRATION-MEASUREMENT
COMPUTATION
EQUIPMENT
GROUP
PARAMETER
PROCESS
SPICE
TOOL
ZONE
6    SCRIPT    Textual Data    COMMENT    MESSAGE
7    UPDATE    Update Data    UPDATE
8    UDI    Unformatted Data Identifier    NO-FORMAT
9    LNAME    Long Name    LONG-NAME
10    SPEC    Specification    ATTRIBUTE
CODE
EFLR
IFLR
OBJECT-TYPE
REPRESENTATION-CODE
SPECIFICATION
UNIT-SYMBOL
11    DICT    Dictionary    BASE-DICTIONARY
IDENTIFIER
LEXICON
OPTION
12-127    -    undefined, reserved    -

"""

EFLRType = collections.namedtuple('EFLRType', 'type description setTypes')


class ScanV1EFLR(object):
    """Class documentation."""
    "Code    Type    Description    Allowable Set Types"
    EFLR_TYPE_MAP = {
        0: EFLRType(
            'FHLR',
            'File Header',
            [
                b'FILE-HEADER',
            ]
        ),
        1: EFLRType(
            'OLR',
            'Origin',
            [
                b'ORIGIN',
                b'WELL-REFERENCE',
            ]
        ),
        2: EFLRType(
            'AXIS',
            'Coordinate Axis',
            [
                b'AXIS',
            ]
        ),
        3: EFLRType(
            'CHANNL',
            'Channel-related information',
            [
                b'CHANNEL',
            ]
        ),
        4: EFLRType(
            'FRAME',
            'Frame Data',
            [
                b'FRAME',
                b'PATH',
            ]
        ),
        5: EFLRType(
            'STATIC',
            'Static Data',
            [
                b'CALIBRATION',
                b'CALIBRATION-COEFFICIENT',
                b'CALIBRATION-MEASUREMENT',
                b'COMPUTATION',
                b'EQUIPMENT',
                b'GROUP',
                b'PARAMETER',
                b'PROCESS',
                b'SPICE',
                b'TOOL',
                b'ZONE',
            ]
        ),
        6: EFLRType(
            'SCRIPT',
            'Textual Data',
            [
                b'COMMENT',
                b'MESSAGE',
            ]
        ),
        7: EFLRType(
            'UPDATE',
            'Update Data',
            [
                b'UPDATE',
            ]
        ),
        8: EFLRType(
            'UDI',
            'Unformatted Data Identifier',
            [
                b'NO-FORMAT',
            ]
        ),
        9: EFLRType(
            'LNAME',
            'Long Name',
            [
                b'LONG-NAME',
            ]
        ),
        10: EFLRType(
            'SPEC',
            'Specification',
            [
                b'ATTRIBUTE',
                b'CODE',
                b'EFLR',
                b'IFLR',
                b'OBJECT-TYPE',
                b'REPRESENTATION-CODE',
                b'SPECIFICATION',
                b'UNIT-SYMBOL',
            ]
        ),
        11: EFLRType(
            'DICT',
            'Dictionary',
            [
                b'BASE-DICTIONARY',
                b'IDENTIFIER',
                b'LEXICON',
                b'OPTION',
            ]
        ),
    }
    IDX_ATTR = 2
    IDX_TYPE = 3
    IDX_NAME_LEN = 5
    IDX_NAME_VALUE = 6

    def __init__(self, theF):
        self.cont = 0
        self.length = 0
        self._fb = FileBuffer.FileBuffer(theF)
        self.pos = 0
        self.next = 0
        self.last = 0
        self.data = ""
        self.objects = {}
        self.objectName = ""
        self.type = ""
        self.parameterCounter = 0
        self.channelCounter = 0


        while True:
            self.length = 0
            try:
                attr = self._fb[self.pos+self.IDX_ATTR]


            except IndexError:
                break

            # Attribute must match 10xxxxxx i.e. EFL and the first segment (no predecessor)
            if attr & 0x80 > 0 and attr & 0x40 == 0 and self.last == 0 and attr & 0x10 == 0 and attr & 0x8 == 0:
                typeCode = self._fb[self.pos+self.IDX_TYPE]
                self.data = ""

                if typeCode in self.EFLR_TYPE_MAP:
                    l = self._fb[self.pos+self.IDX_NAME_LEN]
                    if l > 0:
                        name = self._fb[self.pos+self.IDX_NAME_VALUE:self.pos+self.IDX_NAME_VALUE + l]
                        if name in self.EFLR_TYPE_MAP[typeCode].setTypes:
                            self.cont = 1
                            # Got one!
                            self.length = (self._fb[self.pos] << 8) + self._fb[self.pos+1]
                            self.next = self.length
                            if attr & 0x4:
                                self.length = self.length - 2
                            if attr & 0x2:
                                self.length = self.length - 2
                            if attr & 0x40 == 0 and attr & 0x1:
                                n = self._fb[self.pos+self.length-1]
                                self.length = self.length - n


                            st = 'LRSH  len={:6d} [0x{:04x}] attr=0x{:x} [{:b}] EFLR code={:d} name: {:s}'.format(
                                    self.length,
                                    self.length,
                                    attr,
                                    attr,
                                    typeCode,
                                    name.decode("UTF8"),
                                )

                            print(st)



                            if name.decode("UTF8") == "CHANNEL":

                                ind = self.pos + self.IDX_NAME_VALUE + l

                                self.data = self._fb[ind:self.pos + self.length]
                                if attr & 0x60 > 0:
                                    self.cont = 1
                                    self.last = 1
                                    self.type = "channel"
                                else:
                                    self.parseChannel(0)


                            if name.decode("UTF8") == "FILE-HEADER":

                                ind = self.pos + self.IDX_NAME_VALUE + l
                                self.data = self._fb[ind:self.pos + self.length]
                                self.parseHeader(0)


                            if name.decode("UTF8") == "FRAME":
                                ind = self.pos + self.IDX_NAME_VALUE + l
                                self.data = self._fb[ind:self.pos + self.length]
                                if attr & 0x60 > 0:
                                    self.cont = 1
                                    self.last = 1
                                    self.type = "frame"
                                else:
                                    self.parseFrame(0)

                            if name.decode("UTF8") == "ORIGIN":
                                ind = self.pos + self.IDX_NAME_VALUE + l

                                self.data = self._fb[ind:self.pos + self.length]
                                if attr & 0x60 > 0:
                                    self.cont = 1
                                    self.last = 1
                                    self.type = "origin"
                                else:
                                    print(self._fb[self.pos:self.pos + self.length])
                                    print(self.data)
                                    self.parseOrigin(0)


                            if name.decode("UTF8") == "PARAMETER":
                                ind = self.pos + self.IDX_NAME_VALUE + l + 3
                                self.data = self._fb[ind:self.pos + self.length]
                                if attr & 0x60 > 0:
                                    self.cont = 1
                                    self.last = 1
                                    self.type = "parameter"
                                else:
                                    self.parseParameter(0)




            elif attr & 0x80 > 0 and attr & 0x40 > 0 and attr & 0x10 == 0 and attr & 0x8 == 0 and self.last:

                self.length = (self._fb[self.pos] << 8) + self._fb[self.pos + 1]

                self.next = self.length
                if attr & 0x4:
                    self.length = self.length - 2
                if attr & 0x2:
                    self.length = self.length - 2
                if attr & 0x40 == 0 and attr & 0x1:
                    n = self._fb[self.pos + self.length - 1]
                    self.length = self.length - n


                self.data = self.data + self._fb[self.pos+4:self.pos + self.length]

                if attr & 0x20 == 0:
                    self.last = 0
                    if self.type == "frame":
                        self.p = self.parseFrame(0)
                    elif self.type == "channel":
                        self.p = self.parseChannel(0)
                    elif self.type == "origin":
                        self.p = self.parseOrigin(0)
                    elif self.type == "parameter":
                        self.p = self.parseParameter(0)

                    self.data = ""
                    self.type = ""

            if attr & 0x80 == 0 and attr & 0x10 == 0 and attr & 0x8 == 0:
                #print(self._fb[self.pos:self.pos+100])
                #a = input()
                pass


            if self.length == 0:
                self.pos = self.pos+1

            else:
                self.pos = self.pos + self.next



    def parser(self, ind):
        aa = AttrComp.AttrCompStream(int(self.getBits(ind,0, 3), 2), io.BytesIO(self.data[ind:]))
        aa.readAll()
        aa.clearAttributeList()
        del aa


    def parseHeader(self, ind):
        aa = AttrComp.AttrCompStream(int(self.getBits(ind, 0, 3), 2), io.BytesIO(self.data[ind:]))
        aa.readAll()
        #aa.print()
        self.objectName = aa.getObjName().strip()
        self.objects[self.objectName] = {}
        self.objects[self.objectName]["HEADER"] = aa.getFrame()
        del aa

    def parseFrame(self,ind):
        aa = AttrComp.AttrCompStream(int(self.getBits(ind, 0, 3), 2), io.BytesIO(self.data[ind:]))
        #print(self.data[ind:])
        aa.readAll()
        aa.print()
        self.objects[self.objectName]["FRAME"] = aa.getFrame()
        del aa

    def parseChannel(self,ind):
        aa = AttrComp.AttrCompStream(int(self.getBits(ind, 0, 3), 2), io.BytesIO(self.data[ind:]))
        print(self.data[ind:])
        aa.readAll()
        aa.print()
        if "CHANNEL" in self.objects[self.objectName]:
            self.objects[self.objectName]["CHANNEL_" + str(self.channelCounter)] = aa.getFrame()
        else:
            self.objects[self.objectName]["CHANNEL"] = aa.getFrame()
        self.channelCounter = self.channelCounter + 1
        del aa

    def parseOrigin(self,ind):
        aa = AttrComp.AttrCompStream(int(self.getBits(ind, 0, 3), 2), io.BytesIO(self.data[ind:]))
        #print(self.data[ind:])
        aa.readAll()
        aa.print()
        self.objects[self.objectName]["ORIGIN"] = aa.getFrame()
        del aa

    def parseParameter(self,ind):
        aa = AttrComp.AttrCompStream(int(self.getBits(ind, 0, 3), 2), io.BytesIO(self.data[ind:]))
        print(self.data[ind:])
        aa.readAll()
        aa.print()
        if "PARAMETER" in self.objects[self.objectName]:
            self.objects[self.objectName]["PARAMETER_"+ str(self.parameterCounter)] = aa.getFrame()
        else:
            self.objects[self.objectName]["PARAMETER"] = aa.getFrame()
        self.parameterCounter = self.parameterCounter + 1
        del aa

    def getBits(self,ind,start,end):
        attr = self.data[ind]
        return ("{0:08b}".format(attr))[start:end]


def main():

    path = "/home/lmdc/Downloads/TotalDepth-master/in"
    #file = "1-mrk-3-rjs_wave.dlis"
    #file = "7-GVR-2D-MA_UBI_PRINCIPAL_TVD_8.5..DLIS"
    file = "7-ATL-2HP-RJS_LWD-mem_14.75in_GR-RES_SDTK_ZTK.dlis"
    #file = "OBMI_IP_proc.dlis"

    a = open(path + "/" + file, "rb")

    clkStart = time.clock()
    timStart = time.time()

    myObj = ScanV1EFLR(a)
    print(myObj.objects)
    del myObj

    print('  CPU time = %8.3f (S)' % (time.clock() - clkStart))
    print('Exec. time = %8.3f (S)' % (time.time() - timStart))
    print('Bye, bye!')
    return 0


if __name__ == '__main__':
    sys.exit(main())
