from dash.dash_table import DataTable

from presentation.theme import TABLE_CELL_STYLE, TABLE_CSS, TABLE_DATA_STYLE_CONDITIONAL, TABLE_HEADER_STYLE, TABLE_STYLE


def standard_table(*, columns, data, table_id=None, page_size=10, style_cell_conditional=None):
    kwargs = {}
    if table_id is not None:
        kwargs["id"] = table_id
    if style_cell_conditional is not None:
        kwargs["style_cell_conditional"] = style_cell_conditional
    return DataTable(
        columns=columns,
        data=data,
        page_size=page_size,
        css=TABLE_CSS,
        style_table=TABLE_STYLE,
        style_cell=TABLE_CELL_STYLE,
        style_header=TABLE_HEADER_STYLE,
        style_data_conditional=TABLE_DATA_STYLE_CONDITIONAL,
        **kwargs,
    )

