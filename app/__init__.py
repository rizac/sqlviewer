from flask import Flask

from flask.json import JSONEncoder
from datetime import datetime


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):  # encodes json generators and datetimes. Flask does it already but
        # formats datetims in his way
        try:
            if isinstance(obj, datetime):
                frmt = '%Y-%m-%d %H:%M:%S.%f' if obj.microsecond != 0 else '%Y-%m-%d %H:%M:%S'
                return obj.strftime(frmt)
#                 d = obj.timetuple()
#                 delim = " "
#                 day = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')[d.tm_wday]
#                 month = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
#                          'Nov', 'Dec')[d.tm_mon - 1]
#                 part1 = '%s, %02d%s%s%s%s' % (day, d.tm_mday, delim, month, delim, str(d.tm_year))
#                 part2 = obj.strftime('%H:%M:%S.%f')
#                 return "%s%s%s" % (part1, delim, part2)
                # as a remonder if we want to provide timezone (we don't, is up to the user)
                #  if obj.utcoffset() is not None:
                #      obj = obj - obj.utcoffset()

            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


app = Flask(__name__)

app.json_encoder = CustomJSONEncoder

from app import views  # @NoMove # pylint:disable=E402 @IgnorePep8
