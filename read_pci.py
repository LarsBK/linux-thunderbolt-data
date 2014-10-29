import re
from sys import argv

from pylatex import Document, Section, Subsection, Table, Math, TikZ, Axis, \
    Plot
from pylatex.base_classes import BaseLaTeXClass, BaseLaTeXContainer
from pylatex.utils import italic, dumps_list
import glob

class Rectangle(BaseLaTeXContainer):
    def __init__(self, p1, p2, options="", fill=False):
        packages = []
        self.p1, self.p2 = p1,p2
        self.options = options
        self.fill = fill
        super().__init__(packages=packages)

    def dumps(self):
        if self.fill:
            return "\\filldraw[{0}] {1} rectangle {2} {3};".format(
                    self.options,self.p1, self.p2, dumps_list(self))
        else:
            return "\\draw[{0}] {1} rectangle {2} {3};".format(
                    self.options,self.p1, self.p2, dumps_list(self))

class Grid(BaseLaTeXClass):
    def __init__(self, p1, p2, options="step=1,gray,very thin"):
        packages = []
        self.p1, self.p2 = p1,p2
        self.options = options
        super().__init__(packages=packages)

    def dumps(self):
        return "\draw[{0}] {1} grid {2};".format(self.options,self.p1, self.p2)

class Node(BaseLaTeXContainer):
    def __init__(self, name, options=""):
        packages = []
        self.options = options
        self.name = name
        super().__init__(packages=packages)

    def dumps(self, no_slash=True):
        if no_slash:
            return "node({1}) [{0}] {{ {2} }}".format(
                    self.options,self.name, dumps_list(self))
        else:
            return "\\node({1}) [{0}] {{ {2} }}".format(
                    self.options,self.name, dumps_list(self))



def factory(desc):
    g = PciNode.firstLine.match(desc[0]).groups()
    bus, dev, func, dev_type, name = g
    if dev_type == "PCI bridge":
        return PciBridge(bus,dev,func,dev_type,name,desc)
    else:
        return PciNode(bus,dev,func,dev_type,name,desc)




class PciNode(object):
    firstLine = re.compile(r"([0-f]+):([0-f]+).([0-f]+) (.*?): (.*)")

    def __init__(self, bus, dev, func, dev_type, name, desc):
        self.desc = desc
        self.bus, self.dev, self.func, self.dev_type, self.name  = bus, dev, func,dev_type, name
        self.parse()

    def __str__(self):
        return "{0} [{1},{2},{3}]".format(self.dev_type, self.bus, self.dev,
                self.func)

    def parse(self):
        pass

    def bus_no(self):
        return self.bus

class PciBridge(PciNode):
    BusLine = re.compile(r"Bus: primary=([0-f]+), secondary=([0-f]+), subordinate="
            "([0-f]+), sec-latency=([0-f]+)")
    MmioLine = re.compile(r"Memory behind bridge: ([0-f]+)-([0-f]+)")
    PrefLine = re.compile(r"Prefetchable memory behind bridge: ([0-f]+)-([0-f]+)")

    def parse(self):
        g = None
        m = None
        p = None
        for line in self.desc:
            if g is None:
                g = PciBridge.BusLine.match(line)
            if m is None:
                m = PciBridge.MmioLine.match(line)
            if p is None:
                p = PciBridge.PrefLine.match(line)
        if g is None:
            raise Exception("Error parsing bridge data")
        if m is None:
            self.mmio_start, self.mmio_end = None,None
        else:
            self.mmio_start, self.mmio_end = [int(x, base=16) for x in
                    m.groups()]
        if p is None:
            self.pref_start, self.pref_end = None,None
        else:
            self.pref_start, self.pref_end = [int(x, base=16) for x in
                    p.groups()]
        g = g.groups()
        _, self.bus_sec, self.bus_sub, _ = g
        self.children = []

    def __str__(self):
        return "PCI bridge [{}-{}]".format(self.bus_sec, self.bus_sub)

    def bus_range(self):
        return (self.bus_sec, self.bus_sub)

    def pref_range(self):
        return (self.pref_start, self.pref_end)

    def mmio_range(self):
        return (self.mmio_start, self.mmio_end)

    def add_nodes(self, others):
        unused = []
        for other in others:
            b = int(other.bus_no(), base=16)
            if b >= int(self.bus_sec, base=16) and b <= int(self.bus_sub,
                    base=16):
                self.children.append(other)
            else:
                unused.append(other)
        for c in self.children:
            try:
                self.children = c.add_nodes(self.children)
            except AttributeError:
                pass
        return unused

    def __iter__(self):
        return iter(self.children)

def generate(f):
    devices = []

    current = []
    for line in f:
        if line == "\n":
            try:
                devices.append(factory(current))
            except Exception as e:
                print(e)
            current = []
        else:
            current.append(line.strip())

    on_root = [x for x in devices if int(x.bus_no(), base=16) == 0]
    not_root = [x for x in devices if int(x.bus_no(), base=16) != 0]
    for d in on_root:
        try:
            not_root = d.add_nodes(not_root)
        except AttributeError:
            pass
    return on_root, not_root

def rec_gen(root, bus_doc, mmio_doc, level=0, mm_start=0xd0000000,
        mm_end=0xe0000000):
    mm_scale = 0.1 * (mm_end - mm_start)
    for d in root:
        print(str("    "*level)+ str(d))
        if isinstance(d, PciBridge):
            #Busses
            sc, sb = d.bus_range()
            sc = int(sc, base=16)
            sb = int(sb, base=16)
            r1 = Rectangle((level,sc/5.0),(level+1,(sb+1)/5.0), fill=True,
                options="fill=black!40!white, draw=black")
            n = Node("dev", options="midway")
            n.append("\\tiny{{ \\tiny{{ {0} - {1} }} }}".format(*d.bus_range()))
            r1.append(n)
            bus_doc.append(r1)

            #mmio
            ms, me = d.mmio_range()
            if ms < me and ms >= mm_start and me <= mm_end:
                r2 = Rectangle((level,ms/mm_scale -
                    mm_start/mm_scale),(level+1,me/mm_scale -
                        mm_start/mm_scale), fill=True,
                    options="fill=black!40!white, draw=black")
                n = Node("dev", options="midway,align=center, font=\\tiny\\tiny")
                n.append("{0:x} \\\\ {1:.0f}MB".format(ms, (me - ms) / 1000000))
                r2.append(n)

                mmio_doc.append(r2)
            
            ms, me = d.pref_range()
            if ms < me and ms >= mm_start and me <= mm_end:
                r2 = Rectangle((level,ms/mm_scale -
                    mm_start/mm_scale),(level+1,me/mm_scale -
                        mm_start/mm_scale), fill=True,
                    options="fill=black!40!white, draw=black")
                n = Node("dev", options="midway,align=center, font=\\tiny\\tiny")
                n.append("pref {0:x} \\\\ {1:.0f}MB".format(ms, (me - ms) / 1000000))
                r2.append(n)

                mmio_doc.append(r2)
            rec_gen(d, bus_doc, mmio_doc, level=level+1, mm_start=mm_start,
                    mm_end=mm_end)
        else:
            b = d.bus_no()
            b = int(b, base=16)
            r1 = Rectangle((level,b/5.0),(level+0.5,(b+1)/5.0), fill=True,
                options="fill=black, draw=black")
            if level != 0:
                n = Node("dev", options="right")
                n.append("\\tiny{{ \\tiny{{ {0} }} }}".format(d))
                r1.append(n)
            bus_doc.append(r1)

for filename in glob.glob("**/**/**/**/**/lspci.txt"):
    print(filename)
    try:
        with open(filename,"r") as f:
            doc = Document(filename+"_figure")
            bus_doc = TikZ()
            mmio_doc = TikZ()
            on_root, not_root = generate(f)

            bridges_mm = [ x.mmio_range() for x in on_root if
                    isinstance(x,PciBridge) and x.mmio_range()[1] -
                    x.mmio_range()[0] > 0]
            bridges_mm.extend( [ x.pref_range() for x in on_root if
                    isinstance(x,PciBridge) and x.pref_range()[1] -
                    x.pref_range()[0] > 0] )
            bridges_mm.sort( key=lambda x: x[0])
            mm_start = bridges_mm[0][0]
            bridges_mm.sort( key=lambda x: x[1])
            mm_end = bridges_mm[-1][1]
            print(bridges_mm)
            for a in bridges_mm:
                print( (a[1] - a[0]) / 1000000)
            for b in on_root:
                if isinstance(b, PciBridge):
                    print( b.bus_range() )
            rec_gen(on_root, bus_doc, mmio_doc, mm_start=mm_start, mm_end=mm_end)

#tikz.append(Rectangle((0,0),(1,255/20.0), options="thick"))
#tikz.append(Grid((0,0), (10, 255/20.0),
#    options="step={0},gray,very thin".format(1/20.0)))

            f = open("{0}-bus.tex".format(filename), "w")
            f.write(bus_doc.dumps())
            f.close()
            f = open("{0}-mmio.tex".format(filename), "w")
            f.write(mmio_doc.dumps())
            f.close()

            doc.append(bus_doc)
            doc.append(mmio_doc)
            doc.generate_pdf()
    except Exception as e:
        raise
