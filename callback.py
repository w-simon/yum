#!/usr/bin/python -t
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# Copyright 2002 Duke University 


import rpm
import os
import sys

from i18n import _

class RPMInstallCallback:
    def __init__(self, output=1):
        self.output = output
        self.callbackfilehandles = {}
        self.total_actions = 0
        self.total_installed = 0
        self.installed_pkg_names = []
        self.total_removed = 0
        self.filelog = None
        self.packagedict = {}
        self.myprocess = { 'u': 'Updating', 'e': 'Erasing', 'i': 'Installing',
                           'o': 'Obsoleted' }
        self.mypostprocess = { 'u': 'Updated', 'e': 'Erased', 'i': 'Installed',
                               'o': 'Obsoleted' }
                           
                           
    def _dopkgtup(self, hdr):
        tmpepoch = hdr['epoch']
        if tmpepoch is None: epoch = '0'
        else: epoch = str(tmpepoch)
        
        return (hdr['name'], hdr['arch'], epoch, hdr['version'], hdr['release'])
        
    def _makeHandle(self, hdr):
        handle = '%s:%s.%s-%s-%s' % (hdr['epoch'], hdr['name'], hdr['version'],
          hdr['release'], hdr['arch'])
        
        return handle

    def _localprint(self, msg):
        if self.output:
            print msg

    def _logPkgString(self, hdr):
        """return nice representation of the package for the log"""
        (n,a,e,v,r) = self._dopkgtup(hdr)
        if e == '0':
            pkg = '%s.%s %s-%s' % (n, a, v, r)
        else:
            pkg = '%s.%s %s:%s-%s' % (n, a, e, v, r)
        
        return pkg
        
        
    def callback(self, what, bytes, total, h, user):
        if what == rpm.RPMCALLBACK_TRANS_START:
            if bytes == 6:
                self.total_actions = total
        
        elif what == rpm.RPMCALLBACK_TRANS_PROGRESS:
            pass
        
        elif what == rpm.RPMCALLBACK_TRANS_STOP:
            pass
        
        elif what == rpm.RPMCALLBACK_INST_OPEN_FILE:
            hdr = None
            if h is not None:
                hdr, rpmloc = h
                handle = self._makeHandle(hdr)
                fd = os.open(rpmloc, os.O_RDONLY)
                self.callbackfilehandles[handle]=fd
                self.total_installed += 1
                self.installed_pkg_names.append(hdr['name'])
                return fd
            else:
                self._localprint(_("No header - huh?"))
  
        elif what == rpm.RPMCALLBACK_INST_CLOSE_FILE:
            hdr = None
            if h is not None:
                hdr, rpmloc = h
                handle = self._makeHandle(hdr)
                os.close(self.callbackfilehandles[handle])
                fd = 0
                
                # log stuff
                pkgtup = self._dopkgtup(hdr)
                try:
                    process = self.myprocess[self.packagedict[pkgtup]]
                    processed = self.mypostprocess[self.packagedict[pkgtup]]
                except KeyError, e:
                    pass
                    
                if self.filelog:
                    pkgrep = self._logPkgString(hdr)
                    msg = '%s: %s' % (processed, pkgrep)
                    self.filelog(0, msg)
            

        elif what == rpm.RPMCALLBACK_INST_PROGRESS:
            if h is not None:
                hdr, rpmloc = h
                if total == 0:
                    percent = 0
                else:
                    percent = (bytes*100L)/total
                pkgtup = self._dopkgtup(hdr)
                try:
                    process = self.myprocess[self.packagedict[pkgtup]]
                except KeyError, e:
                    print "Error: invalid process key: %s for %s" % \
                       (self.packagedict[pkgtup], hdr['name'])

                if self.output and sys.stdout.isatty():
                    sys.stdout.write("\r%s: %s %d %% done %d/%d" % (process, 
                       hdr['name'], percent, self.total_installed + self.total_removed, 
                       self.total_actions))
                   
                    if bytes == total:
                        print " "
                        
        elif what == rpm.RPMCALLBACK_UNINST_START:
            pass
            
        elif what == rpm.RPMCALLBACK_UNINST_STOP:
            self.total_removed += 1

            if h not in self.installed_pkg_names:
                msg = _('Erasing: %s %d/%d') % (h, self.total_removed + 
                  self.total_installed, self.total_actions)
                self._localprint(msg)
                
                logmsg = _('Erased: %s' % (h))
                if self.filelog: self.filelog(0, logmsg)
                
            else:
                msg = _('Completing update for %s  - %d/%d') % (h, self.total_removed +
                  self.total_installed, self.total_actions)
                self._localprint(msg)

 
