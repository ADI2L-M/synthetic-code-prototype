from dataclasses import dataclass
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET


_XLSX_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_XLSX_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


@dataclass(frozen=True)
class AuthenticSubmission:
    submission_id: str
    lab: int
    question: int
    task_id: str
    source_code: str
    reference_code: str | None
    source_row: int


def _worksheet_path(target: str) -> str:
    target = target.lstrip("/")
    return target if target.startswith("xl/") else f"xl/{target}"


def _column_name(cell_reference: str) -> str:
    return "".join(character for character in cell_reference if character.isalpha())


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    filename = "xl/sharedStrings.xml"
    if filename not in archive.namelist():
        return []
    root = ET.fromstring(archive.read(filename))
    return [
        "".join(text.text or "" for text in item.iter(f"{{{_XLSX_MAIN}}}t"))
        for item in root.findall(f"{{{_XLSX_MAIN}}}si")
    ]


def _cell_values(row: ET.Element, shared: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for cell in row.findall(f"{{{_XLSX_MAIN}}}c"):
        value = cell.find(f"{{{_XLSX_MAIN}}}v")
        text = "" if value is None else value.text or ""
        if cell.attrib.get("t") == "s" and text:
            text = shared[int(text)]
        values[_column_name(cell.attrib.get("r", ""))] = text
    return values


def _sheet_targets(archive: zipfile.ZipFile) -> dict[str, str]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        item.attrib["Id"]: item.attrib["Target"]
        for item in relationships
    }
    return {
        sheet.attrib["name"]: _worksheet_path(
            targets[
                sheet.attrib[
                    f"{{{_XLSX_REL}}}id"
                ]
            ]
        )
        for sheet in workbook.findall(
            f"{{{_XLSX_MAIN}}}sheets/{{{_XLSX_MAIN}}}sheet"
        )
    }


def task_id_for(
    lab: int,
    question: int,
    grouping_path: Path,
) -> str | None:
    label = f"Lab {lab} Q{question}"
    grouping = json.loads(grouping_path.read_text(encoding="utf-8"))
    for task_id, definition in grouping.items():
        if label in definition.get("direct", []) or label in definition.get(
            "supporting", []
        ):
            return task_id.removesuffix("_conditional_logic").removesuffix(
                "_list_processing"
            ).removesuffix("_numeric_iteration")
    return None


def load_task_submissions(
    workbook_path: Path,
    grouping_path: Path,
    lab: int,
    question: int,
) -> list[AuthenticSubmission]:
    task_id = task_id_for(lab, question, grouping_path)
    if task_id is None:
        raise ValueError(f"No task mapping for Lab {lab} Q{question}")

    sheet_name = f"Lab {lab}"
    response_header = f"Response {question}"
    reference_header = f"Right answer {question}"
    with zipfile.ZipFile(workbook_path) as archive:
        targets = _sheet_targets(archive)
        if sheet_name not in targets:
            raise ValueError(f"Workbook does not contain {sheet_name}")
        root = ET.fromstring(archive.read(targets[sheet_name]))
        rows = root.findall(
            f".//{{{_XLSX_MAIN}}}sheetData/{{{_XLSX_MAIN}}}row"
        )
        if not rows:
            return []
        shared = _shared_strings(archive)
        header_values = _cell_values(rows[0], shared)
        columns_by_header = {
            value: column for column, value in header_values.items()
        }
        response_column = columns_by_header.get(response_header)
        reference_column = columns_by_header.get(reference_header)
        if response_column is None:
            raise ValueError(f"Missing column: {response_header}")

        submissions: list[AuthenticSubmission] = []
        for row in rows[1:]:
            values = _cell_values(row, shared)
            source_code = values.get(response_column, "")
            if not source_code.strip():
                continue
            reference_code = (
                values.get(reference_column, "") if reference_column else ""
            )
            row_number = int(row.attrib.get("r", "0"))
            submissions.append(
                AuthenticSubmission(
                    submission_id=f"Lab_{lab}_Q{question}_R{row_number}",
                    lab=lab,
                    question=question,
                    task_id=task_id,
                    source_code=source_code,
                    reference_code=reference_code or None,
                    source_row=row_number,
                )
            )
        return submissions
