from argparse import ArgumentParser, Namespace
from datetime import datetime, time, timedelta

from rich.console import Console
from rich.table import Table

from worktime.db import Database
from worktime.models import WorkTime


def display_time_diff(duration1: timedelta, duration2: timedelta) -> str:
    if duration1 > duration2:
        delta = duration1 - duration2
        symbol = "+"
    else:
        symbol = "-"
        delta = duration2 - duration1
    return f"{symbol}{display_timedelta(delta)}"


def display_timedelta(duration: timedelta) -> str:
    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}:{minutes:02}:{seconds:02}"


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--database",
        type=str,
        help="Database file (default: %(default)s)",
        default="worktime.db",
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    add_parser = subparsers.add_parser("add", help="Add a new worktime entry")
    start_group = add_parser.add_mutually_exclusive_group(required=True)
    start_group.add_argument(
        "--start", type=datetime.fromisoformat, help="Start datetime in ISO format"
    )
    start_group.add_argument(
        "--start-time",
        type=time.fromisoformat,
        help="Start time for the current day in ISO format",
    )

    end_group = add_parser.add_mutually_exclusive_group(required=True)
    end_group.add_argument(
        "--end", type=datetime.fromisoformat, help="End time in ISO format"
    )
    end_group.add_argument(
        "--end-time",
        type=time.fromisoformat,
        help="End time for the current day in ISO format",
    )

    add_parser.add_argument(
        "--pause",
        type=int,
        help="Pause time in minutes (default: %(default)s)",
        default=30,
    )

    show_parser = subparsers.add_parser("show", help="Show all worktime entries")
    show_parser.add_argument(
        "--total-hours", type=int, help="Total hours (default: %(default)s)", default=32
    )
    show_parser.add_argument(
        "--week", type=int, help="Week number (default: current week)", default=None
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "add":
        if args.start:
            start: datetime = args.start
        else:
            start_time: time = args.start_time
            start = datetime.combine(datetime.now().date(), start_time)
        if not start.tzinfo:
            start = start.replace(tzinfo=datetime.now().astimezone().tzinfo)

        if args.end:
            end: datetime = args.end
        else:
            end_time: time = args.end_time
            end = datetime.combine(datetime.now().date(), end_time)
        if not end.tzinfo:
            end = end.replace(tzinfo=datetime.now().astimezone().tzinfo)

        with Database(args.database) as db:
            db.insert_worktime(WorkTime(start, end, timedelta(minutes=args.pause)))
    elif args.command == "show":
        if args.week:
            now = datetime.fromisocalendar(datetime.now().year, args.week, 1)
        else:
            now = datetime.now()

        table = Table(
            title=f"Worktime for week {now.isocalendar().week} {now.year}",
        )
        table.add_column("ID", justify="right")
        table.add_column("Date")
        table.add_column("Pause", justify="right")
        table.add_column("Duration", justify="right")

        start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = (start + timedelta(days=6)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        with Database(args.database) as db:
            total = timedelta(minutes=0)

            for worktime in db.query_worktime(start, end):
                table.add_row(
                    str(worktime.id),
                    str(worktime.start.date()),
                    str(worktime.pause),
                    str(worktime.duration()),
                )
                total = total + worktime.duration()

        table.add_section()
        table.add_row("", "", "Total work hours", f"{args.total_hours}:00:00")
        table.add_row("", "", "Total work time", display_timedelta(total))
        table.add_row(
            "",
            "",
            "Difference",
            display_time_diff(total, timedelta(hours=args.total_hours)),
        )

        console = Console()
        console.print(table)
