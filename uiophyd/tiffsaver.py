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
    _mtime_window = 0.05
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


    def listtiffs(self, count=None):
        """List the last count tiff files in the output directory.
        """
        print("#", self.outputdir)
        tt = self.timetiffs
        tms = tt.keys()
        if count:  tms = tms[-count:]
        for ti in tms:
            tmiso = datetime.datetime.fromtimestamp(round(ti)).isoformat()
            print(tmiso, os.path.basename(tt[ti]), sep='    ')
        return


    def saveScans(self, scanspec, basename=None):
        """Save the specified scans to the outputdir

        scanspec -- can be an integer index an array of indices or a slice
                    object like numpy.s_[_5:].  This looks up entries with
                    corresponding scan_id in the data broker.
        basename -- optional basename to be used for exporting these scans.
                    If not specified, use self.basename.

        No return value.
        """
        headers = self.findHeaders(scanspec)
        stash_basename = self.basename
        if basename is not None:
            self.basename = basename
        try:
            for h in headers:
                self.writeHeader(h)
        finally:
            self.basename = stash_basename
        return


    def saveNewScans(self):
        "Export scan data that were not yet saved to outputdir."
        lasttime = max([self.start_time] + self.timetiffs.keys())
        db = self.databroker
        headers = db.find_events(start_time=lasttime)
        for header in headers:
            self.writeHeader(header, overwrite=False)
        return


    def writeHeader(self, header, overwrite=False):
        from uiophyd.brokerutils import blank_events
        events = blank_events(header)
        for n, e in enumerate(events):
            fname = self._getOutputFilename(header=header, event=e, index=n)
            self.writeEvent(fname, e, overwrite=overwrite)
        return


    def writeEvent(self, filename, event, overwrite):
        from uiophyd.brokerutils import fill_event
        savedfile = self.findSavedEvent(event)
        if savedfile:
            if overwrite:
                os.remove(savedfile)
            else:
                return
        dd = event.data
        nlight = [k for k in dd if k.endswith('image_lightfield')]
        Alight = dd[nlight[0]][0]
        if isinstance(Alight, basestring):
            fill_event(event)
            Alight = event.data[nlight[0]][0]
        if 3 == Alight.ndim:
            Alight = Alight.sum(axis=0)
        if 0 == Alight.size:
            return
        A = Alight
        tifffile.imsave(filename, A.astype(numpy.float32))
        stinfo = os.stat(filename)
        os.utime(filename, (stinfo.st_atime, event.time))
        return


    def findSavedEvent(self, e):
        """Return full path to a saved tiff file for the specified scan event.

        e    -- event document object.

        Return string or None if the event has not been saved
        """
        import bisect
        tt = self.timetiffs
        tms = tt.keys()
        idx = bisect.bisect(tms, e.time)
        for ti in tms[idx-1:idx+1]:
            if abs(e.time - ti) < self._mtime_window:
                return tt[ti]
        return None


    def findHeaders(self, scanspec):
        """Produce header objects corresponding to scan specification.

        scanspec -- can be an integer index an array of indices,
                    slice object like numpy.s_[_5:] or string uid.

        Return a list of header objects.
        """
        db = self.databroker
        rv = []
        if isinstance(scanspec, int):
            rv.append(db[scanspec])
        elif isinstance(scanspec, slice):
            rv += db[scanspec]
        elif isinstance(scanspec, basestring):
            rv += db.find_headers(uid=scanspec)
        else:
            rv += map(self.findHeaders, scanspec)
        return rv

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
        allfiles = [os.path.join(self.outputdir, f)
                for f in os.listdir(self.outputdir)]
        alltiffs = [f for f in allfiles
                if f.endswith('.tiff') and os.path.isfile(f)]
        tt = sorted((os.path.getmtime(f), f) for f in alltiffs)
        self._timetiffs = OrderedDict(tt)
        self._output_mtime = os.path.getmtime(self.outputdir)
        return self.timetiffs

    # Helpers ----------------------------------------------------------------

    def _getOutputFilename(self, header, event, index):
        scan_id = header.scan_id
        dd = event.data
        suffix = "{:05d}-{:03d}".format(scan_id, index)
        if 'cs700' in dd:
            tk = dd['cs700'][0]
            suffix = "{}-T{:03.1f}".format(suffix, tk)
        fmt = '{self.outputdir}/{self.basename}-{suffix}.tiff'
        fname = fmt.format(self=self, suffix=suffix)
        return fname

# class TiffSaver
