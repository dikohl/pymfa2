#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

testSuite = unittest.TestSuite(unittest.TestLoader().discover("./test"))
test_runner = unittest.TextTestRunner(None, True, 3).run(testSuite)

#entropyResult = {1:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21},2:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21},3:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21},4:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21},5:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21},6:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21}}