from .caat import CAATFormat
from .cocos2d import Cocos2dFormat
from .css import CssFormat
from .html import HtmlFormat
from .img import ImageFormat
from .jsonformat import JSONFormat
from .less import LessFormat
from .scss import ScssFormat

formats = {'css': CssFormat,
           'cocos2d': Cocos2dFormat,
           'img': ImageFormat,
           'html': HtmlFormat,
           'json': JSONFormat,
           'caat': CAATFormat,
           'less': LessFormat,
           'scss': ScssFormat}
