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

    start_time = datetime.datetime(2015, 3, 19)
    start_time = time.mktime(start_time.timetuple())
    _mtime_window = 0.05
    _output_mtime = 0
    _timetiffs = None
    _dryrun = False
    dtype = numpy.float32
    default_suffixes = ("{scan_id:05d}", "{index:03d}",
            "T{event.data[cs700]:03.1f}")


    def __init__(self):
        self.suffixes = list(self.default_suffixes)
        return


    def info(self):
        "Print out TiffSaver configuration."
        print("TiffSaver configuration:")
        print("  outputdir =", self.outputdir)
        print("  basename =", self.basename)
        print("  suffixes =", self.suffixes)
        print("  dtype =", self.dtype)
        print("Last 5 tiff files:")
        tnms = list(self.timetiffs.values())
        for tn in tnms[-5:]:
            print("  " + tn)
        return


    def listtiffs(self, count=None):
        """List the last count tiff files in the output directory.
        """
        print("#", self.outputdir)
        tt = self.timetiffs
        tms = list(tt.keys())
        if count:  tms = tms[-count:]
        for ti in tms:
            tmiso = datetime.datetime.fromtimestamp(round(ti)).isoformat()
            print(tmiso, os.path.basename(tt[ti]), sep='    ')
        return


    def saveScans(self, scanspec,
            basename=None, overwrite=False, dryrun=False):
        """Save the specified scans to the outputdir

        scanspec -- can be an integer index an array of indices or a slice
                    object like numpy.s_[_5:].  This looks up entries with
                    corresponding scan_id in the data broker.
        basename -- optional basename to be used for exporting these scans.
                    If not specified, use self.basename.
        overwrite -- when True, write all specified scans now and remove any
                    previously exported tiff files, even if written using a
                    different basename.  When False, skip all scanspec scans
                    that were already saved.
        dryrun   -- Do not write anything, just print out what would be done.
                    Useful for checking the output names and the suffixes
                    attribute.

        No return value.
        """
        headers = self.findHeaders(scanspec)
        stash_basename = self.basename
        stash_dryrun = self._dryrun
        if basename is not None:
            self.basename = basename
        self._dryrun = dryrun
        try:
            for h in headers:
                self.writeHeader(h, overwrite=overwrite)
        finally:
            self.basename = stash_basename
            self._dryrun = stash_dryrun
        return


    def saveNewScans(self):
        "Export scan data that were not yet saved to outputdir."
        lasttime = max([self.start_time] + list(self.timetiffs.keys()))
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
            msgrm = 'remove existing file {}'.format(savedfile)
            msgskip = 'skip {}, already saved as {}'.format(filename, savedfile)
            if overwrite:
                self._dryordo(msgrm, os.remove, savedfile)
            else:
                self._dryordo(msgskip, lambda : None)
                return
        dd = event.data
        nlight = [k for k in dd if k.endswith('image_lightfield')][0]
        Alight = dd[nlight]
        if isinstance(Alight, str):
            fill_event(event)
            Alight = event.data[nlight]
        ndark = nlight.replace('lightfield', 'darkfield')
        Adark = event.data.get(ndark, 0)
        A = Alight - Adark
        if 3 == A.ndim:
            A = A.sum(axis=0)
        if 0 == A.size:
            return
        if self.dtype is not None:
            A = A.astype(self.dtype)
        def _writetiff():
            tifffile.imsave(filename, A)
            stinfo = os.stat(filename)
            os.utime(filename, (stinfo.st_atime, event.time))
        msg = 'write {} using {}, adjust mtime'.format(
                filename, A.dtype)
        self._dryordo(msg, _writetiff)
        return


    def findSavedEvent(self, e):
        """Return full path to a saved tiff file for the specified scan event.

        e    -- event document object.

        Return string or None if the event has not been saved
        """
        import bisect
        tt = self.timetiffs
        tms = list(tt.keys())
        idx = bisect.bisect(tms, e.time)
        for ti in tms[idx-1:idx+1]:
            if abs(e.time - ti) < self._mtime_window:
                return tt[ti]
        return None


    def findHeaders(self, scanspec):
        """Produce header objects corresponding to scan specification.

        scanspec -- can be an integer index an array of indices,
                    slice object like numpy.s_[-5:] or string uid.

        Return a list of header objects.
        """
        db = self.databroker
        rv = []
        if isinstance(scanspec, int):
            rv.append(db[scanspec])
        elif isinstance(scanspec, slice):
            rv += db[scanspec]
        elif isinstance(scanspec, str):
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
                if f.endswith('.tif') and os.path.isfile(f)]
        tt = sorted((os.path.getmtime(f), f) for f in alltiffs)
        self._timetiffs = OrderedDict(tt)
        self._output_mtime = os.path.getmtime(self.outputdir)
        return self.timetiffs

    # Helpers ----------------------------------------------------------------

    def _getOutputFilename(self, header, event, index):
        sflst = []
        for s in self.suffixes:
            try:
                s2 = s.format(header=header, event=event, index=index,
                        scan_id=header.scan_id)
            except (AttributeError, KeyError):
                continue
            sflst.append(s2)
        tailname = '-'.join([self.basename] + sflst) + '.tif'
        fname = self.outputdir + '/' + tailname
        return fname


    def _dryordo(self, msg, fnc, *args, **kwargs):
        if self._dryrun:
            if msg:
                print('[dryrun]', msg)
        else:
            fnc(*args, **kwargs)
        return

# class TiffSaver
