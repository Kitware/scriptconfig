"""
Proof of concept that opaque submodals are possible, although we do have to
write some custom plubming.
"""
import argparse
import sys


def opaque_main():
    # Pretend this is in a different package you don't control
    parser = argparse.ArgumentParser(prog="opaque-tool")
    parser.add_argument("-n", "--name", required=True, help="Your name")
    parser.add_argument("--loud", action="store_true", help="Shout it!")
    sub = parser.add_subparsers(dest="cmd", required=False)

    # It might even define its own subcommands
    p_greet = sub.add_parser("greet", help="Say hello")
    p_greet.add_argument("--times", type=int, default=1)

    args = parser.parse_args()

    # External CLIs often do this:
    if args.name == "fail":
        sys.exit(2)

    msg = f"hello, {args.name}"
    if args.loud:
        msg = msg.upper()

    if args.cmd == "greet":
        for _ in range(args.times):
            print(msg)
    else:
        print(msg)


def call_external_main(callable_main, prog: str, forwarded_args: list[str]) -> int:
    """
    Run an imported main() as if it were launched standalone.

    - Sets sys.argv to [prog] + forwarded_args so argparse in the external main()
      sees exactly what it expects.
    - Catches SystemExit to return a proper exit code instead of killing our process.
    """
    old_argv = sys.argv[:]
    try:
        sys.argv = [prog] + forwarded_args
        try:
            callable_main()
            return 0
        except SystemExit as e:
            if e.code is None:
                return 0
            if isinstance(e.code, int):
                return e.code
            return 1
    finally:
        sys.argv = old_argv


def cmd_sum(numbers: list[int], start: int) -> int:
    total = start + sum(numbers)
    print(total)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extern_argparse",
        description="My modular CLI (opaque pass-through + native commands)",
        allow_abbrev=False,  # don't let argparse abbreviate flags meant for opaque
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Native, strict subcommand
    p_sum = sub.add_parser("sum", help="Sum integers")
    p_sum.add_argument("numbers", nargs="+", type=int, help="Integers to sum")
    p_sum.add_argument("--start", type=int, default=0, help="Initial value")

    # Opaque pass-through selector (no args defined here)
    sub.add_parser(
        "opaque",
        add_help=False,  # let '-h/--help' after 'opaque' reach the opaque tool
        help="Forward all following args to the opaque external CLI",
        description="Runs the external CLI in-process; no -- needed.",
    )

    return parser


def main():
    parser = build_parser()

    # Parse just enough to know which subcommand was chosen; keep the rest untouched.
    args, unknown = parser.parse_known_args()

    if args.cmd == "opaque":
        # Forward *everything* after 'opaque' verbatim (including options like -n)
        # Optional nicety: drop a leading '--' if the user included it
        forwarded = unknown[1:] if unknown[:1] == ["--"] else unknown
        rc = call_external_main(opaque_main, "opaque-tool", forwarded)
        sys.exit(rc)

    # For non-opaque subcommands, enforce strict parsing: unknown -> error
    if unknown:
        parser.error(f"unrecognized arguments: {' '.join(unknown)}")

    # Handle strict subcommands normally
    if args.cmd == "sum":
        rc = cmd_sum(args.numbers, args.start)
        sys.exit(rc)


if __name__ == "__main__":
    """
    # Use your native command: strict parsing (unknown flags cause errors)
    python extern_argparse.py sum 1 2 3 --start 10
    16

    # Unknown flag for 'sum' -> argparse error (as desired)
    python extern_argparse.py sum 1 2 --bogus

    usage: extern_argparse sum [-h] [--start START] numbers [numbers ...]
    extern_argparse sum: error: unrecognized arguments: --bogus

    # Opaque pass-through: everything after 'opaque' goes to the external CLI
    python extern_argparse.py opaque -n Alice

    hello, Alice

    python extern_argparse.py opaque -n Bob greet --times 2

    hello, Bob
    hello, Bob

    # Exit code propagation still works
    python extern_argparse.py opaque -n fail || echo "exit=$?"
    exit=2

    """
    main()
