#!/usr/bin/python
# -*- coding: utf-8 -*-
# **********************************************************************
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 2
#   of the License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
#   02111-1307, USA.
#
#   (c)2012 - X Engineering Software Systems Corp. (www.xess.com)
# **********************************************************************
"""
XESS error processing class.
"""

import sys

SUCCESS = 0
FAILURE = 1


class XsError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        print 'ERROR: %s' % args[0]


class XsMinorError(XsError):

    pass


class XsMajorError(XsError):

    pass


class XsFatalError(XsError):
    def __init__(self, *args, **kwargs):
        XsError.__init__(self, *args, **kwargs)
        sys.exit(FAILURE)


class XsTerminate(Exception):

    pass
