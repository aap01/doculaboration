#!/usr/bin/env python3

import json
from helper.pandoc.pandoc_util import *
from helper.latex.latex_util import *

#   ----------------------------------------------------------------------------------------------------------------
#   gsheet cell wrappers
#   ----------------------------------------------------------------------------------------------------------------

''' gsheet Cell object wrapper
'''
class Cell(object):

    ''' constructor
    '''
    def __init__(self, row_num, col_num, value, default_format, column_widths):
        self.row_num, self.col_num, self.column_widths, self.default_format = row_num, col_num, column_widths, default_format
        self.value = value
        self.text_format_runs = []
        self.cell_width = self.column_widths[self.col_num]
        self.merge_spec = CellMergeSpec()

        if self.value:
            self.formatted_value = value.get('formattedValue')
            self.user_entered_value = CellValue(value.get('userEnteredValue'), self.formatted_value)
            self.effective_value = CellValue(value.get('effectiveValue'))
            self.user_entered_format = CellFormat(value.get('userEnteredFormat'))
            self.effective_format = CellFormat(value.get('effectiveFormat'), self.default_format)
            for text_format_run in value.get('textFormatRuns', []):
                self.text_format_runs.append(TextFormatRun(text_format_run, self.effective_format.text_format.source))

            self.note = CellNote(value.get('note'))
            self.is_empty = False
            self.is_top_border, self.is_bottom_border = True, True

        else:
            # value can have a special case it can be an empty ditionary when the cell is an inner cell of a column merge
            self.merge_spec.multi_col = MultiSpan.No
            self.user_entered_value = None
            self.effective_value = None
            self.formatted_value = None
            self.user_entered_format = None
            self.effective_format = None
            self.note = CellNote()
            self.is_empty = True
            self.is_top_border, self.is_bottom_border = False, False


    ''' mark the cell multi_col
    '''
    def mark_multicol(self, span):
        self.merge_spec.multi_col = span


    ''' mark the cell multi_col
    '''
    def mark_multirow(self, span):
        self.merge_spec.multi_row = span
        if span == MultiSpan.FirstCell:
            self.is_top_border = True
            self.is_bottom_border = False
        elif span == MultiSpan.InnerCell:
            self.is_top_border = False
            self.is_bottom_border = False
        elif span == MultiSpan.LastCell:
            self.is_top_border = False
            self.is_bottom_border = True
        elif span == MultiSpan.No:
            self.is_top_border = True
            self.is_bottom_border = True


    ''' Copy value, format, from the cell passed
    '''
    def copy_from(self, from_cell):
        self.formatted_value = from_cell.formatted_value
        self.user_entered_value = from_cell.user_entered_value
        self.effective_value = from_cell.effective_value
        self.effective_format = from_cell.effective_format
        self.text_format_runs = from_cell.text_format_runs

        self.merge_spec.multi_col = from_cell.merge_spec.multi_col
        self.merge_spec.col_span = from_cell.merge_spec.col_span
        self.merge_spec.row_span = from_cell.merge_spec.row_span
        self.cell_width = from_cell.cell_width


    ''' Copy the cell as an InnerCell or LastCell assuming it is the FirstCell. This is required for generating extra cells for Multirow
    '''
    def copy_as(self, row_ahead):
        new_cell = Cell(self.row_num + row_ahead, self.col_num, self.value, self.default_format, self.column_widths)

        new_cell.cell_width = self.cell_width
        new_cell.merge_spec.col_span = self.merge_spec.col_span
        new_cell.merge_spec.row_span = self.merge_spec.row_span
        new_cell.merge_spec.multi_col = self.merge_spec.multi_col

        # is it an InnerCell or LastCell
        if row_ahead < (self.merge_spec.row_span - 1):
            # the new cell is an InnerCell of the multirow
            new_cell.merge_spec.multi_row = MultiSpan.InnerCell
            new_cell.is_top_border = False
            new_cell.is_bottom_border = False

        else:
            # the new cell is the LastCell of the multirow
            new_cell.merge_spec.multi_row = MultiSpan.LastCell
            new_cell.is_top_border = False
            new_cell.is_bottom_border = True

        return new_cell


    ''' latex code for cell borders
    '''
    def border_latex(self):
        if self.effective_format:
            t, b, l, r = self.effective_format.borders.to_latex()
            if not self.is_top_border:
                t = '~'

            if not self.is_bottom_border:
                b = '~'

        else:
            # print(f"({self.row_num},{self.col_num}) : no effectiveFormat")
            t, b, l, r = None, None, '', ''

        if t is not None:
            t = f"*{{{self.merge_spec.col_span}}}{t}".strip()

        if b is not None:
            b = f"*{{{self.merge_spec.col_span}}}{b}".strip()

        # print(f"({self.row_num},{self.col_num}) : top    border {t}")
        # print(f"({self.row_num},{self.col_num}) : bottom border {b}")

        return t, b, l, r


    ''' latex code for cell content
    '''
    def content_latex(self):
        # the content is not valid for multirow FirstCell and InnerCell
        if self.merge_spec.multi_row in [MultiSpan.FirstCell, MultiSpan.InnerCell]:
            cell_value = None

        else:
            # textFormatRuns first
            if len(self.text_format_runs):
                run_value_list = []
                processed_idx = len(self.formatted_value)
                for text_format_run in reversed(self.text_format_runs):
                    text = self.formatted_value[:processed_idx]
                    run_value_list.insert(0, text_format_run.to_latex(text))
                    processed_idx = text_format_run.start_index

                cell_value = ''.join(run_value_list)

            # userEnteredValue next, it can be either image or text
            elif self.user_entered_value:
                # if image, userEnteredValue will have an image
                # if text, formattedValue (which we have already included into userEnteredValue) will contain the text
                cell_value = self.user_entered_value.to_latex(self.cell_width, self.effective_format.text_format)

            # there is a 3rd possibility, the cell has no values at all, quite an empty cell
            else:
                cell_value = f"{{}}"


        # cell halign
        if self.effective_format:
            halign = self.effective_format.halign.halign
            bgcolor = self.effective_format.bgcolor.to_latex()
        else:
            halign = HALIGN.get('LEFT')
            bgcolor = self.default_format.bgcolor.to_latex()

        # finally build the cell content
        if cell_value:
            cell_content = f"{halign} {cell_value} \\cellcolor{bgcolor}".strip()
        else:
            cell_content = f"{halign} \\cellcolor{bgcolor}".strip()

        return cell_content


    ''' generates the latex code
    '''
    def to_latex(self):
        latex_lines = []

        latex_lines.append(f"% {self.merge_spec.to_string()}")

        # get the vertical left and right borders
        _, _, l, r = self.border_latex()

        # the cell could be an inner or last cell in a multicolumn setting
        if self.merge_spec.multi_col in [MultiSpan.InnerCell, MultiSpan.LastCell]:
            # we simply do not generate anything
            return latex_lines

        # first we go for multicolumn, multirow and column width part
        if self.effective_format:
            valign = self.effective_format.valign.valign
        else:
            valign = VALIGN.get('MIDDLE')

        cell_col_span = f"\\mc{{{self.merge_spec.col_span}}}{{{l}{valign}{{{self.cell_width}in}}{r}}}"

        # next we build the cell content
        cell_content = self.content_latex()

        # finally we build the whole cell
        if self.merge_spec.multi_row == MultiSpan.LastCell:
            latex_lines.append(f"{cell_col_span} {{\\mr{{{-self.merge_spec.row_span}}}{{=}} {{{cell_content}}}}}")
        else:
            latex_lines.append(f"{cell_col_span} {{{cell_content}}}")

        return latex_lines


''' gsheet Row object wrapper
'''
class Row(object):

    ''' constructor
    '''
    def __init__(self, row_num, row_data, default_format, section_width, column_widths):
        self.row_num, self.section_width, self.column_widths, self.default_format = row_num, section_width, column_widths, default_format
        self.row_name = f"row: [{self.row_num}]"

        self.cells = []
        c = 0
        for value in row_data.get('values', []):
            self.cells.append(Cell(self.row_num, c, value, self.default_format, self.column_widths))
            c = c + 1


    ''' is the row empty (no cells at all)
    '''
    def is_empty(self):
        return (len(self.cells) == 0)


    ''' gets a specific cell by ordinal
    '''
    def get_cell(self, c):
        if c >= 0 and c < len(self.cells):
            return self.cells[c]
        else:
            return None


    ''' inserts a specific cell at a specific ordinal
    '''
    def insert_cell(self, pos, cell):
        # if pos is greater than the last index
        if pos > len(self.cells):
            # insert None objects in between
            fill_from = len(self.cells)
            for i in range(fill_from, pos):
                self.cells.append(None)

        if pos < len(self.cells):
            self.cells[pos] = cell
        else:
            self.cells.append(cell)



    ''' it is true only when the first cell has a out_of_table true value
    '''
    def is_out_of_table(self):
        if len(self.cells) > 0:
            # the first cell is the relevant cell only
            if self.cells[0]:
                return self.cells[0].note.out_of_table
            else:
                return False
        else:
            return False

    ''' it is true only when the first cell has a repeat-rows note with value > 0
    '''
    def is_table_start(self):
        if len(self.cells) > 0:
            # the first cell is the relevant cell only
            if self.cells[0]:
                return (self.cells[0].note.header_rows > 0)
            else:
                return False
        else:
            return False


    ''' generates the top and bottom borders
    '''
    def borders_tb(self):
        top_borders = []
        bottom_borders = []
        c = 0
        for cell in self.cells:
            if cell is None:
                warn(f"{self.row_name} has a Null cell at {c}")

            else:
                t, b, _, _ = cell.border_latex()
                if t is not None:
                    top_borders.append(t)

                if b is not None:
                    bottom_borders.append(b)

            c = c + 1

        top_border = ' '.join(top_borders)
        bottom_border = ' '.join(bottom_borders)

        return f"\\hhline{{{top_border}}}", f"\\hhline{{{bottom_border}}}"


    ''' generates the latex code
    '''
    def to_latex(self):
        row_lines = []

        row_lines.append(f"% {self.row_name}")

        # top and bottom borders
        top_border, bottom_border = self.borders_tb()

        # top border
        row_lines.append(top_border)

        first_cell = True
        c = 0
        for cell in self.cells:
            if cell is None:
                warn(f"{self.row_name} has a Null cell at {c}")
                cell_lines = []
            else:
                cell_lines = cell.to_latex()

            if c > 0 and len(cell_lines) > 1:
                row_lines.append('&')

            row_lines = row_lines + cell_lines
            c = c + 1

        row_lines.append(f"\\tabularnewline")

        # bottom border
        row_lines.append(bottom_border)
        row_lines.append('')

        return row_lines


''' gsheet text format object wrapper
'''
class TextFormat(object):

    ''' constructor
    '''
    def __init__(self, text_format_dict=None):
        self.source = text_format_dict
        if self.source:
            self.fgcolor = RgbColor(text_format_dict.get('foregroundColor'))
            self.font_family = FONT_MAP.get(text_format_dict.get('fontFamily'), '')
            self.font_size = int(text_format_dict.get('fontSize', 0))
            self.is_bold = text_format_dict.get('bold')
            self.is_italic = text_format_dict.get('italic')
            self.is_strikethrough = text_format_dict.get('strikethrough')
            self.is_underline = text_format_dict.get('underline')
        else:
            self.fgcolor = RgbColor()
            self.font_family = ''
            self.font_size = 0
            self.is_bold = False
            self.is_italic = False
            self.is_strikethrough = False
            self.is_underline = False


    def to_latex(self, text):
        content = f"{{{text}}}"

        if self.is_underline: content = f"{{\\underline{content}}}"
        if self.is_strikethrough: content = f"{{\\sout{content}}}"
        if self.is_italic: content = f"{{\\textit{content}}}"
        if self.is_bold: content = f"{{\\textbf{content}}}"

        # color, font, font-size
        if self.font_family != '':
            fontspec = f"\\fontsize{{{self.font_size}pt}}{{{self.font_size}pt}}\\fontspec{{{self.font_family}}}\\color{self.fgcolor.to_latex()}"
        else:
            fontspec = f"\\fontsize{{{self.font_size}pt}}{{{self.font_size}pt}}\\color{self.fgcolor.to_latex()}"


        latex = f"{{{fontspec}{content}}}"
        return latex


''' gsheet cell value object wrapper
'''
class CellValue(object):

    ''' constructor
    '''
    def __init__(self, value_dict, formatted_value=None):
        if value_dict:
            if formatted_value:
                self.string_value = formatted_value
            else:
                self.string_value = value_dict.get('stringValue')

            self.image = value_dict.get('image')
        else:
            self.string_value = ''
            self.image = None


    ''' generates the latex code
    '''
    def to_latex(self, cell_width, format):
        # if image
        if self.image:
            # even now the width may exceed actual cell width, we need to adjust for that
            dpi_x = 150 if self.image['dpi'][0] == 0 else self.image['dpi'][0]
            dpi_y = 150 if self.image['dpi'][1] == 0 else self.image['dpi'][1]
            image_width = self.image['width'] / dpi_x
            image_height = self.image['height'] / dpi_y
            if image_width > cell_width:
                adjust_ratio = (cell_width / image_width)
                # keep a padding of 0.1 inch
                image_width = cell_width - 0.2
                image_height = image_height * adjust_ratio

            latex = f"{{\includegraphics[width={image_width}in]{{{os_specific_path(self.image['path'])}}}}}"

        # if text, formattedValue will contain the text
        else:
            # print(self.string_value)
            latex = format.to_latex(tex_escape(self.string_value))

        return latex


''' Cell Merge spec wrapper
'''
class CellMergeSpec(object):
    def __init__(self):
        self.multi_col = MultiSpan.No
        self.multi_row = MultiSpan.No

        self.col_span = 1
        self.row_span = 1

    def to_string(self):
        return f"multicolumn: {self.multi_col}, multirow: {self.multi_row}"


''' gsheet rowMetadata object wrapper
'''
class RowMetadata(object):

    ''' constructor
    '''
    def __init__(self, row_metadata_dict):
        self.pixel_size = int(row_metadata_dict['pixelSize'])


''' gsheet columnMetadata object wrapper
'''
class ColumnMetadata(object):

    ''' constructor
    '''
    def __init__(self, column_metadata_dict):
        self.pixel_size = int(column_metadata_dict['pixelSize'])


''' gsheet merge object wrapper
'''
class Merge(object):

    ''' constructor
    '''
    def __init__(self, gsheet_merge_dict, start_row, start_column):
        self.start_row = int(gsheet_merge_dict['startRowIndex']) - start_row
        self.end_row = int(gsheet_merge_dict['endRowIndex']) - start_row
        self.start_col = int(gsheet_merge_dict['startColumnIndex']) - start_column
        self.end_col = int(gsheet_merge_dict['endColumnIndex']) - start_column

        self.row_span = self.end_row - self.start_row
        self.col_span = self.end_col - self.start_col


''' gsheet color object wrapper
'''
class RgbColor(object):

    ''' constructor
    '''
    def __init__(self, rgb_dict=None):
        self.red = 0
        self.green = 0
        self.blue = 0

        if rgb_dict:
            self.red = int(float(rgb_dict.get('red', 0)) * 255)
            self.green = int(float(rgb_dict.get('green', 0)) * 255)
            self.blue = int(float(rgb_dict.get('blue', 0)) * 255)


    ''' generates the latex code
    '''
    def to_latex(self):
        return f"[RGB]{{{self.red},{self.green},{self.blue}}}"


''' gsheet cell padding object wrapper
'''
class Padding(object):

    ''' constructor
    '''
    def __init__(self, padding_dict=None):
        if padding_dict:
            self.top = int(padding_dict.get('top', 0))
            self.right = int(padding_dict.get('right', 0))
            self.bottom = int(padding_dict.get('bottom', 0))
            self.left = int(padding_dict.get('left', 0))
        else:
            self.top = 0
            self.right = 0
            self.bottom = 0
            self.left = 0


''' gsheet cell borders object wrapper
'''
class Borders(object):

    ''' constructor
    '''
    def __init__(self, borders_dict=None):
        if borders_dict:
            self.top = Border(borders_dict.get('top'))
            self.right = Border(borders_dict.get('right'))
            self.bottom = Border(borders_dict.get('bottom'))
            self.left = Border(borders_dict.get('left'))
        else:
            self.top = None
            self.right = None
            self.bottom = None
            self.left = None

    def to_latex(self):
        t = self.top.to_latex_h() if self.top else '~'
        b = self.bottom.to_latex_h() if self.bottom else '~'
        l = self.left.to_latex_v() if self.left else ''
        r = self.right.to_latex_v() if self.right else ''

        return t, b, l, r


''' gsheet cell border object wrapper
'''
class Border(object):

    ''' constructor
    '''
    def __init__(self, border_dict=None):
        if border_dict:
            self.style = border_dict.get('style')
            self.width = int(border_dict.get('width')) * 0.4
            self.color = RgbColor(border_dict.get('color'))

            if self.style in ['DOTTED', 'DASHED', 'SOLID']:
                self.style = '-'

            elif self.style in ['DOUBLE']:
                self.style = '='

            elif self.style in ['SOLID_MEDIUM']:
                self.width = self.width * 2
                self.style = '-'

            elif self.style in ['SOLID_THICK']:
                self.width = self.width * 3
                self.style = '-'

            elif self.style in ['NONE']:
                self.style = '~'

            else:
                self.style = '~'

        else:
            self.style = '~'
            self.width = 0
            self.color = RgbColor()

    def to_latex_h(self):
        latex = f"{{>{{\\hborder{{{self.color.red},{self.color.green},{self.color.blue}}}{{{self.width}pt}}}}{self.style}}}"

        return latex


    def to_latex_v(self):
        latex = f"!{{\\vborder{{{self.color.red},{self.color.green},{self.color.blue}}}{{{self.width}pt}}}}"

        return latex


''' gsheet cell format object wrapper
'''
class CellFormat(object):

    ''' constructor
    '''
    def __init__(self, format_dict, default_format=None):
        if format_dict:
            self.bgcolor = RgbColor(format_dict.get('backgroundColor'))
            self.borders = Borders(format_dict.get('borders'))
            self.padding = Padding(format_dict.get('padding'))
            self.halign = HorizontalAlignment(format_dict.get('horizontalAlignment'))
            self.valign = VerticalAlignment(format_dict.get('verticalAlignment'))
            self.text_format = TextFormat(format_dict.get('textFormat'))
        elif default_format:
            self.bgcolor = default_format.bgcolor
            self.borders = default_format.borders
            self.padding = default_format.padding
            self.halign = default_format.halign
            self.valign = default_format.valign
            self.text_format = default_format.text_format
        else:
            self.bgcolor = None
            self.borders = None
            self.padding = None
            self.halign = None
            self.valign = None
            self.text_format = None


''' gsheet text format run object wrapper
'''
class TextFormatRun(object):

    ''' constructor
    '''
    def __init__(self, run_dict=None, default_format=None):
        if run_dict:
            self.start_index = int(run_dict.get('startIndex', 0))
            format = run_dict.get('format')
            new_format = {**default_format, **format}
            self.format = TextFormat(new_format)
        else:
            self.start_index = None
            self.format = None


    ''' generates the latex code
    '''
    def to_latex(self, text):
        latex = self.format.to_latex(tex_escape(text[self.start_index:]))

        return latex


''' gsheet cell notes object wrapper
'''
class CellNote(object):

    ''' constructor
    '''
    def __init__(self, note_json=None):
        self.style = None
        self.out_of_table = False
        self.table_spacing = True
        self.header_rows = 0
        self.new_page = False
        self.keep_with_next = False
        self.page_number_style = None

        if note_json:
            try:
                note_dict = json.loads(note_json)
            except json.JSONDecodeError:
                note_dict = {}

            self.style = note_dict.get('style')

            content = note_dict.get('content')
            if content is not None and content == 'out-of-cell':
                self.out_of_table = True

            spacing = note_dict.get('table-spacing')
            if spacing is not None and spacing == 'no-spacing':
                self.table_spacing = False

            self.header_rows = int(note_dict.get('repeat-rows', 0))
            self.new_page = note_dict.get('new-page') is not None
            self.keep_with_next = note_dict.get('keep-with-next') is not None
            self.page_number_style = note_dict.get('page-number')


''' gsheet vertical alignment object wrapper
'''
class VerticalAlignment(object):

    ''' constructor
    '''
    def __init__(self, valign=None):
        if valign:
            self.valign = VALIGN.get(valign, 'p')
        else:
            self.valign = VALIGN.get('TOP')


''' gsheet horizontal alignment object wrapper
'''
class HorizontalAlignment(object):

    ''' constructor
    '''
    def __init__(self, halign=None):
        if halign:
            self.halign = HALIGN.get(halign, 'LEFT')
        else:
            self.halign = HALIGN.get('LEFT')


''' Helper for cell span specification
'''
class MultiSpan(object):
    No = 'No'
    FirstCell = 'FirstCell'
    InnerCell = 'InnerCell'
    LastCell = 'LastCell'