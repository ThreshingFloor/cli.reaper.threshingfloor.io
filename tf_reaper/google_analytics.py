import signal

import requests
import six.moves.urllib.parse

from .loggers import default_logger


enabled = True


def ga(t, ec, ea, el, cid, ev=False, v=1, tid='UA-115550236-2', extras=None):
    if not enabled:
        return

    params = {
        't': t,
        'ec': ec,
        'ea': ea,
        'el': el,
        'v': v,
        'tid': tid,
        'cid': cid
        }

    if extras:
        params.update(extras)

    if ev:
        params['ev'] = ev

    uri = "https://www.google-analytics.com/collect"

    def timeout_handler(signum, frame):
        raise Exception("Timeout expired reporting analytics.")

    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)
        requests.post(uri, data=six.moves.urllib.parse.urlencode(params),
                      headers={'referer': 'http://cli.threshingfloor.io'})
        signal.alarm(0)
    except Exception as e:
        default_logger.warning("Unable to report analytics: %s" % e)
