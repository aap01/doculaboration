#!/usr/bin/env python3

'''
various utilities for formatting a docx
'''

import lxml

from copy import deepcopy

from helper.logger import *

GSHEET_OXML_BORDER_MAPPING = {
    'DOTTED': 'dotted',
    'DASHED': 'dashed',
    'SOLID': 'single',
    'SOLID_MEDIUM': 'thick',
    'SOLID_THICK': 'triple',
    'DOUBLE': 'double',
    'NONE': 'none'
}


'''
Table of Contents
'''
def add_toc(doc):
    pass


'''
List of Figures
'''
def add_lof(doc):
    pass


'''
List of Tables
'''
def add_lot(doc):
    pass


def add_horizontal_line(paragraph, pos='w:bottom', size='6', color='auto'):
    pass


def append_page_number_only(paragraph):
    pass


def append_page_number_with_pages(paragraph, separator=' of '):
    pass


def rotate_text(cell, direction: str):
    pass


def set_character_style(run, spec):
    pass


def set_cell_bgcolor(cell, color):
    pass


def set_paragraph_bgcolor(paragraph, color):
    pass


def copy_cell_border(from_cell, to_cell):
    pass


def set_cell_border(cell, **kwargs):
    """
    Set cell's border
    Usage:

    set_cell_border(
        cell,
        top={"sz": 12, "val": "single", "color": "#FF0000", "space": "0"},
        bottom={"sz": 12, "color": "#00FF00", "val": "single"},
        start={"sz": 24, "val": "dashed", "shadow": "true"},
        end={"sz": 12, "val": "dashed"},
    )
    """
    pass


def set_paragraph_border(paragraph, **kwargs):
    """
    Set paragraph's border
    Usage:

    set_paragraph_border(
        paragraph,
        top={"sz": 12, "val": "single", "color": "#FF0000", "space": "0"},
        bottom={"sz": 12, "color": "#00FF00", "val": "single"},
        start={"sz": 24, "val": "dashed", "shadow": "true"},
        end={"sz": 12, "val": "dashed"},
    )
    """
    pass


def ooxml_border_from_gsheet_border(borders, key):
    if key in borders:
        border = borders[key]
        red = int(border['color']['red'] * 255) if 'red' in border['color'] else 0
        green = int(border['color']['green'] * 255) if 'green' in border['color'] else 0
        blue = int(border['color']['blue'] * 255) if 'blue' in border['color'] else 0
        color = '{0:02x}{1:02x}{2:02x}'.format(red, green, blue)
        if 'style' in border:
            border_style = border['style']
        else:
            border_style = 'NONE'

        return {"sz": border['width'] * 8, "val": GSHEET_OXML_BORDER_MAPPING[border_style], "color": color, "space": "0"}
    else:
        return None


def insert_image(cell, image_spec):
    '''
        image_spec is like {'url': url, 'path': local_path, 'height': height, 'width': width, 'dpi': im_dpi}
    '''
    if image_spec is not None:
        pass


def set_repeat_table_header(row):
    ''' set repeat table row on every new page
    '''
    return None


def start_table(column_sizes):
    str = '''```{=latex}
\setlength\parindent{0pt}
'''

    s = ['p{{{0}in}}'.format(i) for i in column_sizes]
    table_str = '\\begin{{longtable}}[l]{{|{0}|}}'.format('|'.join(s))

    return str + table_str + '\n'


def end_table():
    s = '''\end{longtable}
```

'''

    return s


def table_header():
    header = '''\hline
\centering\\textbf{\#}
& \\raggedright\\textbf{Name of Employee}
& \\raggedright\\textbf{Saving A/C No}
& \\raggedleft\\textbf{Net Pay in BDT}
\TBstrut
\\tabularnewline \hline
\endhead

'''

    return header


def start_table_row():
    s = '''\TBstrut
'''
    return s 


def end_table_row():
    s = '''\\tabularnewline \hline
'''
    return s 
    

def mark_as_header_row():
    s = '''\endhead
'''
    return s 
    

def text_content(text, halign, column_number=0):
    s = '{0}{1} {2}\n'.format('& ' if column_number else '', halign, text)

    return s
