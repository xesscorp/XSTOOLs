# JTAG class
# File originally from http://excamera.com/sphinx/fpga-xess-python.html  

def islast(o):
    it = o.__iter__()
    e = it.next()
    while True:
        try:
            nxt = it.next()
            yield (False, e)
            e = nxt
        except StopIteration:
            yield (True, e)
            break

class Jtag(object):
    """
    JTAG Class
    Subclassers provide 'tick' and 'bulktdi' methods
    """

    verbose = False

    st = 0
    states = [
        ( "Test-Logic-Reset", 1,  0,  ), #  0
        ( "Run-Test/Idle",    1,  2,  ), #  1
        ( "Select-DR-Scan",   3,  9,  ), #  2
        ( "Capture-DR",       4,  5,  ), #  3
        ( "Shift-DR",         4,  5,  ), #  4
        ( "Exit1-DR",         6,  8,  ), #  5
        ( "Pause-DR",         6,  7,  ), #  6
        ( "Exit2-DR",         4,  8,  ), #  7
        ( "Update-DR",        1,  2,  ), #  8
        ( "Select-IR-Scan",   10, 0,  ), #  9
        ( "Capture-IR",       11, 12, ), #  10
        ( "Shift-IR",         11, 12, ), #  11
        ( "Exit1-IR",         13, 15, ), #  12
        ( "Pause-IR",         13, 14, ), #  13
        ( "Exit2-IR",         11, 15, ), #  14
        ( "Update-IR",        1,  2,  ), #  15
    ]

    def debug_tms(self, tms):
        self.st = self.states[self.st][1 + tms]

    def state(self):
        return self.states[self.st][0]

    def assert_state(self, s):
        assert self.state() == s

    def __repr__(self):
        return "<JTAG object state=%s>" % self.state()

    def debug(self, tms, tdi):
        if self.verbose:
            print "%18s TDI=%d TMS=%d" % (self.state(), tdi, tms)

    def do_bit(self, tms, tdi):
        self.debug_tms(tms)
        self.debug(tms = tms, tdi = tdi)
        return self.tick(tms, tdi)

        sample = self.sample()
        self.debug(tms = tms, tdi = tdi)
        self.operate(tck = 0, tms = tms, tdi = tdi)
        self.operate(tck = 1, tms = tms, tdi = tdi)
        return sample

    def go_state(self, tms):
        self.debug_tms(tms)
        self.debug(tms = tms, tdi = 0)
        return self.tick(tms, 0)

        self.debug(tms = tms, tdi = 0)
        self.operate(tck = 0, tms = tms, tdi = 0)
        self.operate(tck = 1, tms = tms, tdi = 0)

    def go_states(self, *ss):
        for s in ss:
            self.go_state(s)

    def do_nbit(self, n, data):
        r = 0
        for i in range(n):
            assert(self.state().startswith("Shift-"))
            mask = 1 << i
            is_lastbit = (i == (n - 1))
            tdo = self.do_bit(tms = is_lastbit, tdi = (data & mask) != 0)
            if tdo:
                r |= mask
        assert(self.state().startswith("Exit1-"))
        return r

    def do_nbit_cycle(self, n, data):
        r = 0
        for i in range(n):
            mask = 1 << i
            tdo = self.do_bit(tms = 0, tdi = (data & mask) != 0)
            if tdo:
                r |= mask
        return r

    def goTLR(self):
        for i in range(10):
            self.go_state(1)

    def goSelectDRScan(self):
        for i in range(10):
            self.go_state(1)
        self.go_state(0)
        self.go_state(1)
        assert(jt.state() == "Select-DR-Scan")

    def initTAP(self):
        for i in range(10):
            self.go_state(1)
        self.go_state(0)

        self.go_state(1)
        self.go_state(1)
        self.go_state(0)
        self.go_state(0)

    def tlr(self):
        """Go to Test-Logic-Reset"""
        while self.state() != "Test-Logic-Reset":
            self.go_state(1)

    def rti(self):
        """Go to Run-Test/Idle"""
        if self.state() != "Run-Test/Idle":
            self.tlr()
            self.go_state(0)

    def sendbs(self, bs):
        """ Send bitstream over TDI, raising TMS for last bit """
        assert(self.state().startswith("Shift-"))
        if len(bs) < 256:
            for (is_lastbit, d) in islast(bs):
                self.do_bit(tms = is_lastbit, tdi = d)
        else:
            self.bulktdi(bs)
        assert(self.state().startswith("Exit1-"))

    def sendrecvbs(self, bs):
        """ Send bitstream over TDI, raising TMS for last bit, return the accumulated TDO value """
        assert(self.state().startswith("Shift-"))
        r = 0
        mask = 1
        for (is_lastbit, d) in islast(bs):
            tdo = self.do_bit(tms = is_lastbit, tdi = d)
            if tdo:
                r |= mask
            mask <<= 1
        assert(self.state().startswith("Exit1-"))
        return r

    def LoadBSIRthenBSDR(self, instruction, send, receive = False):
        """
        Load the BSIR with an instruction, execute the instruction, and then capture and reload the BSDR.
        after completion, state is Run-Test/Idle.
        """
        if self.state() != "Shift-IR":
            self.rti()
            self.go_states(1,1,0,0)
        self.assert_state("Shift-IR")
        if self.verbose:
            print "IR", list(instruction)
        self.sendbs(instruction)
        self.go_state(1)
        self.assert_state("Update-IR")
        recv = None
        if self.verbose:
            if send:
                print "DR", list(send)
        if send:
            self.go_states(1, 0, 0)
            self.assert_state("Shift-DR")
            if receive:
                recv = self.sendrecvbs(send)
            else:
                self.sendbs(send)
            self.go_state(1)
            self.assert_state("Update-DR")
        self.go_state(0)
        self.assert_state("Run-Test/Idle")
        return recv
