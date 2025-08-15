import io
from openpyxl import Workbook
from flask import send_file

def export_to_excel(queryset, headers, data_mapper, filename):
    """
    Mengekspor data dari queryset ke file Excel.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    sheet.append(headers)

    for item in queryset:
        sheet.append(data_mapper(item))

    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
