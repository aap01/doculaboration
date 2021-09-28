#!/usr/bin/env python3

from helper.logger import *
from helper.latex.latex_helper import LatexToCSection

def generate(section_data, section_specs, context):
    if section_data['section'] != '':
        debug(f"Writing ... {section_data['section'].strip()} {section_data['heading'].strip()}")
    else:
        debug(f"Writing ... {section_data['heading'].strip()}")

    if section_data['section-break'] == '-':
        section_data['section-break'] = 'continuous_portrait'

    # it is a new section
    latex_section = LatexToCSection(section_data, section_specs[section_data['section-break']])

    # TODO: for now we just get the latex code for the section, we need to wrap this into a latex document object and append to that document
    return latex_section.to_latex()
