###############################################################################
##
## Copyright (C) 2014-2015, New York University.
## Copyright (C) 2013-2014, NYU-Poly.
## All rights reserved.
## Contact: contact@vistrails.org
##
## This file is part of VisTrails.
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are met:
##
##  - Redistributions of source code must retain the above copyright notice,
##    this list of conditions and the following disclaimer.
##  - Redistributions in binary form must reproduce the above copyright
##    notice, this list of conditions and the following disclaimer in the
##    documentation and/or other materials provided with the distribution.
##  - Neither the name of the New York University nor the names of its
##    contributors may be used to endorse or promote products derived from
##    this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
## THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
###############################################################################

from __future__ import division

import datetime
import numpy
import sys
import traceback

from PyQt4 import QtCore, QtGui

from vistrails.core.modules.basic_modules import Boolean, File, Float, \
    Integer, List, String

from dat.packages import Variable, FileVariableLoader, VariableOperation, \
    OperationArgument, OperationWizard, translate, derive_varname, \
    get_variable_value

from convert.convert_dates import TimestampsToDates, StringsToDates, \
    DatesToMatplotlib, TimestampsToMatplotlib, StringsToMatplotlib
from read.read_csv import CSVFile, ExtractColumn
from read.read_numpy import NumPyArray


__all__ = ['_variable_loaders', '_variable_operations']


_ = translate('packages.tabledata')


# Builds a DAT variable from a data file
def build_file_variable(filename, dtype, shape=None):
    var = Variable(type=List)
    # We use the high-level interface to build the variable pipeline
    mod = var.add_module(NumPyArray)
    mod.add_function('file', File, filename)
    mod.add_function('datatype', String, dtype)
    if shape is not None:
        mod.add_function('shape', List, repr(shape))
    # We select the 'value' output port of the NumPyArray module as the
    # port that will be connected to plots when this variable is used
    var.select_output_port(mod, 'value')
    return var


def build_csv_variable(filename, delimiter, header_present, column, numeric):
    var = Variable(type=List)

    csvfile = var.add_module(CSVFile)
    csvfile.add_function('file', File, filename)
    if delimiter is not None:
        csvfile.add_function('delimiter', String, delimiter)
    csvfile.add_function('header_present', Boolean, header_present)

    extract = var.add_module(ExtractColumn)
    csvfile.connect_outputport_to('value', extract, 'table')
    if isinstance(column, (int, long)):
        extract.add_function('column_index', Integer, column)
    else:
        extract.add_function('column_name', String, column)
    extract.add_function('numeric', Boolean, numeric)

    var.select_output_port(extract, 'value')
    return var


########################################
# Defines variable loaders
#

# Loads from a raw binary file
class BinaryArrayLoader(FileVariableLoader):
    """Loads a NumPy array using numpy:fromfile().
    """
    FORMATS = [
            ("%s (%s)" % (_("byte"), 'numpy.int8'),
             'int8'),
            ("%s (%s)" % (_("unsigned byte"), 'numpy.uint8'),
             'uint8'),
            ("%s (%s)" % (_("short"), 'numpy.int16'),
             'int16'),
            ("%s (%s)" % (_("unsigned short"), 'numpy.uint16'),
             'uint16'),
            ("%s (%s)" % (_("32-bit integer"), 'numpy.int32'),
             'int32'),
            ("%s (%s)" % (_("32-bit unsigned integer"), 'numpy.uint32'),
             'uint32'),
            ("%s (%s)" % (_("64-bit integer"), 'numpy.int64'),
             'int64'),
            ("%s (%s)" % (_("64-bit unsigned integer"), 'numpy.uint64'),
             'uint64'),

            ("%s (%s)" % (_("32-bit floating number"), 'numpy.float32'),
             'float32'),
            ("%s (%s)" % (_("64-bit floating number"), 'numpy.float64'),
             'float64'),
            ("%s (%s)" % (_("128-bit floating number"), 'numpy.float128'),
             'float128'),

            ("%s (%s)" % (_("64-bit complex number"), 'numpy.complex64'),
             'complex64'),
            ("%s (%s)" % (_("128-bit complex number"), 'numpy.complex128'),
             'complex128'),
            ("%s (%s)" % (_("256-bit complex number"), 'numpy.complex256'),
             'complex128'),
    ]

    @classmethod
    def can_load(cls, filename):
        return (filename.lower().endswith('.dat') or
                filename.lower().endswith('.ima'))

    def __init__(self, filename):
        FileVariableLoader.__init__(self)
        self.filename = filename
        self._varname = derive_varname(filename, remove_ext=True,
                                       remove_path=True, prefix="nparray_")

        layout = QtGui.QFormLayout()

        self._format_field = QtGui.QComboBox()
        for label, dtype in BinaryArrayLoader.FORMATS:
            self._format_field.addItem(label)
        layout.addRow(_("Data &format:"), self._format_field)

        self._shape = QtGui.QLineEdit()
        layout.addRow(_("&Shape:"), self._shape)
        shape_label = QtGui.QLabel(_("Comma-separated list of dimensions"))
        label_font = shape_label.font()
        label_font.setItalic(True)
        shape_label.setFont(label_font)
        layout.addRow('', shape_label)

        self.setLayout(layout)

    def load(self):
        shape = str(self._shape.text())
        if not shape:
            shape = None
        else:
            shape = [int(d.strip()) for d in shape.split(',')]
        return build_file_variable(
                self.filename,
                BinaryArrayLoader.FORMATS[
                        self._format_field.currentIndex()][1],
                shape)

    def get_default_variable_name(self):
        return self._varname


# Loads from a NPY array
def npy_load(self, filename):
    return build_file_variable(filename, 'npy')


def npy_get_varname(filename):
    return derive_varname(filename, remove_ext=True,
                          remove_path=True, prefix="nparray_")


NPYArrayLoader = FileVariableLoader.simple(
        extension='.npy',
        load=npy_load,
        get_varname=npy_get_varname)


# Loads from a CSV file
class CSVLoader(FileVariableLoader):
    @classmethod
    def can_load(cls, filename):
        return filename.lower().endswith('.csv')

    def __init__(self, filename):
        FileVariableLoader.__init__(self)
        self._filename = filename

        # Defaults
        self._delimiter = None
        self._header_present = True
        self._column_names = None
        self._selected_column = None
        self._varname = derive_varname("csv_data")

        layout = QtGui.QVBoxLayout()
        options = QtGui.QFormLayout()

        # header_present
        self._header_present_checkbox = QtGui.QCheckBox()
        self._header_present_checkbox.setChecked(True)

        def header_present_cb(state):
            self._header_present = state == QtCore.Qt.Checked
            self.read_file()
        self.connect(
                self._header_present_checkbox,
                QtCore.SIGNAL('stateChanged(int)'),
                header_present_cb)
        options.addRow(_("First line has the column names"),
                       self._header_present_checkbox)

        # delimiter, will be initialized on the first call to read_file
        self._delimiter_input = QtGui.QLineEdit()
        self._delimiter_input.setMaxLength(1)
        self._delimiter_input.setSizePolicy(
                QtGui.QSizePolicy.Fixed,
                self._delimiter_input.sizePolicy().verticalPolicy())

        def delimiter_cb(text):
            if len(text) == 1:
                self._delimiter = str(text)
                self.read_file()
            self._delimiter_tab_button.setEnabled(text != '\t')
        self.connect(
                self._delimiter_input,
                QtCore.SIGNAL('textChanged(QString)'),
                delimiter_cb)
        delimiter_right = QtGui.QHBoxLayout()
        delimiter_right.addWidget(self._delimiter_input)
        self._delimiter_tab_button = QtGui.QPushButton("Use tab")
        self.connect(self._delimiter_tab_button, QtCore.SIGNAL('clicked()'),
                     lambda: self._delimiter_input.setText('\t'))
        delimiter_right.addWidget(self._delimiter_tab_button)
        options.addRow(_("Column separator:"), delimiter_right)

        # numeric, checked by default
        self._numeric_checkbox = QtGui.QCheckBox()
        self._numeric_checkbox.setChecked(True)
        options.addRow(_("load as Numpy array:"), self._numeric_checkbox)

        layout.addLayout(options)

        # Range selector
        self._range1 = QtGui.QSpinBox()
        self._range1.setRange(0, sys.maxint)
        self._range2 = QtGui.QSpinBox()
        self._range2.setRange(0, sys.maxint)
        self._range2.setSpecialValueText(_("end"))
        range_layout = QtGui.QHBoxLayout()
        range_layout.addWidget(self._range1)
        range_layout.addStretch()
        range_layout.addWidget(QtGui.QLabel('-'))
        range_layout.addStretch()
        range_layout.addWidget(self._range2)
        options.addRow(_("Range of rows to load:"), range_layout)

        self._table = QtGui.QTableWidget()
        self._table.setSelectionBehavior(QtGui.QTableWidget.SelectColumns)
        self._table.setSelectionMode(QtGui.QTableWidget.SingleSelection)
        self.connect(self._table, QtCore.SIGNAL('itemSelectionChanged()'),
                     self._selection_changed)
        layout.addWidget(self._table)

        self.setLayout(layout)

        self.read_file()

    def read_file(self):
        column_count, self._column_names, self._delimiter = CSVFile.read_file(
                self._filename,
                self._delimiter,
                self._header_present)
        self._delimiter_input.setText(self._delimiter)
        self._table.setColumnCount(column_count)
        self._table.setRowCount(3)
        if self._column_names is not None:
            for col, name in enumerate(self._column_names):
                item = QtGui.QTableWidgetItem(name)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setFlags(QtCore.Qt.ItemIsEnabled |
                              QtCore.Qt.ItemIsSelectable)
                self._table.setItem(0, col, item)
        with open(self._filename, 'rb') as fp:
            if self._header_present:
                fp.readline()
            for row in xrange(1 if self._column_names is not None else 0, 3):
                line = fp.readline()
                line = line.split(self._delimiter)
                for col in xrange(min(column_count, len(line))):
                    item = QtGui.QTableWidgetItem(line[col])
                    item.setFlags(QtCore.Qt.ItemIsEnabled |
                                  QtCore.Qt.ItemIsSelectable)
                    self._table.setItem(row, col, item)

        self._table.clearSelection()

    def _selection_changed(self):
        selected = self._table.selectedRanges()
        if selected:
            selected = selected[0]
            self._selected_column = selected.leftColumn()
            if (self._selected_column > self._table.columnCount() or
                    self._selected_column > len(self._column_names)):
                self._selected_column = None
                self._table.setSelection(QtCore.QRect(),
                                         QtGui.QItemSelectionModel.Clear)
                return
            if self._column_names is not None:
                column = derive_varname(
                        self._column_names[self._selected_column])
            else:
                column = "col%d" % self._selected_column
            self._varname = derive_varname(self._filename, remove_ext=True,
                                           remove_path=True,
                                           suffix='_%s' % column)
            self.default_variable_name_changed(self._varname)
        else:
            self.default_variable_name_changed('csv_data')
            self._selected_column = None

    def load(self):
        if self._selected_column is None:
            QtGui.QMessageBox.warning(
                    self,
                    _("Error"),
                    _("You must select a column to load"))
            return
        if self._header_present:
            column = self._column_names[self._selected_column]
        else:
            column = self._selected_column
        return build_csv_variable(
                self._filename,
                self._delimiter,
                self._header_present,
                column,
                self._numeric_checkbox.isChecked())

    def get_default_variable_name(self):
        return self._varname


_variable_loaders = {
        BinaryArrayLoader: _("Numpy plain binary array"),
        NPYArrayLoader: _("Numpy .NPY format"),
        CSVLoader: _("CSV table")
}


########################################
# Defines variable operations
#

class DateConversionWizard(OperationWizard):
    TIMESTAMP = 0
    MATPLOTLIB = 1
    DATESTRING = 2
    DATETIME = 3

    item_string = [
            _("UNIX timestamps"),
            _("Matplotlib format (days)"),
            _("Date as a string"),
            _("Datetime object"),
        ]

    output_formats = [
            [DATETIME, MATPLOTLIB],
            [],
            [DATETIME, MATPLOTLIB],
            [MATPLOTLIB],
        ]

    def __init__(self, parent):
        self._sample = None
        OperationWizard.__init__(self, parent,
                                 variables=OperationWizard.VAR_SELECT)

    def create_ui(self):
        layout = QtGui.QVBoxLayout()
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel(_("Input format")), 0, 0)
        self._input_format = QtGui.QComboBox()
        self.connect(
                self._input_format,
                QtCore.SIGNAL('currentIndexChanged(int)'),
                self._input_fmt_changed)
        grid.addWidget(self._input_format, 1, 0)
        self._input_sample = QtGui.QTableWidget(0, 1)
        self._input_sample.horizontalHeader().hide()
        grid.addWidget(self._input_sample, 2, 0)

        grid.addWidget(QtGui.QLabel(_("Output format")), 0, 1)
        self._output_format = QtGui.QComboBox()
        self.connect(
                self._output_format,
                QtCore.SIGNAL('currentIndexChanged(int)'),
                self._output_fmt_changed)
        grid.addWidget(self._output_format, 1, 1)
        self._output_sample = QtGui.QTableWidget(0, 1)
        self._output_sample.horizontalHeader().hide()
        grid.addWidget(self._output_sample, 2, 1)

        layout.addLayout(grid)

        params = QtGui.QFormLayout()
        self._format = QtGui.QLineEdit()
        self._format.setPlaceholderText('%Y-%m-%d %H:%M:%S')
        self.connect(
                self._format,
                QtCore.SIGNAL('textChanged(const QString&)'),
                self._output_fmt_changed)
        params.addRow(_("Date format:"), self._format)
        self._timezone = QtGui.QLineEdit()
        self._timezone.setPlaceholderText('UTC')
        self.connect(
                self._timezone,
                QtCore.SIGNAL('textChanged(const QString&)'),
                self._output_fmt_changed)
        params.addRow(_("Timezone:"), self._timezone)

        layout.addLayout(params)

        return layout

    def _input_fmt_changed(self, idx):
        fmt = self._input_format.itemData(idx)

        self._output_format.clear()
        for i, ofmt in enumerate(self.output_formats[fmt]):
            self._output_format.addItem(self.item_string[ofmt], ofmt)
        self._output_fmt_changed(self._output_format.currentIndex())

    def _output_fmt_changed(self, *args):
        self._output_sample.clear()
        idx = self._output_format.currentIndex()
        if idx == -1 or self._sample is None:
            return

        ifmt = self._input_format.itemData(self._input_format.currentIndex())
        ofmt = self._output_format.itemData(idx)

        try:
            if ifmt == self.TIMESTAMP and ofmt == self.DATETIME:
                self._format.setEnabled(False)
                self._timezone.setEnabled(False)
                output = TimestampsToDates.convert(self._sample)
            elif ifmt == self.TIMESTAMP and ofmt == self.MATPLOTLIB:
                self._format.setEnabled(False)
                self._timezone.setEnabled(False)
                output = TimestampsToMatplotlib.convert(self._sample)
            elif ifmt == self.DATESTRING and ofmt == self.DATETIME:
                self._format.setEnabled(True)
                self._timezone.setEnabled(True)
                output = StringsToDates.convert(
                        self._sample,
                        unicode(self._format.text()),
                        unicode(self._timezone.text()))
            elif ifmt == self.DATESTRING and ofmt == self.MATPLOTLIB:
                self._format.setEnabled(True)
                self._timezone.setEnabled(True)
                output = StringsToMatplotlib.convert(
                        self._sample,
                        unicode(self._format.text()),
                        unicode(self._timezone.text()))
            elif ifmt == self.DATETIME and ofmt == self.MATPLOTLIB:
                self._format.setEnabled(False)
                self._timezone.setEnabled(False)
                output = DatesToMatplotlib.convert(self._sample)
            else:
                raise RuntimeError("This line shouldn't be reachable")
        except Exception, e:
            if not isinstance(e, ValueError):
                traceback.print_exc()
            self.set_error(e)
        else:
            self.set_error(None)
            self._output_sample.setRowCount(len(output))
            for row, v in enumerate(output):
                item = QtGui.QTableWidgetItem(unicode(v))
                item.setFlags(QtCore.Qt.ItemIsEnabled)
                self._output_sample.setItem(row, 0, item)

    def make_operation(self, varname):
        ifmt = self._input_format.itemData(self._input_format.currentIndex())
        idx = self._output_format.currentIndex()
        ofmt = self._output_format.itemData(idx)

        new_var = Variable(type=List)
        orig_var = self.get_variable_argument()

        def insert_conv(conv_mod, iport, oport):
            mod = new_var.add_module(conv_mod)
            orig_var.connect_to(mod, iport)
            new_var.select_output_port(mod, oport)
            return mod

        if ifmt == self.TIMESTAMP and ofmt == self.DATETIME:
            insert_conv(TimestampsToDates, 'timestamps', 'dates')
        elif ifmt == self.TIMESTAMP and ofmt == self.MATPLOTLIB:
            insert_conv(TimestampsToMatplotlib, 'timestamps', 'dates')
        elif ifmt == self.DATESTRING and ofmt == self.DATETIME:
            m = insert_conv(StringsToDates, 'strings', 'dates')
            m.add_function('format', String, self._format.text())
            m.add_function('timezone', String, self._timezone.text())
        elif ifmt == self.DATESTRING and ofmt == self.MATPLOTLIB:
            m = insert_conv(StringsToMatplotlib, 'strings', 'dates')
            m.add_function('format', String, self._format.text())
            m.add_function('timezone', String, self._timezone.text())
        elif ifmt == self.DATETIME and ofmt == self.MATPLOTLIB:
            insert_conv(DatesToMatplotlib, 'datetimes', 'dates')
        else:
            raise RuntimeError("This line shouldn't be reachable")

        return new_var

    def variable_filter(self, variable):
        # Only show List variables on the right
        return variable.type.module is List

    def set_input_formats(self, *args, **kwargs):
        # Keyword-only
        default = kwargs.pop('default', None)
        if kwargs:
            raise TypeError("Unexpected keyword argument")

        self._input_format.setEnabled(True)
        self._input_format.clear()
        default_index = -1
        for i, fmt in enumerate(args):
            self._input_format.addItem(self.item_string[fmt], fmt)
            if default == fmt:
                default_index = i
        if default_index != -1:
            self._input_format.setCurrentIndex(default_index)

    def variable_selected(self, variable):
        try:
            value = get_variable_value(variable)
        except ValueError, e:
            self.set_error(_("Error while getting the variable's value:\n"
                             "%s" % e.message))
            return

        if not isinstance(value, (numpy.ndarray, list)):
            self.set_error(_("Input variable did not return a list"))
            return

        cols = min(len(value), 5)
        self._sample = value[:cols]

        self._input_sample.clear()
        self._input_sample.setRowCount(cols)
        for row, v in enumerate(self._sample):
            item = QtGui.QTableWidgetItem(unicode(v))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self._input_sample.setItem(row, 0, item)

        if isinstance(value, numpy.ndarray):
            if len(value) == 0:  # not value doesn't work on numpy arrays
                self.set_error(_("This variable is an empty array"))
                return
            self.set_input_formats(self.TIMESTAMP, self.MATPLOTLIB,
                                   default=self.TIMESTAMP)
        else:  # isinstance(value, list)
            if not value:
                self.set_error(_("This variable is an empty list"))
                return
            first_item = value[0]
            if isinstance(first_item, basestring):
                self.set_input_formats(self.DATESTRING)
            elif isinstance(first_item, datetime.datetime):
                self.set_input_formats(self.DATETIME)
            elif isinstance(first_item, (float, int, long)):
                self.set_input_formats(self.TIMESTAMP, self.MATPLOTLIB)


_variable_operations = [
    VariableOperation(
        '*',
        subworkflow='{package_dir}/dat-operations/scale_array.xml',
        args=[
            OperationArgument('array', List),
            OperationArgument('num', Float),
        ],
        return_type=List,
        symmetric=True),
    VariableOperation(
        'convert_dates',
        return_type=List,
        wizard=DateConversionWizard)
]
