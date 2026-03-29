"""Sphinx documentation configuration for tmuxp."""

from __future__ import annotations

import pathlib
import sys

# Get the project root dir, which is the parent dir of this
cwd = pathlib.Path(__file__).parent
project_root = cwd.parent
src_root = project_root / "src"

sys.path.insert(0, str(src_root))
sys.path.insert(0, str(cwd / "_ext"))  # for local aafig extension

# package data
about: dict[str, str] = {}
with (src_root / "tmuxp" / "__about__.py").open() as fp:
    exec(fp.read(), about)

from gp_sphinx.config import make_linkcode_resolve, merge_sphinx_config  # noqa: E402

import tmuxp  # noqa: E402

conf = merge_sphinx_config(
    project=about["__title__"],
    version=about["__version__"],
    copyright=about["__copyright__"],
    source_repository=f"{about['__github__']}/",
    docs_url=about["__docs__"],
    source_branch="master",
    light_logo="img/tmuxp.svg",
    dark_logo="img/tmuxp.svg",
    extra_extensions=["aafig", "sphinx_argparse_neo.exemplar"],
    intersphinx_mapping={
        "python": ("https://docs.python.org/", None),
        "libtmux": ("https://libtmux.git-pull.com/", None),
    },
    linkcode_resolve=make_linkcode_resolve(tmuxp, about["__github__"]),
    # tmuxp-specific overrides
    theme_options={"mask_icon": "/_static/img/tmuxp.svg"},
    html_extra_path=["manifest.json"],
    html_favicon="_static/favicon.ico",
    aafig_format={"latex": "pdf", "html": "gif"},
    aafig_default_options={"scale": 0.75, "aspect": 0.5, "proportional": True},
    rediraffe_redirects="redirects.txt",
)
globals().update(conf)
