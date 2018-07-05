import re, time
import pexpect


def scanble(hci="hci0", timeout=1):
    conn = pexpect.spawn("sudo hciconfig %s reset" % hci)
    time.sleep(0.2)

    conn = pexpect.spawn("sudo timeout %d hcitool lescan" % timeout)
    time.sleep(0.2)

    conn.expect("LE Scan \.+", timeout=timeout)
    output = ""
    adr_pat = "(?P<addr>([0-9A-F]{2}:){5}[0-9A-F]{2}) (?P<name>.*)"
    while True:
        try:
            res = conn.expect(adr_pat)
            output += conn.after
        except pexpect.EOF:
            break

    lines = re.split('\r?\n', output.strip())
    lines = list(set(lines))
    lines = [line for line in lines if re.match(adr_pat, line)]
    lines = [re.match(adr_pat, line).groupdict() for line in lines]
    lines = [line for line in lines if re.match('.*', line['name'])]

    return lines

class BLEDevice:
    def __init__(self, addr=None,printCharacteristics=False):
        self.services = {}
        self.characteristics = {}
        if addr is not None:
            self.connect(addr)
            self.getcharacteristics(printCharacteristics=printCharacteristics)

    def connect(self, addr):
        print("connecting...")
        # Run gatttool interactively.
        self.gatt = pexpect.spawn("gatttool -b " + addr + " -I")
        self.gatt.expect('\[LE\]>', timeout=10)
        self.gatt.sendline('connect')
        self.gatt.expect('Connection successful.*\[LE\]>', timeout=5)
        print("Successfully connected!")

    def getservices(self):
        pass

    def getcharacteristics(self,printCharacteristics=False):
        self.gatt.sendline('characteristics')
        time.sleep(0.2)
        ch_pat='handle: (\S+), char properties: (\S+), char value handle: (\S+), uuid: (\S+)'
        #self.gatt.expect('\[LE\]>')
        while True:
            try:
                self.gatt.expect(ch_pat, timeout=2)
                ch_tuple = self.gatt.match.groups()
                uuid = ch_tuple[3][4:8]
                self.characteristics[uuid]=ch_tuple
                if printCharacteristics:
                    print(ch_tuple)
            except pexpect.TIMEOUT:
                break
        print("got all characteristics.")

    def gethandle(self, uuid):
        ch = self.characteristics[uuid]
        return int(ch[0],16)

    def getvaluehandle(self, uuid):
        ch = self.characteristics[uuid]
        return int(ch[2],16)

    def writecmd(self, handle, value,verbose=False):
        cmd = "char-write-cmd 0x%04x %s" % (handle, value)
        if verbose:
            print(cmd)
        #cmd = "char-write-cmd 0x%02x %s" % (handle, value.encode('hex'))
        self.gatt.sendline(cmd)
        
    def writereq(self, handle, value,verbose=False):
        cmd = "char-write-req 0x%02x %s" % (handle, value)
        if verbose:
            print(cmd)
        #cmd = "char-write-cmd 0x%02x %s" % (handle, value.encode('hex'))
        self.gatt.sendline(cmd)

    def notify(self):
        while True:
            try:
                num = self.gatt.expect('Notification handle = .*? \r', timeout=4)
            except pexpect.TIMEOUT:
                break
            if num == 0:
                hxstr = self.gatt.after.split()[3:]
                handle = long(float.fromhex(hxstr[0]))
                #print "Received: ", hxstr[2:]
                #return "".join(chr(int(x,16)) for x in hxstr[2:])
                to_return = {}
                to_return["handle"]=handle
                to_return["value"]="".join(chr(int(x,16)) for x in hxstr[2:])
                return to_return
        return None
