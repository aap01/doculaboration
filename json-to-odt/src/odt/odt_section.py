#!/usr/bin/env python3

import json
from odt.odt_cell import *
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

        self.section_contents = OdtContent(section_data.get('contents'), self.section_width, self.section_index)


    ''' Header/Footer processing
    '''
    def process_header_footer(self, odt, master_page, page_layout):
        if self._section_data['header-odd']:
            self.header_odd.to_odt(odt, master_page, page_layout)

        if self._section_data['header-first']:
            self.header_first.to_odt(odt, master_page, page_layout)

        if self._section_data['header-even']:
            self.header_even.to_odt(odt, master_page, page_layout)

        if self._section_data['footer-odd']:
            self.footer_odd.to_odt(odt, master_page, page_layout)

        if self._section_data['footer-first']:
            self.footer_first.to_odt(odt, master_page, page_layout)

        if self._section_data['footer-even']:
            self.footer_even.to_odt(odt, master_page, page_layout)


    ''' generates the odt code
    '''
    def to_odt(self, odt):
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

        return paragraph



''' Odt table section object
'''
class OdtTableSection(OdtSectionBase):

    ''' constructor
    '''
    def __init__(self, section_data, config):
        super().__init__(section_data, config)


    ''' generates the odt code
    '''
    def to_odt(self, odt):
        super().to_odt(odt)
        self.section_contents.to_odt(odt)



''' Odt ToC section object
'''
class OdtToCSection(OdtSectionBase):

    ''' constructor
    '''
    def __init__(self, section_data, config):
        super().__init__(section_data, config)


    ''' generates the odt code
    '''
    def to_odt(self, odt):
        super().to_odt(odt)
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
    def to_odt(self, odt):
        super().to_odt(odt)
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
    def to_odt(self, odt):
        super().to_odt(odt)
        toc = create_lof()
        if toc:
            odt.text.addElement(toc)



''' Odt section content base object
'''
class OdtContent(object):

    ''' constructor
    '''
    def __init__(self, content_data, section_width, section_index):
        self.content_data = content_data
        self.section_width = section_width
        self.section_index = section_index
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
                    self.column_widths = [ (x.pixel_size * self.section_width / all_column_widths_in_pixel) for x in self.column_metadata_list ]

                    # rowData
                    r = 0
                    for row_data in data.get('rowData', []):
                        # self.cell_matrix.append(Row(r, row_data, self.default_format, self.section_width, self.column_widths, self.row_metadata_list[r].inches))
                        self.cell_matrix.append(Row(r, row_data, self.section_width, self.column_widths, self.row_metadata_list[r].inches))
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
                        # next_cell_in_row.copy_format_from(first_cell)

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
    '''
    def to_odt(self, odt):
        # iterate through tables and blocks contents
        for block in self.content_list:
            odt_element = block.to_odt(odt)
            if odt_element:
                odt.text.addElement(odt_element)



''' Odt Page Header Footer object
'''
class OdtPageHeaderFooter(OdtContent):

    ''' constructor
        header_footer : header/footer
        odd_even      : first/odd/even(left)
    '''
    def __init__(self, content_data, section_width, section_index, header_footer, odd_even):
        super().__init__(content_data, section_width, section_index)
        self.header_footer, self.odd_even = header_footer, odd_even
        self.id = f"{self.header_footer}{self.odd_even}{section_index}"


    ''' generates the odt code
    '''
    def to_odt(self, odt, master_page, page_layout):
        if self.content_data is None:
            return

        header_footer_style = create_header_footer(master_page, page_layout, self.header_footer, self.odd_even)
        if header_footer_style:
            # iterate through tables and blocks contents
            first_block = True
            for block in self.content_list:
                odt_element = block.to_odt(odt)
                if odt_element:
                    header_footer_style.addElement(odt_element)

                first_block = False



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
    def to_odt(self, odt):
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

        table_header_rows = create_table_header_rows()
        # iteraate header rows render the table's contents
        for row in self.table_cell_matrix[0:self.header_row_count]:
            table_row = row.to_table_row(odt, self.table_name)
            table_header_rows.addElement(table_row)

        table.addElement(table_header_rows)

        # iteraate rows and cells to render the table's contents
        for row in self.table_cell_matrix[self.header_row_count:]:
            table_row = row.to_table_row(odt, self.table_name)
            table.addElement(table_row)

        return table



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
    def to_odt(self, odt):
        # generate the block, only the first cell of the data_row to be produced
        if len(self.data_row.cells) > 0:
            # We take the first cell, the cell will take the whole row width
            cell_to_produce = self.data_row.get_cell(0)
            cell_to_produce.cell_width = sum(cell_to_produce.column_widths)

            paragraph, image = cell_to_produce.to_paragraph(odt, for_table_cell=False)
            if image:
                picture_path = image['image']
                width = image['width']
                height = image['height']

                draw_frame = create_image_frame(odt, picture_path, IMAGE_POSITION[cell_to_produce.effective_format.valign.valign], IMAGE_POSITION[cell_to_produce.effective_format.halign.halign], width, height)
                paragraph.addElement(draw_frame)

            return paragraph

        return None
