#!/usr/bin/env python


from dataportal.broker.simple_broker import fill_event
from metadatastore.api import find_events

def blank_events(header):
    "Return a list of unfilled events."
    descriptors = header.event_descriptors
    if len(descriptors) > 1:
        raise NotImplementedError
    descriptor, = descriptors
    raw_events = find_events(descriptor=descriptor)
    # order in chronological order
    raw_events.reverse()
    return raw_events


def events_generator(header):
    "Return a generator of Events. Large (nonscalar) data is lazy-loaded."
    for e in blank_events(header):
        fill_event(e)
        yield e
