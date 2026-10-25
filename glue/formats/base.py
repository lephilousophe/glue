import json
import os
import plistlib
import textwrap

from jinja2 import Template

from glue import __version__
from glue.helpers import nearest_fration, round_up


class BaseFormat:

    extension = None
    build_per_ratio = False

    def __init__(self, sprite):
        self.sprite = sprite

    def output_dir(self, *args, **kwargs):
        return self.sprite.config[f'{self.format_label}_dir']

    def output_filename(self, ratio=None, *args, **kwargs):
        if self.build_per_ratio:
            if ratio is None:
                msg = f"Format {self.__class__} output_filename requires a ratio."
                raise AttributeError(msg)
            ratio_suffix = f'@{ratio:.1f}x' if int(ratio) != ratio else f'@{int(ratio)}x'
            if ratio_suffix == '@1x':
                ratio_suffix = ''
            return f'{self.sprite.name}{ratio_suffix}'
        return self.sprite.name

    def output_path(self, *args, **kwargs):
        return os.path.join(self.output_dir(*args, **kwargs), f'{self.output_filename(*args, **kwargs)}.{self.extension}')

    def build(self):
        if self.build_per_ratio:
            for ratio in self.sprite.config['ratios']:
                self.save(ratio=ratio)
        else:
            self.save()

    def save(self, *args, **kwargs):
        raise NotImplementedError

    def needs_rebuild(self):
        return True

    def validate(self):
        pass

    @property
    def format_label(self):
        from glue.formats import formats
        return {v: k for k, v in formats.items()}[self.__class__]

    @classmethod
    def populate_argument_parser(cls, parser):
        pass

    @classmethod
    def apply_parser_contraints(cls, parser, options):
        pass

    def fix_windows_path(self, path):
        if os.name == 'nt':
            path = path.replace('\\', '/')
        return path


class BaseTextFormat(BaseFormat):

    def get_context(self, *args, **kwargs):
        sprite_path = os.path.relpath(self.sprite.sprite_path(), self.output_dir())
        sprite_path = self.fix_windows_path(sprite_path)
        context = {'version': __version__,
                   'hash': self.sprite.hash,
                   'name': self.sprite.name,
                   'sprite_path': sprite_path,
                   'sprite_filename': os.path.basename(sprite_path),
                   'width': round_up(self.sprite.canvas_size[0] / self.sprite.max_ratio),
                   'height': round_up(self.sprite.canvas_size[1] / self.sprite.max_ratio),
                   'images': [],
                   'ratios': {}}

        for i, img in enumerate(self.sprite.images):
            base_x = img.x * -1 - img.margin[3] * self.sprite.max_ratio
            base_y = img.y * -1 - img.margin[0] * self.sprite.max_ratio
            base_abs_x = img.x + img.margin[3] * self.sprite.max_ratio
            base_abs_y = img.y + img.margin[0] * self.sprite.max_ratio

            image = {'filename': img.filename,
                         'last': i == len(self.sprite.images) - 1,
                         'x': round_up(base_x / self.sprite.max_ratio),
                         'y': round_up(base_y / self.sprite.max_ratio),
                         'abs_x': round_up(base_abs_x / self.sprite.max_ratio),
                         'abs_y': round_up(base_abs_y / self.sprite.max_ratio),
                         'height': round_up((img.height / self.sprite.max_ratio) + img.padding[0] + img.padding[2]),
                         'width': round_up((img.width / self.sprite.max_ratio) + img.padding[1] + img.padding[3]),
                         'original_width': img.original_width,
                         'original_height': img.original_height,
                         'ratios': {}}

            for r in self.sprite.ratios:
                image['ratios'][r] = {'filename': img.filename,
                                          'last': i == len(self.sprite.images) - 1,
                                          'x': round_up(base_x / self.sprite.max_ratio * r),
                                          'y': round_up(base_y / self.sprite.max_ratio * r),
                                          'abs_x': round_up(base_abs_x / self.sprite.max_ratio * r),
                                          'abs_y': round_up(base_abs_y / self.sprite.max_ratio * r),
                                          'height': round_up((img.height + img.padding[0] + img.padding[2]) / self.sprite.max_ratio * r),
                                          'width': round_up((img.width + img.padding[1] + img.padding[3]) / self.sprite.max_ratio * r)}

            context['images'].append(image)

        # Ratios
        for r in self.sprite.ratios:
            ratio_sprite_path = os.path.relpath(self.sprite.sprite_path(ratio=r), self.output_dir())
            ratio_sprite_path = self.fix_windows_path(ratio_sprite_path)
            context['ratios'][r] = {'ratio': r,
                                        'fraction': nearest_fration(r),
                                        'sprite_path': ratio_sprite_path,
                                        'sprite_filename': os.path.basename(ratio_sprite_path),
                                        'width': round_up(self.sprite.canvas_size[0] / self.sprite.max_ratio * r),
                                        'height': round_up(self.sprite.canvas_size[1] / self.sprite.max_ratio * r)}

        return context

    def render(self, *args, **kwargs):
        raise NotImplementedError

    def save(self, *args, **kwargs):
        # Create the destination directory if required
        if not os.path.exists(self.output_dir(*args, **kwargs)):
            os.makedirs(self.output_dir(*args, **kwargs))

        with open(self.output_path(*args, **kwargs), 'w', encoding='utf-8') as f:
            f.write(self.render(*args, **kwargs))


class BaseJSONFormat(BaseTextFormat):

    meta_key = 'meta'

    def needs_rebuild(self):
        for ratio in self.sprite.config['ratios']:
            json_path = self.output_path(ratio)
            try:
                with open(json_path, encoding='utf-8') as f:
                    data = json.loads(f.read())
                    if data[self.meta_key]['hash'] != self.sprite.hash:
                        return True
            except (OSError, ValueError, KeyError):
                return True
        return False

    def render(self, *args, **kwargs):
        return json.dumps(self.get_context(*args, **kwargs), indent=4)


class BasePlistFormat(BaseTextFormat):

    meta_key = 'metadata'

    def render(self, *args, **kwargs):
        context = self.get_context(*args, **kwargs)
        return plistlib.dumps(context).decode('unicode_escape')

    def needs_rebuild(self):
        for ratio in self.sprite.config['ratios']:
            cocos2d_path = self.output_path(ratio)
            try:
                with open(cocos2d_path, 'rb') as f:
                    data = plistlib.load(f)
                if data[self.meta_key]['hash'] != self.sprite.hash:
                    return True
            except (OSError, ValueError, KeyError):
                return True
        return False


class JinjaTextFormat(BaseTextFormat):

    template = ''

    def render(self, *args, **kwargs):
        context = self.get_context(*args, **kwargs)
        template = self.template
        custom_template_config = f'{self.format_label}_template'
        if self.sprite.config.get(custom_template_config):
            with open(self.sprite.config[custom_template_config]) as f:
                template = f.read()
        return Template(textwrap.dedent(template).strip()).render(**context)
