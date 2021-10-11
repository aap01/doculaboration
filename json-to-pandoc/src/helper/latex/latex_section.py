#!/usr/bin/env python3

import json
from helper.pandoc.pandoc_util import *
from helper.latex.latex_cell import *
from helper.latex.latex_util import *

#   ----------------------------------------------------------------------------------------------------------------
#   latex section objects wrappers
#   ----------------------------------------------------------------------------------------------------------------

''' Latex section base object
'''
class LatexSectionBase(object):

    ''' constructor
    '''
    def __init__(self, section_data, section_spec):
        self.section_spec = section_spec
        self.section_break = section_data['section-break']
        self.section_width = float(self.section_spec['page_width']) - float(self.section_spec['left_margin']) - float(self.section_spec['right_margin']) - float(self.section_spec['gutter'])

        self.no_heading = section_data['no-heading']
        self.section = section_data['section']
        self.heading = section_data['heading']
        self.level = section_data['level']
        self.page_numbering = section_data['page-number']

        section_contents = section_data.get('contents')

        self.title = None
        self.row_count = 0
        self.column_count = 0

        self.start_row = 0
        self.start_column = 0

        self.cell_matrix = []
        self.row_metadata_list = []
        self.column_metadata_list = []
        self.merge_list = []

        self.default_format = None

        if section_contents:
            self.has_content = True

            properties = section_contents.get('properties')
            self.default_format = CellFormat(properties.get('defaultFormat'))

            sheets = section_contents.get('sheets')
            if isinstance(sheets, list) and len(sheets) > 0:
                sheet_properties = sheets[0].get('properties')
                if sheet_properties:
                    self.title = sheet_properties.get('title')
                    if 'gridProperties' in sheet_properties:
                        self.row_count = max(int(sheet_properties['gridProperties'].get('rowCount', 0)) - 2, 0)
                        self.column_count = max(int(sheet_properties['gridProperties'].get('columnCount', 0)) - 1, 0)

                data_list = sheets[0].get('data')
                if isinstance(data_list, list) and len(data_list) > 0:
                    data = data_list[0]
                    self.start_row = int(data.get('startRow', 0))
                    self.start_column = int(data.get('startColumn', 0))

                    # rowMetadata
                    for row_metadata in data.get('rowMetadata', []):
                        self.row_metadata_list.append(RowMetadata(row_metadata))

                    # columnMetadata
                    for column_metadata in data.get('columnMetadata', []):
                        self.column_metadata_list.append(ColumnMetadata(column_metadata))

                    # merges
                    for merge in sheets[0].get('merges', []):
                        self.merge_list.append(Merge(merge, self.start_row, self.start_column))

                    # column width needs adjustment as \tabcolsep is COLSEPin. This means each column has a COLSEP inch on left and right as space which needs to be removed from column width
                    all_column_widths_in_pixel = sum(x.pixel_size for x in self.column_metadata_list)
                    self.column_widths = [ (x.pixel_size * self.section_width / all_column_widths_in_pixel) - (COLSEP * 2) for x in self.column_metadata_list ]

                    # rowData
                    r = 0
                    for row_data in data.get('rowData', []):
                        self.cell_matrix.append(Row(r, row_data, self.default_format, self.section_width, self.column_widths))
                        r = r + 1

        else:
            self.has_content = False

        # we need a list to hold the tables and block for the cells
        self.content_list = []

        # generate the header block
        header_block = LatexSectionHeader(self.section_spec, self.section_break, self.level, self.no_heading, self.section, self.heading, self.title)
        self.content_list.append(header_block)


    ''' processes the cells to generate the proper order of tables and blocks
    '''
    def process(self):
        pass


    ''' generates the latex code
    '''
    def to_latex(self):
        return ''


''' Latex section object
'''
class LatexSection(LatexSectionBase):

    ''' constructor
    '''
    def __init__(self, section_data, section_spec):
        super().__init__(section_data, section_spec)


    ''' processes the cells to
        1. identify missing cells/contents for merged cells
        2. generate the proper order of tables and blocks
    '''
    def process(self):

        # first we identify the missing cells or blank cells for merged spans
        for merge in self.merge_list:
            first_row = merge.start_row
            first_col = merge.start_col
            last_row = merge.end_row
            last_col = merge.end_col
            row_span = merge.row_span
            col_span = merge.col_span
            first_row_object = self.cell_matrix[first_row]
            first_cell = first_row_object.get_cell(first_col)

            if first_cell is None:
                warn(f"cell [{first_row},{first_col}] starts a span, but it is not there")
                continue

            # get the total width of the first_cell when merged
            for c in range(first_col + 1, last_col):
                first_cell.cell_width = first_cell.cell_width + first_cell.column_widths[c] + COLSEP * 2

            if col_span > 1:
                first_cell.cell_width = first_cell.cell_width + ((col_span -1) * 2 * VBORDER_WIDTH)

            first_cell.merge_spec.col_span = col_span
            first_cell.merge_spec.row_span = row_span

            # we start with row spans first as they are the complex ones
            if row_span > 1:
                # for rowspans, there can be two cases - the rowspan may be single column, or it can be multi column
                first_cell.mark_multirow(MultiSpan.FirstCell)
                if col_span > 1:
                    # for multi column row spans, subsequent cells in the same columns of the FirstCell will be either empty or missing
                    # debug(f"cell [{first_row},{first_col}] starts a span of {row_span} rows and {col_span} columns")
                    first_cell.mark_multicol(MultiSpan.FirstCell)
                    # TODO 2
                    # we may have empty cells in this same row which are part of this column merge, we need to mark their multi_col property correctly
                    for c in range(first_col+1, last_col):
                        # debug(f"..cell [{first_row},{c}] is part of column merge")
                        next_cell_in_row = first_row_object.get_cell(c)

                        if next_cell_in_row is None:
                            # the cell may not be existing at all, we have to create
                            # debug(f"..cell [{first_row},{c}] does not exist, the merge is the last merge for the row")
                            # debug(f"..cell [{first_row},{c}] to be inserted")
                            next_cell_in_row = Cell(first_row, c, {}, first_cell.default_format, first_cell.column_widths)
                            first_row_object.insert_cell(c, next_cell_in_row)

                        if next_cell_in_row.is_empty:
                            if c == last_col-1:
                                # the last cell of the merge to be marked as LastCell
                                # debug(f"..cell [{first_row},{c}] is the LastCell of the column merge")
                                next_cell_in_row.mark_multicol(MultiSpan.LastCell)

                            else:
                                # the inner cells of the merge to be marked as InnerCell
                                # debug(f"..cell [{first_row},{c}] is an InnerCell of the column merge")
                                next_cell_in_row.mark_multicol(MultiSpan.InnerCell)

                        else:
                            warn(f"..cell [{first_row},{c}] is not empty, it must be part of another column merge which is an issue")


                # for row spans, subsequent cells in the same column of the FirstCell will be either empty or missing
                # debug(f"cell [{first_row},{first_col}] starts a single-column span of {row_span} rows")
                # iterate through the next rows
                for r in range(first_row+1, last_row):
                    next_row_object = self.cell_matrix[r]
                    cell_in_next_row = next_row_object.get_cell(first_col)
                    if cell_in_next_row is None:
                        # the cell may not be existing at all, we have to create
                        # debug(f"..cell [{r},{first_col}] does not exist, it is to be created")
                        cell_in_next_row = Cell(r, first_col, {}, first_cell.default_format, first_cell.column_widths)
                        next_row_object.insert_cell(first_col, cell_in_next_row)

                    if cell_in_next_row.is_empty:
                        # cells in subsequent rows should have the same value and format as the first_cell when it is row merge
                        cell_in_next_row.copy_from(first_cell)
                        if r == last_row-1:
                            # the last cell of the merge to be marked as LastCell
                            # debug(f"..cell [{r},{first_col}] is the LastCell of the row merge")
                            cell_in_next_row.mark_multirow(MultiSpan.LastCell)

                        else:
                            # the inner cells of the merge to be marked as InnerCell
                            # debug(f"..cell [{r},{first_col}] is an InnerCell of the row merge")
                            cell_in_next_row.mark_multirow(MultiSpan.InnerCell)

                    else:
                        warn(f"..cell [{r},{first_col}] is not empty, it must be part of another row merge which is an issue")

            elif col_span > 1:
                # for colspans, we may get empty cells in subsequent columns of this row
                first_cell.mark_multicol(MultiSpan.FirstCell)
                # debug(f"cell [{first_row},{first_col}] starts a single-row span of {col_span} columns")

                # we may have empty cells in this same row which are part of this column merge, we need to mark their multi_col property correctly
                for c in range(first_col+1, last_col):
                    # debug(f"..cell [{first_row},{c}] is part of column merge")
                    next_cell_in_row = first_row_object.get_cell(c)

                    if next_cell_in_row is None:
                        # the cell may not be existing at all, we have to create
                        # debug(f"..cell [{first_row},{c}] does not exist, the merge is the last merge for the row")
                        # debug(f"..cell [{first_row},{c}] to be inserted")
                        next_cell_in_row = Cell(first_row, c, {}, first_cell.default_format, first_cell.column_widths)
                        first_row_object.insert_cell(c, next_cell_in_row)

                    if next_cell_in_row.is_empty:
                        if c == last_col-1:
                            # the last cell of the merge to be marked as LastCell
                            # debug(f"..cell [{first_row},{c}] is the LastCell of the column merge")
                            next_cell_in_row.mark_multicol(MultiSpan.LastCell)

                        else:
                            # the inner cells of the merge to be marked as InnerCell
                            # debug(f"..cell [{first_row},{c}] is an InnerCell of the column merge")
                            next_cell_in_row.mark_multicol(MultiSpan.InnerCell)

                    else:
                        warn(f"..cell [{first_row},{c}] is not empty, it must be part of another column merge which is an issue")


    ''' processes the cells to split the cells into tables and blocks nd ordering the tables and blocks properly
    '''
    def split(self):
        # we have a concept of in-cell content and out-of-cell content
        # in-cell contents are treated as part of a table, while out-of-cell contents are treated as independent paragraphs, images etc. (blocks)
        next_table_starts_in_row = 0
        next_table_ends_in_row = 0
        for r in range(0, self.row_count):
            # the first cell of the row tells us whether it is in-cell or out-of-cell
            data_row = self.cell_matrix[r]
            if data_row.is_out_of_table():
                # there may be a pending/running table
                if r > next_table_starts_in_row:
                    table = LatexTable(self.cell_matrix, next_table_starts_in_row, r - 1, self.column_widths)
                    self.content_list.append(table)

                block = LatexParagraph(data_row, r)
                self.content_list.append(block)

                next_table_starts_in_row = r + 1

            # the row may start with a note of repeat-rows which means that a new table is atarting
            elif data_row.is_table_start():
                # there may be a pending/running table
                if r > next_table_starts_in_row:
                    table = LatexTable(self.cell_matrix, next_table_starts_in_row, r - 1, self.column_widths)
                    self.content_list.append(table)

                    next_table_starts_in_row = r

            else:
                next_table_ends_in_row = r

        # there may be a pending/running table
        if next_table_ends_in_row >= next_table_starts_in_row:
            table = LatexTable(self.cell_matrix, next_table_starts_in_row, next_table_ends_in_row, self.column_widths)
            self.content_list.append(table)


    ''' generates the latex code
    '''
    def to_latex(self):
        # process and split
        self.process()
        self.split()

        latex_lines = []

        # iterate to through tables and blocks contents
        for block in self.content_list:
            latex_lines = latex_lines + block.to_latex()

        return latex_lines


''' Latex section object
'''
class LatexToCSection(LatexSectionBase):

    ''' constructor
    '''
    def __init__(self, section_data, section_spec):
        super().__init__(section_data, section_spec)


    ''' processes the cells to generate the proper order of tables and blocks
    '''
    def process(self):
        pass

    ''' generates the latex code
    '''
    def to_latex(self):
        # process first
        self.process()

        latex_lines = []

        # iterate to through tables and blocks contents
        for block in self.content_list:
            latex_lines = latex_lines + block.to_latex()

        return latex_lines


''' Latex Block object wrapper base class (plain latex, table, header etc.)
'''
class LatexBlock(object):

    ''' generates latex code
    '''
    def to_latex(self):
        pass


''' Latex Header Block wrapper
'''
class LatexSectionHeader(LatexBlock):

    ''' constructor
    '''
    def __init__(self, section_spec, section_break, level, no_heading, section, heading, title):
        self.section_spec, self.section_break, self.level, self.no_heading, self.section, self.heading, self.title = section_spec, section_break, level, no_heading, section, heading, title

    ''' generates latex code
    '''
    def to_latex(self):
        header_lines = []
        header_lines.append('')
        header_lines.append(begin_latex())
        header_lines.append(f"% LatexSection: {self.title}")

        if self.section_break.startswith('newpage_'):
            header_lines.append(f"\\newpage")

        header_lines.append(f"\pdfpagewidth {self.section_spec['page_width']}in")
        header_lines.append(f"\pdfpageheight {self.section_spec['page_height']}in")
        header_lines.append(f"\\newgeometry{{top={self.section_spec['top_margin']}in, bottom={self.section_spec['bottom_margin']}in, left={self.section_spec['left_margin']}in, right={self.section_spec['right_margin']}in}}")

        header_lines.append(end_latex())

        # heading
        if not self.no_heading:
            if self.section != '':
                heading_text = f"{'#' * self.level} {self.section} - {self.heading}".strip()
            else:
                heading_text = f"{'#' * self.level} {self.heading}".strip()

            # headings are styles based on level
            if self.level != 0:
                header_lines.append(heading_text)
                header_lines.append('\n')
            else:
                header_lines.append(begin_latex())
                header_lines.append(f"\\titlestyle{{{heading_text}}}")
                header_lines.append(end_latex())

        return header_lines


''' Latex Table object wrapper
'''
class LatexTable(LatexBlock):

    ''' constructor
    '''
    def __init__(self, cell_matrix, start_row, end_row, column_widths):
        self.start_row, self.end_row, self.column_widths = start_row, end_row, column_widths
        self.table_cell_matrix = cell_matrix[start_row:end_row+1]
        self.row_count = len(self.table_cell_matrix)
        self.table_name = f"LatexTable: {self.start_row}-{self.end_row}[{self.row_count}]"

        # header row if any
        self.header_row_count = self.table_cell_matrix[0].get_cell(0).note.header_rows


    ''' generates the latex code
    '''
    def to_latex(self):
        table_col_spec = '|'.join([f"p{{{i}in}}" for i in self.column_widths])
        table_lines = []

        table_lines.append(begin_latex())
        table_lines.append(f"% LatexTable: ({self.start_row}-{self.end_row}) : {self.row_count} rows")
        table_lines.append(f"\\setlength\\parindent{{0pt}}")
        table_lines.append(f"\\begin{{longtable}}[l]{{|{table_col_spec}|}}\n")

        # generate the table
        r = 1
        for row in self.table_cell_matrix:
            table_lines = table_lines + row.to_latex()

            # header row
            if self.header_row_count == r:
                table_lines.append(f"\\endhead\n")

            r = r + 1

        table_lines.append(f"\\end{{longtable}}")
        table_lines.append(end_latex())
        return table_lines


''' Latex Block object wrapper
'''
class LatexParagraph(LatexBlock):

    ''' constructor
    '''
    def __init__(self, data_row, row_number):
        self.data_row = data_row
        self.row_number = row_number

    ''' generates the latex code
    '''
    def to_latex(self):
        block_lines = []
        block_lines.append(begin_latex())
        block_lines.append(f"% LatexParagraph: row {self.row_number}")

        # TODO 3: generate the block
        if len(self.data_row.cells) > 0:
            row_text = self.data_row.get_cell(0).content_latex()
            block_lines.append(row_text)

        block_lines.append(end_latex())
        return block_lines
