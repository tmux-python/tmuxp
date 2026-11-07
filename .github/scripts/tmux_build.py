"""Build and validate the private tmux installation used by GitHub Actions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import tempfile
import tomllib

_REPOSITORY = "https://github.com/tmux/tmux.git"
with (pathlib.Path(__file__).parents[1] / "tmux-releases.toml").open("rb") as _pins:
    _RELEASES: dict[str, str] = tomllib.load(_pins)["releases"]

_BUILD_ENV = {
    "CC": "cc",
    "CFLAGS": "-O2",
    "CPPFLAGS": "",
    "LDFLAGS": "",
    "MAKEFLAGS": "",
}


class _CleanupError(RuntimeError):
    """The private smoke-test daemon could not be cleaned up."""


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _output(args: list[str]) -> str:
    return subprocess.run(
        args, check=True, capture_output=True, text=True
    ).stdout.strip()


def _identity(version: str) -> dict[str, str]:
    parts = [os.environ.get(name, "") for name in ("ImageOS", "ImageVersion")]
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", part) for part in parts):
        msg = "Missing or invalid runner image identity"
        raise ValueError(msg)
    image = "-".join(parts)
    source = _RELEASES.get(version)
    if source is None:
        source = _output(
            ["git", "ls-remote", _REPOSITORY, "refs/heads/master"]
        ).split()[0]
        if not re.fullmatch(r"[0-9a-f]{40}", source):
            msg = "Could not resolve tmux master to a commit"
            raise ValueError(msg)
    return {
        "version": version,
        "source": source,
        "image": image,
        "arch": platform.machine(),
        "recipe": _sha256(pathlib.Path(__file__)),
        "compiler": _output(["cc", "--version"]),
        "packages": _output(
            [
                "dpkg-query",
                "-W",
                "-f=${Package}=${Version}\n",
                "gcc",
                "libc6",
                "libevent-dev",
                "libncurses-dev",
                "libutempter-dev",
                "bison",
                "autoconf",
                "automake",
                "pkg-config",
            ]
        ),
    }


def _cache_key(identity: dict[str, str]) -> str:
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return f"tmux-v2-{identity['version']}-{digest}"


def _probe(binary: pathlib.Path, version: str) -> None:
    reported = subprocess.run(
        [str(binary), "-V"], check=True, capture_output=True, text=True, timeout=1
    ).stdout.strip()
    if not reported.startswith("tmux ") or (
        version != "master" and reported != f"tmux {version}"
    ):
        msg = f"Expected tmux {version}, got {reported!r}"
        raise ValueError(msg)
    env = {k: v for k, v in os.environ.items() if k not in {"TMUX", "TMUX_PANE"}}
    env.update({"SHELL": "/bin/sh", "TERM": "xterm-256color", "LC_ALL": "C.UTF-8"})
    with tempfile.TemporaryDirectory(prefix="lt-ci-") as temporary:
        socket = pathlib.Path(temporary) / "socket"
        command = [str(binary), "-f", "/dev/null", "-S", str(socket)]
        try:
            subprocess.run(
                [*command, "new-session", "-d", "-s", "probe", "exec cat"],
                check=True,
                capture_output=True,
                env=env,
                timeout=1,
            )
            connected = subprocess.run(
                [*command, "display-message", "-p", "#{version}"],
                check=True,
                capture_output=True,
                text=True,
                env=env,
                timeout=1,
            ).stdout.strip()
            if reported != f"tmux {connected}":
                msg = f"Connected daemon version differs: {connected!r}"
                raise ValueError(msg)
        finally:
            if socket.exists():
                try:
                    subprocess.run(
                        [*command, "kill-server"],
                        check=True,
                        capture_output=True,
                        env=env,
                        timeout=1,
                    )
                except (OSError, subprocess.SubprocessError) as error:
                    msg = "Failed to clean up the private tmux smoke test"
                    raise _CleanupError(msg) from error


def _valid(prefix: pathlib.Path, identity: dict[str, str]) -> bool:
    binary = prefix / "bin" / "tmux"
    try:
        if prefix.is_symlink() or binary.parent.is_symlink() or binary.is_symlink():
            return False
        record = json.loads((prefix / "build.json").read_text())
        if record != {"identity": identity, "sha256": _sha256(binary)}:
            return False
        _probe(binary, identity["version"])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"tmux cache rejected: {error}", flush=True)
        return False
    return True


def _build(prefix: pathlib.Path, identity: dict[str, str]) -> None:
    env = dict(os.environ, **_BUILD_ENV)
    with tempfile.TemporaryDirectory(
        prefix="tmux-source-", dir=prefix.parent
    ) as temporary:
        work = pathlib.Path(temporary)
        version = identity["version"]
        if version == "master":
            source = work / "tmux"
            subprocess.run(["git", "init", str(source)], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(source),
                    "fetch",
                    "--depth=1",
                    _REPOSITORY,
                    identity["source"],
                ],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(source), "checkout", "--detach", "FETCH_HEAD"],
                check=True,
            )
            if (
                _output(["git", "-C", str(source), "rev-parse", "HEAD"])
                != identity["source"]
            ):
                msg = "Fetched tmux commit differs from the cache identity"
                raise ValueError(msg)
            subprocess.run(["sh", "autogen.sh"], check=True, cwd=source, env=env)
        else:
            archive = work / "tmux.tar.gz"
            subprocess.run(
                [
                    "curl",
                    "--fail",
                    "--location",
                    "--retry",
                    "2",
                    "--output",
                    str(archive),
                    f"https://github.com/tmux/tmux/releases/download/{version}/tmux-{version}.tar.gz",
                ],
                check=True,
            )
            if _sha256(archive) != identity["source"]:
                msg = "Downloaded tmux archive does not match its pinned SHA256"
                raise ValueError(msg)
            subprocess.run(
                [
                    "tar",
                    "--extract",
                    "--gzip",
                    "--file",
                    str(archive),
                    "--directory",
                    str(work),
                    "--no-same-owner",
                    "--no-same-permissions",
                ],
                check=True,
            )
            source = work / f"tmux-{version}"
        subprocess.run(
            ["./configure", f"--prefix={prefix}"], check=True, cwd=source, env=env
        )
        jobs = min(4, len(os.sched_getaffinity(0)))
        subprocess.run(["make", f"-j{jobs}"], check=True, cwd=source, env=env)
        subprocess.run(["make", "install"], check=True, cwd=source, env=env)


def _prepare(prefix: pathlib.Path, identity: dict[str, str]) -> bool:
    if _valid(prefix, identity):
        print(f"Validated cached tmux {identity['version']}", flush=True)
        return False
    if prefix.is_symlink():
        prefix.unlink()
    elif prefix.exists():
        shutil.rmtree(prefix)
    _build(prefix, identity)
    binary = prefix / "bin" / "tmux"
    _probe(binary, identity["version"])
    (prefix / "build.json").write_text(
        json.dumps(
            {
                "identity": identity,
                "sha256": _sha256(binary),
            },
            sort_keys=True,
        )
        + "\n"
    )
    return True


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["plan", "prepare"])
    parser.add_argument("version", choices=[*_RELEASES, "master"])
    args = parser.parse_args()
    root = pathlib.Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    prefix = root / f"tmux-{args.version}"
    plan = root / f"tmux-{args.version}.json"
    if args.phase == "plan":
        identity = _identity(args.version)
        plan.write_text(json.dumps(identity, sort_keys=True) + "\n")
        print(json.dumps(identity, indent=2), flush=True)
        with pathlib.Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
            output.write(f"prefix={prefix}\nkey={_cache_key(identity)}\n")
    else:
        identity = json.loads(plan.read_text())
        if identity["version"] != args.version:
            msg = "Build plan version does not match the requested tmux"
            raise ValueError(msg)
        rebuilt = _prepare(prefix, identity)
        if rebuilt and os.environ.get("CACHE_HIT") == "true":
            print(
                "::warning::Invalid exact cache rebuilt locally. Change the build "
                "recipe to invalidate the immutable cache entry on subsequent runs."
            )
        with pathlib.Path(os.environ["GITHUB_PATH"]).open("a") as output:
            output.write(f"{prefix / 'bin'}\n")


if __name__ == "__main__":
    _main()
