'''Helper functions for convenient interactive use of pylab from ipython.
'''


from __builtin__ import sum


def figshow():
    '''Update and show all the figures, if possible in a non-blocking way.
    '''
    import inspect
    from matplotlib.pyplot import show
    _redraw()
    argspec = inspect.getargspec(show)
    if argspec.args or argspec.varargs:
        show(0)
    else:
        show()
    return


def moveline(lineid, dy=0, dx=0):
    '''Move or distribute the specified lines along x or y axis.

    lineid   -- integer zero based index or a matplotlib Line2D instance.
                Can be also a list of indices or Line2D objects.
                When 'all', use all line object in the current axes.
    dy       -- amount of shift in the y-direction, scalar or array
    dx       -- amount of shift in the x-direction, scalar or array

    No return value.
    '''
    import numpy
    linehandles = findlines(lineid)
    for hi, dxi, dyi in numpy.broadcast(linehandles, dx, dy):
        lm = _getLineModifiers(hi)
        lm['dx'] += dxi
        lm['dy'] += dyi
        _applyLineModifiers(hi)
    if linehandles:
        _redraw()
    return


def scaleline(lineid, scale=None, ascale=None, scalemax=None, scaleto=None,
        lsqscaleto=None, xbounds=None):
    '''Rescale the y-values of the specified matplotlib Line2D objects.
    Use only one of the scale, scalemax, scaleto or lsqscaleto arguments.

    lineid   -- integer zero based index or a matplotlib Line2D instance.
                Can be also a list of indices or Line2D objects.
                When 'all', use all line object in the current axes.
    scale    -- scale multiplier value.  If iterable, apply different
                scale to corresponding Line2D objects.
    ascale   -- absolute scale with respect to unscaled line.  If iterable,
                apply different scale to corresponding Line2D objects.
    scalemax -- scale by maximum.  Rescale all lines so that their maximum
                equals scalemax.  When iterable, apply corresponding
                absolute scale to every line object.
    scaleto  -- rescale lines to match the maximum of a reference line object.
                scaleto is either an integer, zero-based index or a Line2D
                instance.
    lsqscaleto -- scale lines according to the least squares fit to a given
                reference line object.  The argument is either an integer,
                zero-based index or a Line2D instance.
    xbounds  -- optional pair of x-boundaries for the least squares scaling.
                Only effective for the lsqscaleto mode.

    No return value.
    '''
    import numpy
    linehandles = findlines(lineid)
    linemods = [_getLineModifiers(hi) for hi in linehandles]
    n = len(linehandles)
    if scale is not None:
        for hi, lm in zip(linehandles, linemods):
            lm['scale'] *= scale
            _applyLineModifiers(hi)
    elif ascale is not None:
        for hi, lm in zip(linehandles, linemods):
            lm['scale'] = ascale
            _applyLineModifiers(hi)
    elif scalemax is not None:
        for hi, lm in zip(linehandles, linemods):
            ymx = numpy.max(lm['ydata']) or 1.0
            lm['scale'] = scalemax / ymx
            _applyLineModifiers(hi)
    elif scaleto is not None:
        href = findlines(scaleto)[0]
        lm = _getLineModifiers(href)
        hmax = numpy.max(lm['ydata'] * lm['scale'])
        scaleline(lineid, scalemax=hmax)
    elif lsqscaleto is not None:
        if xbounds is None:
            xbounds = (-numpy.inf, +numpy.inf)
        xlo, xhi = xbounds
        href = findlines(lsqscaleto)[0]
        lm = _getLineModifiers(href)
        xref = href.get_xdata()
        yref = lm['ydata'] * lm['scale']
        for hi, lm in zip(linehandles, linemods):
            xi = hi.get_xdata()
            xilo = max([xlo, xref[0], xi[0]])
            xihi = min([xhi, xref[-1], xi[-1]])
            indices = numpy.logical_and(xilo <= xi, xi <= xihi)
            xi = xi[indices]
            yi = lm['ydata'][indices] * lm['scale']
            yrefi = numpy.interp(xi, xref, yref)
            sc = numpy.dot(yrefi, yi) / (numpy.dot(yi, yi) or 1.0)
            lm['scale'] *= sc
            _applyLineModifiers(hi)
    else:
        emsg = "Use scale, scalemax, scaleto or lsqscaleto argument."
        raise ValueError(emsg)
    if linehandles:
        _redraw()
    return


def difflines(lineid_ref, lineid_other, baseline=0.0):
    '''Add a difference line between the specified Line2D objects.

    lineid_ref   -- reference line from which the other one is subtracted.
                    Integer, zero based index or a matplotlib Line2D object.
    lineid_other -- line compared to the reference.
                    Integer, zero based index or a matplotlib Line2D object.
    baseline     -- optional baseline for the difference curve

    Return a single-element list with the difference line handle.
    '''
    import numpy
    from matplotlib.pyplot import plot
    href = findlines(lineid_ref)[0]
    hother = findlines(lineid_other)[0]
    xref, yref = href.get_data()
    xother, yother = hother.get_data()
    if xother[0] > xother[-1]:
        xother = xother[::-1]
        yother = yother[::-1]
    indices = numpy.logical_and(
            max(xref.min(), xother[0]) <= xref,
            xref <= min(xref.max(), xother[-1]))
    xd = xref[indices]
    yd = yref[indices] - numpy.interp(xd, xother, yother)
    hd = plot(xd, yd, hold=True)
    if baseline:
        moveline(hd, baseline)
    else:
        _redraw()
    return hd


def resetline(lineid):
    '''Cancel any moveline or scaleline calls on the specified lines.

    lineid   -- integer zero based index or a matplotlib Line2D instance.
                Can be also a list of indices or Line2D objects.
                When 'all', use all line object in the current axes.

    No return value.
    '''
    linehandles = findlines(lineid)
    linemods = [_getLineModifiers(hi) for hi in linehandles]
    for hi, lm in zip(linehandles, linemods):
        lm.update(dx=0.0, dy=0.0, scale=1.0)
        _applyLineModifiers(hi)
        freezeline(hi)
    if linehandles:
        _redraw()
    return


def freezeline(lineid):
    '''Discard any original data for the specified lines.
    A further call to resetline would revert to the current data.

    lineid   -- integer zero based index or a matplotlib Line2D instance.
                Can be also a list of indices or Line2D objects.
                When 'all', use all line object in the current axes.

    No return value.
    '''
    linehandles = findlines(lineid)
    for hi in linehandles:
        lid = id(hi)
        _linemods.pop(lid, None)
    return


def removeline(lineid):
    '''Remove specified lines from the figure.

    lineid   -- integer zero based index or a matplotlib Line2D instance.
                Can be also a list of indices or Line2D objects.
                When 'all', use all line object in the current axes.

    No return value.
    '''
    linehandles = findlines(lineid)
    for hi in linehandles:
        lid = id(hi)
        _linemods.pop(lid, None)
        hi.remove()
    if linehandles:
        _redraw()
    return


def getlinex(lineid):
    '''Return x data from the specified line(s) in the figure.

    lineid   -- integer zero based index or a matplotlib Line2D instance.
                Can be also a list of indices or Line2D objects.

    Return numpy array.
    '''
    import numpy
    linehandles = findlines(lineid)
    rv = numpy.array([h.get_xdata() for h in linehandles])
    if rv.shape[0] == 1:
        rv = rv[0]
    return rv


def getliney(lineid):
    '''Return y data from the specified line(s) in the figure.

    lineid   -- integer zero based index or a matplotlib Line2D instance.
                Can be also a list of indices or Line2D objects.

    Return numpy array.
    '''
    import numpy
    linehandles = findlines(lineid)
    rv = numpy.array([h.get_ydata() for h in linehandles])
    if rv.shape[0] == 1:
        rv = rv[0]
    return rv


def getlinedata(lineid):
    '''Return an (x0, y0, x1, y1,...) array from the specified line(s).

    lineid   -- integer zero based index or a matplotlib Line2D instance.
                Can be also a list of indices or Line2D objects.

    Return numpy array.
    '''
    import numpy
    linehandles = findlines(lineid)
    rv = numpy.array(sum([h.get_data() for h in linehandles], ()))
    return rv


def getlinemodifiers(lineid):
    '''Return a dictionary with ("scale", "dx", "dy") keys for scale
    and offset modifiers of the specified line.  When lineid matches
    several line objects, only the first one is used.

    lineid   -- integer zero based index or a matplotlib Line2D instance.
                Can be also a list of indices or Line2D objects.

    Return dictionary.
    '''
    linehandles = findlines(lineid)
    lm = _getLineModifiers(linehandles[0])
    rv = dict((k, lm[k]) for k in ('scale', 'dx', 'dy'))
    return rv


def blanklinemarkers(lineid, filled=False,
        marker=None, color=None, width=None, **kw):
    '''Clear markerfacecolor for the specified lines and adjust the
    edge width and color according to the owner line.

    lineid   -- integer zero based index or a matplotlib Line2D instance.
                Can be also a list of indices or Line2D objects.
    filled   -- when True, restore the markerfacecolor
    color    -- use instead of line color when specified
    width    -- use for markeredge width if specified, otherwise use
                the line width.
    kw       -- optional keyword arguments for additional line properties

    No return value.
    '''
    from matplotlib.artist import setp
    linehandles = findlines(lineid)
    for hi in linehandles:
        mi = hi.get_marker() if marker is None else marker
        ci = hi.get_color() if color is None else color
        mfc = ci if filled else 'none'
        mec = ci
        mwi = hi.get_linewidth() if width is None else width
        hi.set_marker(mi)
        hi.set_markerfacecolor(mfc)
        hi.set_markeredgecolor(mec)
        hi.set_markeredgewidth(mwi)
        if kw:  setp(hi, **kw)
    if linehandles:
        _redraw()
    return


def findlines(lineid='all'):
    '''Convert lineid to a list of matplotlib Line2D instances.

    lineid   -- integer zero based index or a matplotlib Line2D instance.
                Can be also a slice, list of indices or Line2D objects.
                When 'all', use all line object in the current axis.

    Return a list of Line2D instances.
    '''
    from matplotlib import pyplot
    if _isiterablenotstring(lineid):
        rv = sum(map(findlines, lineid), [])
        return rv
    if isinstance(lineid, pyplot.Line2D):
        return [lineid]
    curaxes = findaxes()
    lines = curaxes and curaxes[0].get_lines()[:]
    if lineid == 'all':
        rv = lines
    elif isinstance(lineid, slice):
        rv = lines[lineid]
    else:
        rv = [lines[int(lineid)]]
    return rv


def colorcycle(index=None, handles=None):
    '''Return a list of colors used for new lines in the axis.

    index    -- optional integer index for a color from the cycle
                Return complete colorcycle when None.  Return a single
                color when integer.  Return a list of colors when
                iterable.
    handles  -- optional matplotlib object or iterable of objects, whose
                color would be set according to the index.

    Return string or a list of strings.
    '''
    from matplotlib import rcParams
    ccycle = rcParams['axes.color_cycle'][:]
    if index is None:
        rv = ccycle
    elif _isiterablenotstring(index):
        rv = [colorcycle(i) for i in index]
    else:
        nmidx = index % len(ccycle)
        rv = ccycle[nmidx]
    if handles is not None:
        from matplotlib.artist import setp
        if type(rv) is list:
            for c, h in zip(rv, handles):
                setp(h, color=c)
        else:
            setp(handles, color=rv)
        _redraw()
    return rv


def colorbyvalue(handles, values=None, bounds=None, prop='color', cmap=None):
    '''Return a list of colors converted from colormap and specified values.

    handles  -- iterable of matplotlib objects, whose colors would be set
                according to the colormap.
    values   -- optional values to be converted to colors.
                Defaults to range(len(handles)).
    bounds   -- tuple of (lower, upper) bounds for values tranformation.
                Defaults to (0, len(handles) - 1).
    prop     -- artist property that should be assigned the color, e.g.,
                'facecolor', 'edgecolor'.  Can be also a callable function
                which is executed as prop(handle_i, color_i).
    cmap     -- optional name of the colormap to be used or a Colormap object.

    No return value.
    '''
    import numpy
    from matplotlib.cm import get_cmap
    if len(handles) < 2:  return
    if values is None:
        values = numpy.arange(len(handles), dtype=float)
    x = numpy.asarray(values)
    # cmap argument
    cmap = get_cmap(cmap)
    # bounds argument
    if bounds is None:
        bounds = (0.0, 1.0)
        xfin = x[numpy.isfinite(x)]
        if xfin.size:
            bounds = (xfin.min(), xfin.max())
    xt = (x - 1.0 * bounds[0]) / (bounds[1] - bounds[0])
    colors = cmap(xt)
    if callable(prop):
        fset = prop
    else:
        fset = getattr(type(handles[0]), 'set_' + prop)
    for hi, ci in zip(handles, colors):
        fset(hi, ci)
    _redraw()
    return


def minortickmarks(dx=None, dy=None, axisid=None):
    '''Display minor tick marks on x or y-axis with the specified step.
    Remove either tickmarks when set to '', 'null' or 'none'.

    dx       -- spacing for x-axis minor tickmarks.
                Remove minor tickmarks when '', 'none' or 'null'.
    dy       -- spacing for y-axis minor tickmarks.
                Remove minor tickmarks when '', 'none' or 'null'.
    axisid   -- integer zero based index or a matplotlib Axes instance.
                Can be also a list of indices or Axes objects.
                Use the current axis if None or ''.
                When 'all', use all axes in the current figure.
                When tuple (h, k, l) use suplot(h, k, l).

    No return value.
    '''
    import matplotlib.ticker
    def _getlocator(axy, step):
        if not step or step in ('null', 'none', 'off'):
            locator = matplotlib.ticker.NullLocator()
        elif step in ('on', 'auto'):
            if axy.get_scale() == 'log':
                s = axy._scale
                locator = matplotlib.ticker.LogLocator(s.base, s.subs)
            else:
                locator = matplotlib.ticker.AutoMinorLocator()
        else:
            locator = matplotlib.ticker.MultipleLocator(step)
        return locator
    axeshandles = findaxes(axisid)
    for ax in axeshandles:
        for axy, step in zip([ax.xaxis, ax.yaxis], [dx, dy]):
            if step is not None:
                axy.set_minor_locator(_getlocator(axy, step))
    if axeshandles:
        _redraw()
    return


def xminortickmarks(dx, axisid=None):
    '''Display x-axis minor tick marks with the specified step.

    dx       -- spacing for the x minor tickmarks.
                Remove tickmarks when set to 0, '', 'null' or 'none'.
    axisid   -- integer zero based index or a matplotlib Axes instance.
                Can be also a list of indices or Axes objects.
                Use the current axis if None or ''.
                When 'all', use all axes in the current figure.
                When tuple (h, k, l) use suplot(h, k, l).

    No return value.
    '''
    minortickmarks(axisid=axisid, dx=dx)
    return


def yminortickmarks(dy, axisid=None):
    '''Display y-axis minor tick marks with the specified step.

    dy       -- spacing for the y minor tickmarks.
                Remove tickmarks when set to '', 'null' or 'none'.
    axisid   -- integer zero based index or a matplotlib Axes instance.
                Can be also a list of indices or Axes objects.
                Use the current axis if None or ''.
                When 'all', use all axes in the current figure.
                When tuple (h, k, l) use suplot(h, k, l).

    No return value.
    '''
    minortickmarks(dy=dy, axisid=axisid)
    return


def legendhide(hidden=True, axisid=None):
    '''Hide or show legend in the specified axis.

    hidden   -- set the legend invisible if True, show it otherwise.
    axisid   -- integer zero based index or a matplotlib Axes instance.
                Can be also a list of indices or Axes objects.
                Use the current axis if None or ''.
                When 'all', use all axes in the current figure.
                When tuple (h, k, l) use suplot(h, k, l).

    No return value.
    '''
    axeshandles = findaxes(axisid)
    needsredraw = False
    for ax in axeshandles:
        hlg = ax.get_legend()
        if not hlg or bool(hlg.get_visible()) is (not hidden):
            continue
        hlg.set_visible(not hidden)
        needsredraw = True
    if needsredraw:
        _redraw()
    return


def legendremove(axisid=None):
    '''Remove the legend from either the current or specified axis.

    axisid   -- integer zero based index or a matplotlib Axes instance.
                Can be also a list of indices or Axes objects.
                Use the current axis if None or ''.
                When 'all', use all axes in the current figure.
                When tuple (h, k, l) use suplot(h, k, l).

    No return value.
    '''
    axeshandles = findaxes(axisid)
    needsredraw = False
    for ax in axeshandles:
        hlg = ax.legend_
        if hlg is None:
            continue
        ax.legend_ = None
        needsredraw = True
    if needsredraw:
        _redraw()
    return


def axsizeinches(width, height, axisid=None):
    '''Adjust the owner figure size to get the specified size of the axis box.

    width    -- width of the axis box in inches
    height   -- height of the axis box in inches
    axisid   -- integer zero based index or a matplotlib Axes instance.
                Can be also a list of indices or Axes objects.
                Use the current axis if None or ''.
                When 'all', use all axes in the current figure.
                When tuple (h, k, l) use suplot(h, k, l).

    No return value.
    '''
    axeshandles = findaxes(axisid)
    for ax in axeshandles:
        fig = ax.get_figure()
        bb = ax.get_position().size
        wfig = width / bb[0]
        hfig = height / bb[1]
        fig.set_size_inches(wfig, hfig)
    return


def axrelim(axisid=None):
    '''Recalculate the limits of the current or specified axis.

    axisid   -- integer zero based index or a matplotlib Axes instance.
                Can be also a list of indices or Axes objects.
                Use the current axis if None or ''.
                When 'all', use all axes in the current figure.
                When tuple (h, k, l) use suplot(h, k, l).

    No return value.
    '''
    axeshandles = findaxes(axisid)
    for ax in axeshandles:
        ax.relim()
        ax.axis('normal')
    if axeshandles:
        _redraw()
    return


def axdo(axisid, function=None, *args, **kwargs):
    '''Call a function or method on all specified matplotlib Axes.
    This executes a function(ax, *args, **kwargs) for every axisid Axes.

    axisid   -- integer zero based index or a matplotlib Axes instance.
                Can be also a list of indices or Axes objects.
                Use the current axis if None or ''.
                When 'all', use all axes in the current figure.
                When tuple (h, k, l) use suplot(h, k, l).
    function -- callable object or a method name of the Axes class.
                By default it is pyplot.setp.
                The function is called for every axisid Axes.
    *args    -- optional positional arguments for the function call
    *kwargs  -- optional keyword arguments for the function call


    Return a list of returned values from all function calls.
    '''
    from matplotlib.pyplot import Axes, setp
    axeshandles = findaxes(axisid)
    if isinstance(function, basestring):
        function = getattr(Axes, function)
    if function is None:
        function = setp
    rv = [function(ax, *args, **kwargs) for ax in axeshandles]
    if len(rv):
        _redraw()
    return rv


def findaxes(axisid=None, sca=False, fignum=None):
    '''Convert axisid to a list of matplotlib Axes instances.

    axisid   -- integer zero based index or a matplotlib Axes instance.
                Can be also a list of indices or Axes objects.
                Use the current axis if None or ''.
                When 'all', use all axes in the current figure.
                When axisid >= 111 or 'h,k,l' use suplot(hkl).
    sca      -- flag for setting the last found axis as the current one
                The return value is also changed from a list to the
                last found Axes object or None.
    fignum   -- integer figure number for selecting axis in other
                figure than the current one

    Return a list of Axes instances.
    Return an empty list if no axes exist in the current figure.
    '''
    import numpy
    from matplotlib import pyplot
    from matplotlib import _pylab_helpers
    def _dosca(foundaxes):
        if foundaxes and sca:
            pyplot.sca(foundaxes[-1])
        return foundaxes
    fnums = pyplot.get_fignums()
    if not fnums or (fignum is not None and not fignum in fnums):
        return []
    if fignum is None:
        thefigure = pyplot.gcf()
    else:
        figman = _pylab_helpers.Gcf.figs[fignum]
        thefigure = figman.canvas.figure
    if isinstance(axisid, pyplot.Axes):
        return _dosca([axisid])
    # resolve subplot ids
    issubplotid = (isinstance(axisid, tuple) and len(axisid) == 3 and
            all([numpy.issubdtype(type(i), int) for i in axisid]))
    if issubplotid:
        return _dosca([thefigure.add_subplot(*axisid)])
    issubplotid = numpy.issubdtype(type(axisid), int) and 111 <= axisid
    if issubplotid:
        return _dosca([thefigure.add_subplot(axisid)])
    # find current or all axes
    figaxes = thefigure.get_axes()[:]
    if axisid in (None, ''):
        rv = figaxes and [thefigure.gca()]
        return _dosca(rv)
    if axisid == 'all':
        return _dosca(figaxes)
    elif isinstance(axisid, slice):
        return _dosca(figaxes[axisid])
    # resolve other string IDs
    if isinstance(axisid, basestring):
        words = [w.split() or [''] for w in axisid.split(',')]
        words = sum(words, [])
        return findaxes(words, sca=sca)
    # take care of iterables
    if _isiterablenotstring(axisid):
        rv = []
        fn = thefigure.number
        for aid in axisid:
            if isinstance(aid, basestring):
                if aid.isdigit():
                    rv += findaxes(int(aid), fignum=fn)
                    continue
                if aid.startswith('f') and aid[1:].isdigit():
                    fn = int(aid[1:])
                    continue
            rv += findaxes(aid, fignum=fn)
    # or assume it is an integer index
    else:
        rv = [figaxes[axisid]]
    return _dosca(rv)


def findtexts(textid='all'):
    '''Convert textid to a list of matplotlib Text instances.

    textid   -- integer zero based index or a matplotlib Text instance.
                Can be also a slice, list of indices or Text objects.
                When 'all', use all text objects in the current axis.

    Return a list of Text instances.
    '''
    from matplotlib import pyplot
    if _isiterablenotstring(textid):
        rv = sum(map(findtexts, textid), [])
        return rv
    if isinstance(textid, pyplot.Text):
        return [textid]
    curaxes = findaxes()
    alltexts = curaxes and curaxes[0].texts[:]
    if textid == 'all':
        rv = alltexts
    elif isinstance(textid, slice):
        rv = alltexts[textid]
    else:
        rv = [alltexts[int(textid)]]
    return rv


def movetext(textid, x=None, y=None, dx=None, dy=None):
    '''Convert textid to a list of matplotlib Text instances.

    textid   -- integer zero based index or a matplotlib Text instance.
                Can be also a list of indices or Text objects.
                When 'all', use all text objects in the current axis.
    x, y     -- new x, y positions of the specified text objects,
                floating point numbers or arrays.
                Positions are not changed when None.
    dx, dy   -- offsets in the x or y directions, numbers or arrays.
                These are applied after setting the x, y coordinates.

    Return a list of Text instances.
    '''
    import numpy
    texthandles = findtexts(textid)
    for hti, xi, yi, dxi, dyi in numpy.broadcast(texthandles, x, y, dx, dy):
        xt, yt = hti.get_position()
        if xi is not None:
            xt = xi
        if dxi is not None:
            xt += dxi
        if yi is not None:
            yt = yi
        if dyi is not None:
            yt += dyi
        hti.set_position((xt, yt))
    if texthandles:
        _redraw()
    return


def nowarnings():
    '''Disable the annoying backend warnings from the matplotlib.
    '''
    import warnings
    warnings.filterwarnings('ignore', module='matplotlib.backends.*')
    return


def _isiterable(obj):
    '''Return True if object supports iteration protocol.
    '''
    try:
        iter(obj)
        rv = True
    except TypeError:
        rv = False
    return rv


def _isiterablenotstring(obj):
    '''Return True if object supports iteration, but is not a string.
    '''
    rv = _isiterable(obj) and not isinstance(obj, basestring)
    return rv


def _getLineModifiers(line2d):
    '''Return a dictionary of "xdata", "ydata", "dx", "dy", "scale"
    for a given matplotlib Line2D instance.
    '''
    import numpy
    lid = id(line2d)
    lm = _linemods.setdefault(lid, {})
    x = line2d.get_xdata()
    if 'xdata' not in lm or len(x) != len(lm['xdata']):
        lm.update(xdata=x + 0.0, ydata=line2d.get_ydata() + 0.0,
                dx=0.0, dy=0.0, scale=1.0)
    return lm
_linemods = {}


def _applyLineModifiers(line2d):
    '''Apply offset and scale modifiers on the specified Line2D instance.
    '''
    lm = _getLineModifiers(line2d)
    x1 = lm['xdata'] + lm['dx']
    y1 = lm['ydata'] * lm['scale'] + lm['dy']
    line2d.set_data((x1, y1))
    return


def _redraw():
    from matplotlib.pyplot import isinteractive, draw
    if isinteractive():
        draw()
    return


def loadTiff(filename, frame=0):
    import tifffile
    tf = tifffile.TIFFfile(filename)
    rv = tf[frame].asarray()
    return rv


def xaty(x, y, value, xbounds=None):
    '''Return interpolated x-values where the xy curve crosses the value.

    x        -- array of x-values
    y        -- array of y-values
    value    -- constant y that is crossed by the curve
    xbounds  -- optional limit for the x-values

    Return an array of the interpolated x values.
    '''
    import numpy
    xa = numpy.asarray(x)
    ya = numpy.asarray(y)
    assert numpy.isscalar(value)
    yds = numpy.sign(ya - value).astype(int)
    ilo = (yds[:-1] * yds[1:] <= 0) & numpy.logical_or(yds[:-1], yds[1:])
    ihi = numpy.roll(ilo, 1)
    wlo = ya[ihi] - value
    whi = value - ya[ilo]
    rv = (xa[ilo] * wlo + xa[ihi] * whi) / (ya[ihi] - ya[ilo])
    if xbounds is not None:
        indices = (xbounds[0] <= rv) & (rv <= xbounds[1])
        rv = rv[indices]
    return rv


def localminima(y, mask=None):
    '''Return indices of the local minima in the y array.

    y    -- one dimensional array
    mask -- optional boolean mask applied to the result.

    Return indices of the local minima.
    '''
    import numpy
    ya = numpy.asarray(y)
    assert ya.ndim == 1
    assert mask is None or (
            ya.shape == mask.shape and mask.dtype is numpy.dtype(bool))
    f = numpy.r_[True, ya[1:] < ya[:-1]] & numpy.r_[ya[:-1] < ya[1:], True]
    if mask is not None:
        f = f & mask
    rv = f.nonzero()[0]
    return rv


def localmaxima(y, mask=None):
    '''Return indices of the local maxima in the y array.

    y    -- one dimensional array
    mask -- optional boolean mask applied to the result.

    Return indices of the local maxima.
    '''
    import numpy
    ya = numpy.asarray(y)
    return localminima(-ya, mask)


def reportzcoord(axisid=None):
    '''Report z-coordinate under the cursor for the last image in the axis.

    axisid   -- integer zero based index or a matplotlib Axes instance.
                Can be also a list of indices or Axes objects.
                Use the current axis if None or ''.
                When 'all', use all axes in the current figure.
                When axisid >= 111 or 'h,k,l' use suplot(hkl).

    No return value.
    Return a list of Axes instances.
    '''
    axeshandles = findaxes(axisid)
    if not axeshandles:  return
    if len(axeshandles) > 1:
        for ax in axeshandles:
            reportzcoord(ax)
        return
    ax = axeshandles[0]
    A = ax.images[-1].get_array().data
    def format_xyzcoords(x, y):
        col = int(x + 0.5)
        row = int(y + 0.5)
        inside = (0 <= row < A.shape[0]) and (0 <= col < A.shape[1])
        fmt = 'x={x:.6g}, y={y:.6g}' + ', z={z:.6g}' if inside else ''
        rv = fmt.format(x=x, y=y, z=A[row, col])
        return rv
    ax.format_coord = format_xyzcoords
    return
