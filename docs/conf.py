# flake8: NOQA E5
import inspect
import os
import sys
from os.path import dirname, relpath
from pathlib import Path

import tmuxp

# Get the project root dir, which is the parent dir of this
cwd = Path.cwd()
project_root = cwd.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(cwd / "_ext"))

# package data
about = {}
with open("../tmuxp/__about__.py") as fp:
    exec(fp.read(), about)

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx.ext.todo",
    "sphinx.ext.napoleon",
    "sphinx.ext.linkcode",
    "aafig",
    "sphinx_issues",
    "myst_parser",
    "sphinx_click.ext",  # sphinx-click
    "sphinx_inline_tabs",
    "sphinx_copybutton",
    "sphinxext.opengraph",
    "myst_parser",
]

myst_enable_extensions = ["colon_fence"]

issues_github_path = about["__github__"].replace("https://github.com/", "")

templates_path = ["_templates"]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

master_doc = "index"

project = about["__title__"]
copyright = about["__copyright__"]

version = "%s" % (".".join(about["__version__"].split("."))[:2])
release = "%s" % (about["__version__"])

exclude_patterns = ["_build"]

pygments_style = "monokai"
pygments_dark_style = "monokai"

html_css_files = ["css/custom.css"]
html_extra_path = ["manifest.json"]
html_static_path = ["_static"]
html_theme = "furo"
html_theme_path = []
html_theme_options = {
    "light_logo": "img/tmuxp.svg",
    "dark_logo": "img/tmuxp.svg",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": about["__github__"],
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}
html_sidebars = {
    "**": [
        "sidebar/scroll-start.html",
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/navigation.html",
        "sidebar/projects.html",
        "sidebar/scroll-end.html",
    ]
}

# sphinxext.opengraph
ogp_site_url = about["__docs__"]
ogp_image = "_static/img/icons/icon-192x192.png"
ogp_desscription_length = about["__description__"]
ogp_site_name = about["__title__"]

# sphinx-copybutton
copybutton_prompt_text = (
    r">>> |\.\.\. |> |\$ |\# | In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
)
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True

htmlhelp_basename = "%sdoc" % about["__title__"]

latex_documents = [
    (
        "index",
        "{}.tex".format(about["__package_name__"]),
        "{} Documentation".format(about["__title__"]),
        about["__author__"],
        "manual",
    )
]

man_pages = [
    (
        "index",
        about["__package_name__"],
        "{} Documentation".format(about["__title__"]),
        about["__author__"],
        1,
    )
]

texinfo_documents = [
    (
        "index",
        "{}".format(about["__package_name__"]),
        "{} Documentation".format(about["__title__"]),
        about["__author__"],
        about["__package_name__"],
        about["__description__"],
        "Miscellaneous",
    )
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/", None),
    "libtmux": ("https://libtmux.git-pull.com/", None),
    "click": ("http://click.pocoo.org/5", None),
}

# aafig format, try to get working with pdf
aafig_format = dict(latex="pdf", html="gif")

aafig_default_options = dict(scale=0.75, aspect=0.5, proportional=True)


def linkcode_resolve(domain, info):  # NOQA: C901
    """
    Determine the URL corresponding to Python object

    Notes
    -----
    From https://github.com/numpy/numpy/blob/v1.15.1/doc/source/conf.py, 7c49cfa
    on Jul 31. License BSD-3. https://github.com/numpy/numpy/blob/v1.15.1/LICENSE.txt
    """
    if domain != "py":
        return None

    modname = info["module"]
    fullname = info["fullname"]

    submod = sys.modules.get(modname)
    if submod is None:
        return None

    obj = submod
    for part in fullname.split("."):
        try:
            obj = getattr(obj, part)
        except Exception:
            return None

    # strip decorators, which would resolve to the source of the decorator
    # possibly an upstream bug in getsourcefile, bpo-1764286
    try:
        unwrap = inspect.unwrap
    except AttributeError:
        pass
    else:
        obj = unwrap(obj)

    try:
        fn = inspect.getsourcefile(obj)
    except Exception:
        fn = None
    if not fn:
        return None

    try:
        source, lineno = inspect.getsourcelines(obj)
    except Exception:
        lineno = None

    if lineno:
        linespec = "#L%d-L%d" % (lineno, lineno + len(source) - 1)
    else:
        linespec = ""

    fn = relpath(fn, start=dirname(tmuxp.__file__))

    if "dev" in about["__version__"]:
        return "{}/blob/master/{}/{}{}".format(
            about["__github__"],
            about["__package_name__"],
            fn,
            linespec,
        )
    else:
        return "{}/blob/v{}/{}/{}{}".format(
            about["__github__"],
            about["__version__"],
            about["__package_name__"],
            fn,
            linespec,
        )
