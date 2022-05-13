#!/usr/bin/env python3

import json
from odt.odt_util import *

#   ----------------------------------------------------------------------------------------------------------------
#   odt section (not oo section, gsheet section) objects wrappers
#   ----------------------------------------------------------------------------------------------------------------

''' Odt section base object
'''
class OdtSectionBase(object):

    ''' constructor
    '''
    def __init__(self, section_data, config):
        self._config = config
        self._section_data = section_data

        self.section = self._section_data['section']
        self.level = self._section_data['level']
        self.page_numbering = self._section_data['hide-pageno']
        self.section_index = self._section_data['section-index']
        self.section_width = self._section_data['width']
        self.section_break = self._section_data['section-break']
        self.page_break = self._section_data['page-break']

        # headers and footers
        self.header_first = OdtPageHeaderFooter(self._section_data['header-first'], self.section_width, self.section_index, header_footer='header', odd_even='first')
        self.header_odd = OdtPageHeaderFooter(self._section_data['header-odd'], self.section_width, self.section_index, header_footer='header', odd_even='odd')
        self.header_even = OdtPageHeaderFooter(self._section_data['header-even'], self.section_width, self.section_index, header_footer='header', odd_even='even')
        self.footer_first = OdtPageHeaderFooter(self._section_data['footer-first'], self.section_width, self.section_index, header_footer='footer', odd_even='first')
        self.footer_odd = OdtPageHeaderFooter(self._section_data['footer-odd'], self.section_width, self.section_index, header_footer='footer', odd_even='odd')
        self.footer_even = OdtPageHeaderFooter(self._section_data['footer-even'], self.section_width, self.section_index, header_footer='footer', odd_even='even')

        self.section_contents = OdtContent(section_data.get('contents'), self.section_width)


    ''' Header/Footer processing
    '''
    def process_header_footer(self, odt, master_page, page_layout):
        if self._section_data['header-odd']:
            self.header_odd.page_header_footer_to_odt(odt, master_page, page_layout)

        if self._section_data['header-first']:
            self.header_first.page_header_footer_to_odt(odt, master_page, page_layout)

        if self._section_data['header-even']:
            self.header_even.page_header_footer_to_odt(odt, master_page, page_layout)

        if self._section_data['footer-odd']:
            self.footer_odd.page_header_footer_to_odt(odt, master_page, page_layout)

        if self._section_data['footer-first']:
            self.footer_first.page_header_footer_to_odt(odt, master_page, page_layout)

        if self._section_data['footer-even']:
            self.footer_even.page_header_footer_to_odt(odt, master_page, page_layout)


    ''' generates the odt code
    '''
    def section_to_odt(self, odt):
        # master-page is created, decide on headers and footers
        master_page = get_master_page(odt, self._section_data['master-page'])
        page_layout = get_page_layout(odt, self._section_data['page-layout'])

        if master_page and page_layout:
            self.process_header_footer(odt, master_page, page_layout)

        style_attributes = {}

        # identify what style the heading will be and its content
        if not self._section_data['hide-heading']:
            heading_text = self._section_data['heading']
            if self._section_data['section'] != '':
                heading_text = f"{self._section_data['section']} {heading_text}"

            if self._section_data['level'] == 0:
                parent_style_name = 'Title'
            else:
                parent_style_name = f"Heading_20_{self._section_data['level']}"

            # debug(f"..... {parent_style_name} - {heading_text}")
        else:
            heading_text = ''
            parent_style_name = 'Text_20_body'

        style_attributes['parentstylename'] = parent_style_name

        paragraph_attributes = None
        # handle section-break and page-break
        if self._section_data['section-break']:
            # if it is a new-section, we create a new paragraph-style based on parent_style_name with the master-page and apply it
            style_name = f"P{self._section_data['section-index']}-P0-with-section-break"
            style_attributes['masterpagename'] = self._section_data['master-page']
            # debug(f"..... Section Break with MasterPage {self._section_data['master-page']}")
        else:
            if self._section_data['page-break']:
                # if it is a new-page, we create a new paragraph-style based on parent_style_name with the page-break and apply it
                paragraph_attributes = {'breakbefore': 'page'}
                style_name = f"P{self._section_data['section-index']}-P0-with-page-break"
                # debug(f"..... Page Break with MasterPage {self._section_data['master-page']}")
            else:
                style_name = f"P{self._section_data['section-index']}-P0"
                # debug(f"..... Continuous with MasterPage {self._section_data['master-page']}")

        style_attributes['name'] = style_name

        style_name = create_paragraph_style(odt, style_attributes=style_attributes, paragraph_attributes=paragraph_attributes)
        # debug(f"..... Paragraph style {style_name} created")
        paragraph = create_paragraph(odt, style_name, text_content=heading_text)
        odt.text.addElement(paragraph)



''' Odt table section object
'''
class OdtTableSection(OdtSectionBase):

    ''' constructor
    '''
    def __init__(self, section_data, config):
        super().__init__(section_data, config)


    ''' generates the odt code
    '''
    def section_to_odt(self, odt):
        super().section_to_odt(odt)
        self.section_contents.content_to_odt(odt=odt, container=odt.text)



''' Odt ToC section object
'''
class OdtToCSection(OdtSectionBase):

    ''' constructor
    '''
    def __init__(self, section_data, config):
        super().__init__(section_data, config)


    ''' generates the odt code
    '''
    def section_to_odt(self, odt):
        super().section_to_odt(odt)
        toc = create_toc()
        if toc:
            odt.text.addElement(toc)



''' Odt LoT section object
'''
class OdtLoTSection(OdtSectionBase):

    ''' constructor
    '''
    def __init__(self, section_data, config):
        super().__init__(section_data, config)


    ''' generates the odt code
    '''
    def section_to_odt(self, odt):
        super().section_to_odt(odt)
        toc = create_lot()
        if toc:
            odt.text.addElement(toc)



''' Odt LoF section object
'''
class OdtLoFSection(OdtSectionBase):

    ''' constructor
    '''
    def __init__(self, section_data, config):
        super().__init__(section_data, config)


    ''' generates the odt code
    '''
    def section_to_odt(self, odt):
        super().section_to_odt(odt)
        toc = create_lof()
        if toc:
            odt.text.addElement(toc)



''' Odt section content base object
'''
class OdtContent(object):

    ''' constructor
    '''
    def __init__(self, content_data, content_width):
        self.content_data = content_data
        self.content_width = content_width
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

        # we need a list to hold the tables and block for the cells
        self.content_list = []

        if content_data:
            self.has_content = True

            properties = content_data.get('properties')
            # self.default_format = CellFormat(properties.get('defaultFormat'))

            sheets = content_data.get('sheets')
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

                    all_column_widths_in_pixel = sum(x.pixel_size for x in self.column_metadata_list)
                    self.column_widths = [ (x.pixel_size * self.content_width / all_column_widths_in_pixel) for x in self.column_metadata_list ]

                    # rowData
                    r = 0
                    for row_data in data.get('rowData', []):
                        self.cell_matrix.append(Row(r, row_data, self.content_width, self.column_widths, self.row_metadata_list[r].inches))
                        r = r + 1

            # process and split
            self.process()
            self.split()

        else:
            self.has_content = False


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

            if col_span > 1:
                first_cell.merge_spec.multi_col = MultiSpan.FirstCell
            else:
                first_cell.merge_spec.multi_col = MultiSpan.No

            if row_span > 1:
                first_cell.merge_spec.multi_row = MultiSpan.FirstCell
            else:
                first_cell.merge_spec.multi_row = MultiSpan.No

            first_cell.merge_spec.col_span = col_span
            first_cell.merge_spec.row_span = row_span

            # considering merges, we have effective cell width and height
            first_cell.effective_cell_width = sum(first_cell.column_widths[first_cell.col_num:first_cell.col_num + col_span])
            effective_row_height = 0
            for r in range(first_row, last_row):
                effective_row_height = effective_row_height + self.cell_matrix[r].row_height

            first_cell.effective_cell_height = effective_row_height

            # for row spans, subsequent cells in the same column of the FirstCell will be either empty or missing, iterate through the next rows
            for r in range(first_row, last_row):
                next_row_object = self.cell_matrix[r]
                row_height = next_row_object.row_height

                # we may have empty cells in this same row which are part of this column merge, we need to mark their multi_col property correctly
                for c in range(first_col, last_col):
                    # exclude the very first cell
                    if r == first_row and c == first_col:
                        continue

                    # debug(f"..cell [{r+1},{c+1}] is part of column merge")
                    next_cell_in_row = next_row_object.get_cell(c)

                    if next_cell_in_row is None:
                        # the cell may not be existing at all, we have to create
                        # debug(f"..cell [{r+1},{c+1}] does not exist, to be inserted")
                        # next_cell_in_row = Cell(r, c, None, first_cell.default_format, first_cell.column_widths, row_height)
                        next_cell_in_row = Cell(r, c, None, first_cell.column_widths, row_height)
                        next_row_object.insert_cell(c, next_cell_in_row)

                    if next_cell_in_row.is_empty:
                        # debug(f"..cell [{r+1},{c+1}] is empty")
                        # the cell is a newly inserted one, its format should be the same (for borders, colors) as the first cell so that we can draw borders properly
                        next_cell_in_row.copy_format_from(first_cell)

                        # mark cells for multicol only if it is multicol
                        if col_span > 1:
                            if c == first_col:
                                # the last cell of the merge to be marked as LastCell
                                # debug(f"..cell [{r+1},{c+1}] is the LastCell of the column merge")
                                next_cell_in_row.mark_multicol(MultiSpan.FirstCell)

                            elif c == last_col-1:
                                # the last cell of the merge to be marked as LastCell
                                # debug(f"..cell [{r+1},{c+1}] is the LastCell of the column merge")
                                next_cell_in_row.mark_multicol(MultiSpan.LastCell)

                            else:
                                # the inner cells of the merge to be marked as InnerCell
                                # debug(f"..cell [{r+1},{c+1}] is an InnerCell of the column merge")
                                next_cell_in_row.mark_multicol(MultiSpan.InnerCell)

                        else:
                            next_cell_in_row.mark_multicol(MultiSpan.No)


                        # mark cells for multirow only if it is multirow
                        if row_span > 1:
                            if r == first_row:
                                # the last cell of the merge to be marked as LastCell
                                # debug(f"..cell [{r+1},{c+1}] is the LastCell of the row merge")
                                next_cell_in_row.mark_multirow(MultiSpan.FirstCell)

                            elif r == last_row-1:
                                # the last cell of the merge to be marked as LastCell
                                # debug(f"..cell [{r+1},{c+1}] is the LastCell of the row merge")
                                next_cell_in_row.mark_multirow(MultiSpan.LastCell)

                            else:
                                # the inner cells of the merge to be marked as InnerCell
                                # debug(f"..cell [{r+1},{c+1}] is an InnerCell of the row merge")
                                next_cell_in_row.mark_multirow(MultiSpan.InnerCell)

                        else:
                            next_cell_in_row.mark_multirow(MultiSpan.No)

                    else:
                        warn(f"..cell [{r+1},{c+1}] is not empty, it must be part of another column/row merge which is an issue")

        return


    ''' processes the cells to split the cells into tables and blocks and orders the tables and blocks properly
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
                    table = OdtTable(self.cell_matrix, next_table_starts_in_row, r - 1, self.column_widths)
                    self.content_list.append(table)

                block = OdtParagraph(data_row, r)
                self.content_list.append(block)

                next_table_starts_in_row = r + 1

            # the row may start with a note of repeat-rows which means that a new table is atarting
            elif data_row.is_table_start():
                # there may be a pending/running table
                if r > next_table_starts_in_row:
                    table = OdtTable(self.cell_matrix, next_table_starts_in_row, r - 1, self.column_widths)
                    self.content_list.append(table)

                    next_table_starts_in_row = r

            else:
                next_table_ends_in_row = r

        # there may be a pending/running table
        if next_table_ends_in_row >= next_table_starts_in_row:
            table = OdtTable(self.cell_matrix, next_table_starts_in_row, next_table_ends_in_row, self.column_widths)
            self.content_list.append(table)


    ''' generates the odt code
        container may be odt.text or a table-cell
    '''
    def content_to_odt(self, odt, container):
        # iterate through tables and blocks contents
        for block in self.content_list:
            block.block_to_odt(odt=odt, container=container)
            # odt_element = block.block_to_odt(odt=odt, container=container)
            # # for a paragrpah or table it can be a single element, for an embedded content it can be a list
            # if odt_element:
            #     if isinstance(odt_element, list):
            #         for e in odt_element:
            #             container.addElement(e)
            #     else:
            #         container.addElement(odt_element)



''' Odt Page Header Footer object
'''
class OdtPageHeaderFooter(OdtContent):

    ''' constructor
        header_footer : header/footer
        odd_even      : first/odd/even(left)
    '''
    def __init__(self, content_data, section_width, section_index, header_footer, odd_even):
        super().__init__(content_data, section_width)
        self.header_footer, self.odd_even = header_footer, odd_even
        self.id = f"{self.header_footer}{self.odd_even}{section_index}"


    ''' generates the odt code
    '''
    def page_header_footer_to_odt(self, odt, master_page, page_layout):
        if self.content_data is None:
            return

        header_footer_style = create_header_footer(master_page, page_layout, self.header_footer, self.odd_even)
        if header_footer_style:
            # iterate through tables and blocks contents
            for block in self.content_list:
                block.block_to_odt(odt=odt, container=header_footer_style)
                # odt_element = block.block_to_odt(odt=odt, container=header_footer_style)
                # if odt_element:
                #     header_footer_style.addElement(odt_element)
                #
                # first_block = False



''' Odt Block object wrapper base class (plain odt, table, header etc.)
'''
class OdtBlock(object):

    ''' constructor
    '''
    def __init__(self):
        pass



''' Odt Table object wrapper
'''
class OdtTable(OdtBlock):

    ''' constructor
    '''
    def __init__(self, cell_matrix, start_row, end_row, column_widths):
        self.start_row, self.end_row, self.column_widths = start_row, end_row, column_widths
        self.table_cell_matrix = cell_matrix[start_row:end_row+1]
        self.row_count = len(self.table_cell_matrix)
        self.table_name = f"Table_{random_string()}"

        # header row if any
        self.header_row_count = self.table_cell_matrix[0].get_cell(0).note.header_rows


    ''' generates the odt code
    '''
    def block_to_odt(self, odt, container):
        # let us see how the cells look now
        # debug(f"Table [{self.table_name}]")
        # for row in self.table_cell_matrix:
        #     debug(row.row_name)
        #     for cell in row.cells:
        #         debug(f".. {cell}")

        # create the table with styles
        table_style_attributes = {'name': f"{self.table_name}_style"}
        table_properties_attributes = {'width': f"{sum(self.column_widths)}in"}
        table = create_table(odt, self.table_name, table_style_attributes=table_style_attributes, table_properties_attributes=table_properties_attributes)

        # table-columns
        for c in range(0, len(self.column_widths)):
            col_a1 = COLUMNS[c]
            col_width = self.column_widths[c]
            table_column_name = f"{self.table_name}.{col_a1}"
            # print(f"{col_a1:>2} : {col_width:1.4f}in")
            table_column_style_attributes = {'name': f"{table_column_name}_style"}
            table_column_properties_attributes = {'columnwidth': f"{col_width}in", 'useoptimalcolumnwidth': False}
            table_column = create_table_column(odt, table_column_name, table_column_style_attributes, table_column_properties_attributes)
            table.addElement(table_column)

        # iterate header rows render the table's contents
        table_header_rows = create_table_header_rows()
        for row in self.table_cell_matrix[0:self.header_row_count]:
            table_row = row.row_to_odt_table_row(odt, self.table_name)
            table_header_rows.addElement(table_row)

        table.addElement(table_header_rows)

        # iterate rows and cells to render the table's contents
        for row in self.table_cell_matrix[self.header_row_count:]:
            table_row = row.row_to_odt_table_row(odt, self.table_name)
            table.addElement(table_row)

        container.addElement(table)



''' Odt Block object wrapper
'''
class OdtParagraph(OdtBlock):

    ''' constructor
    '''
    def __init__(self, data_row, row_number):
        self.data_row = data_row
        self.row_number = row_number

    ''' generates the odt code
    '''
    def block_to_odt(self, odt, container):
        # generate the block, only the first cell of the data_row to be produced
        if len(self.data_row.cells) > 0:
            # We take the first cell, the cell will take the whole row width
            cell_to_produce = self.data_row.get_cell(0)
            cell_to_produce.cell_width = sum(cell_to_produce.column_widths)

            cell_to_produce.cell_to_odt(odt=odt, container=container, for_table_cell=False)


#   ----------------------------------------------------------------------------------------------------------------
#   gsheet cell wrappers
#   ----------------------------------------------------------------------------------------------------------------

''' gsheet Cell object wrapper
'''
class Cell(object):

    ''' constructor
    '''
    def __init__(self, row_num, col_num, value, column_widths, row_height):
        self.row_num, self.col_num, self.column_widths = row_num, col_num, column_widths
        self.cell_name = f"cell: [{self.row_num},{self.col_num}]"
        self.value = value
        self.text_format_runs = []
        self.cell_width = self.column_widths[self.col_num]
        self.cell_height = row_height
        self.merge_spec = CellMergeSpec()

        # considering merges, we have effective cell width and height
        self.effective_cell_width = self.cell_width
        self.effective_cell_height = self.cell_height

        if self.value:
            self.note = CellNote(value.get('note'))
            self.formatted_value = self.value.get('formattedValue', '')

            # self.effective_format = CellFormat(self.value.get('effectiveFormat'), self.default_format)
            self.effective_format = CellFormat(self.value.get('effectiveFormat'))

            for text_format_run in self.value.get('textFormatRuns', []):
                self.text_format_runs.append(TextFormatRun(text_format_run, self.effective_format.text_format.source))


            # we need to identify exactly what kind of value the cell contains
            if 'contents' in self.value:
                self.cell_value = ContentValue(self.effective_format, self.value['contents'])

            elif 'userEnteredValue' in self.value:
                if 'image' in self.value['userEnteredValue']:
                    self.cell_value = ImageValue(self.effective_format, self.value['userEnteredValue']['image'])

                else:
                    if len(self.text_format_runs):
                        self.cell_value = TextRunValue(self.effective_format, self.text_format_runs, self.formatted_value)

                    elif self.note.page_number:
                        self.cell_value = PageNumberValue(self.effective_format, short=False)

                    else:
                        self.cell_value = StringValue(self.effective_format, self.value['userEnteredValue'], self.formatted_value)

            else:
                self.cell_value = None


            # presence of userEnteredFormat makes the cell non-empty
            if 'userEnteredFormat' in self.value:
                self.is_empty = False
            else:
                self.is_empty = True

        else:
            # value can have a special case it can be an empty ditionary when the cell is an inner cell of a column merge
            self.merge_spec.multi_col = MultiSpan.No
            self.note = CellNote()
            self.cell_value = None
            self.formatted_value = None
            # self.user_entered_format = None
            self.effective_format = None
            self.is_empty = True


    ''' string representation
    '''
    def __repr__(self):
        s = f"[{self.row_num+1},{self.col_num+1:>2}], value: {not self.is_empty:<1}, mr: {self.merge_spec.multi_row:<9}, mc: {self.merge_spec.multi_col:<9} [{self.formatted_value}]"
        return s


    ''' odt code for cell content
    '''
    def cell_to_odt_table_cell(self, odt, table_name):
        self.table_name = table_name
        col_a1 = COLUMNS[self.col_num]
        table_cell_style_attributes = {'name': f"{self.table_name}.{col_a1}{self.row_num+1}_style"}

        table_cell_properties_attributes = {}
        if self.effective_format:
            table_cell_properties_attributes = self.effective_format.table_cell_attributes(self.merge_spec)
        else:
            warn(f"{self} : NO effective_format")

        if not self.is_empty:
            # wrap this into a table-cell
            table_cell_attributes = self.merge_spec.table_cell_attributes()
            table_cell = create_table_cell(odt, table_cell_style_attributes, table_cell_properties_attributes, table_cell_attributes)

            if table_cell:
                self.cell_to_odt(odt=odt, container=table_cell, for_table_cell=True)

        else:
            # wrap this into a covered-table-cell
            table_cell = create_covered_table_cell(odt, table_cell_style_attributes, table_cell_properties_attributes)

        return table_cell


    ''' odt code for cell content
    '''
    def cell_to_odt(self, odt, container, for_table_cell=False):
        style_attributes = self.note.style_attributes()
        paragraph_attributes = {**self.note.paragraph_attributes(),  **self.effective_format.paragraph_attributes(for_table_cell, self.merge_spec)}
        text_attributes = self.effective_format.text_format.text_attributes()

        # for string and image it returns a paragraph, for embedded content a list
        # the content is not valid for multirow LastCell and InnerCell
        if self.merge_spec.multi_row in [MultiSpan.No, MultiSpan.FirstCell] and self.merge_spec.multi_col in [MultiSpan.No, MultiSpan.FirstCell]:
            # debug(self.cell_value)
            if self.cell_value:
                self.cell_value.value_to_odt(odt, container, self.effective_cell_width, self.effective_cell_height, style_attributes, paragraph_attributes, text_attributes)
            else:
                warn(f"{self} is None")



    ''' Copy format from the cell passed
    '''
    def copy_format_from(self, from_cell):
        self.effective_format = from_cell.effective_format


    ''' mark the cell multi_col
    '''
    def mark_multicol(self, span):
        self.merge_spec.multi_col = span


    ''' mark the cell multi_col
    '''
    def mark_multirow(self, span):
        self.merge_spec.multi_row = span



''' gsheet Row object wrapper
'''
class Row(object):

    ''' constructor
    '''
    # def __init__(self, row_num, row_data, default_format, section_width, column_widths, row_height):
    def __init__(self, row_num, row_data, section_width, column_widths, row_height):
        # self.row_num, self.default_format, self.section_width, self.column_widths, self.row_height = row_num, default_format, section_width, column_widths, row_height
        self.row_num, self.section_width, self.column_widths, self.row_height = row_num, section_width, column_widths, row_height
        self.row_name = f"row: [{self.row_num+1}]"

        self.cells = []
        c = 0
        for value in row_data.get('values', []):
            # self.cells.append(Cell(self.row_num, c, value, self.default_format, self.column_widths, self.row_height))
            self.cells.append(Cell(self.row_num, c, value, self.column_widths, self.row_height))
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


    ''' generates the odt code
    '''
    def row_to_odt_table_row(self, odt, table_name):
        self.table_name = table_name

        # create table-row
        table_row_style_attributes = {'name': f"{self.table_name}-{self.row_num}"}
        row_height = f"{self.row_height}in"
        # debug(f".. row {self.row_name} {row_height}")
        table_row_properties_attributes = {'keeptogether': True, 'minrowheight': row_height, 'useoptimalrowheight': True}
        table_row = create_table_row(odt, table_row_style_attributes, table_row_properties_attributes)

        # iterate over the cells
        c = 0
        for cell in self.cells:
            if cell is None:
                warn(f"{self.row_name} has a Null cell at {c}")
            else:
                table_cell = cell.cell_to_odt_table_cell(odt, self.table_name)
                if table_cell:
                    table_row.addElement(table_cell)

            c = c + 1

        return table_row



''' gsheet text format object wrapper
'''
class TextFormat(object):

    ''' constructor
    '''
    def __init__(self, text_format_dict=None):
        self.source = text_format_dict
        if self.source:
            self.fgcolor = RgbColor(text_format_dict.get('foregroundColor'))
            if 'fontFamily' in text_format_dict:
                self.font_family = text_format_dict['fontFamily']

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


    ''' attributes dict for TextProperties
    '''
    def text_attributes(self):
        attributes = {}

        attributes['color'] = self.fgcolor.value()
        if self.font_family != '':
            attributes['fontname'] = self.font_family

        attributes['fontsize'] = self.font_size

        if self.is_bold:
            attributes['fontweight'] = "bold"

        if self.is_italic:
            attributes['fontstyle'] = "italic"

        if self.is_underline:
            attributes['textunderlinestyle'] = "solid"
            attributes['textunderlinewidth'] = "auto"
            attributes['textunderlinecolor'] = "font-color"

        if self.is_strikethrough:
            attributes['textlinethroughstyle'] = "solid"
            attributes['textlinethroughtype'] = "single"

        return attributes



''' gsheet cell value object wrapper
'''
class CellValue(object):

    ''' constructor
    '''
    def __init__(self, effective_format):
        self.effective_format = effective_format



''' string type CellValue
'''
class StringValue(CellValue):

    ''' constructor
    '''
    def __init__(self, effective_format, string_value, formatted_value=None):
        super().__init__(effective_format)
        if formatted_value:
            self.value = formatted_value
        else:
            if 'stringValue' in string_value:
                self.value = string_value['string_value']
            else:
                self.value = ''


    ''' string representation
    '''
    def __repr__(self):
        s = f"string : [{self.value}]"
        return s


    ''' generates the odt code
    '''
    def value_to_odt(self, odt, container, cell_width, cell_height, style_attributes, paragraph_attributes, text_attributes):
        if container is None:
            container = odt.text

        style_name = create_paragraph_style(odt, style_attributes=style_attributes, paragraph_attributes=paragraph_attributes, text_attributes=text_attributes)
        paragraph = create_paragraph(odt, style_name, text_content=self.value)

        container.addElement(paragraph)


''' text-run type CellValue
'''
class TextRunValue(CellValue):

    ''' constructor
    '''
    def __init__(self, effective_format, text_format_runs, formatted_value):
        super().__init__(effective_format)
        self.text_format_runs = text_format_runs
        self.formatted_value = formatted_value


    ''' string representation
    '''
    def __repr__(self):
        s = f"text-run : [{self.formatted_value}]"
        return s


    ''' generates the odt code
    '''
    def value_to_odt(self, odt, container, cell_width, cell_height, style_attributes, paragraph_attributes, text_attributes):
        if container is None:
            container = odt.text

        run_value_list = []
        processed_idx = len(self.formatted_value)
        for text_format_run in reversed(self.text_format_runs):
            text = self.formatted_value[:processed_idx]
            run_value_list.insert(0, text_format_run.text_attributes(text))
            processed_idx = text_format_run.start_index

        style_name = create_paragraph_style(odt, style_attributes=style_attributes, paragraph_attributes=paragraph_attributes)
        paragraph = create_paragraph(odt, style_name, run_list=run_value_list)

        container.addElement(paragraph)



''' page-number type CellValue
'''
class PageNumberValue(CellValue):

    ''' constructor
    '''
    def __init__(self, effective_format, short=False):
        super().__init__(effective_format)
        self.short = short


    ''' string representation
    '''
    def __repr__(self):
        s = f"page-number"
        return s


    ''' generates the odt code
    '''
    def value_to_odt(self, odt, container, cell_width, cell_height, style_attributes, paragraph_attributes, text_attributes):
        if container is None:
            container = odt.text

        style_name = create_paragraph_style(odt, style_attributes=style_attributes, paragraph_attributes=paragraph_attributes, text_attributes=text_attributes)
        paragraph = create_page_number(style_name=style_name, short=self.short)

        container.addElement(paragraph)



''' image type CellValue
'''
class ImageValue(CellValue):

    ''' constructor
    '''
    def __init__(self, effective_format, image_value):
        super().__init__(effective_format)
        self.value = image_value


    ''' string representation
    '''
    def __repr__(self):
        s = f"image : [{self.value}]"
        return s


    ''' generates the odt code
    '''
    def value_to_odt(self, odt, container, cell_width, cell_height, style_attributes, paragraph_attributes, text_attributes):
        if container is None:
            container = odt.text

        # even now the width may exceed actual cell width, we need to adjust for that
        dpi_x = 72 if self.value['dpi'][0] == 0 else self.value['dpi'][0]
        dpi_y = 72 if self.value['dpi'][1] == 0 else self.value['dpi'][1]
        image_width_in_pixel = self.value['size'][0]
        image_height_in_pixel = self.value['size'][1]
        image_width_in_inches =  image_width_in_pixel / dpi_x
        image_height_in_inches = image_height_in_pixel / dpi_y

        if self.value['mode'] == 1:
            # image is to be scaled within the cell width and height
            # debug(f"image : [{image_width_in_inches}in X {image_height_in_inches}in, cell-width [{cell_width}in], cell-height [{cell_height}in]")
            if image_width_in_inches > cell_width:
                adjust_ratio = (cell_width / image_width_in_inches)
                image_width_in_inches = image_width_in_inches * adjust_ratio
                image_height_in_inches = image_height_in_inches * adjust_ratio

            if image_height_in_inches > cell_height:
                adjust_ratio = (cell_height / image_height_in_inches)
                image_width_in_inches = image_width_in_inches * adjust_ratio
                image_height_in_inches = image_height_in_inches * adjust_ratio

        elif self.value['mode'] == 3:
            # image size is unchanged
            pass

        else:
            # treat it as if image mode is 3
            pass

        text_attributes['fontsize'] = 2
        picture_path = self.value['path']

        draw_frame = create_image_frame(odt, picture_path, IMAGE_POSITION[self.effective_format.valign.valign], IMAGE_POSITION[self.effective_format.halign.halign], image_width_in_inches, image_height_in_inches)

        style_name = create_paragraph_style(odt, style_attributes=style_attributes, paragraph_attributes=paragraph_attributes, text_attributes=text_attributes)
        paragraph = create_paragraph(odt, style_name)

        paragraph.addElement(draw_frame)

        container.addElement(paragraph)



''' content type CellValue
'''
class ContentValue(CellValue):

    ''' constructor
    '''
    def __init__(self, effective_format, content_value):
        super().__init__(effective_format)
        self.value = content_value


    ''' string representation
    '''
    def __repr__(self):
        s = f"content : [{self.value['sheets'][0]['properties']['title']}]"
        return s


    ''' generates the odt code
    '''
    def value_to_odt(self, odt, container, cell_width, cell_height, style_attributes, paragraph_attributes, text_attributes):
        self.contents = OdtContent(self.value, cell_width)
        self.contents.content_to_odt(odt=odt, container=container)



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
            self.wrapping = Wrapping(format_dict.get('wrapStrategy'))
        elif default_format:
            self.bgcolor = default_format.bgcolor
            self.borders = default_format.borders
            self.padding = default_format.padding
            self.halign = default_format.halign
            self.valign = default_format.valign
            self.text_format = default_format.text_format
            self.wrapping = default_format.wrapping
        else:
            self.bgcolor = None
            self.borders = None
            self.padding = None
            self.halign = None
            self.valign = None
            self.text_format = None
            self.wrapping = None


    ''' attributes dict for TableCellProperties
    '''
    def table_cell_attributes(self, cell_merge_spec):
        attributes = {}

        attributes['verticalalign'] = self.valign.valign
        attributes['backgroundcolor'] = self.bgcolor.value()
        attributes['wrapoption'] = self.wrapping.wrapping
        more_attributes = {**self.borders.table_cell_attributes(cell_merge_spec), **self.padding.table_cell_attributes()}

        return {**attributes, **more_attributes}


    ''' attributes dict for ParagraphProperties
    '''
    def paragraph_attributes(self, for_table_cell, cell_merge_spec):
        attributes = {'textalign': self.halign.halign}

        if not for_table_cell:
            attributes['verticalalign'] = self.valign.valign
            attributes['backgroundcolor'] = self.bgcolor.value()
            # attributes['wrapoption'] = self.wrapping.wrapping
            more_attributes = {**self.borders.table_cell_attributes(cell_merge_spec), **self.padding.table_cell_attributes()}

            return {**attributes, **more_attributes}

        return attributes


    ''' image position as required by BackgroundImage
    '''
    def image_position(self):
        return f"{IMAGE_POSITION[self.valign.valign]} {IMAGE_POSITION[self.halign.halign]}"



''' gsheet cell borders object wrapper
'''
class Borders(object):

    ''' constructor
    '''
    def __init__(self, borders_dict=None):
        self.top = None
        self.right = None
        self.bottom = None
        self.left = None

        if borders_dict:
            if 'top' in borders_dict:
                self.top = Border(borders_dict.get('top'))

            if 'right' in borders_dict:
                self.right = Border(borders_dict.get('right'))

            if 'bottom' in borders_dict:
                self.bottom = Border(borders_dict.get('bottom'))

            if 'left' in borders_dict:
                self.left = Border(borders_dict.get('left'))


    ''' string representation
    '''
    def __repr__(self):
        return f"t: [{self.top}], b: [{self.bottom}], l: [{self.left}], r: [{self.right}]"


    ''' table-cell attributes
    '''
    def table_cell_attributes(self, cell_merge_spec):
        attributes = {}

        # top and bottom
        if cell_merge_spec.multi_row in [MultiSpan.No, MultiSpan.FirstCell]:
            if self.top:
                attributes['bordertop'] = self.top.value()

            if self.bottom:
                attributes['borderbottom'] = self.bottom.value()

        if cell_merge_spec.multi_row in [MultiSpan.LastCell]:
            if self.bottom:
                attributes['borderbottom'] = self.bottom.value()


        # left and right
        if cell_merge_spec.multi_col in [MultiSpan.No, MultiSpan.FirstCell]:
            if self.left:
                attributes['borderleft'] = self.left.value()

            if self.right:
                attributes['borderright'] = self.right.value()

        if cell_merge_spec.multi_col in [MultiSpan.LastCell]:
            if self.right:
                attributes['borderright'] = self.right.value()


        return attributes



''' gsheet cell border object wrapper
'''
class Border(object):

    ''' constructor
    '''
    def __init__(self, border_dict):
        self.style = None
        self.width = None
        self.color = None

        if border_dict:
            self.width = border_dict.get('width') / 2
            self.color = RgbColor(border_dict.get('color'))

            # TODO: handle double
            self.style = GSHEET_ODT_BORDER_MAPPING.get(self.style, 'solid')


    ''' string representation
    '''
    def __repr__(self):
        return f"{self.width}pt {self.style} {self.color.value()}"


    ''' value
    '''
    def value(self):
        return f"{self.width}pt {self.style} {self.color.value()}"



''' Cell Merge spec wrapper
'''
class CellMergeSpec(object):
    def __init__(self):
        self.multi_col = MultiSpan.No
        self.multi_row = MultiSpan.No

        self.col_span = 1
        self.row_span = 1


    ''' string representation
    '''
    def to_string(self):
        return f"multicolumn: {self.multi_col}, multirow: {self.multi_row}"


    ''' table-cell attributes
    '''
    def table_cell_attributes(self):
        attributes = {}

        if self.col_span > 1:
            attributes['numbercolumnsspanned'] = self.col_span

        if self.row_span:
            attributes['numberrowsspanned'] = self.row_span

        return attributes



''' gsheet rowMetadata object wrapper
'''
class RowMetadata(object):

    ''' constructor
    '''
    def __init__(self, row_metadata_dict):
        self.pixel_size = int(row_metadata_dict['pixelSize'])
        self.inches = row_height_in_inches(self.pixel_size)



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


    ''' string representation
    '''
    def __repr__(self):
        return ''.join('{:02x}'.format(a) for a in [self.red, self.green, self.blue])


    ''' color key for tabularray color name
    '''
    def key(self):
        return ''.join('{:02x}'.format(a) for a in [self.red, self.green, self.blue])


    ''' color value for tabularray color
    '''
    def value(self):
        return '#' + ''.join('{:02x}'.format(a) for a in [self.red, self.green, self.blue])



''' gsheet cell padding object wrapper
'''
class Padding(object):

    ''' constructor
    '''
    def __init__(self, padding_dict=None):
        if padding_dict:
            # self.top = int(padding_dict.get('top', 0))
            # self.right = int(padding_dict.get('right', 0))
            # self.bottom = int(padding_dict.get('bottom', 0))
            # self.left = int(padding_dict.get('left', 0))
            self.top = 1
            self.right = 2
            self.bottom = 0
            self.left = 2
        else:
            self.top = 1
            self.right = 2
            self.bottom = 0
            self.left = 2


    ''' string representation
    '''
    def table_cell_attributes(self):
        attributes = {}

        attributes['paddingtop'] = f"{self.top}pt"
        attributes['paddingright'] = f"{self.right}pt"
        attributes['paddingbottom'] = f"{self.bottom}pt"
        attributes['paddingleft'] = f"{self.left}pt"

        return attributes



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


    ''' generates the odt code
    '''
    def text_attributes(self, text):
        return {'text': text[self.start_index:], 'text-attributes': self.format.text_attributes()}



''' gsheet cell notes object wrapper
    TODO: handle keep-with-previous defined in notes
'''
class CellNote(object):

    ''' constructor
    '''
    def __init__(self, note_json=None):
        self.out_of_table = False
        self.table_spacing = True
        self.page_number = False
        self.header_rows = 0

        self.style = None
        self.new_page = False
        self.keep_with_next = False
        self.keep_with_previous = False

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
            self.keep_with_previous = note_dict.get('keep-with-previous') is not None
            self.page_number = note_dict.get('page-number') is not None


    ''' style attributes dict to create Style
    '''
    def style_attributes(self):
        attributes = {}

        if self.style is not None:
            attributes['parentstylename'] = self.style

        return attributes


    ''' paragraph attrubutes dict to craete ParagraphProperties
    '''
    def paragraph_attributes(self):
        attributes = {}

        if self.new_page:
            attributes['breakbefore'] = 'page'

        if self.keep_with_next:
            attributes['keepwithnext'] = 'always'

        return attributes



''' gsheet vertical alignment object wrapper
'''
class VerticalAlignment(object):

    ''' constructor
    '''
    def __init__(self, valign=None):
        if valign:
            self.valign = TEXT_VALIGN_MAP.get(valign, 'top')
        else:
            self.valign = TEXT_VALIGN_MAP.get('TOP')



''' gsheet horizontal alignment object wrapper
'''
class HorizontalAlignment(object):

    ''' constructor
    '''
    def __init__(self, halign=None):
        if halign:
            self.halign = TEXT_HALIGN_MAP.get(halign, 'left')
        else:
            self.halign = TEXT_HALIGN_MAP.get('LEFT')



''' gsheet wrapping object wrapper
'''
class Wrapping(object):

    ''' constructor
    '''
    def __init__(self, wrap=None):
        if wrap:
            self.wrapping = WRAP_STRATEGY_MAP.get(wrap, 'WRAP')
        else:
            self.wrapping = WRAP_STRATEGY_MAP.get('WRAP')



''' Helper for cell span specification
'''
class MultiSpan(object):
    No = 'No'
    FirstCell = 'FirstCell'
    InnerCell = 'InnerCell'
    LastCell = 'LastCell'