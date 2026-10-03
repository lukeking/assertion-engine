"""Validated read-only playback with an explicit headless PNG destination."""

import argparse
import os
import sys
import tempfile
from pathlib import Path

from assertion_engine.artifacts import ArtifactValidationError
from assertion_engine.playback.loader import load_pair
from assertion_engine.playback.matplotlib_view import MatplotlibView
from assertion_engine.playback.view_model import PlaybackSession


def _output_path(value: str, inputs: tuple[Path, Path]) -> Path:
    output = Path(value)
    if not output.parent.is_dir():
        raise ValueError(f"headless output parent must already exist: {output.parent}")
    if output.is_dir():
        raise ValueError(f"headless output must name a file: {output}")
    if output.resolve() in (path.resolve() for path in inputs):
        raise ValueError(f"headless output cannot replace an input artifact: {output}")
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="assertion-playback")
    parser.add_argument("--telemetry", required=True)
    parser.add_argument("--ground-truth", required=True)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--headless-output")
    view = None
    staging = None
    try:
        args = parser.parse_args(argv)
        inputs = (Path(args.telemetry), Path(args.ground_truth))
        try:
            pair = load_pair(*inputs)
            session = PlaybackSession(*pair, speed=args.speed)
            output = (
                _output_path(args.headless_output, inputs)
                if args.headless_output is not None
                else None
            )
        except (ArtifactValidationError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 2
        if output is not None:
            import matplotlib

            matplotlib.use("Agg", force=True)
            while session.state != "completed":
                session.step()
        view = MatplotlibView(session)
        if output is None:
            view.show()
        else:
            # Stage only after all arguments and artifacts pass validation. A failed
            # render leaves an existing PNG intact and removes this invocation's file.
            descriptor, name = tempfile.mkstemp(
                prefix=".assertion-playback-", suffix=".png", dir=output.parent
            )
            staging = Path(name)
            os.close(descriptor)
            view.save(staging)
            os.replace(staging, output)
        return 0
    except SystemExit as error:
        return error.code
    except Exception as error:
        print(f"playback failed: {error}", file=sys.stderr)
        return 1
    finally:
        if staging is not None and staging.exists():
            staging.unlink()
        if view is not None:
            view.close()


if __name__ == "__main__":
    raise SystemExit(main())
