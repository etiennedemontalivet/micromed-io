"""
Read data sent by Micromed through TCP.
"""
import logging

import click
from pathlib import Path
from micromed_io.trc import MicromedTRC


@click.command(context_settings=dict(max_content_width=120))
@click.option(
    "--dirpath",
    default="./",
    type=str,
    required=False,
    help="the relative or absolute path containing the TRC files to rename",
    show_default=True,
)
@click.option(
    "--format",
    default="%Y%m%d-%H%M%S",
    type=str,
    required=False,
    help="the datetime format to use - must be compliant with python strftime",
    show_default=True,
)
def run(dirpath: str = "./", format: str = "%Y%m%d-%H%M%S") -> None:
    """Rename the standard TRC files to include the recording date in the filename"""
    logging.basicConfig(
        level=0,
        format=(
            "[%(asctime)s - %(filename)s:%(lineno)d]\t\t%(levelname)s\t\t%(message)s"
        ),
    )
    try:
        for file in Path(dirpath).glob("*.TRC"):
            mmtrc = MicromedTRC(file)
            logging.info(
                f"Renaming to: {file.name}__{mmtrc.get_header().recording_date.strftime(format)}"
            )
            file.rename(
                file.parent
                / f"{file.name}__{mmtrc.get_header().recording_date.strftime(format)}.TRC"
            )

    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    run()
