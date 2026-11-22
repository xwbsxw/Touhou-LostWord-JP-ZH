# -*- coding: utf-8 -*-
from lw_story_sc_m1_p1 import SC as P1
from lw_story_sc_m1_p2 import SC as P2
from lw_story_sc_m1_p3 import SC as P3
from lw_story_sc_m1_p4 import SC as P4
from lw_story_sc_m1_p5 import SC as P5
from lw_story_sc_m1_p6 import SC as P6
from lw_story_sc_m1_p7 import SC as P7
from lw_story_sc_m1_p8 import SC as P8
from lw_story_sc_m1_p9 import SC as P9
from lw_story_sc_m1_p10 import SC as P10

BUNDLE = '580339df439f3804b452f0120b0854d0/f1b3616d93c0177db247fb42ae622dbf'
ORDINAL = True
ALLOW_PARTIAL = True
SC = {}
for p in (P1, P2, P3, P4, P5, P6, P7, P8, P9, P10,): SC.update(p)
