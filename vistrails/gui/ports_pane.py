from PyQt4 import QtCore, QtGui
from itertools import izip
import os

from core import debug
from core.modules.module_registry import get_module_registry
from core.system import vistrails_root_directory
from gui.common_widgets import QToolWindowInterface
from gui.theme import CurrentTheme

class Parameter(object):
    def __init__(self, desc):
        self.type = desc.name
        self.identifier = desc.identifier
        self.namespace = None if not desc.namespace else desc.namespace
        self.strValue = ''
        
class ParameterEntry(QtGui.QTreeWidgetItem):
    plus_icon = QtGui.QIcon(os.path.join(vistrails_root_directory(),
                                         'gui/resources/images/plus.png'))
    minus_icon = QtGui.QIcon(os.path.join(vistrails_root_directory(),
                                          'gui/resources/images/minus.png'))
    def __init__(self, port_spec, function=None, parent=None):
        QtGui.QTreeWidgetItem.__init__(self, parent)
        self.setFirstColumnSpanned(True)
        self.port_spec = port_spec
        self.function = function

    def get_widget(self):
        reg = get_module_registry()

        # widget = QtGui.QDockWidget()
        # widget.setFeatures(QtGui.QDockWidget.DockWidgetClosable |
        #                    QtGui.QDockWidget.DockWidgetVerticalTitleBar)
        widget = QtGui.QWidget()

        h_layout = QtGui.QHBoxLayout()
        h_layout.insertSpacing(0, 10)
        h_layout.setMargin(2)
        h_layout.setSpacing(2)

        v_layout = QtGui.QVBoxLayout()
        v_layout.setAlignment(QtCore.Qt.AlignVCenter)
        delete_button = QtGui.QToolButton()
        delete_button.setIconSize(QtCore.QSize(8,8))
        delete_button.setIcon(ParameterEntry.minus_icon)
        def delete_method():
            if self.function is not None:
                self.group_box.parent().parent().parent().delete_method(
                    self, self.port_spec.name, self.function.real_id)
            else:
                self.group_box.parent().parent().parent().delete_method(
                    self, self.port_spec.name, None)
                
        QtCore.QObject.connect(delete_button, QtCore.SIGNAL("clicked()"), 
                               delete_method)
        v_layout.addWidget(delete_button)
        
        add_button = QtGui.QToolButton()
        add_button.setIcon(ParameterEntry.plus_icon)
        add_button.setIconSize(QtCore.QSize(8,8))
        def add_method():
            self.group_box.parent().parent().parent().add_method(
                self.port_spec.name)
        QtCore.QObject.connect(add_button, QtCore.SIGNAL("clicked()"), 
                               add_method)
        v_layout.addWidget(add_button)
        h_layout.addLayout(v_layout)
        
        self.my_widgets = []
        self.group_box = QtGui.QGroupBox()
        layout = QtGui.QGridLayout()
        layout.setMargin(5)
        layout.setSpacing(5)
        self.group_box.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.group_box.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                     QtGui.QSizePolicy.Fixed)
        self.group_box.palette().setColor(QtGui.QPalette.Window,
                                     CurrentTheme.METHOD_SELECT_COLOR)

        if self.function is not None:
            params = self.function.parameters
        else:
            params = [None,] * len(self.port_spec.descriptors())

        for i, (desc, param) in enumerate(izip(self.port_spec.descriptors(), 
                                               params)):
            print 'adding desc', desc.name
            # ps_label = ''
            # if port_spec.labels is not None and len(port_spec.labels) > i:
            #     ps_label = str(port_spec.labels[i])
            # label = QHoverAliasLabel(p.alias, p.type, ps_label)

            label = QtGui.QLabel(desc.name)
            widget_class = desc.module.get_widget_class()
            if param is not None:
                obj = param
            else:
                obj = Parameter(desc)
            param_widget = widget_class(obj, self.group_box)
            self.my_widgets.append(param_widget)
            layout.addWidget(label, i, 0)
            layout.addWidget(param_widget, i, 1)

        self.group_box.setLayout(layout)
        def updateMethod():
            if self.function is not None:
                real_id = self.function.real_id
            else:
                real_id = -1
            self.group_box.parent().parent().parent().update_method(
                self, self.port_spec.name, self.my_widgets, real_id)
        self.group_box.updateMethod = updateMethod
        h_layout.addWidget(self.group_box)
        widget.setLayout(h_layout)
        return widget

class PortItem(QtGui.QTreeWidgetItem):
    null_icon = QtGui.QIcon()
    eye_icon = QtGui.QIcon(os.path.join(vistrails_root_directory(),
                                        'gui/resources/images/eye.png'))
    eye_disabled_icon = \
        QtGui.QIcon(os.path.join(vistrails_root_directory(),
                                 'gui/resources/images/eye_gray.png'))
    conn_icon = \
        QtGui.QIcon(os.path.join(vistrails_root_directory(),
                                 'gui/resources/images/connection.png'))

    def __init__(self, port_spec, is_connected, is_optional, is_visible,
                 parent=None):
        QtGui.QTreeWidgetItem.__init__(self, parent)
        # self.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        self.setFlags(QtCore.Qt.ItemIsEnabled)
        # self.setCheckState(0, QtCore.Qt.Unchecked)
        self.port_spec = port_spec
        self.is_connected = is_connected
        self.is_optional = is_optional
        self.is_visible = is_visible
        self.build_item(port_spec, is_connected, is_optional, is_visible)

    def visible(self):
        return not self.is_optional or self.is_visible

    def set_visible(self, visible):
        self.is_visible = visible
        if visible:
            self.setIcon(0, PortItem.eye_icon)
        else:
            self.setIcon(0, PortItem.null_icon)

    def get_visible(self):
        return self.visible_checkbox

    def get_connected(self):
        return self.connected_checkbox

    def is_constant(self):
        return get_module_registry().is_method(self.port_spec)

    def build_item(self, port_spec, is_connected, is_optional, is_visible):
        if not is_optional:
            self.setIcon(0, PortItem.eye_disabled_icon)
        elif is_visible:
            self.setIcon(0, PortItem.eye_icon)
            
        # if port_spec is not a method, make it gray
        if is_connected:
            self.setIcon(1, PortItem.conn_icon)
        self.setText(2, port_spec.name)

        if not self.is_constant():
            self.setForeground(2, 
                               QtGui.QBrush(QtGui.QColor.fromRgb(128,128,128)))

        self.visible_checkbox = QtGui.QCheckBox()
        self.connected_checkbox = QtGui.QCheckBox()

class PortsList(QtGui.QTreeWidget):
    def __init__(self, port_type, parent=None):
        QtGui.QTreeWidget.__init__(self, parent)
        self.port_type = port_type
        self.setColumnCount(3)
        self.setColumnWidth(0,24)
        self.setColumnWidth(1,24)
        self.setRootIsDecorated(False)
        self.setIndentation(0)
        self.setHeaderHidden(True)
        self.connect(self, QtCore.SIGNAL("itemClicked(QTreeWidgetItem*, int)"),
                     self.item_clicked)
        self.module = None
        self.port_spec_items = {}

    def update_module(self, module):
        """ update_module(module: Module) -> None        
        Setup this tree widget to show functions of module
        
        """
        self.clear()
        self.module = module
        self.port_spec_items = {}
        self.function_map = {}
        if module and module.is_valid:
            reg = get_module_registry()
            descriptor = module.module_descriptor
            if self.port_type == 'input':
                port_specs = module.destinationPorts()
                connected_ports = module.connected_input_ports
                visible_ports = module.visible_input_ports
            elif self.port_type == 'output':
                port_specs = module.sourcePorts()
                connected_ports = module.connected_output_ports
                visible_ports = module.visible_output_ports
            else:
                raise Exception("Unknown port type: '%s'" % self.port_type)
            
            for port_spec in sorted(port_specs, key=lambda x: x.name):
                connected = port_spec.name in connected_ports and \
                    connected_ports[port_spec.name] > 0
                item = PortItem(port_spec, 
                                connected,
                                port_spec.optional,
                                port_spec.name in visible_ports)
                self.addTopLevelItem(item)
                self.port_spec_items[port_spec.name] = (port_spec, item)

            if self.port_type == 'input':
                for function in module.functions:
                    if not function.is_valid:
                        debug.critical("function '%s' not valid", function.name)
                        continue
                    port_spec, item = self.port_spec_items[function.name]
                    subitem = ParameterEntry(port_spec, function)
                    self.function_map[function.real_id] = subitem
                    item.addChild(subitem)
                    subitem.setFirstColumnSpanned(True)
                    self.setItemWidget(subitem, 0, subitem.get_widget())
                    item.setExpanded(True)
                
                    # self.setItemWidget(item, 0, item.get_visible())
                    # self.setItemWidget(item, 1, item.get_connected())

                    # i = QTreeWidgetItem(self)
                    # self.addTopLevelItem(i)
                    # i.setText(2, port_spec.name)
                    # visible_checkbox = QtGui.QCheckBox()
                    # self.setItemWidget(i, 0, visible_checkbox)
                    # connceted_checkbox = QtGui.QCheckBox()
                    # connected_checkbox.setEnabled(False)
                    # self.setItemWidget(i, 1, connected_checkbox)
                

            # base_items = {}
            # # Create the base widget item for each descriptor
            # for descriptor in moduleHierarchy:
            #     baseName = descriptor.name
            #     base_package = descriptor.identifier
            #     baseItem = QMethodTreeWidgetItem(None,
            #                                      None,
            #                                      self,
            #                                      (QtCore.QStringList()
            #                                       <<  baseName
            #                                       << ''))
            #     base_items[descriptor] = baseItem

            # method_specs = {}
            # # do this in reverse to ensure proper overloading
            # # !!! NOTE: we have to use ***all*** input ports !!!
            # # because a subclass can overload a port with a 
            # # type that isn't a method
            # for descriptor in reversed(moduleHierarchy):
            #     method_specs.update((name, (descriptor, spec))
            #                         for name, spec in \
            #                             registry.module_ports('input', 
            #                                                   descriptor))

            # # add local registry last so that it takes precedence
            # method_specs.update((spec.name, (descriptor, spec))
            #                     for spec in module.port_spec_list
            #                     if spec.type == 'input')

            # for _, (desc, method_spec) in sorted(method_specs.iteritems()):
            #     if registry.is_method(method_spec):
            #         baseItem = base_items[desc]
            #         sig = method_spec.short_sigstring
            #         QMethodTreeWidgetItem(module,
            #                               method_spec,
            #                               baseItem,
            #                               (QtCore.QStringList()
            #                                << method_spec.name
            #                                << sig))

            # self.expandAll()
            # self.resizeColumnToContents(2)        

    def item_clicked(self, item, col):
        if item.parent() is not None:
            return

        if self.port_type == 'input':
            visible_ports = self.module.visible_input_ports
        elif self.port_type == 'output':
            visible_ports = self.module.visible_output_ports
        else:
            raise Exception("Unknown port type: '%s'" % self.port_type)

        if col == 0:
            if item.is_optional:
                item.set_visible(not item.is_visible)
                if item.is_visible:
                    visible_ports.add(item.port_spec.name)
                else:
                    visible_ports.discard(item.port_spec.name)
                self.controller.current_pipeline_view.recreate_module(
                    self.controller.current_pipeline, self.module.id)
        if col == 2:
            if item.isExpanded():
                item.setExpanded(False)
            elif item.childCount() > 0:
                item.setExpanded(True)
            elif item.childCount() == 0 and item.is_constant():
                subitem = ParameterEntry(item.port_spec)
                item.addChild(subitem)
                subitem.setFirstColumnSpanned(True)
                self.setItemWidget(subitem, 0, subitem.get_widget())
                item.setExpanded(True)
        
    def set_controller(self, controller):
        self.controller = controller

    def update_method(self, subitem, port_name, widgets, real_id=-1):
        print 'updateMethod called', port_name
        if self.controller:
            _, item = self.port_spec_items[port_name]
            # FIXME solve issue with labels
            self.controller.update_function(self.module,
                                            port_name,
                                            [str(w.contents())
                                             for w in widgets],
                                            real_id,
                                            [])

            # FIXME need to get the function set on the item somehow
            # HACK for now
            for function in self.module.functions:
                if function.real_id not in self.function_map:
                    self.function_map[function.real_id] = subitem
                    subitem.function = function
                                            
    def delete_method(self, subitem, port_name, real_id=None):
        if real_id is not None and self.controller:
            print "got to delete"
            self.controller.delete_function(real_id, self.module.id)
        _, item = self.port_spec_items[port_name]
        item.removeChild(subitem)
        # how to delete items...x
        # subitem.deleteLater()
            

    def add_method(self, port_name):
        port_spec, item = self.port_spec_items[port_name]
        subitem = ParameterEntry(port_spec)
        item.addChild(subitem)
        subitem.setFirstColumnSpanned(True)
        self.setItemWidget(subitem, 0, subitem.get_widget())
        item.setExpanded(True)
        
        # if methodBox.controller:
        #     methodBox.lockUpdate()
        #     methodBox.controller.update_function(methodBox.module,
        #                                          self.function.name,
        #                                          [str(w.contents()) 
        #                                           for w in self.widgets],
        #                                          self.function.real_id,
        #                                          [str(label.alias)
        #                                           for label in self.labels])
            
        #     methodBox.unlockUpdate()


class QPortsPane(QtGui.QWidget, QToolWindowInterface):
    def __init__(self, port_type, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QWidget.__init__(self, parent, flags)
        self.port_type = port_type
        self.build_widget()
        self.controller = None

    def build_widget(self):
        self.tree_widget = PortsList(self.port_type)
        layout = QtGui.QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.tree_widget)
        self.setLayout(layout)
        self.setWindowTitle('%s Ports' % self.port_type.capitalize())

    def set_controller(self, controller):
        self.controller = controller
        self.tree_widget.set_controller(controller)

    def update_module(self, module):
        self.tree_widget.update_module(module)
    
