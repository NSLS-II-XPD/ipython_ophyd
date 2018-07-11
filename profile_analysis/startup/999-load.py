#from xpdan.startup.analysis import start_analysis
#from xpdan.startup.analysis import (_mask_kwargs as mask_kwargs, _pdf_kwargs as pdf_kwargs, _fq_kwargs as fq_kwargs, _mask_setting as mask_setting, _save_kwargs as save_kwargs)

from bluesky.callbacks.zmq import RemoteDispatcher
from bluesky.utils import install_qt_kicker
from xpdconf.conf import glbl_dict

from xpdan.pipelines.main import *  # noqa: F403, F401
from xpdan.pipelines.save import *  # noqa: F403, F401
# from xpdan.pipelines.vis import *  # noqa: F403, F401
# from xpdan.pipelines.qoi import *  # noqa: F403, F401
from xpdan.pipelines.main import (mask_kwargs as _mask_kwargs,
                                  pdf_kwargs as _pdf_kwargs,
                                  fq_kwargs as _fq_kwargs,
                                  mask_setting as _mask_setting)
from xpdan.pipelines.save import save_kwargs as _save_kwargs
from bluesky.callbacks.broker import LiveImage
from shed.translation import ToEventStream
from xpdview.callbacks import LiveWaterfall

# from xpdan.pipelines.qoi import (
#     pdf_argrelmax_kwargs as _pdf_argrelmax_kwargs,
#     mean_argrelmax_kwargs as _mean_argrelmax_kwargs)

img_counter.sink(print)

ToEventStream(bg_corrected_img,
              ('image',)).starsink(
    LiveImage('image', window_title='Background_corrected_img',
              cmap='viridis'))

# polarization corrected img with mask overlayed
ToEventStream(
    pol_corrected_img.combine_latest(mask).starmap(overlay_mask),
    ('image',)).starsink(LiveImage('image', window_title='final img',
                                   limit_func=lambda im: (
                                       np.nanpercentile(im, 2.5),
                                       np.nanpercentile(im, 97.5)
                                   ), cmap='viridis'))

iq_em = (ToEventStream(mean
                       .combine_latest(q, emit_on=0), ('iq', 'q'))
         .starsink(LiveWaterfall('q', 'iq', units=('1/A', 'Intensity'),
                                 window_title='{} vs {}'.format('iq', 'q')),
                   stream_name='{} {} vis'.format('q', 'iq')))
(ToEventStream(mean
               .combine_latest(tth, emit_on=0), ('iq', 'tth'))
 .starsink(LiveWaterfall('tth', 'iq', units=('Degree', 'Intensity'),
                         window_title='{} vs {}'.format('iq', 'tth')),
           stream_name='{} {} vis'.format('tth', 'iq')))
# F(Q)
ToEventStream(fq, ('q', 'fq')).starsink(
    LiveWaterfall('q', 'fq', units=('1/A', 'Intensity'),
                  window_title='F(Q)'), stream_name='F(Q) vis')
# PDF
ToEventStream(pdf, ('r', 'gr')).starsink(
    LiveWaterfall('r', 'gr', units=('A', '1/A**2'),
                  window_title='PDF'), stream_name='G(r) vis')


def start_analysis(mask_kwargs=None,
                   pdf_kwargs=None, fq_kwargs=None, mask_setting=None,
                   save_kwargs=None,
                   # pdf_argrelmax_kwargs=None,
                   # mean_argrelmax_kwargs=None
                   ):
    """Start analysis pipeline

    Parameters
    ----------
    mask_kwargs : dict
        The kwargs passed to the masking see xpdtools.tools.mask_img
    pdf_kwargs : dict
        The kwargs passed to the pdf generator, see xpdtools.tools.pdf_getter
    fq_kwargs : dict
        The kwargs passed to the fq generator, see xpdtools.tools.fq_getter
    mask_setting : dict
        The setting of the mask
    save_kwargs : dict
        The kwargs passed to the main formatting node (mostly the filename
        template)
    """
    # if pdf_argrelmax_kwargs is None:
    #     pdf_argrelmax_kwargs = {}
    # if mean_argrelmax_kwargs is None:
    #     mean_argrelmax_kwargs = {}
    d = RemoteDispatcher(glbl_dict['proxy_address'])
    install_qt_kicker(
        loop=d.loop)  # This may need to be d._loop depending on tag
    if mask_setting is None:
        mask_setting = {}
    if fq_kwargs is None:
        fq_kwargs = {}
    if pdf_kwargs is None:
        pdf_kwargs = {}
    if mask_kwargs is None:
        mask_kwargs = {}
    if save_kwargs is None:
        save_kwargs = {}
    for a, b in zip([mask_kwargs, pdf_kwargs, fq_kwargs, mask_setting,
                     save_kwargs,
                     # pdf_argrelmax_kwargs,
                     # mean_argrelmax_kwargs
                     ],
                    [_mask_kwargs, _pdf_kwargs, _fq_kwargs, _mask_setting,
                     _save_kwargs,
                     # _pdf_argrelmax_kwargs,
                     # _mean_argrelmax_kwargs
                     ]):
        if a:
            b.update(a)

    d.subscribe(lambda *x: raw_source.emit(x))
    print('Starting Analysis Server')
    d.start()
