import re
from collections import defaultdict
from datetime import date, datetime
from openpyxl import load_workbook


def read_tables(path):
    """Accept V23 stacked All_In_One tables or separate named worksheets.

    Never execute formulas/macros or interpret cell content as instructions.
    Every original column and physical row coordinate is preserved.
    """
    tables = defaultdict(list)
    inventory = []
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        for sheet in wb:
            table, headers, expected, count, type_counts = sheet.title, None, None, 0, defaultdict(lambda: defaultdict(int))
            for row_number, values in enumerate(sheet.values, 1):
                values = [v.isoformat() if isinstance(v, (date, datetime)) else v for v in values]
                populated = [v for v in values if v is not None]
                if not populated:
                    continue
                marker = re.search(r'[｜|]([A-Za-z][A-Za-z0-9_]+)[｜|]\s*(\d+)\s*行', str(values[0]))
                if marker and len(populated) == 1:
                    if headers is not None:
                        inventory.append(dict(sheet=sheet.title, table=table, rows=count, declared_rows=expected,
                            columns=[h for h in headers if h], observed_dtypes={k:dict(v) for k,v in type_counts.items()}))
                    table, expected, headers, count, type_counts = marker[1], int(marker[2]), None, 0, defaultdict(lambda: defaultdict(int))
                    continue
                if headers is None:
                    # Ignore the workbook title above the first table.
                    if len(populated) == 1:
                        continue
                    headers = [str(v) if v is not None else None for v in values]
                    names = [v for v in headers if v]
                    if len(names) != len(set(names)):
                        raise ValueError(f'Duplicate column names: {sheet.title}:{row_number}')
                    continue
                record = {k: values[i] if i < len(values) else None for i, k in enumerate(headers) if k}
                for key, value in record.items():
                    if value is None:
                        kind = 'null'
                    elif isinstance(value, bool):
                        kind = 'boolean'
                    elif isinstance(value, int):
                        kind = 'integer'
                    elif isinstance(value, float):
                        kind = 'number'
                    elif isinstance(value, str):
                        try:
                            float(value)
                            kind = 'numeric_string'
                        except ValueError:
                            kind = 'string'
                    else:
                        kind = type(value).__name__
                    type_counts[key][kind] += 1
                record['_source'] = dict(source_sheet=sheet.title, source_table=table, source_row=row_number)
                tables[table].append(record)
                count += 1
            if headers is not None:
                inventory.append(dict(sheet=sheet.title, table=table, rows=count, declared_rows=expected,
                    columns=[h for h in headers if h], observed_dtypes={k:dict(v) for k,v in type_counts.items()}))
    finally:
        wb.close()
    for item in inventory:
        if item['declared_rows'] is not None and item['rows'] != item['declared_rows']:
            raise ValueError(f'Table row-count mismatch: {item}')
    return dict(tables), inventory
