#!/usr/bin/env python3

'''
various utilities for rendering json content into a pandoc, mostly for Formatter of type Table
'''

import json
import time
import pprint

from lxml import etree

from helper.logger import *
from helper.pandoc.pandoc_util import *

VALIGN = {'TOP': 'p', 'MIDDLE': 'm', 'BOTTOM': 'b'}
HALIGN = {'LEFT': '\\raggedright', 'CENTER': '\centering', 'RIGHT': '\\raggedleft', 'JUSTIFY': ''}

''' given a gsheet sections->contents generates the latex code
'''
def section_to_latex(data, container_width, repeat_rows=0):

    debug('.. inserting contents')

    start_row, start_col = data['sheets'][0]['data'][0]['startRow'], data['sheets'][0]['data'][0]['startColumn']
    worksheet_rows = data['sheets'][0]['properties']['gridProperties']['rowCount']
    worksheet_cols = data['sheets'][0]['properties']['gridProperties']['columnCount']
    row_data = data['sheets'][0]['data'][0]['rowData']

    # we have a concept of in-cell content and out-of-cell content
    # in-cell content means the content will go inside an existing table cell (specified by a 'content' key with value anything but 'out-of-cell' or no 'content' key at all in 'notes')
    # out-of-cell content means the content will be inserted as a new table directly in the doc (specified by a 'content' key with value 'out-of-cell' in 'notes')

    # when there is an out-of-cell content, we need to put the content inside the document by getting out of any table cell if we are already inside any cell
    # this means we need to look into the first column of each row and identify if we have an out-of-cell content
    # if we have such a content, anything prior to this content will go in one table, the out-of-cell content will go into the document and subsequent cells will go into another table after the put-of-cell content
    # we basically need content segmentation/segrefation into parts


    out_of_cell_content_rows = []
    # we are looking for out-of-cell content
    for row_num in range(start_row + 1, worksheet_rows + 1):
        # we look only in the first column
        # debug('at row : {0}/{1}'.format(row_num, worksheet_rows))
        row_data_index = row_num - start_row - 1
        # debug('at row index: {0}'.format(row_data_index))

        # TODO: it may be that the full row is merged and may not have any value
        if 'values' not in row_data[row_data_index]:
            continue

        # get the first cell notes
        first_cell_data = row_data[row_data_index]['values'][0]
        first_cell_note_json = {}
        if 'note' in first_cell_data:
            try:
                first_cell_note_json = json.loads(first_cell_data['note'])
            except json.JSONDecodeError:
                pass

        # see the 'content' tag
        out_of_cell_content = False
        if 'content' in first_cell_note_json:
            if first_cell_note_json['content'] == 'out-of-cell':
                out_of_cell_content = True

        # if content is out of cell, mark the row
        if out_of_cell_content:
            out_of_cell_content_rows.append(row_num)

    # we have found all rows which are to be rendered out-of-cell that is directly into the doc, not inside any existing table cell
    # now we have to segment the rows into table segments and out-of-cell segments
    start_at_row = start_row + 1
    row_segments = []
    for row_num in out_of_cell_content_rows:
        if row_num > start_at_row:
            row_segments.append({'table': (start_at_row, row_num - 1)})

        row_segments.append({'no-table': (row_num, row_num)})
        start_at_row = row_num + 1

    # there may be trailing rows after the last out-of-cell content row, they will merge into a table
    if start_at_row <= worksheet_rows:
        row_segments.append({'table': (start_at_row, worksheet_rows)})

    # we have got the segments, now we render them - if table, we render as table, if no-table, we render into the doc
    segment_count = 0
    for row_segment in row_segments:
        segment_count = segment_count + 1
        if 'table' in row_segment:
            # debug('table segment {0}/{1} : spanning rows [{2}:{3}]'.format(segment_count, len(row_segments), row_segment['table'][0], row_segment['table'][1]))
            content_text = content_text + insert_content_as_table(data=data, start_row=start_row, start_col=start_col, row_from=row_segment['table'][0], row_to=row_segment['table'][1], container_width=container_width, repeat_rows=repeat_rows)
        elif 'no-table' in row_segment:
            # debug('no-table segment {0}/{1} : at row [{2}]'.format(segment_count, len(row_segments), row_segment['no-table'][0]))
            content_text = content_text + insert_content_into_doc(data=data, start_row=start_row, row_from=row_segment['no-table'][0], container_width=container_width)
        else:
            warn('something unsual happened - unknown row segment type')

    return content_text


''' given a gsheet sections->contents generates the latex code
'''
def insert_content(data, container_width, repeat_rows=0):
    content_text = ''

    debug('.. inserting contents')

    start_row, start_col = data['sheets'][0]['data'][0]['startRow'], data['sheets'][0]['data'][0]['startColumn']
    worksheet_rows = data['sheets'][0]['properties']['gridProperties']['rowCount']
    worksheet_cols = data['sheets'][0]['properties']['gridProperties']['columnCount']
    row_data = data['sheets'][0]['data'][0]['rowData']

    # we have a concept of in-cell content and out-of-cell content
    # in-cell content means the content will go inside an existing table cell (specified by a 'content' key with value anything but 'out-of-cell' or no 'content' key at all in 'notes')
    # out-of-cell content means the content will be inserted as a new table directly in the doc (specified by a 'content' key with value 'out-of-cell' in 'notes')

    # when there is an out-of-cell content, we need to put the content inside the document by getting out of any table cell if we are already inside any cell
    # this means we need to look into the first column of each row and identify if we have an out-of-cell content
    # if we have such a content, anything prior to this content will go in one table, the out-of-cell content will go into the document and subsequent cells will go into another table after the put-of-cell content
    # we basically need content segmentation/segrefation into parts


    out_of_cell_content_rows = []
    # we are looking for out-of-cell content
    for row_num in range(start_row + 1, worksheet_rows + 1):
        # we look only in the first column
        # debug('at row : {0}/{1}'.format(row_num, worksheet_rows))
        row_data_index = row_num - start_row - 1
        # debug('at row index: {0}'.format(row_data_index))

        # TODO: it may be that the full row is merged and may not have any value
        if 'values' not in row_data[row_data_index]:
            continue

        # get the first cell notes
        first_cell_data = row_data[row_data_index]['values'][0]
        first_cell_note_json = {}
        if 'note' in first_cell_data:
            try:
                first_cell_note_json = json.loads(first_cell_data['note'])
            except json.JSONDecodeError:
                pass

        # see the 'content' tag
        out_of_cell_content = False
        if 'content' in first_cell_note_json:
            if first_cell_note_json['content'] == 'out-of-cell':
                out_of_cell_content = True

        # if content is out of cell, mark the row
        if out_of_cell_content:
            out_of_cell_content_rows.append(row_num)

    # we have found all rows which are to be rendered out-of-cell that is directly into the doc, not inside any existing table cell
    # now we have to segment the rows into table segments and out-of-cell segments
    start_at_row = start_row + 1
    row_segments = []
    for row_num in out_of_cell_content_rows:
        if row_num > start_at_row:
            row_segments.append({'table': (start_at_row, row_num - 1)})

        row_segments.append({'no-table': (row_num, row_num)})
        start_at_row = row_num + 1

    # there may be trailing rows after the last out-of-cell content row, they will merge into a table
    if start_at_row <= worksheet_rows:
        row_segments.append({'table': (start_at_row, worksheet_rows)})

    # we have got the segments, now we render them - if table, we render as table, if no-table, we render into the doc
    segment_count = 0
    for row_segment in row_segments:
        segment_count = segment_count + 1
        if 'table' in row_segment:
            # debug('table segment {0}/{1} : spanning rows [{2}:{3}]'.format(segment_count, len(row_segments), row_segment['table'][0], row_segment['table'][1]))
            content_text = content_text + insert_content_as_table(data=data, start_row=start_row, start_col=start_col, row_from=row_segment['table'][0], row_to=row_segment['table'][1], container_width=container_width, repeat_rows=repeat_rows)
        elif 'no-table' in row_segment:
            # debug('no-table segment {0}/{1} : at row [{2}]'.format(segment_count, len(row_segments), row_segment['no-table'][0]))
            content_text = content_text + insert_content_into_doc(data=data, start_row=start_row, row_from=row_segment['no-table'][0], container_width=container_width)
        else:
            warn('something unsual happened - unknown row segment type')

    return content_text


def insert_content_as_table(data, start_row, start_col, row_from, row_to, container_width, repeat_rows=0):
    content_text = ''

    start_time = int(round(time.time() * 1000))
    current_time = int(round(time.time() * 1000))
    last_time = current_time

    # calculate table dimension
    table_rows = row_to - row_from + 1
    table_cols = data['sheets'][0]['properties']['gridProperties']['columnCount'] - start_col

    merge_data = {}
    if 'merges' in data['sheets'][0]:
        merge_data = data['sheets'][0]['merges']

    # create the table
    # table = container.add_table(table_rows, table_cols, Pt(container_width))

    # resize columns as per data
    column_data = data['sheets'][0]['data'][0]['columnMetadata']
    total_width = sum(x['pixelSize'] for x in column_data)

    # column width needs adjustment as \tabcolsep is 0.04in. This means each column has a 0.04 inch on left and right as space which needs to be removed from column width
    column_widths = [ (x['pixelSize'] * container_width / total_width) - (0.04 * 2) for x in column_data ]

    # start a longtable with the sepecic column_widths
    content_text = content_text + start_table(column_widths)

    # TODO: if the table had too many columns, use a style where there is smaller left, right margin
    if len(column_widths) > 10:
        pass

    last_time = current_time

    # populate cells
    # total_rows = len(data['sheets'][0]['data'][0]['rowData'])
    total_rows = table_rows
    i = 0
    current_time = int(round(time.time() * 1000))
    info('  .. rendering {0} rows'.format(total_rows))
    last_time = current_time

    # TODO: handle table related instructions from notes. table related instructions are given as notes in the very first cell (row 0, col 0). they may be
    # table-style - to apply style to whole table (NOT IMPLEMENTED YET)
    # table-spacing - no-spacing means cell paragraphs must not have any spacing throughout the table, useful for source code rendering
    # table-header-rows - number of header rows to repeat across pages (NOT IMPLEMENTED YET)

    row_data = data['sheets'][0]['data'][0]['rowData']

    # get the first cell notes
    # if there is a note, see if it is a JSON, it may contain table specific styling directives
    first_cell_data = row_data[row_from - (start_row + 1)]['values'][0]
    first_cell_note_json = {}
    if 'note' in first_cell_data:
        try:
            first_cell_note_json = json.loads(first_cell_data['note'])
        except json.JSONDecodeError:
            pass

    # handle table-spacing in notes, if the value is no-spacing then all cell paragraphs must have no spacing
    if 'table-spacing' in first_cell_note_json:
        table_spacing = first_cell_note_json['table-spacing']
    else:
        table_spacing = ''

    repeating_row_count = 0
    # handle repeat-rows directive. The value is an integer telling us how many rows (from the first row) should be repeated in pages for this table
    if 'repeat-rows' in first_cell_note_json:
        repeating_row_count = int(first_cell_note_json['repeat-rows'])
    else:
        repeating_row_count = 0

    table_row_index = 0
    for data_row_index in range(row_from - (start_row + 1), row_to - (start_row + 0)):
        if 'values' in row_data[data_row_index]:
            row_values = row_data[data_row_index]['values']

            # we need two lists for holding the top and bottom borders for cells so that we can put them before the cell content and after the cell content
            top_borders, bottom_borders = [], []

            # start a table row
            content_text = content_text + start_table_row()

            cells_latex = ''
            for c in range(0, len(row_values)):
                cell_latex, top_border_latex, bottom_border_latex = cell_latex_elements(row_values[c], column_widths[c], data_row_index, c, start_row, start_col, merge_data, column_widths, table_spacing)
                cells_latex = cells_latex + cell_latex
                top_borders.append(top_border_latex)
                bottom_borders.append(bottom_border_latex)

            # now we have the borders
            top_borders_latex = '\hhline{{ {} }}'.format(' '.join(top_borders))
            bottom_borders_latex = '\hhline{{ {} }}'.format(' '.join(bottom_borders))

            content_text = content_text + top_borders_latex + '\n' + cells_latex

            # end a table row
            content_text = content_text + end_table_row()

            # only then put the bottom border
            content_text = content_text + bottom_borders_latex + '\n\n'

            # mark as header row if it is a header row
            if table_row_index < repeating_row_count:
                content_text = content_text + mark_as_header_row()

            if table_row_index % 100 == 0:
                current_time = int(round(time.time() * 1000))
                info('  .... cell rendered for {0}/{1} rows : {2} ms'.format(table_row_index, total_rows, current_time - last_time))
                last_time = current_time

        table_row_index = table_row_index + 1

    current_time = int(round(time.time() * 1000))
    container: info('  .. rendering cell complete for {0} rows : {1} ms\n'.format(total_rows, current_time - start_time))
    last_time = current_time

    content_text = content_text + end_table()

    info('.. content insertion completed : {0} ms\n'.format(current_time - start_time))

    return content_text


def insert_content_into_doc(data, start_row, row_from, container_width):
    content_text = ''

    # the content is by default one row content and we are only interested in the first column value
    row_data = data['sheets'][0]['data'][0]['rowData']
    first_cell_data = row_data[row_from - (start_row + 1)]['values'][0]

    # thre may be two cases
    # the value may have a 'contents' object in which case we call insert_content
    if 'contents' in first_cell_data:
        content_text = content_text + insert_content(first_cell_data['contents'], container_width)

    # or it may be anything else
    else:
        content_text = content_text + render_content_in_doc(first_cell_data)

    return content_text


def cell_latex_elements(cell_data, width, r, c, start_row, start_col, merge_data, column_widths, table_spacing):
    cell_latex, top_border_latex, bottom_border_latex = '', '', ''

    # paragraph spacing
    if table_spacing == 'no-spacing':
        # pf = paragraph.paragraph_format
        # pf.line_spacing = 1.0
        # pf.space_before = Pt(0)
        # pf.space_after = Pt(0)
        pass

    # handle the notes first
    # if there is a note, see if it is a JSON, it may contain style, page-numering, new-page, keep-with-next directive etc.
    note_json = {}
    if 'note' in cell_data:
        try:
            note_json = json.loads(cell_data['note'])
        except json.JSONDecodeError:
            pass

    # process new-page
    if 'new-page' in note_json:
        cell_latex = cell_latex + new_page()

    # process keep-with-next
    if 'keep-with-next' in note_json:
        pass

    # do some special processing if the cell_data is {}
    if cell_data == {} or 'effectiveFormat' not in cell_data:
        return cell_latex, top_border_latex, bottom_border_latex

    text_format = cell_data['effectiveFormat']['textFormat']
    effective_format = cell_data['effectiveFormat']

    # alignments
    if 'verticalAlignment' in effective_format:
        vertical_alignment = VALIGN[effective_format['verticalAlignment']]
    else:
        vertical_alignment = VALIGN['MIDDLE']

    if 'horizontalAlignment' in effective_format:
        horizontal_alignment = HALIGN[effective_format['horizontalAlignment']]
    else:
        horizontal_alignment = HALIGN['LEFT']

    # background color
    bgcolor = cell_bgcolor(effective_format['backgroundColor'])

    # text-rotation
    if 'textRotation' in effective_format:
        text_rotation = effective_format['textRotation']
        # rotate_text(cell, 'btLr')

    # cell can be merged, so we need width after merge (in Inches) and spans
    cell_width, column_span, row_span = merged_cell_span(r, c, start_row, start_col, merge_data, column_widths)

    # borders
    if 'borders' in effective_format:
        left_border = latex_border_from_gsheet_border(effective_format['borders'], 'left')
        right_border = latex_border_from_gsheet_border(effective_format['borders'], 'right')
        top_border = latex_border_from_gsheet_border(effective_format['borders'], 'top').replace('{}', str(column_span))
        bottom_border = latex_border_from_gsheet_border(effective_format['borders'], 'bottom').replace('{}', str(column_span))
    else:
        left_border, right_border, top_border, bottom_border = '', '', '*{{{}}}{{~}}'.format(column_span), '*{{{}}}{{~}}'.format(column_span)

    # TODO: images
    if 'userEnteredValue' in cell_data:
        userEnteredValue = cell_data['userEnteredValue']
        if 'image' in userEnteredValue:
            image = userEnteredValue['image']

            # even now the width may exceed actual cell width, we need to adjust for that
            dpi_x = 150 if image['dpi'][0] == 0 else image['dpi'][0]
            dpi_y = 150 if image['dpi'][1] == 0 else image['dpi'][1]
            image_width = image['width'] / dpi_x
            image_height = image['height'] / dpi_y
            if image_width > cell_width:
                adjust_ratio = (cell_width / image_width)
                # keep a padding of 0.1 inch
                image_width = cell_width - 0.2
                image_height = image_height * adjust_ratio

            # TODO: cell_latex may have prior content, merge
            cell_latex_fragment, top_border_latex, bottom_border_latex = image_content(path=image['path'], image_width=image_width, image_height=image_height, bgcolor=bgcolor, left_border=left_border, right_border=right_border, top_border=top_border, bottom_border=bottom_border, halign=horizontal_alignment, valign=vertical_alignment, cell_width=cell_width, column_number=c, column_span=column_span, row_span=row_span)
            cell_latex = cell_latex + cell_latex_fragment
            return cell_latex, top_border_latex, bottom_border_latex

    # TODO: before rendering cell, see if it embeds another worksheet
    if 'contents' in cell_data:
        table = insert_content(cell_data['contents'], doc, cell_width, container=None, cell=cell)
        # polish_table(table)
        return cell_latex, top_border_latex, bottom_border_latex

    # texts
    if 'formattedValue' in cell_data:
        text = cell_data['formattedValue']
    else:
        text = ''


    # process notes
    # TODO: note specifies style
    if 'style' in note_json:
        pass

    # TODO: note specifies page numbering
    if 'page-number' in note_json:
        pass

    # TODO: finally cell content, add runs
    if 'textFormatRuns' in cell_data:
        text_runs = cell_data['textFormatRuns']
        # split the text into run-texts
        run_texts = []
        for i in range(len(text_runs) - 1, -1, -1):
            text_run = text_runs[i]
            if 'startIndex' in text_run:
                run_texts.insert(0, text[text_run['startIndex']:])
                text = text[:text_run['startIndex']]
            else:
                run_texts.insert(0, text)

        # now render runs
        for i in range(0, len(text_runs)):
            # get formatting
            format = text_runs[i]['format']

            run = paragraph.add_run(run_texts[i])
            set_character_style(run, {**text_format, **format})
    else:
        # TODO: cell_latex may have prior content, merge
        cell_latex_fragment, top_border_latex, bottom_border_latex = text_content(text=text, bgcolor=bgcolor, left_border=left_border, right_border=right_border, top_border=top_border, bottom_border=bottom_border, halign=horizontal_alignment, valign=vertical_alignment, cell_width=cell_width, column_number=c, column_span=column_span, row_span=row_span)
        cell_latex = cell_latex + cell_latex_fragment

    return cell_latex, top_border_latex, bottom_border_latex


def render_content_in_doc(cell_data):
    content_text = ''

    # handle the notes first
    # if there is a note, see if it is a JSON, it may contain style, page-numering, new-page, keep-with-next directive etc.
    note_json = {}
    if 'note' in cell_data:
        try:
            note_json = json.loads(cell_data['note'])
        except json.JSONDecodeError:
            pass

    # process new-page
    if 'new-page' in note_json:
        content_text = content_text + new_page()

    # process keep-with-next
    if 'keep-with-next' in note_json:
        pass

    # do some special processing if the cell_data is {}
    if cell_data == {} or 'effectiveFormat' not in cell_data:
        return content_text

    text_format = cell_data['effectiveFormat']['textFormat']
    effective_format = cell_data['effectiveFormat']

    # alignments
    # cell.vertical_alignment = VALIGN[effective_format['verticalAlignment']]
    if 'horizontalAlignment' in effective_format:
        pass

    # borders
    if 'borders' in cell_data['effectiveFormat']:
        borders = cell_data['effectiveFormat']['borders']
        # set_paragraph_border(paragraph, top=ooxml_border_from_gsheet_border(borders, 'top'), bottom=ooxml_border_from_gsheet_border(borders, 'bottom'), start=ooxml_border_from_gsheet_border(borders, 'left'), end=ooxml_border_from_gsheet_border(borders, 'right'))

    # background color
    bgcolor = cell_data['effectiveFormat']['backgroundColor']
    if bgcolor != {}:
        red = int(bgcolor['red'] * 255) if 'red' in bgcolor else 0
        green = int(bgcolor['green'] * 255) if 'green' in bgcolor else 0
        blue = int(bgcolor['blue'] * 255) if 'blue' in bgcolor else 0
        # set_paragraph_bgcolor(paragraph, RGBColor(red, green, blue))

    # images
    if 'userEnteredValue' in cell_data:
        userEnteredValue = cell_data['userEnteredValue']
        if 'image' in userEnteredValue:
            image = userEnteredValue['image']
            # run = paragraph.add_run()

            # even now the width may exceed actual cell width, we need to adjust for that
            # determine cell_width based on merge scenario
            dpi_x = 150 if image['dpi'][0] == 0 else image['dpi'][0]
            dpi_y = 150 if image['dpi'][1] == 0 else image['dpi'][1]
            image_width = image['width'] / dpi_x
            image_height = image['height'] / dpi_y
            if image_width > cell_width:
                adjust_ratio = (cell_width / image_width)
                # keep a padding of 0.1 inch
                image_width = cell_width - 0.2
                image_height = image_height * adjust_ratio

            # run.add_picture(image['path'], height=Inches(image_height), width=Inches(image_width))

    # before rendering cell, see if it embeds another worksheet
    if 'contents' in cell_data:
        content_text = content_text + insert_content(cell_data['contents'], cell_width)
        return content_text

    # texts
    if 'formattedValue' not in cell_data:
        return content_text

    text = cell_data['formattedValue']

    # process notes
    # note specifies style
    if 'style' in note_json:
        return content_text

    # note specifies page numbering
    if 'page-number' in note_json:
        # append_page_number_with_pages(paragraph)
        # append_page_number_only(paragraph)
        return content_text

    # finally cell content, add runs
    if 'textFormatRuns' in cell_data:
        text_runs = cell_data['textFormatRuns']
        # split the text into run-texts
        run_texts = []
        for i in range(len(text_runs) - 1, -1, -1):
            text_run = text_runs[i]
            if 'startIndex' in text_run:
                run_texts.insert(0, text[text_run['startIndex']:])
                text = text[:text_run['startIndex']]
            else:
                run_texts.insert(0, text)

        # now render runs
        for i in range(0, len(text_runs)):
            # get formatting
            format = text_runs[i]['format']

            # run = paragraph.add_run(run_texts[i])
            # set_character_style(run, {**text_format, **format})
    else:
        # run = paragraph.add_run(text)
        # set_character_style(run, text_format)
        pass

    return content_text


def set_header(doc, section, header_first, header_odd, header_even, actual_width, linked_to_previous=False):
    first_page_header = section.first_page_header
    odd_page_header = section.header
    even_page_header = section.even_page_header

    section.first_page_header.is_linked_to_previous = linked_to_previous
    section.header.is_linked_to_previous = linked_to_previous
    section.even_page_header.is_linked_to_previous = linked_to_previous

    if len(first_page_header.tables) == 0:
        if header_first is not None: insert_content(header_first, doc, actual_width, container=first_page_header, cell=None)

    if len(odd_page_header.tables) == 0:
        if header_odd is not None: insert_content(header_odd, doc, actual_width, container=odd_page_header, cell=None)

    if len(even_page_header.tables) == 0:
        if header_even is not None: insert_content(header_even, doc, actual_width, container=even_page_header, cell=None)


def set_footer(doc, section, footer_first, footer_odd, footer_even, actual_width, linked_to_previous=False):
    first_page_footer = section.first_page_footer
    odd_page_footer = section.footer
    even_page_footer = section.even_page_footer

    section.first_page_footer.is_linked_to_previous = linked_to_previous
    section.footer.is_linked_to_previous = linked_to_previous
    section.even_page_footer.is_linked_to_previous = linked_to_previous

    if len(first_page_footer.tables) == 0:
        if footer_first is not None: insert_content(footer_first, doc, actual_width, container=first_page_footer, cell=None)

    if len(odd_page_footer.tables) == 0:
        if footer_odd is not None: insert_content(footer_odd, doc, actual_width, container=odd_page_footer, cell=None)

    if len(even_page_footer.tables) == 0:
        if footer_even is not None: insert_content(footer_even, doc, actual_width, container=even_page_footer, cell=None)
