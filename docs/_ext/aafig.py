"""aafig plugin for sphinx.

sphinxcontrib.aafig
~~~~~~~~~~~~~~~~~~~

Allow embedded ASCII art to be rendered as nice looking images
using the aafigure reStructuredText extension.

See the README file for details.

:author: Leandro Lucarella <llucax@gmail.com>
:license: BOLA, see LICENSE for details
"""

import locale
import logging
import posixpath
import typing as t
from hashlib import sha1 as sha
from os import path

from docutils import nodes
from docutils.parsers.rst.directives import flag, images, nonnegative_int
from sphinx.errors import SphinxError
from sphinx.util.osutil import ensuredir, relative_uri

if t.TYPE_CHECKING:
    from sphinx.application import Sphinx


try:
    import aafigure
except ImportError:
    aafigure = None


logger = logging.getLogger(__name__)

DEFAULT_FORMATS = {"html": "svg", "latex": "pdf", "text": None}


def merge_dict(
    dst: t.Dict[str, t.Optional[str]],
    src: t.Dict[str, t.Optional[str]],
) -> t.Dict[str, t.Optional[str]]:
    for k, v in src.items():
        if k not in dst:
            dst[k] = v
    return dst


def get_basename(
    text: str,
    options: t.Dict[str, str],
    prefix: t.Optional[str] = "aafig",
) -> str:
    options = options.copy()
    if "format" in options:
        del options["format"]
    hashkey = text + str(options)
    _id = sha(hashkey.encode("utf-8")).hexdigest()
    return f"{prefix}-{_id}"


class AafigError(SphinxError):
    category = "aafig error"


class AafigDirective(images.Image):  # type:ignore
    """Directive to insert an ASCII art figure to be rendered by aafigure."""

    has_content = True
    required_arguments = 0
    own_option_spec: t.ClassVar = {
        "line_width": float,
        "background": str,
        "foreground": str,
        "fill": str,
        "aspect": nonnegative_int,
        "textual": flag,
        "proportional": flag,
    }
    option_spec = images.Image.option_spec.copy()
    option_spec.update(own_option_spec)

    def run(self) -> t.List[nodes.Node]:
        aafig_options = {}
        own_options_keys = [self.own_option_spec.keys(), "scale"]
        for k, v in self.options.items():
            if k in own_options_keys:
                # convert flags to booleans
                if v is None:
                    v = True
                # convert percentage to float
                if k in {"scale", "aspect"}:
                    v = float(v) / 100.0
                aafig_options[k] = v
                del self.options[k]
        self.arguments = [""]
        (image_node,) = images.Image.run(self)
        if isinstance(image_node, nodes.system_message):
            return [image_node]
        text = "\n".join(self.content)
        image_node.aafig = {"options": aafig_options, "text": text}
        return [image_node]


def render_aafig_images(app: "Sphinx", doctree: nodes.Node) -> None:
    format_map = app.builder.config.aafig_format
    merge_dict(format_map, DEFAULT_FORMATS)
    if aafigure is None:
        logger.warning(
            "aafigure module not installed, ASCII art images "
            "will be rendered as literal text",
        )
    for img in doctree.traverse(nodes.image):
        if not hasattr(img, "aafig"):
            continue
        if aafigure is None:
            continue
        options = img.aafig["options"]
        text = img.aafig["text"]
        _format = app.builder.format
        merge_dict(options, app.builder.config.aafig_default_options)
        if _format in format_map:
            options["format"] = format_map[_format]
        else:
            logger.warning(
                'unsupported builder format "%s", please '
                "add a custom entry in aafig_format config "
                "option for this builder" % _format,
            )
            img.replace_self(nodes.literal_block(text, text))
            continue
        if options["format"] is None:
            img.replace_self(nodes.literal_block(text, text))
            continue
        try:
            fname, _outfn, _id, extra = render_aafigure(app, text, options)
        except AafigError as exc:
            logger.warning("aafigure error: " + str(exc))
            img.replace_self(nodes.literal_block(text, text))
            continue
        img["uri"] = fname
        # FIXME: find some way to avoid this hack in aafigure
        if extra:
            (width, height) = (x.split('"')[1] for x in extra.split())
            if "width" not in img:
                img["width"] = width
            if "height" not in img:
                img["height"] = height


class AafigureNotInstalled(AafigError):
    def __init__(self, *args: object, **kwargs: object) -> None:
        return super().__init__("aafigure module not installed", *args, **kwargs)


def render_aafigure(
    app: "Sphinx",
    text: str,
    options: t.Dict[str, str],
) -> t.Tuple[str, str, t.Optional[str], t.Optional[str]]:
    """Render an ASCII art figure into the requested format output file."""
    if aafigure is None:
        raise AafigureNotInstalled

    fname = get_basename(text, options)
    fname = "{}.{}".format(get_basename(text, options), options["format"])
    if app.builder.format == "html":
        # HTML
        imgpath = relative_uri(app.builder.env.docname, "_images")
        relfn = posixpath.join(imgpath, fname)
        outfn = path.join(app.builder.outdir, "_images", fname)
    else:
        # Non-HTML
        if app.builder.format != "latex":
            logger.warning(
                "aafig: the builder format %s is not officially "
                "supported, aafigure images could not work. "
                "Please report problems and working builder to "
                "avoid this warning in the future" % app.builder.format,
            )
        relfn = fname
        outfn = path.join(app.builder.outdir, fname)
    metadata_fname = "%s.aafig" % outfn

    try:
        if path.isfile(outfn):
            extra = None
            if options["format"].lower() == "svg":
                f = None
                try:
                    try:
                        with open(
                            metadata_fname, encoding=locale.getpreferredencoding(False)
                        ) as f:
                            extra = f.read()
                    except Exception as e:
                        raise AafigError from e
                finally:
                    if f is not None:
                        f.close()
            return relfn, outfn, None, extra
    except AafigError:
        pass

    ensuredir(path.dirname(outfn))

    try:
        (visitor, output) = aafigure.render(text, outfn, options)
        output.close()
    except aafigure.UnsupportedFormatError as e:
        raise AafigError(str(e)) from e

    extra = None
    if options["format"].lower() == "svg":
        extra = visitor.get_size_attrs()
        with open(
            metadata_fname, "w", encoding=locale.getpreferredencoding(False)
        ) as f:
            f.write(extra)

    return relfn, outfn, None, extra


def setup(app: "Sphinx") -> None:
    app.add_directive("aafig", AafigDirective)
    app.connect("doctree-read", render_aafig_images)
    app.add_config_value("aafig_format", DEFAULT_FORMATS, "html")
    app.add_config_value("aafig_default_options", {}, "html")


# vim: set expandtab shiftwidth=4 softtabstop=4 :
