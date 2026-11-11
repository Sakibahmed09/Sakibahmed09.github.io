"""Sakib Grotesk 0.4 — parametric outline study after Söhne public specimens.
Run with Python 3 and fonttools[woff]. No third-party outlines are imported.
"""
from pathlib import Path
import math, string, unicodedata, json
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.areaPen import AreaPen
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
from fontTools.varLib import build
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont
from fontTools.agl import UV2AGL

ROOT=Path(__file__).resolve().parent
MASTERS=ROOT/'masters'; MASTERS.mkdir(exist_ok=True)
OUT=ROOT/'build'; OUT.mkdir(exist_ok=True)

class Drawing:
 def __init__(self):self.pen=TTGlyphPen(None)
 def path(self,commands,hole=False):
  rec=RecordingPen(); current=(0,0)
  for c in commands:
   op,*v=c
   if op=='M':current=(v[0],v[1]);rec.moveTo(current)
   elif op=='L':current=(v[0],v[1]);rec.lineTo(current)
   elif op=='Q':rec.qCurveTo((v[0],v[1]),(v[2],v[3]));current=(v[2],v[3])
   elif op=='C':
    p0=current;p1=(v[0],v[1]);p2=(v[2],v[3]);p3=(v[4],v[5])
    def point(t):return tuple((1-t)**3*p0[i]+3*(1-t)**2*t*p1[i]+3*(1-t)*t*t*p2[i]+t**3*p3[i] for i in [0,1])
    for i in range(6):
     a=point(i/6);b=point((i+1)/6);m=point((i+.5)/6)
     rec.qCurveTo(tuple(2*m[j]-(a[j]+b[j])/2 for j in [0,1]),b)
    current=p3
  rec.closePath(); ap=AreaPen(None);rec.replay(ap)
  rec.replay(ReverseContourPen(self.pen) if (ap.value<0)!=hole else self.pen)
 def poly(self,*pts):self.path([('M',*pts[0])]+[('L',*p) for p in pts[1:]])
 def rect(self,x,y,w,h):self.poly((x,y),(x+w,y),(x+w,y+h),(x,y+h))
 def oval(self,x,y,w,h,hole=False):
  k=.55228475;cx=x+w/2;cy=y+h/2;rx=w/2;ry=h/2
  self.path([('M',cx+rx,cy),('C',cx+rx,cy+k*ry,cx+k*rx,cy+ry,cx,cy+ry),('C',cx-k*rx,cy+ry,cx-rx,cy+k*ry,cx-rx,cy),('C',cx-rx,cy-k*ry,cx-k*rx,cy-ry,cx,cy-ry),('C',cx+k*rx,cy-ry,cx+rx,cy-k*ry,cx+rx,cy)],hole)
 def ring(self,x,y,w,h,th,tv=None):
  tv=tv or th*.88;self.oval(x,y,w,h);self.oval(x+th,y+tv,w-2*th,h-2*tv,True)
 def line(self,x1,y1,x2,y2,t):
  l=math.hypot(x2-x1,y2-y1);nx=-(y2-y1)*t/2/l;ny=(x2-x1)*t/2/l
  self.poly((x1+nx,y1+ny),(x2+nx,y2+ny),(x2-nx,y2-ny),(x1-nx,y1-ny))
 def finish(self):
  g=self.pen.glyph()
  if g.numberOfContours>0:g.flags[0]|=0x40
  return g

# Same contour topology in every weight master; aside argument retained internally at zero.
def draw(ch,wght,aside):
 d=Drawing();t=88+(wght-400)*.24;f=0;h=t*.84;adv=560
 def stem(x,y=0,height=520,bottom=True):d.rect(x,y,t,height)
 def bowl(x=38,y=-10,w=470,hh=540):d.ring(x,y,w,hh,t,h)
 def dot(x,y,r=None):
  r=r or t*.56
  if y==49:y=r
  d.rect(x-r,y-r,2*r,2*r)
 def arch(x=66,width=414,top=530,bottom=0):
  d.path([('M',x,bottom),('L',x,520),('L',x+t,520),('L',x+t,446),('C',x+t+37,502,x+width*.53,top,x+width*.65,top),('C',x+width*.89,top,x+width,460,x+width,337),('L',x+width,bottom),('L',x+width-t,bottom),('L',x+width-t,329),('C',x+width-t,423,x+width*.80,top-h,x+width*.62,top-h),('C',x+t+(width-2*t)*.20,top-h,x+t,397,x+t,309),('L',x+t,bottom)])
 def cshape(cap=False):
  H=710 if cap else 530;W=590 if cap else 500;mid=(H-10)/2;cx=W*.57
  d.path([('M',W-15,H-83),('C',W-62,H-23,W-125,H,cx,H),('C',106,H,38,H*.80,38,mid),('C',38,H*.20,106,-10,cx,-10),('C',W-125,-10,W-58,15,W-10,82),('L',W-55,82+h*.61),('C',W-98,29+h,W-137,-10+h,cx,-10+h),('C',153,-10+h,38+t,H*.24,38+t,mid),('C',38+t,H*.76,153,H-h,cx,H-h),('C',W-137,H-h,W-99,H-h-31,W-61,H-83-h*.55)])
  return W+30
 def sshape(H=520,W=465):
  p=[('M',439,445),('C',395,502,329,530,247,530),('C',126,530,52,465,52,380),('C',52,285-h*.1,115,265-h*.2,243,265-h*.5),('C',458-t,210,458-t,184,458-t,136),('C',458-t,82+h*.25,330-t*.25,h-10,259,h-10),('C',178,h-10,116,h+19,28+t*.57,95+t*.57),('L',28,95),('C',77,26,164,-10,258,-10),('C',379,-10,458,48,458,139),('C',458,260+h*.2,385,265+h*.2,263,265+h*.5),('C',165,265+h*.7,52+t,350,52+t,390),('C',52+t,530-h,201,530-h,252,530-h),('C',312,530-h,350,530-h-22,439-t*.65,445-t*.65)]
  d.path([tuple([c[0]]+sum(([c[i]*W/465,c[i+1]*H/520] for i in range(1,len(c),2)),[])) for c in p])
 def desc_tail(x,top=0):
  d.path([('M',x,top),('L',x,-55),('C',x,-230,160,-260,65,-150),('L',100+f*12,-100),('C',170,-180,x-t,-177,x-t,-45),('L',x-t,top)])
 if ch in 'oO0':
  if ch=='o':bowl(38,-10,484,540);adv=560
  elif ch=='O':bowl(40,-12,624,724);adv=704
  else:bowl(40,-12,534,724);adv=614
 elif ch in 'cC':adv=cshape(ch=='C')
 elif ch=='e':
  # Open aperture, even roof, and a slightly forward counter. The earlier
  # one-curve counter never reached its intended height and blackened the eye.
  d.path([('M',500,239),('L',500,278),('C',500,436,424,530,279,530),('C',130,530,38,421,38,260),('C',38,96,133,-10,290,-10),('C',377,-10,444,18,493,81),('L',450,126+8*f),('C',410,77,358,h-10,293,h-10),('C',182,h-10,38+t,127,38+t,239),('L',500,239)])
  d.path([('M',38+t+2,239+h),('L',500-t,239+h),('C',500-t,407,378,530-h,279,530-h),('C',180,530-h,38+t+13,405,38+t+2,239+h)],True);adv=540
 elif ch=='a':
  # A continuous double-storey construction; no ellipse attached to a stem.
  d.path([('M',447+t,0),('C',381+t,-16,421,-2,412,65),('C',364,13,305,-10,228,-10),('C',112,-10,42,48,42,144),('C',42,247,125,280,267,311),('L',402,343),('L',402,347),('C',402,426,356,530-h,275,530-h),('C',208,530-h,153,444,99,404),('L',65,453),('C',126,502,200,530,280,530),('C',414,530,402+t,467,402+t,345),('L',402+t,99),('C',402+t,67,418+t,57,447+t,65),('L',447+t,0)])
  d.path([('M',402,274),('L',275,244),('C',176,220,42+t,209,42+t,150),('C',42+t,87,160,h-10,235,h-10),('C',329,h-10,402,115,402,201),('L',402,274)],True);adv=476+t
 elif ch in 'bdpq':
  desc=ch in 'pq';low=-205 if desc else 0;top=520 if desc else 700
  outer=[('M',65,low),('L',65,top),('L',65+t,top),('L',65+t,458),('C',187,506,236,530,299,530),('C',432,530,510,426,510,260),('C',510,94,430,-10,294,-10),('C',230,-10,182,17,65+t,67),('L',65+t,low)]
  inner=[('M',65+t,260),('C',65+t,134,201,h-10,286,h-10),('C',385,h-10,510-t,137,510-t,260),('C',510-t,383,385,530-h,286,530-h),('C',201,530-h,65+t,386,65+t,260)]
  def mirror(cmds):return [tuple([c[0]]+sum(([565-c[i],c[i+1]] for i in range(1,len(c),2)),[])) for c in cmds]
  d.path(mirror(outer) if ch in 'dq' else outer);d.path(mirror(inner) if ch in 'dq' else inner,True);adv=570
 elif ch=='g':
  d.path([('M',440,520),('L',440+t,520),('L',440+t,9),('C',440+t,-121,430,-198,280,-198),('C',162,-198,84,-151,48,-67),('L',124,-36),('C',155,-99,204,-126,279,-126),('C',384,-126,440,-82,440,12),('L',440,76),('C',399,18,338,-10,268,-10),('C',124,-10,38,96,38,260),('C',38,425,125,530,269,530),('C',340,530,399,502,440,449)])
  d.path([('M',440,260),('C',440,383,379,530-h,286,530-h),('C',184,530-h,38+t,382,38+t,260),('C',38+t,137,185,h-10,287,h-10),('C',380,h-10,440,135,440,260)],True);adv=590
 elif ch in 'nh':
  arch();adv=553
  if ch=='h':stem(66,490,210)
 elif ch=='m':
  arch(65,280+t);arch(345,280+t);adv=690+t
 elif ch=='u':
  d.path([('M',65,520),('L',65,183),('C',65,60,114,-10,210,-10),('C',274,-10,366,18,413,74),('L',413,0),('L',413+t,0),('L',413+t,520),('L',413,520),('L',413,211),('C',413,123,347,h-10,256,h-10),('C',183,h-10,65+t,97,65+t,191),('L',65+t,520)])
  adv=550
 elif ch=='r':
  d.path([('M',65,0),('L',65,520),('L',65+t,520),('L',65+t,425),('C',65+t+37,502,249,535,330,527),('L',330,527-t),('C',217,546-t,65+t,389,65+t,261),('L',65+t,0)]);adv=365
 elif ch in 'iljı':
  adv=242;d.rect(76,0,t,700 if ch=='l' else 520)
  if ch in 'ij':dot(76+t/2,700-t*.56)
  if ch=='j':
   d.path([('M',76,5),('L',76,-29),('C',76,-105,53,-128,-14,-120),('L',-14,-190),('C',109,-210,76+t,-147,76+t,-23),('L',76+t,5)])
 elif ch=='k':
  stem(65,0,700)
  d.poly((65+t,238),(379,520),(489,520),(65+t,128))
  d.poly((281,333),(510,0),(397,0),(219,260));adv=535
 elif ch=='t':
  d.path([('M',104,665),('L',104+t,665),('L',104+t,156),('C',104+t,77,235,57,319,75),('L',319,2),('C',183,-27,104,14,104,144)]);d.rect(25,520-h,295,h);adv=360
 elif ch=='f':
  d.path([('M',105,0),('L',105,516),('C',105,662,172,727,309,711),('L',309,638),('C',230,649,105+t,618,105+t,523),('L',105+t,0)]);d.rect(28,520-h,277,h);adv=335
 elif ch=='s':sshape();adv=490
 elif ch in 'vw':
  if ch=='v':
   d.poly((17,520),(17+t,520),(265,103),(426,520),(517,520),(311,0),(215,0));adv=535
  else:
   d.poly((18,520),(18+t,520),(163,111),(275,520),(367,520),(478,111),(572,520),(661,520),(523,0),(430,0),(319,390),(207,0),(114,0));adv=680
 elif ch=='x':
  d.poly((25,520),(25+t*1.08,520),(504,0),(504-t*1.08,0));d.poly((411,520),(510,520),(120,0),(21,0));adv=535
 elif ch=='y':
  d.poly((17,520),(17+t*1.06,520),(263,107),(425,520),(519,520),(303,-15),(216,0))
  d.path([('M',303,-15),('C',249,-157,214,-201,60,-190),('L',60,-117),('C',142,-125,178,-116,216,0)]);adv=535
 elif ch=='z':d.poly((42,520),(470,520),(470,520-h),(130,h),(481,h),(481,0),(32,0),(32,h),(380,520-h),(42,520-h));adv=520
 elif ch in 'HIEF':
  adv={'H':715,'I':250,'E':605,'F':566}[ch];stem(70,0,700)
  if ch=='H':stem(adv-70-t,0,700);d.rect(70,318,adv-140,h)
  elif ch=='I':
   d=Drawing();d.rect((adv-t)/2,0,t,700)
  else:
   d.rect(70,700-h,adv-110,h);d.rect(70,324,adv-140,h)
   if ch=='E':d.rect(70,0,adv-102,h)
 elif ch in 'LT':
  if ch=='L':stem(70,0,700);d.rect(70,0,430,h);adv=540
  else:d.rect(25,700-h,530,h);stem(290-t/2,0,700);adv=580
 elif ch=='A':
  d.poly((15,0),(283,700),(393,700),(665,0),(665-t*1.04,0),(338,603),(15+t*1.04,0))
  d.rect(153,211,369,h);adv=682
 elif ch in 'VWMN':
  if ch=='V':d.poly((20,700),(20+t*1.07,700),(312,113),(530,700),(608,700),(350,0),(270,0));adv=630
  elif ch=='W':
   for x in [18,360]:d.poly((x,700),(x+t,700),(x+190,108),(x+330,700),(x+405,700),(x+240,0),(x+152,0))
   adv=800
  elif ch=='N':stem(70,0,700);stem(520,0,700);d.poly((70,700),(70+t,700),(520+t,0),(520,0));adv=660
  else:
   stem(60,0,700);stem(670-t,0,700);d.poly((60,700),(60+t,700),(365,146),(670-t,700),(670,700),(410,40),(321,40));adv=730
 elif ch in 'BPRD':
  adv=600;stem(70,0,700)
  if ch=='D':
   d.path([('M',70,700),('L',285,700),('C',675,700,675,0,285,0),('L',70,0),('L',70,h),('L',285,h),('C',560,h,560,700-h,285,700-h),('L',70,700-h)])
   adv=642
  else:
   d.path([('M',70,700),('L',304,700),('C',620,700,620,303,304,303),('L',70,303),('L',70,303+h),('L',299,303+h),('C',510,303+h,510,700-h,299,700-h),('L',70,700-h)])
   if ch=='R':d.poly((280,347),(280+t*1.15,347),(591,0),(480,0));adv=622
   if ch=='B':
    d.path([('M',70,365),('L',320,365),('C',670,365,670,0,320,0),('L',70,0),('L',70,h),('L',315,h),('C',545,h,545,365-h,315,365-h),('L',70,365-h)])
    adv=640
 elif ch=='G':
  d.path([('M',665,0),('L',665,359),('L',375,359),('L',375,359-h),('L',665-t,359-h),('C',665-t,140,506,h-12,369,h-12),('C',209,h-12,40+t,148,40+t,350),('C',40+t,552,215,712-h,368,712-h),('C',478,712-h,555,574,584,491),('L',665,519),('C',620,640,515,712,365,712),('C',165,712,40,570,40,350),('C',40,131,165,-12,363,-12),('C',467,-12,552,30,586,89),('L',596,0)]);adv=710
 elif ch=='Q':bowl(36,-10,590,720);d.line(350,176,644+f*26,-100,t*.85);adv=670
 elif ch=='S':sshape(700,540);adv=573
 elif ch=='J':
  d.path([('M',402,700),('L',402,210),('C',402,2,145,8,100,166),('L',30,146),('C',62,-90,402+t,-83,402+t,210),('L',402+t,700)])
  adv=540
 elif ch=='K':
  stem(70,0,700);d.poly((70+t,331),(480,700),(574,700),(70+t,218));d.poly((263,439),(592,0),(480,0),(205,366));adv=620
 elif ch=='U':
  d.path([('M',65,700),('L',65,220),('C',65,-85,590,-85,590,220),('L',590,700),('L',590-t,700),('L',590-t,230),('C',590-t,30,65+t,30,65+t,230),('L',65+t,700)]);adv=655
 elif ch=='X':d.poly((25,700),(25+t*1.24,700),(615,0),(615-t*1.24,0));d.poly((518,700),(610,700),(112,0),(20,0));adv=640
 elif ch=='Y':
  d.poly((15,700),(15+t*1.2,700),(304,391),(520,700),(610,700),(340,310),(340,0),(340-t,0),(340-t,310));adv=625
 elif ch=='Z':d.poly((37,700),(558,700),(558,700-h),(130,h),(568,h),(568,0),(28,0),(28,h),(465,700-h),(37,700-h));adv=600
 elif ch=='1':
  d.path([('M',369,0),('L',369,700),('L',369-t,700),('C',280,602,225,579,104,579),('L',104,506),('L',369-t,506),('L',369-t,0)]);adv=490
 elif ch=='2':
  d.path([('M',58,510),('C',6,652,118,712,265,712),('C',416,712,515,633,515,510),('C',515,395,435,321,317,229),('L',127,h),('L',526,h),('L',526,0),('L',32,0),('L',32,h),('L',261,264),('C',374,354,515-t,419,515-t,510),('C',515-t,589,370,712-h,267,712-h),('C',170,712-h,116,582,145,510)]);adv=565
 elif ch=='3':
  d.path([('M',54,594),('C',215,806,510,728,510,537),('C',510,438,455,382,372,350),('C',575,300,574,-10,292,-10),('C',151,-10,74,50,34,120),('L',93,164),('C',172,26,510-t,26,510-t,193),('C',510-t,292,335,317,220,317),('L',220,382),('C',347,382,440,427,440,531),('C',440,655,206,686,110,550)]);adv=550
 elif ch=='4':
  d.poly((335,700),(430,700),(430,0),(430-t,0),(430-t,597),(114,237),(520,237),(520,237-h),(40,237-h),(40,246));adv=550
 elif ch=='5':
  d.path([('M',485,700),('L',485,700-h),('L',144,700-h),('L',127,416),('C',360,523,520,416,520,220),('C',520,-54,147,-87,34,116),('L',95,155),('C',197,-7,520-t,37,520-t,218),('C',520-t,398,217,400,110,319),('L',52,350),('L',83,700)]);adv=550
 elif ch in '68':
  d.ring(40,-10,470,400,t,h)
  if ch=='8':d.ring(65,332,420,378,t,h)
  else:d.path([('M',40,190),('C',15,622,259,832,495,653),('L',458,590),('C',244,739,109,538,40+t,250)])
  adv=550
 elif ch=='7':d.poly((35,700),(522,700),(522,700-h),(237,0),(150,0),(431,700-h),(35,700-h));adv=550
 elif ch=='9':
  d.ring(40,311,470,399,t,h);d.path([('M',510,510),('C',535,78,291,-132,55,47),('L',92,110),('C',306,-39,441,162,510-t,450)]);adv=550
 elif ch in '.,:;!·':
  adv=240;dot(120,290 if ch=='·' else 49)
  if ch in ':;':dot(120,414)
  if ch in ',;':d.poly((160,60),(161,-22),(74,-116),(57,-97),(105,-10))
  if ch=='!':d.poly((79,700),(161,700),(148,210),(92,210))
 elif ch=='?':
  d.path([('M',28,549),('C',75,784,510,775,510,540),('C',510,395,315,370,315,230),('L',315-t,230),('C',248,425,510-t,440,510-t,540),('C',510-t,689,149,688,98,526)]);dot(280,49);adv=550
 elif ch in "'‘’":
  adv=220;pts=[(65,710),(152,710),(145,612),(86,539),(60,555),(96,627),(65,627)]
  if ch=='‘':pts=[(220-x,1249-y) for x,y in pts]
  d.poly(*pts)
 elif ch in '"“”':
  adv=360
  for x in [55,209]:
   pts=[(x,710),(x+87,710),(x+80,612),(x+21,539),(x-5,555),(x+31,627),(x,627)]
   if ch=='“':pts=[(2*x+87-px,1249-py) for px,py in pts]
   d.poly(*pts)
 elif ch in '-–—_=':
  adv={'-':360,'–':550,'—':950,'_':550,'=':550}[ch];d.rect(35,-60 if ch=='_' else 255,adv-70,h)
  if ch=='=':d.rect(35,415,adv-70,h)
 elif ch in '()[]{}':
  adv=320;left=ch in '([{'
  if ch in '()':
   cmds=[('M',262,800),('C',55,570,55,130,262,-100),('L',208,-139),('C',-10,103,-10,590,208,839)]
   if not left:cmds=[tuple([c[0]]+sum(([320-c[i],c[i+1]] for i in range(1,len(c),2)),[])) for c in cmds]
   d.path(cmds)
  elif ch in '{}':
   cmds=[('M',285,800),('C',100,830,135,600,135,470),('Q',135,350,45,350),('L',45,280),('Q',135,280,135,160),('C',135,30,100,-200,285,-170),('L',285,-105),('C',177,-118,205,12,205,160),('Q',205,300,125,315),('Q',205,330,205,470),('C',205,618,177,748,285,735)]
   if not left:cmds=[tuple([c[0]]+sum(([330-c[i],c[i+1]] for i in range(1,len(c),2)),[])) for c in cmds]
   d.path(cmds);adv=350
  else:
   x=82 if left else 170;d.rect(x,-100,t,900);d.rect(82,-100,160,h);d.rect(82,800-h,160,h)
 elif ch in '/\\':d.line(35 if ch=='/' else 390,-100,390 if ch=='/' else 35,760,h);adv=425
 elif ch=='+':d.rect(40,280,470,h);d.rect(275-h/2,80,h,470);adv=550
 elif ch=='*':
  for a in [0,math.pi/3,2*math.pi/3]:d.line(270-180*math.cos(a),510-180*math.sin(a),270+180*math.cos(a),510+180*math.sin(a),h*.7)
  adv=540
 elif ch=='#':
  for x in [150,350]:d.line(x,0,x+80,700,h)
  d.rect(30,200,530,h);d.rect(55,430,530,h);adv=620
 elif ch=='%':
  d.ring(25,400,245,310,h*.7);d.ring(340,-10,245,310,h*.7);d.line(60,0,550,700,h);adv=620
 elif ch=='&':
  d.path([('M',520,568),('C',520,780,140,760,140,548),('C',140,400,535,20,620,-15),('L',659,46),('C',520,150,140+t,450,140+t,550),('C',140+t,675,520-t,675,520-t,568),('C',520-t,430,40,346,40,160),('C',40,-88,536,-88,589,335),('L',518,335),('C',475,18,40+t,12,40+t,160),('C',40+t,300,520,393,520,568)]);adv=700
 elif ch in '£$€':
  if ch=='£':
   d.path([('M',485,594),('C',335,797,112,731,112,505),('L',112,150),('C',112,90,75,55,45,0),('L',520,0),('L',520,h),('L',149,h),('C',183,117,112+t,155,112+t,202),('L',112+t,505),('C',112+t,669,329,692,429,546)]);d.rect(35,320,365,h)
  else:
   if ch=='$':sshape(700,510);d.rect(235,-85,h*.75,875)
   else:cshape(True);d.rect(5,300,405,h*.65);d.rect(5,415,405,h*.65)
  adv=590
 elif ch=='@':
  d.ring(25,-125,750,850,h*.72);d.ring(215,100,345,448,h*.8);d.rect(504,100,h*.8,448);adv=810
 elif ch in '<>':
  if ch=='<':d.poly((450,570),(450,490),(130,300),(450,110),(450,30),(40,270),(40,330))
  else:d.poly((40,570),(40,490),(360,300),(40,110),(40,30),(450,270),(450,330))
  adv=500
 elif ch=='|':d.rect(100,-100,h,900);adv=260
 elif ch=='~':
  d.path([('M',40,260),('C',140,460,360,180,460,380),('L',490,310),('C',385,110,165,390,65,190)]);adv=540
 elif ch=='^':d.poly((50,530),(228,740),(300,740),(478,530),(390,530),(264,677),(138,530));adv=530
 elif ch=='`':d.poly((70,735),(155,735),(260,595),(212,595));adv=280
 elif ch==' ':adv=250
 elif ch=='…':
  for x in [120,360,600]:dot(x,49)
  adv=720
 elif ch in '←→':
  d.rect(30,300,650,h)
  if ch=='→':d.poly((450,550),(700,300+h/2),(450,85),(410,135),(600,300+h/2),(410,500))
  else:d.poly((260,550),(10,300+h/2),(260,85),(300,135),(110,300+h/2),(300,500))
  adv=720
 else:
  d.rect(50,0,460,700);d.rect(50+t,h,460-2*t,700-2*h);adv=560
 return d.finish(),adv

BASE=list(string.ascii_letters+string.digits+string.punctuation+' ‘’.“”–—…£€←→·ı')
BASE=list(dict.fromkeys(BASE))
CMAP={ord(c):UV2AGL.get(ord(c),f'uni{ord(c):04X}') for c in BASE}
CMAP[160]='space'
ACCENTS={'acute':[(0,0),(80,0),(180,135),(65,135)],'grave':[(0,135),(110,135),(185,0),(105,0)],'circumflex':[(0,0),(105,130),(160,130),(265,0),(185,0),(132,66),(80,0)],'tilde':[(0,20),(60,90),(130,60),(190,30),(245,90),(270,45),(210,-10),(140,20),(70,45),(30,-5)],'dieresis':None,'ring':None,'cedilla':[(90,0),(150,0),(120,-55),(185,-85),(160,-165),(70,-180),(45,-130),(105,-125),(110,-95),(60,-70)]}
# Western European precomposed accents; explicit support is listed in coverage.json.
COMPOSE={}
for cp in range(192,256):
 dec=unicodedata.normalize('NFD',chr(cp))
 marks={'\u0300':'grave','\u0301':'acute','\u0302':'circumflex','\u0303':'tilde','\u0308':'dieresis','\u030a':'ring','\u0327':'cedilla'}
 if len(dec)==2 and dec[0] in string.ascii_letters and dec[1] in marks:
  gn=UV2AGL.get(cp,f'uni{cp:04X}');CMAP[cp]=gn;COMPOSE[gn]=(dec[0],marks[dec[1]])
ORDER=['.notdef']+list(dict.fromkeys(CMAP.values()))+['mark.'+n for n in ACCENTS]

def master(weight,aside):
 glyphs={};metrics={}
 for c in BASE:
  name=CMAP[ord(c)];g,w=draw(c,weight,aside);glyphs[name]=g;metrics[name]=(w,0)
 d=Drawing();d.ring(50,0,450,700,55);glyphs['.notdef']=d.finish();metrics['.notdef']=(550,50)
 for name,pts in ACCENTS.items():
  d=Drawing()
  if name=='dieresis':d.rect(5,10,74,74);d.rect(163,10,74,74)
  elif name=='ring':d.ring(30,-5,150,150,32,32)
  else:d.poly(*pts)
  glyphs['mark.'+name]=d.finish();metrics['mark.'+name]=(280,0)
 for name,(base,accent) in COMPOSE.items():
  bn=CMAP[ord('ı' if base=='i' else base)];pen=TTGlyphPen(glyphs);pen.addComponent(bn,(1,0,0,1,0,0))
  x=(metrics[bn][0]-260)/2;y=0 if accent=='cedilla' else (780 if base.isupper() else 590)
  pen.addComponent('mark.'+accent,(1,0,0,1,x,y));glyphs[name]=pen.glyph();metrics[name]=metrics[bn]
 fb=FontBuilder(1000,isTTF=True);fb.setupGlyphOrder(ORDER);fb.setupCharacterMap(CMAP);fb.setupGlyf(glyphs)
 # Match LSB to actual xMin; incorrect values cause variable-font outline shifts.
 for name,g in glyphs.items():
  g.recalcBounds(glyphs);metrics[name]=(metrics[name][0],getattr(g,'xMin',0))
 fb.setupHorizontalMetrics(metrics);fb.setupHorizontalHeader(ascent=950,descent=-260,lineGap=0)
 fb.setupNameTable({'familyName':'Sakib Grotesk','styleName':f'W{weight} Aside{aside}','uniqueFontIdentifier':f'SakibGrotesk-0.400-{weight}-{aside}','fullName':f'Sakib Grotesk {weight} {aside}','psName':f'SakibGrotesk-{weight}-{aside}','version':'Version 0.400','copyright':'Newly drawn reconstruction study for Sakib Ahmed, 2026. Visual reference: Söhne by Klim Type Foundry.','description':'Visual reconstruction study for sakib.lol, based on public Söhne specimens. Weight axis. Newly drawn outlines.'})
 fb.setupOS2(version=4,sTypoAscender=950,sTypoDescender=-260,sTypoLineGap=0,usWinAscent=960,usWinDescent=280,sxHeight=520,sCapHeight=700,usWeightClass=weight,fsType=0,fsSelection=0x80)
 fb.setupPost();fb.setupMaxp()
 kern={'To':-45,'Ta':-40,'Te':-40,'Ty':-24,'Tr':-24,'Tu':-20,'Yo':-48,'Ya':-44,'Ye':-44,'WA':-35,'AV':-50,'VA':-50,'AW':-35,'AT':-30,'FA':-38,'Fo':-20,'LT':-35,'LV':-35,'LY':-40,'PA':-42,'Po':-15,'Vo':-35,'Va':-35,'Ve':-35,'Wo':-20,'Wa':-20,'oo':-6,'ra':-10,'ro':-10,'ri':-10,'rk':-8,'sa':-9,'ak':-10,'ki':-15,'ib':-8,'lo':-8,'ol':-8,'ll':-10,'t.':-15,'r.':-28,'f.':-20}
 fea='languagesystem DFLT dflt; languagesystem latn dflt; feature kern {\n'
 for pair,val in kern.items():fea+=f'pos {CMAP[ord(pair[0])]} {CMAP[ord(pair[1])]} {val};\n'
 fea+='} kern;'
 addOpenTypeFeaturesFromString(fb.font,fea)
 path=MASTERS/f'Margin-{weight}-{aside}.ttf';fb.save(path);return path

ds=DesignSpaceDocument()
a=AxisDescriptor();a.name='Weight';a.tag='wght';a.minimum=400;a.default=400;a.maximum=650;ds.addAxis(a)
for w in [400,500,650]:
 p=master(w,0);s=SourceDescriptor();s.path=str(p);s.name=str(w);s.familyName='Sakib Grotesk';s.styleName=str(w);s.location={'Weight':w};s.copyInfo=s.copyLib=s.copyFeatures=(w==400);ds.addSource(s)
for name,w in [('Regular',400),('Medium',500),('Semibold',600)]:
 i=InstanceDescriptor();i.name=name;i.familyName='Sakib Grotesk';i.styleName=name;i.location={'Weight':w};ds.addInstance(i)
ds.write(MASTERS/'SakibGrotesk.designspace')
vf,_,_=build(ds)
for nid,value in [(1,'Sakib Grotesk'),(2,'Regular'),(4,'Sakib Grotesk Variable'),(6,'SakibGrotesk-Variable')]:
 for record in vf['name'].names:
  if record.nameID==nid:record.string=value.encode(record.getEncoding())
vf.save(OUT/'SakibGrotesk-Variable.ttf');vf.flavor='woff2';vf.save(OUT/'SakibGrotesk-Variable.woff2');vf.flavor=None
for name,w in [('Regular',400),('Medium',500),('Semibold',600)]:
 inst=instantiateVariableFont(vf,{'wght':w},inplace=False)
 for record in inst['name'].names:
  if record.nameID in [1,2,4,6]:
   value={1:'Sakib Grotesk '+name,2:'Regular',4:'Sakib Grotesk '+name,6:'SakibGrotesk-'+name}[record.nameID];record.string=value.encode(record.getEncoding())
 inst.save(OUT/f'SakibGrotesk-{name}.ttf')
 if name=='Regular':
  inst.flavor='woff2';inst.save(OUT/'SakibGrotesk-Regular.woff2')
coverage={'version':'0.400','glyph_count':len(ORDER),'unicode_count':len(CMAP),'characters':''.join(chr(c) for c in sorted(CMAP)),'axes':{'wght':[400,400,650]},'status':'Newly drawn reconstruction study after public Söhne specimens; not Söhne font software.'}
(ROOT/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))
print('Built Sakib Grotesk: variable TTF/WOFF2 and three static cuts.')
