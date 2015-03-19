#!/usr/bin/env python


import os.path
import tifffile
import numpy


class TiffSaver(object):

    _outputdir = ''
    _basename = ''
    _databroker = None

    start_time = datetime.datetime(2015, 03, 19)
    start_time = time.mktime(start_time)


    def savescans(self, sids, basename=None):
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


    def writeScan(self, sid):
        db = self.databroker
        header = db[sid]
        events = db.fetch_events(header)
        if not events:  return
        ev, = events
        dd = ev.data
        nlight = [k for k in dd if k.endswith('image_lightfield')]
        ndark = [k for k in dd if k.endswith('image_darkfield')]
        Alight = dd[nlight[0]]
        Adark = numpy.zeros(1, 1)
        if ndark and dd[ndark[0]].size:
            Adark = dd[ndark[0]]
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
