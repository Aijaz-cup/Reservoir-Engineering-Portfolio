"""Structural and metadata audit of Volve 15/9-F-14 FPWD pressure tests.

The workflow reads the 14 time-indexed Schlumberger StethoScope 675 LAS
files, verifies their sampling structure and pressure-channel availability,
and extracts source-reported test metadata for subsequent independent
pressure-transient interpretation.
"""

from pathlib import Path
import re

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "15_9-F-14"
)

REPORT_DIR = PROJECT_DIR / "report"

NULL_DEFAULT = -999.25

PSI_TO_BAR = 0.0689475729

# The Schlumberger report BAR formation-pressure value is reproduced from
# the LAS pPFOR value by adding one standard atmosphere after psi-to-bar
# conversion. The source LAS does not explicitly label pPFOR as psig, so
# the two pressure references are retained explicitly.
STANDARD_ATMOSPHERE_BAR = 1.01325


def numeric_value(text):
    """Return the first numeric value contained in text."""

    if text is None:
        return np.nan

    match = re.search(
        r"[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?",
        str(text),
    )

    if match is None:
        return np.nan

    return float(
        match.group(0)
    )


def header_value(lines, mnemonic):
    """Return a LAS header value for a mnemonic."""

    pattern = re.compile(
        r"^\s*"
        + re.escape(mnemonic)
        + r"\.\s*([^:]+)",
        re.IGNORECASE,
    )

    for line in lines:
        match = pattern.match(line)

        if match:
            return match.group(1).strip()

    return None


def phase_definition(lines):
    """Read channel names, units, and descriptions."""

    start = None

    for index, line in enumerate(lines):
        if line.strip().lower().startswith(
            "~phase_definition_rmdata"
        ):
            start = index + 1
            break

    if start is None:
        raise ValueError(
            "Phase definition was not found."
        )

    channels = []

    pattern = re.compile(
        r"^\s*([^. \t]+)\.([^:]*)\s*:\s*(.*)$"
    )

    for line in lines[start:]:

        if line.startswith("~"):
            break

        match = pattern.match(line)

        if match is None:
            continue

        channels.append(
            {
                "Mnemonic": match.group(1).strip(),
                "Unit": match.group(2).strip(),
                "Description": match.group(3).strip(),
            }
        )

    return channels


def phase_data(
    lines,
    channels,
    null_value,
):
    """Read the time-indexed numerical LAS data block."""

    start = None

    for index, line in enumerate(lines):
        if line.strip().lower().startswith(
            "~phase_data_rmdata"
        ):
            start = index + 1
            break

    if start is None:
        raise ValueError(
            "Phase data section was not found."
        )

    names = [
        channel["Mnemonic"]
        for channel in channels
    ]

    records = []

    for line in lines[start:]:

        if line.startswith("~"):
            break

        if not line.strip():
            continue

        values = [
            value.strip()
            for value in line.split(",")
        ]

        if len(values) != len(names):
            continue

        row = []

        for value in values:

            try:
                number = float(value)
            except ValueError:
                number = np.nan

            if (
                np.isfinite(number)
                and abs(number - null_value)
                < 1.0e-9
            ):
                number = np.nan

            row.append(number)

        records.append(row)

    return pd.DataFrame(
        records,
        columns=names,
    )


def interpretation_blocks(
    lines,
    null_value,
):
    """Read source Polaris interpretation blocks."""

    block_header = re.compile(
        r"^~PolarisInterpretation_Parameters"
        r"\[(\d+)\]",
        re.IGNORECASE,
    )

    parameter_pattern = re.compile(
        r"^\s*(p[A-Za-z0-9_]+)"
        r"\s*\.([^:]*)\s*:\s*(.*)$"
    )

    blocks = []
    current = None

    for line in lines:

        header_match = block_header.match(
            line.strip()
        )

        if header_match:

            if current is not None:
                blocks.append(current)

            current = {
                "Block": int(
                    header_match.group(1)
                )
            }

            continue

        if (
            current is not None
            and line.startswith("~")
        ):
            blocks.append(current)
            current = None
            continue

        if current is None:
            continue

        parameter_match = (
            parameter_pattern.match(line)
        )

        if parameter_match is None:
            continue

        mnemonic = parameter_match.group(1)

        left_side = (
            parameter_match.group(2)
            .strip()
        )

        numbers = re.findall(
            r"[-+]?\d+(?:\.\d+)?"
            r"(?:[Ee][-+]?\d+)?",
            left_side,
        )

        if not numbers:
            continue

        value = float(
            numbers[-1]
        )

        if abs(
            value - null_value
        ) < 1.0e-9:
            value = np.nan

        current[mnemonic] = value

    if current is not None:
        blocks.append(current)

    return blocks


def test_number(path):
    """Extract test number from filename."""

    match = re.search(
        r"_(\d+)\.LAS$",
        path.name,
        re.IGNORECASE,
    )

    if match is None:
        raise ValueError(
            "Unable to determine test number: {}".format(
                path.name
            )
        )

    return int(
        match.group(1)
    )


def parse_test(path):
    """Audit one FPWD pressure-test LAS file."""

    text = path.read_text(
        encoding="latin-1",
        errors="replace",
    )

    lines = text.splitlines()

    null_value = numeric_value(
        header_value(
            lines,
            "NULL",
        )
    )

    if not np.isfinite(
        null_value
    ):
        null_value = NULL_DEFAULT

    channels = phase_definition(
        lines
    )

    data = phase_data(
        lines,
        channels,
        null_value,
    )

    blocks = interpretation_blocks(
        lines,
        null_value,
    )

    final_block = (
        blocks[-1]
        if blocks
        else {}
    )

    if "TIME" not in data.columns:
        raise ValueError(
            "TIME channel missing from {}".format(
                path.name
            )
        )

    if "AQAP" not in data.columns:
        raise ValueError(
            "AQAP pressure channel missing from {}".format(
                path.name
            )
        )

    time = (
        data["TIME"]
        .dropna()
        .to_numpy(dtype=float)
    )

    time_differences = np.diff(
        time
    )

    drawdown_start = final_block.get(
        "pDDS",
        np.nan,
    )

    buildup_start = final_block.get(
        "pBUS",
        np.nan,
    )

    buildup_end = final_block.get(
        "pBUE",
        np.nan,
    )

    test_window = data

    if (
        np.isfinite(drawdown_start)
        and np.isfinite(buildup_end)
    ):
        test_window = data.loc[
            (
                data["TIME"]
                >= drawdown_start
            )
            & (
                data["TIME"]
                <= buildup_end
            )
        ].copy()

    aqap_window = (
        test_window["AQAP"]
        .dropna()
    )

    source_pressure_psi = (
        final_block.get(
            "pPFOR",
            np.nan,
        )
    )

    source_pressure_bar_converted = (
        source_pressure_psi
        * PSI_TO_BAR
        if np.isfinite(
            source_pressure_psi
        )
        else np.nan
    )

    source_pressure_bar_report_reference = (
        source_pressure_bar_converted
        + STANDARD_ATMOSPHERE_BAR
        if np.isfinite(
            source_pressure_bar_converted
        )
        else np.nan
    )

    minimum_test_pressure = (
        float(
            aqap_window.min()
        )
        if not aqap_window.empty
        else np.nan
    )

    pressure_span = (
        source_pressure_bar_report_reference
        - minimum_test_pressure
        if (
            np.isfinite(
                source_pressure_bar_report_reference
            )
            and np.isfinite(
                minimum_test_pressure
            )
        )
        else np.nan
    )

    return {
        "Test": test_number(path),
        "File": path.name,
        "Well": header_value(
            lines,
            "WELL",
        ),
        "Run": numeric_value(
            header_value(
                lines,
                "RUN",
            )
        ),
        "MD m": numeric_value(
            header_value(
                lines,
                "MD",
            )
        ),
        "TVD m": numeric_value(
            header_value(
                lines,
                "TVD",
            )
        ),
        "Header Step s": numeric_value(
            header_value(
                lines,
                "STEP",
            )
        ),
        "Samples": int(
            len(data)
        ),
        "Time Start s": (
            float(time[0])
            if len(time)
            else np.nan
        ),
        "Time End s": (
            float(time[-1])
            if len(time)
            else np.nan
        ),
        "Median dt s": (
            float(
                np.median(
                    time_differences
                )
            )
            if len(
                time_differences
            )
            else np.nan
        ),
        "Monotonic Time": (
            bool(
                np.all(
                    time_differences > 0
                )
            )
            if len(
                time_differences
            )
            else False
        ),
        "Channels": int(
            len(channels)
        ),
        "AQAP Valid Fraction": float(
            data["AQAP"]
            .notna()
            .mean()
        ),
        "Interpretation Blocks": int(
            len(blocks)
        ),
        "Drawdown Start s": (
            drawdown_start
        ),
        "Buildup Start s": (
            buildup_start
        ),
        "Buildup End s": (
            buildup_end
        ),
        "Buildup Duration s": (
            buildup_end
            - buildup_start
            if (
                np.isfinite(
                    buildup_start
                )
                and np.isfinite(
                    buildup_end
                )
            )
            else np.nan
        ),
        "Drawdown Volume cc": (
            final_block.get(
                "pDDV",
                np.nan,
            )
        ),
        "Source Mobility mD/cP": (
            final_block.get(
                "pDDM",
                np.nan,
            )
        ),
        "Source Formation Pressure psi": (
            source_pressure_psi
        ),
        "Source Formation Pressure bar converted": (
            source_pressure_bar_converted
        ),
        "Source Formation Pressure bar": (
            source_pressure_bar_report_reference
        ),
        "Source Last Buildup Pressure psi": (
            final_block.get(
                "pPLRB",
                np.nan,
            )
        ),
        "Source Viscosity cP": (
            final_block.get(
                "pVIS",
                np.nan,
            )
        ),
        "Source Porosity %": (
            final_block.get(
                "pPORO",
                np.nan,
            )
        ),
        "Source 60s Slope": (
            final_block.get(
                "pQ60s",
                np.nan,
            )
        ),
        "AQAP Window Min bar": (
            minimum_test_pressure
        ),
        "AQAP Window Max bar": (
            float(
                aqap_window.max()
            )
            if not aqap_window.empty
            else np.nan
        ),
        "Pressure Drawdown Span bar": (
            pressure_span
        ),
    }


def main():
    """Execute the 14-test FPWD data audit."""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = list(
        RAW_DIR.glob(
            "FM_PRESS_RAW_RUN5_MWD_*.LAS"
        )
    )

    files = sorted(
        files,
        key=test_number,
    )

    if len(files) != 14:
        raise ValueError(
            "Expected 14 F-14 LAS tests; found {}.".format(
                len(files)
            )
        )

    records = [
        parse_test(path)
        for path in files
    ]

    audit = pd.DataFrame(
        records
    )

    audit_path = (
        REPORT_DIR
        / "f14_fpwd_data_audit.csv"
    )

    audit.to_csv(
        audit_path,
        index=False,
    )

    first_text = files[0].read_text(
        encoding="latin-1",
        errors="replace",
    )

    first_lines = (
        first_text.splitlines()
    )

    channel_table = pd.DataFrame(
        phase_definition(
            first_lines
        )
    )

    channel_path = (
        REPORT_DIR
        / "f14_fpwd_channel_inventory.csv"
    )

    channel_table.to_csv(
        channel_path,
        index=False,
    )

    structural_ok = (
        len(audit) == 14
        and audit[
            "Monotonic Time"
        ].all()
        and np.allclose(
            audit["Median dt s"],
            0.0625,
            atol=1.0e-9,
        )
        and (
            audit["Channels"]
            == 58
        ).all()
        and (
            audit[
                "Interpretation Blocks"
            ]
            >= 1
        ).all()
        and audit[
            "Source Formation Pressure psi"
        ].notna().all()
    )

    display_columns = [
        "Test",
        "MD m",
        "TVD m",
        "Samples",
        "Time End s",
        "Median dt s",
        "Buildup Duration s",
        "Source Formation Pressure bar",
        "Source Mobility mD/cP",
        "Pressure Drawdown Span bar",
    ]

    print()
    print(
        "15/9-F-14 FPWD DATA AUDIT"
    )
    print()

    print(
        audit[
            display_columns
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "Tests                 : {}".format(
            len(audit)
        )
    )

    print(
        "Pressure channels     : {}".format(
            int(
                audit[
                    "Channels"
                ].iloc[0]
            )
        )
    )

    print(
        "Nominal sample step   : {:.4f} s".format(
            float(
                audit[
                    "Median dt s"
                ].median()
            )
        )
    )

    print(
        "TVD range             : {:.2f} - {:.2f} m".format(
            audit["TVD m"].min(),
            audit["TVD m"].max(),
        )
    )

    print(
        "Source pressure range : {:.2f} - {:.2f} bar".format(
            audit[
                "Source Formation Pressure bar"
            ].min(),
            audit[
                "Source Formation Pressure bar"
            ].max(),
        )
    )

    print()
    print(
        "Structural QC         : {}".format(
            "PASS"
            if structural_ok
            else "REVIEW REQUIRED"
        )
    )

    print()
    print(
        "Outputs:"
    )

    print(
        "  {}".format(
            audit_path
        )
    )

    print(
        "  {}".format(
            channel_path
        )
    )


if __name__ == "__main__":
    main()
