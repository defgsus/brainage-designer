import argparse
import multiprocessing

from bad import logger
from bad.server import Server
from bad.process import ProcessScheduler

# add plugins here
import bad.plugins.essential
import bad.plugins.preprocess
import bad.plugins.analysis


def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument(
        "service", type=str, nargs="?", default="both",
        choices=["server", "scheduler", "both"],
        help="Choose to run the web-server, the process scheduler or both",
    )


def run_server(args):
    server = Server()
    try:
        server.run()
    except KeyboardInterrupt:
        logger.log.info("server stopped")

    server.terminate()


def run_scheduler(args):
    scheduler = ProcessScheduler()
    try:
        scheduler.run()
    except KeyboardInterrupt:
        logger.log.info("scheduler stopped")


def run_both(args):
    proc = multiprocessing.Process(target=run_scheduler, args=(args, ))
    proc.start()

    try:
        server = Server()
        try:
            server.run()
        except KeyboardInterrupt:
            logger.log.info("stopped")

        server.terminate()
    finally:
        if hasattr(proc, "kill"):
            proc.kill()
        else:
            proc.terminate()


def main(args):
    if args.service == "server":
        run_server(args)
    elif args.service == "scheduler":
        run_scheduler(args)
    else:
        run_both(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    main(parser.parse_args())
