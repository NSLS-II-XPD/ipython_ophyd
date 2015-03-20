#!/usr/bin/env python


from __future__ import print_function
import os.path
import time
import datetime

import tifffile
import numpy


class TiffSaver(object):

    _outputdir = '/tmp'
    _basename = 'scan'
    _databroker = None

    start_time = datetime.datetime(2015, 03, 19)
    start_time = time.mktime(start_time.timetuple())
    _mtime_window = 1
    _output_mtime = 0
    _timetiffs = None


    def info(self):
        "Print out TiffSaver configuration."
        print("TiffSaver configuration:")
        print("  outputdir =", self.outputdir)
        print("  basename =", self.basename)
        print("Last 5 tiff files:")
        tnms = self.timetiffs.values()
        for tn in tnms[-5:]:
            print("  " + tn)
        return


    def saveScans(self, sids, basename=None):
        scanlist = self._expandScanIDs(sids)
        stash_basename = self.basename
        if basename is not None:
            self.basename = basename
        try:
            for sid in scanlist:
                self.writeScan(sid)
        finally:
            self.basename = stash_basename
        return


    def saveNewScans(self):
        "Export scan data that were not yet saved to outputdir."
        lasttime = max([self.start_time] + self.timetiff.keys())
        db = self.databroker
        headers = db.find_events(start_time=lasttime)
        for header in headers:
            self.writeScan(header.scan_id)
        return


    def writeScan(self, sid):
        db = self.databroker
        header = db[sid]
        events = db.fetch_events(header)
        if not events:  return
        ev, = events
        dd = ev.data
        nlight = [k for k in dd if k.endswith('image_lightfield')]
        ndark = [k for k in dd if k.endswith('image_darkfield')]
        Alight = dd[nlight[0]][0]
        Adark = numpy.zeros(1, 1)
        if ndark and dd[ndark[0]][0].size:
            Adark = dd[ndark[0]][0]
        framecount = 1
        if 3 == Alight.ndim:
            framecount = Alight.shape[0]
            Alight = Alight.sum(axis=0)
        if 3 == Adark.ndim:
            Adark = Adark.mean(axis=0)
        A = Alight - framecount * Adark
        fmt = '{self.outputdir}/{self.basename}-{sid:05d}.tiff'
        fname = fmt.format(self=self, sid=header.scan_id)
        tifffile.imsave(fname, A)
        stinfo = os.stat(fname)
        os.utime(fname, (stinfo.st_atime, header.stop_time))
        return


    def isAlreadySaved(self, sid):
        """True if the specified scan_id was already saved in outputdir.
        """
        import bisect
        header = self.databroker[sid]
        stop_time = header.stop_time
        tifftimes = self.timetiff.keys()
        idx = bisect.bisect(tifftimes, stop_time)
        deltas = [abs(stop_time - ti) for ti in tifftimes[idx-1:idx+1]]
        rv = deltas and min(deltas) < self._mtime_window
        return bool(rv)

    # Properties -------------------------------------------------------------

    @property
    def outputdir(self):
        """Path to the tiff output directory.  When set, relative paths
        are expanded to a full physical path.
        """
        return self._outputdir

    @outputdir.setter
    def outputdir(self, value):
        if not os.path.isdir(value):
            emsg = "{!r} is not a directory.".format(value)
            raise ValueError(emsg)
        self._outputdir = os.path.abspath(value)
        return


    @property
    def basename(self):
        """Basename for the tiff files to be written.
        """
        return self._basename

    @basename.setter
    def basename(self, value):
        if '/' in value or '\\' in value:
            emsg = "Basename must not contain '/' or '\\'."
            raise ValueError(emsg)
        self._basename = value.strip().rstrip('-')
        return


    @property
    def databroker(self):
        "Return the active databroker instance."
        if self._databroker is None:
            from dataportal.broker import DataBroker
            self._databroker = DataBroker
        return self._databroker


    @property
    def timetiffs(self):
        "Ordered dictionary of mtimes and tiff files in outputdir."
        from collections import OrderedDict
        if os.path.getmtime(self.outputdir) == self._output_mtime:
            return self._timetiffs
        allfiles = os.listdir(self.outputdir)
        alltiffs = [f for f in allfiles
                if f.endswith('.tiff') and os.path.isfile(f)]
        tt = sorted((os.path.getmtime(f), f) for f in alltiffs)
        self._timetiffs = OrderedDict(tt)
        self._output_mtime = os.path.getmtime(self.outputdir)
        return self.timetiffs

# class TiffSaver
