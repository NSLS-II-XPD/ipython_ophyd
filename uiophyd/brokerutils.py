#!/usr/bin/env python


from dataportal.broker.simple_broker import fill_event
from metadatastore.api import find_events

def blank_events(header):
    "Return a list of unfilled events."
    from dataportal.broker import DataBroker as db
    raw_events = list(db.fetch_events(header, fill=False))
    raw_events.reverse()
    return raw_events


def events_generator(header):
    "Return a generator of Events. Large (nonscalar) data is lazy-loaded."
    for e in blank_events(header):
        fill_event(e)
        yield e


def ui_imagearray(header, index=0):
    "Return image array from the header object and event index."
    e = blank_events(header)[index]
    fill_event(e)
    nm = [k for k in e.data if k.endswith('image_lightfield')][0]
    rv = e.data[nm][0]
    return rv


def ui_nonzerofraction(header, index=0):
    x = ui_imagearray(header, index)
    cnz = (x.flatten() != 0).sum()
    rv = float(cnz) / x.size
    return rv
