# -*- coding: utf-8 -*-
"""统一的中日文本转换器，可用环境变量切换目标字形。

    LW_MODE=sc   （默认）保持国服简体，不做 OpenCC 转换
    LW_MODE=tw   转成繁中（s2twp）

历史上这些脚本固定用 s2twp 把国服简体转成繁中；实测发现
s2twp 会带台湾用词（通过->透過、消息->訊息、软件->軟體），
再用 t2s 转回来会有 ~10% 失真。所以简体模式直接从源头不转换。

用法：
    from lw_cc import cc
    text = cc.convert(text)
"""
import os
from opencc import OpenCC

MODE = os.environ.get('LW_MODE', 'sc').lower()
_S2TWP = OpenCC('s2twp')
_T2S = OpenCC('t2s')


class _Converter:
    def __init__(self, mode):
        self.mode = mode

    def convert(self, s):
        if not isinstance(s, str) or not s:
            return s
        if self.mode == 'tw':
            return _S2TWP.convert(s)
        if self.mode == 'sc':
            return s                      # 国服原文已是简体，原样保留
        if self.mode == 't2s':
            return _T2S.convert(s)
        return s


cc = _Converter(MODE)


def to_simplified(s):
    """把繁体文本转简体（只用于本来就写成繁体的字典/规则输出）。"""
    return _T2S.convert(s) if isinstance(s, str) and s else s
