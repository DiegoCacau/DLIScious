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
"""Tests ...

Created on Oct 11, 2011

@author: paulross

See RP66v2 Sect. 8.6:

Table 10 - Attribute Components
*Note    Format Bit    Symbol    Characteristic    Representation Code    Global Default Value
1    5    l    label    IDENT    (see note)
2    4    c    count    UVARI    1
2    3    r    representation code    USHORT    IDENT
2    2    u    unit    UNITS    null
3    1    v    value    (see note)    null
"""

__author__ = 'Paul Ross'
__date__ = '2011-08-03'
__version__ = '0.1.0'
__rights__ = 'Copyright (c) 2011 Paul Ross.'

import Commitar.RepCode as RepCode
import datetime



class Attribute(object):
    # Rep code IDENT
    lable = None
    # Rep code UVARI, defaults to 1
    count = 1
    # Rep code USHORT, defaults to IDENT (19)
    repCode = 19
    # Rep code UNITS
    units = None
    # Single value or list of values if count > 1
    value = None

    role = None

    def __init__(self,lable,count,repCode,units,value, role):
        self.lable = lable
        self.count = count
        self.repCode = repCode
        self.units = units
        self.value = value
        self.role = role

    def __str__(self):

        return 'lable={:s} count={:s} rc={:s} ({:s}) units={:s} value={:s} role={:s}\n'.format(
            str(self.lable),
            str(self.count),
            str(self.repCode),
            RepCode.codeToName(self.repCode),
            str(self.units),
            str(self.value),
            str(self.role)
        )

    def getLabel(self):
        return self.lable

    def getCount(self):
        return self.count

    def getRepCode(self):
        return self.repCode

    def getUnits(self):
        return self.units

    def getValue(self):
        return self.value

    def getRole(self):
        return self.role


class AttrCompBase(object):
    """Represents an Attribute Component. See RP66v2 Sect. 8.6."""
    # Global defaults
    DEFAULT_COUNT = 1
    DEFAULT_REP_CODE = 19
    # Rep code IDENT
    lable = None
    # Rep code UVARI, defaults to 1
    count = 1
    # Rep code USHORT, defaults to IDENT (19)
    repCode = 19
    # Rep code UNITS
    units = None
    # Single value or list of values if count > 1
    value = None

    attributeList = []

    def __str__(self):

        return 'lable={:s} count={:s} rc={:s} ({:s}) units={:s} value={:s}\n'.format(
            str(self.lable),
            str(self.count),
            str(self.repCode),
            RepCode.codeToName(self.repCode),
            str(self.units),
            str(self.value)
        )

    def read(self, formatBits, theStream):

        if formatBits & 0x10:

            self.lable = RepCode.IDENTStream(theStream)
            print(self.lable)
        if formatBits & 0x8:
            self.count = RepCode.readUVARI(theStream)
            print(self.count)
        if formatBits & 0x4:
            self.repCode = RepCode.readUSHORT(theStream)
            print(self.repCode)
        if formatBits & 0x2:
            self.units = RepCode.UNITSStream(theStream)
            print(self.units)
        if formatBits & 0x1:

            if self.count > 1:
                self.value = [RepCode.readIndirectRepCode(self.repCode, theStream) for i in range(self.count)]
            else:
                self.value = RepCode.readIndirectRepCode(self.repCode, theStream)





    def readAsTemplate(self, formatBits, theStream):
        """Treats self as a template and reads from a stream.
        Returns a new AttrCompBase with the merged attributes."""
        r = AttrCompBase()
        for k in self.__dict__.keys():
            attr = getattr(self, k)
            setattr(r, k, attr)
        r.read(formatBits, theStream)
        return r

    def clearAttributeList(self):
        self.attributeList = []

class AttrCompStream(AttrCompBase):

    def print(self):
        for i in range(len(self.attributeList)):
            print(self.attributeList[i].lable._payload.decode("utf-8"))

        for i in range(len(self.dataList)):
            print(self.dataList[i])

    def getFrame(self):
        head = []
        data = []
        ret = {}
        head.append("")
        for i in range(len(self.attributeList)):
            head.append(self.attributeList[i].lable._payload.decode("utf-8").strip())

        for i in range(len(self.dataList)):
            data.append(self.dataList[i])

        ret["header"] = head
        ret["data"] = data

        return ret

    def getObjName(self):
        j=1
        header = []
        header.append("")
        for i in range(len(self.attributeList)):
            header.append(self.attributeList[i].lable._payload.decode("utf-8"))
            #print(header[j])
            if "ID" == header[j]:
                #obj = self.dataList[0][0]+self.dataList[0][j]
                obj = self.dataList[0][j]
                #self.attributeList = []
                #self.dataList = []
                return (obj)
            j=j+1

        return 0


    def writeFile(self,file):

        header=[]
        header.append("")
        for i in range(len(self.attributeList)):
            header.append(self.attributeList[i].lable._payload.decode("utf-8"))

        with open(file, "a") as f:
            f.write("\n\n")
            for i in range(len(header)):
                f.write(header[i]+ ", ")
            f.write("\n")

            for i in range(len(self.dataList)):
                for j in self.dataList[i]:
                    f.write(str(j)+", ")

                f.write("\n")
            f.write("\n\n")


    def __init__(self, formatBits, theStream):
        """Constructed with a bit mask whose 5 bits determine which field to
        read from the stream."""
        super().__init__()
        self.theStream = theStream
        self.dataList = []


    def read(self):

        attr = self.theStream.read(1)[0]
        attr = self.getBits(3,8,attr)

        super().read(int(attr,2),self.theStream)



    def readAll(self):
        self.clearAttributeList()
        self.size = 0
        self.ok = 0

        attr = self.theStream.read(1)[0]
        #print(attr)

        while(int(attr) != 52 and int(attr) != 60 and int(attr) != 56):
            #print(attr)
            attr = self.theStream.read(1)[0]
        self.ok = 1


        while True:

            if self.ok == 1:
                self.ok = 0
            else:
                attr = self.theStream.read(1)[0]
            attr2 = self.getBits(3, 8, attr)

            bits1_3 = self.getBits(0, 3, attr)

            if bits1_3 == "000":
                continue


            if ( bits1_3 != '001' and bits1_3 != '010'):
                break

            self.size = self.size + 1

            super().read(int(attr2, 2), self.theStream)
            self.role = self.getBits(0,3,self.repCode)
            attribute = Attribute(self.lable, self.count, self.repCode, self.units, self.value, self.role)
            self.attributeList.append(attribute)


        #self.print()
        while self.getBits(0, 3, attr) == '011':
            attr2 = self.getBits(3, 8, attr)
            self.l = []
            if int(attr2,2) & 0x10:

                id1 = self.theStream.read(1)[0]
                id2 = self.theStream.read(1)[0]
                name = RepCode.IDENTStream(self.theStream)

                self.l.append(str(id1)+"&"+str(id2)+"&"+str(name)[2:-1])


            attr = self.theStream.read(1)[0]

            attr = self.readWithTemplate(0,attr)

            try:
                bits1_3 = self.getBits(0, 3, attr)
            except:
                return


    def getBits(self,start,end,attr):
        return ("{0:08b}".format(attr))[start:end]

    def repcodeToString(self,a):

        if type(a) != RepCode.OBJREFStream and type(a) != RepCode.OBNAMEStream and type(a) != RepCode.DTIMEStream:
            st = str(a)
            if (len(st) > 1 and st[0] == "b" and st[len(st) - 1] == "'"):
                return(st[2:-1])
            else:
                return(st)
        elif type(a) == RepCode.DTIMEStream:
            s = a.mktime()

            return datetime.datetime.fromtimestamp(
                int(s)
            ).strftime('%d-%m-%Y %H:%M:%S')
        else:
            s = (a.identifier).payload
            return(s.decode("utf-8"))


    def readWithTemplate(self, ind, attr):

        bits1_3 = self.getBits(0, 3, attr)


        while ind < len(self.attributeList) and (bits1_3 == '000' or bits1_3 == '001' or bits1_3 == '010'):
            bits1_3 = self.getBits(0, 3, attr)
            a = None

            count = 1
            if bits1_3 == "001":
                repCode = self.attributeList[ind].repCode
                self.units = 0

                if attr & 0x10:
                    self.lable = RepCode.readIDENT(self.theStream)
                if attr & 0x8:
                    count = RepCode.readUVARI(self.theStream)
                if attr & 0x4:
                    repCode = RepCode.readUSHORT(self.theStream)
                if attr & 0x2:
                    self.units = RepCode.readUNITS(self.theStream)
                if attr & 0x1:
                    if count > 1:
                        a = [RepCode.readIndirectRepCode(repCode, self.theStream) for i in range(count)]
                    else:
                        a = RepCode.readIndirectRepCode(repCode, self.theStream)

                ind = ind + 1

            else:

                a = 0
                ind = ind + 1

            if count > 1 and attr & 0x1:
                lst = []
                for i in a:
                    if(self.units):
                        lst.append(self.repcodeToString(i).strip()  + " " + self.repcodeToString(self.units).strip())
                    else:
                        lst.append(self.repcodeToString(i).strip())
                self.l.append(lst)
            else:

                if self.units:
                    self.l.append(self.repcodeToString(a).strip() + " " + self.repcodeToString(self.units).strip())
                else:
                    self.l.append(self.repcodeToString(a).strip())

            self.units = 0



            if (ind == len(self.attributeList) - 1):
                self.dataList.append(self.l)

            try:
                attr = self.theStream.read(1)[0]
            except:
                return
            bits1_3 = self.getBits(0, 3, attr)

        return attr



