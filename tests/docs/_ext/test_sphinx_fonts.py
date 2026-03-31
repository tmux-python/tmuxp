"""Tests for sphinx_fonts Sphinx extension."""

from __future__ import annotations

import logging
import pathlib
import types
import typing as t
import urllib.error

import pytest
import sphinx_fonts

# --- _cache_dir tests ---


def test_cache_dir_returns_home_cache_path() -> None:
    """_cache_dir returns ~/.cache/sphinx-fonts."""
    result = sphinx_fonts._cache_dir()
    assert result == pathlib.Path.home() / ".cache" / "sphinx-fonts"


# --- _cdn_url tests ---


class CdnUrlFixture(t.NamedTuple):
    """Test fixture for CDN URL generation."""

    test_id: str
    package: str
    version: str
    font_id: str
    subset: str
    weight: int
    style: str
    expected_url: str


CDN_URL_FIXTURES: list[CdnUrlFixture] = [
    CdnUrlFixture(
        test_id="normal_weight",
        package="@fontsource/open-sans",
        version="5.2.5",
        font_id="open-sans",
        subset="latin",
        weight=400,
        style="normal",
        expected_url=(
            "https://cdn.jsdelivr.net/npm/@fontsource/open-sans@5.2.5"
            "/files/open-sans-latin-400-normal.woff2"
        ),
    ),
    CdnUrlFixture(
        test_id="bold_italic",
        package="@fontsource/roboto",
        version="5.0.0",
        font_id="roboto",
        subset="latin-ext",
        weight=700,
        style="italic",
        expected_url=(
            "https://cdn.jsdelivr.net/npm/@fontsource/roboto@5.0.0"
            "/files/roboto-latin-ext-700-italic.woff2"
        ),
    ),
]


@pytest.mark.parametrize(
    list(CdnUrlFixture._fields),
    CDN_URL_FIXTURES,
    ids=[f.test_id for f in CDN_URL_FIXTURES],
)
def test_cdn_url(
    test_id: str,
    package: str,
    version: str,
    font_id: str,
    subset: str,
    weight: int,
    style: str,
    expected_url: str,
) -> None:
    """_cdn_url formats the CDN URL template correctly."""
    result = sphinx_fonts._cdn_url(package, version, font_id, subset, weight, style)
    assert result == expected_url


def test_cdn_url_matches_template() -> None:
    """_cdn_url produces URLs matching CDN_TEMPLATE structure."""
    url = sphinx_fonts._cdn_url(
        "@fontsource/inter", "5.1.0", "inter", "latin", 400, "normal"
    )
    assert url.startswith("https://cdn.jsdelivr.net/npm/")
    assert "@fontsource/inter@5.1.0" in url
    assert url.endswith(".woff2")


# --- _unicode_range tests ---


def test_unicode_range_latin() -> None:
    """_unicode_range returns a non-empty range for 'latin'."""
    result = sphinx_fonts._unicode_range("latin")
    assert result.startswith("U+")
    assert "U+0000" in result


def test_unicode_range_latin_ext() -> None:
    """_unicode_range returns a non-empty range for 'latin-ext'."""
    result = sphinx_fonts._unicode_range("latin-ext")
    assert result.startswith("U+")
    assert result != sphinx_fonts._unicode_range("latin")


def test_unicode_range_unknown_subset() -> None:
    """_unicode_range returns empty string for unknown subsets."""
    result = sphinx_fonts._unicode_range("klingon")
    assert result == ""


def test_unicode_range_all_known_subsets_non_empty() -> None:
    """Every subset in _UNICODE_RANGES produces a non-empty range."""
    for subset, urange in sphinx_fonts._UNICODE_RANGES.items():
        assert urange.startswith("U+"), f"subset {subset!r} has invalid range"
        assert sphinx_fonts._unicode_range(subset) == urange


# --- _download_font tests ---


def test_download_font_cached(
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """_download_font returns True and logs debug when file exists."""
    dest = tmp_path / "font.woff2"
    dest.write_bytes(b"cached-data")

    with caplog.at_level(logging.DEBUG, logger="sphinx_fonts"):
        result = sphinx_fonts._download_font("https://example.com/font.woff2", dest)

    assert result is True
    debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
    assert any("cached" in r.message for r in debug_records)


def test_download_font_success(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """_download_font downloads and returns True on success."""
    dest = tmp_path / "subdir" / "font.woff2"

    def fake_urlretrieve(url: str, filename: t.Any) -> tuple[str, t.Any]:
        pathlib.Path(filename).write_bytes(b"font-data")
        return (str(filename), None)

    monkeypatch.setattr("sphinx_fonts.urllib.request.urlretrieve", fake_urlretrieve)

    with caplog.at_level(logging.INFO, logger="sphinx_fonts"):
        result = sphinx_fonts._download_font("https://example.com/font.woff2", dest)

    assert result is True
    info_records = [r for r in caplog.records if r.levelno == logging.INFO]
    assert any("downloaded" in r.message for r in info_records)


def test_download_font_url_error(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """_download_font returns False and warns on URLError."""
    dest = tmp_path / "font.woff2"

    msg = "network error"

    def fake_urlretrieve(url: str, filename: t.Any) -> t.NoReturn:
        raise urllib.error.URLError(msg)

    monkeypatch.setattr("sphinx_fonts.urllib.request.urlretrieve", fake_urlretrieve)

    with caplog.at_level(logging.WARNING, logger="sphinx_fonts"):
        result = sphinx_fonts._download_font("https://example.com/font.woff2", dest)

    assert result is False
    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("failed" in r.message for r in warning_records)


def test_download_font_os_error(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """_download_font returns False and warns on OSError."""
    dest = tmp_path / "font.woff2"

    msg = "disk full"

    def fake_urlretrieve(url: str, filename: t.Any) -> t.NoReturn:
        raise OSError(msg)

    monkeypatch.setattr("sphinx_fonts.urllib.request.urlretrieve", fake_urlretrieve)

    with caplog.at_level(logging.WARNING, logger="sphinx_fonts"):
        result = sphinx_fonts._download_font("https://example.com/font.woff2", dest)

    assert result is False
    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("failed" in r.message for r in warning_records)


def test_download_font_partial_file_cleanup(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_download_font removes partial file on failure."""
    dest = tmp_path / "cache" / "partial.woff2"

    msg = "disk full"

    def fake_urlretrieve(url: str, filename: t.Any) -> t.NoReturn:
        pathlib.Path(filename).write_bytes(b"partial")
        raise OSError(msg)

    monkeypatch.setattr("sphinx_fonts.urllib.request.urlretrieve", fake_urlretrieve)

    result = sphinx_fonts._download_font("https://example.com/font.woff2", dest)

    assert result is False
    assert not dest.exists()


# --- _on_builder_inited tests ---


def _make_app(
    tmp_path: pathlib.Path,
    *,
    builder_format: str = "html",
    fonts: list[dict[str, t.Any]] | None = None,
    preload: list[tuple[str, int, str]] | None = None,
    fallbacks: list[dict[str, str]] | None = None,
    variables: dict[str, str] | None = None,
) -> types.SimpleNamespace:
    """Create a fake Sphinx app namespace for testing."""
    config = types.SimpleNamespace(
        sphinx_fonts=fonts if fonts is not None else [],
        sphinx_font_preload=preload if preload is not None else [],
        sphinx_font_fallbacks=fallbacks if fallbacks is not None else [],
        sphinx_font_css_variables=variables if variables is not None else {},
    )
    builder = types.SimpleNamespace(format=builder_format)
    return types.SimpleNamespace(
        builder=builder,
        config=config,
        outdir=str(tmp_path / "output"),
    )


def test_on_builder_inited_non_html(tmp_path: pathlib.Path) -> None:
    """_on_builder_inited returns early for non-HTML builders."""
    app = _make_app(tmp_path, builder_format="latex")
    sphinx_fonts._on_builder_inited(app)
    assert not hasattr(app, "_font_faces")


def test_on_builder_inited_empty_fonts(tmp_path: pathlib.Path) -> None:
    """_on_builder_inited returns early when no fonts configured."""
    app = _make_app(tmp_path, fonts=[])
    sphinx_fonts._on_builder_inited(app)
    assert not hasattr(app, "_font_faces")


def test_on_builder_inited_with_fonts(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_on_builder_inited processes fonts and stores results on app."""
    monkeypatch.setattr("sphinx_fonts._cache_dir", lambda: tmp_path / "cache")

    fonts = [
        {
            "package": "@fontsource/open-sans",
            "version": "5.2.5",
            "family": "Open Sans",
            "weights": [400, 700],
            "styles": ["normal"],
        },
    ]
    app = _make_app(tmp_path, fonts=fonts)

    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    for weight in [400, 700]:
        (cache / f"open-sans-latin-{weight}-normal.woff2").write_bytes(b"data")

    sphinx_fonts._on_builder_inited(app)

    assert len(app._font_faces) == 2
    assert app._font_faces[0]["family"] == "Open Sans"
    assert app._font_faces[0]["weight"] == "400"
    assert app._font_faces[1]["weight"] == "700"
    assert app._font_preload_hrefs == []
    assert app._font_fallbacks == []
    assert app._font_css_variables == {}


def test_on_builder_inited_download_failure(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_on_builder_inited skips font_faces entry on download failure."""
    monkeypatch.setattr("sphinx_fonts._cache_dir", lambda: tmp_path / "cache")

    msg = "offline"

    def fake_urlretrieve(url: str, filename: t.Any) -> t.NoReturn:
        raise urllib.error.URLError(msg)

    monkeypatch.setattr("sphinx_fonts.urllib.request.urlretrieve", fake_urlretrieve)

    fonts = [
        {
            "package": "@fontsource/inter",
            "version": "5.0.0",
            "family": "Inter",
            "weights": [400],
            "styles": ["normal"],
        },
    ]
    app = _make_app(tmp_path, fonts=fonts)

    sphinx_fonts._on_builder_inited(app)

    assert len(app._font_faces) == 0


def test_on_builder_inited_explicit_subset(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_on_builder_inited respects explicit subset in font config."""
    monkeypatch.setattr("sphinx_fonts._cache_dir", lambda: tmp_path / "cache")

    fonts = [
        {
            "package": "@fontsource/noto-sans",
            "version": "5.0.0",
            "family": "Noto Sans",
            "subset": "latin-ext",
            "weights": [400],
            "styles": ["normal"],
        },
    ]
    app = _make_app(tmp_path, fonts=fonts)

    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    (cache / "noto-sans-latin-ext-400-normal.woff2").write_bytes(b"data")

    sphinx_fonts._on_builder_inited(app)

    assert app._font_faces[0]["filename"] == "noto-sans-latin-ext-400-normal.woff2"


def test_on_builder_inited_multiple_subsets(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_on_builder_inited downloads files for each subset and includes unicode_range."""
    monkeypatch.setattr("sphinx_fonts._cache_dir", lambda: tmp_path / "cache")

    fonts = [
        {
            "package": "@fontsource/ibm-plex-sans",
            "version": "5.2.8",
            "family": "IBM Plex Sans",
            "subsets": ["latin", "latin-ext"],
            "weights": [400],
            "styles": ["normal"],
        },
    ]
    app = _make_app(tmp_path, fonts=fonts)

    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    (cache / "ibm-plex-sans-latin-400-normal.woff2").write_bytes(b"data")
    (cache / "ibm-plex-sans-latin-ext-400-normal.woff2").write_bytes(b"data")

    sphinx_fonts._on_builder_inited(app)

    assert len(app._font_faces) == 2
    filenames = [f["filename"] for f in app._font_faces]
    assert "ibm-plex-sans-latin-400-normal.woff2" in filenames
    assert "ibm-plex-sans-latin-ext-400-normal.woff2" in filenames

    # unicode_range should be populated for known subsets
    latin_face = next(f for f in app._font_faces if "latin-400" in f["filename"])
    assert latin_face["unicode_range"].startswith("U+")
    latin_ext_face = next(f for f in app._font_faces if "latin-ext" in f["filename"])
    assert latin_ext_face["unicode_range"].startswith("U+")
    assert latin_face["unicode_range"] != latin_ext_face["unicode_range"]


def test_on_builder_inited_legacy_subset_gets_unicode_range(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy single 'subset' config still produces unicode_range in font_faces."""
    monkeypatch.setattr("sphinx_fonts._cache_dir", lambda: tmp_path / "cache")

    fonts = [
        {
            "package": "@fontsource/noto-sans",
            "version": "5.0.0",
            "family": "Noto Sans",
            "subset": "latin",
            "weights": [400],
            "styles": ["normal"],
        },
    ]
    app = _make_app(tmp_path, fonts=fonts)

    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    (cache / "noto-sans-latin-400-normal.woff2").write_bytes(b"data")

    sphinx_fonts._on_builder_inited(app)

    assert len(app._font_faces) == 1
    assert app._font_faces[0]["unicode_range"].startswith("U+")


def test_on_builder_inited_preload_uses_primary_subset(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preload uses the first (primary) subset when multiple are configured."""
    monkeypatch.setattr("sphinx_fonts._cache_dir", lambda: tmp_path / "cache")

    fonts = [
        {
            "package": "@fontsource/ibm-plex-sans",
            "version": "5.2.8",
            "family": "IBM Plex Sans",
            "subsets": ["latin", "latin-ext"],
            "weights": [400],
            "styles": ["normal"],
        },
    ]
    preload = [("IBM Plex Sans", 400, "normal")]
    app = _make_app(tmp_path, fonts=fonts, preload=preload)

    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    (cache / "ibm-plex-sans-latin-400-normal.woff2").write_bytes(b"data")
    (cache / "ibm-plex-sans-latin-ext-400-normal.woff2").write_bytes(b"data")

    sphinx_fonts._on_builder_inited(app)

    # Preload should only include the primary (first) subset
    assert app._font_preload_hrefs == ["ibm-plex-sans-latin-400-normal.woff2"]


def test_on_builder_inited_preload_match(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_on_builder_inited builds preload_hrefs for matching preload specs."""
    monkeypatch.setattr("sphinx_fonts._cache_dir", lambda: tmp_path / "cache")

    fonts = [
        {
            "package": "@fontsource/open-sans",
            "version": "5.2.5",
            "family": "Open Sans",
            "weights": [400],
            "styles": ["normal"],
        },
    ]
    preload = [("Open Sans", 400, "normal")]
    app = _make_app(tmp_path, fonts=fonts, preload=preload)

    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    (cache / "open-sans-latin-400-normal.woff2").write_bytes(b"data")

    sphinx_fonts._on_builder_inited(app)

    assert app._font_preload_hrefs == ["open-sans-latin-400-normal.woff2"]


def test_on_builder_inited_preload_no_match(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_on_builder_inited produces empty preload when family doesn't match."""
    monkeypatch.setattr("sphinx_fonts._cache_dir", lambda: tmp_path / "cache")

    fonts = [
        {
            "package": "@fontsource/open-sans",
            "version": "5.2.5",
            "family": "Open Sans",
            "weights": [400],
            "styles": ["normal"],
        },
    ]
    preload = [("Nonexistent Font", 400, "normal")]
    app = _make_app(tmp_path, fonts=fonts, preload=preload)

    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    (cache / "open-sans-latin-400-normal.woff2").write_bytes(b"data")

    sphinx_fonts._on_builder_inited(app)

    assert app._font_preload_hrefs == []


def test_on_builder_inited_fallbacks_and_variables(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_on_builder_inited stores fallbacks and CSS variables on app."""
    monkeypatch.setattr("sphinx_fonts._cache_dir", lambda: tmp_path / "cache")

    fonts = [
        {
            "package": "@fontsource/inter",
            "version": "5.0.0",
            "family": "Inter",
            "weights": [400],
            "styles": ["normal"],
        },
    ]
    fallbacks = [{"family": "system-ui", "style": "normal", "weight": "400"}]
    variables = {"--font-body": "Inter, system-ui"}
    app = _make_app(tmp_path, fonts=fonts, fallbacks=fallbacks, variables=variables)

    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    (cache / "inter-latin-400-normal.woff2").write_bytes(b"data")

    sphinx_fonts._on_builder_inited(app)

    assert app._font_fallbacks == fallbacks
    assert app._font_css_variables == variables


# --- _on_html_page_context tests ---


def test_on_html_page_context_with_attrs() -> None:
    """_on_html_page_context injects font data from app attributes."""
    app = types.SimpleNamespace(
        _font_preload_hrefs=["font-400.woff2"],
        _font_faces=[
            {
                "family": "Inter",
                "weight": "400",
                "style": "normal",
                "filename": "font-400.woff2",
            },
        ],
        _font_fallbacks=[{"family": "system-ui"}],
        _font_css_variables={"--font-body": "Inter"},
    )
    context: dict[str, t.Any] = {}

    sphinx_fonts._on_html_page_context(
        app,
        "index",
        "page.html",
        context,
        None,
    )

    assert context["font_preload_hrefs"] == ["font-400.woff2"]
    assert context["font_faces"] == app._font_faces
    assert context["font_fallbacks"] == [{"family": "system-ui"}]
    assert context["font_css_variables"] == {"--font-body": "Inter"}


def test_on_html_page_context_without_attrs() -> None:
    """_on_html_page_context uses defaults when app attrs are missing."""
    app = types.SimpleNamespace()
    context: dict[str, t.Any] = {}

    sphinx_fonts._on_html_page_context(
        app,
        "index",
        "page.html",
        context,
        None,
    )

    assert context["font_preload_hrefs"] == []
    assert context["font_faces"] == []
    assert context["font_fallbacks"] == []
    assert context["font_css_variables"] == {}


# --- setup tests ---


def test_setup_return_value() -> None:
    """Verify setup() returns correct metadata dict."""
    config_values: list[tuple[str, t.Any, str]] = []
    connections: list[tuple[str, t.Any]] = []

    app = types.SimpleNamespace(
        add_config_value=lambda name, default, rebuild: config_values.append(
            (name, default, rebuild)
        ),
        connect=lambda event, handler: connections.append((event, handler)),
    )

    result = sphinx_fonts.setup(app)

    assert result == {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def test_setup_config_values() -> None:
    """Verify setup() registers all expected config values."""
    config_values: list[tuple[str, t.Any, str]] = []
    connections: list[tuple[str, t.Any]] = []

    app = types.SimpleNamespace(
        add_config_value=lambda name, default, rebuild: config_values.append(
            (name, default, rebuild)
        ),
        connect=lambda event, handler: connections.append((event, handler)),
    )

    sphinx_fonts.setup(app)

    config_names = [c[0] for c in config_values]
    assert "sphinx_fonts" in config_names
    assert "sphinx_font_fallbacks" in config_names
    assert "sphinx_font_css_variables" in config_names
    assert "sphinx_font_preload" in config_names
    assert all(c[2] == "html" for c in config_values)


def test_setup_event_connections() -> None:
    """Verify setup() connects to builder-inited and html-page-context events."""
    config_values: list[tuple[str, t.Any, str]] = []
    connections: list[tuple[str, t.Any]] = []

    app = types.SimpleNamespace(
        add_config_value=lambda name, default, rebuild: config_values.append(
            (name, default, rebuild)
        ),
        connect=lambda event, handler: connections.append((event, handler)),
    )

    sphinx_fonts.setup(app)

    event_names = [c[0] for c in connections]
    assert "builder-inited" in event_names
    assert "html-page-context" in event_names

    handlers = {c[0]: c[1] for c in connections}
    assert handlers["builder-inited"] is sphinx_fonts._on_builder_inited
    assert handlers["html-page-context"] is sphinx_fonts._on_html_page_context
