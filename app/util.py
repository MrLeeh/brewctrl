from datetime import timedelta


def format_td(td: timedelta):
    m, s = divmod(td.seconds, 60)
    h, m = divmod(m, 60)

    template = '{h:02}:{m:02}:{s:02}'
    return template.format(h=h, m=m, s=s)
