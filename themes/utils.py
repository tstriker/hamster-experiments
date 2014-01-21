import os, shutil
import cairo
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GdkPixbuf

from lib import graphics

def install_font(font_filename):
    fonts_dir = os.path.join(os.environ['HOME'], '.fonts')
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)

    font_path = os.path.join(fonts_dir, font_filename)
    if not os.path.exists(font_path):
        shutil.copyfile(os.path.join("assets", font_filename), font_path)


class override(object):
    """decorator that replaces do_render with the declared function and
    stores the original _do_render in case we might want it bit later"""
    def __init__(self, target_class):
        self.target_class = target_class

    def __call__(self, fn):
        name = fn.__name__
        # backup original
        setattr(self.target_class, "_original_%s" % name, getattr(self.target_class, name))
        # replace with the new one
        setattr(self.target_class, name, fn)



images = {}
def get_image(path, left = None, right = None, top = None, bottom = None):
    """returns image sliced up in margins as specified by left, right, top, bottom.
    The result is a Slice9 object below that has .render function for simplified
    rendering"""
    image = images.get((path, left, right, top, bottom))
    if not image:
        if any((left is not None, right is not None, top is not None, bottom is not None)):
            image = Slice9(path, left, right, top, bottom)
        else:
            image = Image(path)
    return image


# TODO - figure if perhaps this belongs to graphics
def vertical_gradient(sprite, start_color, end_color, start_y, end_y):
    linear = cairo.LinearGradient(0, start_y, 0, end_y)
    linear.add_color_stop_rgb(0, *graphics.Colors.parse(start_color))
    linear.add_color_stop_rgb(1, *graphics.Colors.parse(end_color))
    sprite.graphics.set_source(linear)



class Image(object):
    def __init__(self, image):
        if image is None:
            return
        elif isinstance(image, basestring):
            # in case of string we think it's a path - try opening it!
            if os.path.exists(image) == False:
                return

            if os.path.splitext(image)[1].lower() == ".png":
                image = cairo.ImageSurface.create_from_png(image)
            else:
                image = gdk.pixbuf_new_from_file(image)

        self.image_data, self.width, self.height = image, image.get_width(), image.get_height()

    def render(self, graphics, width = None, height = None, x_offset = 0, y_offset = 0):
        graphics.save_context( )
        graphics.translate( x_offset, y_offset )
        graphics.rectangle( 0, 0, width or self.width, height or self.height)
        graphics.clip()
        graphics.set_source_surface(self.image_data)
        graphics.paint()
        graphics.restore_context()


class Slice9(object):
    def __init__(self, image, left=0, right=0, top=0, bottom=0,
                 stretch_w = True, stretch_h = True):

        if isinstance(image, basestring):
            image = get_image(image)
        else:
            image = Image(image)

        self.width, self.height = image.width, image.height

        self.left, self.right = left, right
        self.top, self.bottom = top, bottom
        self.slices = []
        def get_slice(x, y, w, h):
            # we are grabbing bigger area and when painting will crop out to
            # just the actual needed pixels. This is done because otherwise when
            # stretching border, it uses white pixels to blend in
            x, y = x - 1, y - 1
            img = cairo.ImageSurface(cairo.FORMAT_ARGB32, w+2, h+2)
            ctx = cairo.Context(img)

            if isinstance(image.image_data, GdkPixbuf.Pixbuf):
                ctx.set_source_pixbuf(image.image_data, -x, -y)
            else:
                ctx.set_source_surface(image.image_data, -x, -y)

            ctx.rectangle(0, 0, w+2, h+2)
            ctx.clip()
            ctx.paint()
            return img, w, h

        # run left-right, top-down and slice image into 9 pieces
        exes = (0, left, image.width - right, image.width)
        ys = (0, top, image.height - bottom, image.height)
        for y1, y2 in zip(ys, ys[1:]):
            for x1, x2 in zip(exes, exes[1:]):
                self.slices.append(get_slice(x1, y1, x2 - x1, y2 - y1))

        self.stretch_w, self.stretch_h = stretch_w, stretch_h
        self.stretch_filter_mode = cairo.FILTER_BEST


    def render(self, graphics, width, height, x_offset=0, y_offset=0):
        """renders the image in the given graphics context with the told width
        and height"""
        def put_pattern(image, x, y, w, h):
            if w <= 0 or h <= 0:
                return

            graphics.save_context()


            if not self.stretch_w or not self.stretch_h:
                # if we repeat then we have to cut off the top-left margin
                # that we put in there so that stretching does not borrow white
                # pixels
                img = cairo.ImageSurface(cairo.FORMAT_ARGB32, image[1], image[2])
                ctx = cairo.Context(img)
                ctx.set_source_surface(image[0],
                                       0 if self.stretch_w else -1,
                                       0 if self.stretch_h else -1)
                ctx.rectangle(0, 0, image[1], image[2])
                ctx.clip()
                ctx.paint()
            else:
                img = image[0]

            pattern = cairo.SurfacePattern(img)
            pattern.set_extend(cairo.EXTEND_REPEAT)
            pattern.set_matrix(cairo.Matrix(x0 = 1 if self.stretch_w else 0,
                                            y0 = 1 if self.stretch_h else 0,
                                            xx = (image[1]) / float(w) if self.stretch_w else 1,
                                            yy = (image[2]) / float(h) if self.stretch_h else 1))
            pattern.set_filter(self.stretch_filter_mode)

            # truncating as fill on half pixel will lead to nasty gaps
            graphics.translate(int(x + x_offset), int(y + y_offset))
            graphics.set_source(pattern)
            graphics.rectangle(0, 0, int(w), int(h))
            graphics.clip()
            graphics.paint()
            graphics.restore_context()


        graphics.save_context()

        left, right, = self.left, self.right
        top, bottom = self.top, self.bottom

        # top-left
        put_pattern(self.slices[0], 0, 0, left, top)

        # top center - repeat width
        put_pattern(self.slices[1], left, 0, width - left - right, top)

        # top-right
        put_pattern(self.slices[2], width - right, 0, right, top)

        # left - repeat height
        put_pattern(self.slices[3], 0, top, left, height - top - bottom)

        # center - repeat width and height
        put_pattern(self.slices[4], left, top, width - left - right, height - top - bottom)

        # right - repeat height
        put_pattern(self.slices[5], width - right, top, right, height - top - bottom)

        # bottom-left
        put_pattern(self.slices[6], 0, height - bottom, left, bottom)

        # bottom center - repeat width
        put_pattern(self.slices[7], left, height - bottom, width - left - right, bottom)

        # bottom-right
        put_pattern(self.slices[8], width - right, height - bottom, right, bottom)

        graphics.rectangle(x_offset, y_offset, width, height)
        graphics.new_path()

        graphics.restore_context()




class SpriteSheetImage(graphics.Sprite):
    def __init__(self, sheet, offset_x, offset_y, width, height, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)

        #: Image or BitmapSprite object that has the graphics on it
        self.sheet = sheet

        self.offset_x = offset_x
        self.offset_y = offset_y
        self.width = width
        self.height = height

    def _draw(self, context, opacity = 1, parent_matrix = None):
        if not getattr(self.sheet, "cache_surface", None):
            # create cache surface similar to context and paint the image if not there
            # the cache surface is/was essential to performance
            # this somewhat upside down as ideally one might want to have a "cache surface instruction"
            surface = context.get_target().create_similar(self.sheet.cache_mode,
                                                          self.sheet.width,
                                                          self.sheet.height)
            local_context = cairo.Context(surface)
            if isinstance(self.sheet.image_data, GdkPixbuf.Pixbuf):
                local_context.set_source_pixbuf(self.sheet.image_data, 0, 0)
            else:
                local_context.set_source_surface(self.sheet.image_data)
            local_context.paint()
            self.sheet.cache_surface = surface


        # add instructions with the resulting surface
        if self._sprite_dirty:
            self.graphics.save_context()
            self.graphics.set_source_surface(self.sheet.cache_surface, -self.offset_x, -self.offset_y)
            self.graphics.rectangle(0, 0, self.width, self.height)
            self.graphics.clip()
            self.graphics.paint()
            self.graphics.restore_context()

        graphics.Sprite._draw(self,  context, opacity, parent_matrix)
