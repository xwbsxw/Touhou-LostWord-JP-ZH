# -*- coding: utf-8 -*-
from lw_story_sc_m2_p1 import SC as P1
from lw_story_sc_m2_p2 import SC as P2
from lw_story_sc_m2_p3 import SC as P3
from lw_story_sc_m2_p4 import SC as P4
from lw_story_sc_m2_p5 import SC as P5
from lw_story_sc_m2_p6 import SC as P6
from lw_story_sc_m2_p7 import SC as P7
from lw_story_sc_m2_p8 import SC as P8
from lw_story_sc_m2_p9 import SC as P9
from lw_story_sc_m2_p10 import SC as P10
from lw_story_sc_m2_p11 import SC as P11

BUNDLE = '359f1d36f245cd68b87dbfaf9058ec92/b4dfaae3c99fce9525f61ceca3bb1bf9'
ORDINAL = True
ALLOW_PARTIAL = True
SC = {}
for p in (P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11,): SC.update(p)
