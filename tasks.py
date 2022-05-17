import os
import sys
import shutil
import logging
from pathlib import Path
from invoke import task

logger = logging
logger_kwargs = {
    "level": logging.INFO,
    "format": "%(asctime)s %(levelname)s - %(message)s",
    "force": True,
}
logger.basicConfig(**logger_kwargs)


def _get_ctx_abs_path(ctx, *path) -> str:
    return os.path.join(os.path.abspath(ctx.cwd), *path)


@task
def clean(ctx):
    shutil.rmtree(
        _get_ctx_abs_path(ctx, "htmlcov"),
        ignore_errors=True,
    )
    shutil.rmtree(
        _get_ctx_abs_path(ctx, ".pytest_cache"),
        ignore_errors=True,
    )
    shutil.rmtree(_get_ctx_abs_path(ctx, ".tox"), ignore_errors=True)
    Path(_get_ctx_abs_path(ctx, ".coverage")).unlink(missing_ok=True)
    shutil.rmtree(_get_ctx_abs_path(ctx, "tests", "__out__"), ignore_errors=True)
    shutil.rmtree(_get_ctx_abs_path(ctx, "build"), ignore_errors=True)
    shutil.rmtree(_get_ctx_abs_path(ctx, "dist"), ignore_errors=True)
    shutil.rmtree(
        _get_ctx_abs_path(ctx, f"py_ios_device.egg-info"),
        ignore_errors=True,
    )


@task(clean)
def build(ctx, skip_uninstall=False):
    ctx.run(f"{sys.executable} setup.py bdist_wheel", hide="out")
    dist = _get_ctx_abs_path(ctx, "dist")
    wheel_file = os.path.join(dist, os.listdir(dist)[0])
    assert wheel_file.endswith(".whl")
    ctx.run(f"pip3 install {wheel_file}", hide="out")
    if not skip_uninstall:
        uninstall(ctx)


@task(clean)
def install(ctx):
    build(ctx, skip_uninstall=True)
    clean(ctx)


@task
def uninstall(ctx):
    ctx.run(f"pip3 uninstall py-ios-device -y", hide="out")


@task
def style_check(ctx):
    ctx.run("black . --check --diff")


@task
def reformat_code(ctx):
    ctx.run("black .")


@task
def test(ctx):
    ctx.run("tox")
    print(
        f"Coverage html report: "
        f'file://{os.path.join(os.path.dirname(__file__), "htmlcov", "index.html")}'
    )


@task(build)
def publish(ctx):
    ctx.run(f"{sys.executable} -m twine upload dist/*")
