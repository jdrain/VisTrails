
import ast
import inspect
from xml.etree import cElementTree as ET

def capfirst(s):
    return s[0].upper() + s[1:]

class SpecList(object):
    """ A class with module specifications and custom code
        This describes how the wrapped methods/classes will
        maps to modules in vistrails
    """

    def __init__(self, module_specs=[], custom_code=""):
        self.module_specs = module_specs
        self.custom_code = custom_code

    def write_to_xml(self, fname):
        root = ET.Element("specs")
        subelt = ET.Element("customCode")
        subelt.text = self.custom_code
        root.append(subelt)
        for spec in self.module_specs:
            root.append(spec.to_xml())
        tree = ET.ElementTree(root)

        def indent(elem, level=0):
            i = "\n" + level*"  "
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "  "
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for elem in elem:
                    indent(elem, level+1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = i
        indent(tree.getroot())

        tree.write(fname)

    @staticmethod
    def read_from_xml(fname, klass=None):
        if klass is None:
            klass = ModuleSpec
        module_specs = []
        custom_code = ""
        tree = ET.parse(fname)
        for elt in tree.getroot():
            if elt.tag == "moduleSpec":
                module_specs.append(klass.from_xml(elt))
            elif elt.tag == "customCode":
                custom_code = elt.text
        retval = SpecList(module_specs, custom_code)
        # for spec in retval.module_specs:
        #     print "==", spec.name, "=="
        #     for ps in spec.port_specs:
        #         print " ", ps.arg, ps.name
        return retval

class ModuleSpec(object):
    """ Represents specification of a module
        This mirrors how the module will look in the vistrails registry
    """

    # From Modulesettings. See core.modules.config._documentation
    ms_attrs = ['name',
                'configure_widget',
                'constant_widget',
                'constant_widgets',
                'signature',
                'constant_signature',
                'color',
                'fringe',
                'left_fringe',
                'right_fringe',
                'abstract',
                'namespace',
                'package_version',
                'hide_descriptor']
    attrs = ['module_name', # Name of module (can be overridden by modulesettings)
             'superklass',  # class to inherit from
             'code_ref',    # reference to wrapped class/method
             'docstring',   # module __doc__
             'output_type', # None(=single), list(ordered), or dict(attr=value)
             'callback',    # name of attribute for progress callback
             'tempfile',    # attribute name for temporary file creation method
             'outputs',     # attribute name for list of connected output port names
             'cacheable']   # should this module be cached
    attrs.extend(ms_attrs)

    def __init__(self, module_name, superklass=None, code_ref=None, docstring="",
                 output_type=None, callback=None, tempfile=None, outputs=None,
                 cacheable=True, input_port_specs=None, output_port_specs=None,
                 **kwargs):
        if input_port_specs is None:
            input_port_specs = []
        if output_port_specs is None:
            output_port_specs = []

        self.module_name = module_name
        self.superklass = superklass
        self.code_ref = code_ref
        self.docstring = docstring
        self.output_type = output_type
        self.callback = callback
        self.tempfile = tempfile
        self.outputs = outputs
        self.cacheable = cacheable

        self.input_port_specs = input_port_specs
        self.output_port_specs = output_port_specs

        for attr in self.ms_attrs:
            setattr(self, attr, kwargs.get(attr, None))

    def to_xml(self, elt=None):
        if elt is None:
            elt = ET.Element("moduleSpec")
        elt.set("module_name", self.module_name)
        elt.set("superclass", self.superklass)
        elt.set("code_ref", self.code_ref)
        subelt = ET.Element("docstring")
        subelt.text = unicode(self.docstring)
        elt.append(subelt)
        if self.output_type is not None:
            elt.set("output_type", self.output_type)
        if self.callback is not None:
            elt.set("callback", self.callback)
        if self.tempfile is not None:
            elt.set("tempfile", self.tempfile)
        if self.outputs is not None:
            elt.set("outputs", self.outputs)
        if self.cacheable is False:
            elt.set("cacheable", unicode(self.cacheable))

        for attr in self.ms_attrs:
            value = getattr(self, attr)
            if value is not None:
                elt.set(attr, repr(value))

        for port_spec in self.input_port_specs:
            subelt = port_spec.to_xml()
            elt.append(subelt)
        for port_spec in self.output_port_specs:
            subelt = port_spec.to_xml()
            elt.append(subelt)
        return elt

    @classmethod
    def from_xml(cls, elt):
        module_name = elt.get("module_name", "")
        superklass = elt.get("superclass", "")
        code_ref = elt.get("code_ref", "")
        output_type = elt.get("output_type", None)
        callback = elt.get("callback", "")
        tempfile = elt.get("tempfile", "")
        outputs = elt.get("outputs", "")
        cacheable = ast.literal_eval(elt.get("cacheable", "True"))

        kwargs = {}
        for attr in cls.ms_attrs:
            value = elt.get(attr, None)
            if value is not None:
                kwargs[attr] = ast.literal_eval(value)

        docstring = ""
        input_port_specs = []
        output_port_specs = []
        for child in elt.getchildren():
            if child.tag == "inputPortSpec":
                input_port_specs.append(InputPortSpec.from_xml(child))
            elif child.tag == "outputPortSpec":
                output_port_specs.append(OutputPortSpec.from_xml(child))
            elif child.tag == "docstring":
                if child.text:
                    docstring = child.text
        return cls(module_name, superklass, code_ref, docstring, output_type,
                   callback, tempfile, outputs, cacheable,
                   input_port_specs, output_port_specs, **kwargs)

    def get_output_port_spec(self, compute_name):
        for ps in self.output_port_specs:
            if ps.compute_name == compute_name:
                return ps
        return None

    def get_module_settings(self):
        """ Returns modulesettings dict

        """
        attrs = {}
        for attr in self.ms_attrs:
            value = getattr(self, attr)
            if value is not None:
                attrs[attr] = value
        return attrs

class VTKModuleSpec(ModuleSpec):
    """ Represents specification of a vtk module

        Adds attribute is_algorithm
    """

    def __init__(self, module_name, superklass=None, code_ref=None,
                 docstring="", output_type=None, callback=None,
                 tempfile=None, outputs=None, cacheable=True,
                 input_port_specs=None, output_port_specs=None,
                 is_algorithm=False, **kwargs):
        ModuleSpec.__init__(self, module_name, superklass, code_ref,
                            docstring, output_type, callback, tempfile,
                            outputs, cacheable,
                            input_port_specs, output_port_specs, **kwargs)
        self.is_algorithm = is_algorithm

    def to_xml(self, elt=None):
        elt = ModuleSpec.to_xml(self, elt)
        if self.is_algorithm is True:
            elt.set("is_algorithm", unicode(self.is_algorithm))
        return elt

    @classmethod
    def from_xml(cls, elt):
        inst = ModuleSpec.from_xml(elt)
        inst.is_algorithm = ast.literal_eval(elt.get("is_algorithm", "False"))
        return inst


class PortSpec(object):
    """ Represents specification of a port
    """
    xml_name = "portSpec"
    # attrs tuple means (default value, [is subelement, [run eval]])
    # Subelement: ?
    # eval: serialize as string and use eval to get value back
    # FIXME: subelement/eval not needed if using json
    attrs = {"name": "",                         # port name
             "method_name": "",                  # method/attribute name
             "port_type": None,                  # type signature in vistrails
             "docstring": ("", True),            # documentation
             "min_conns": (0, False, True),      # set min_conns (1=required)
             "max_conns": (-1, False, True),     # Set max_conns (default -1)
             "show_port": (False, False, True),  # Set not optional (use connection)
             "hide": (False, False, True),       # hides/disables port (is this needed?)
             "sort_key": (-1, False, True),      # sort_key
             "shape": (None, False, True),       # physical shape
             "depth": (0, False, True),          # expected list depth
             "other_params": (None, True, True)} # prepended params used with indexed methods

    def __init__(self, arg, **kwargs):
        self.arg = arg # argument name
        self.set_defaults(**kwargs)
        self.port_types = []

    def set_defaults(self, **kwargs):
        for attr, props in self.attrs.iteritems():
            if isinstance(props, tuple):
                default_val = props[0]
            else:
                default_val = props
            if attr in kwargs:
                setattr(self, attr, kwargs[attr])
            else:
                setattr(self, attr, default_val)

        if not self.name:
            self.name = self.arg

        if not self.method_name:
            self.method_name = self.name

    def to_xml(self, elt=None):
        if elt is None:
            elt = ET.Element(self.xml_name)
        elt.set("arg", self.arg)
        for attr, props in self.attrs.iteritems():
            attr_val = getattr(self, attr)
            is_subelt = False
            if isinstance(props, tuple):
                default_val = props[0]
                if len(props) > 1:
                    is_subelt = props[1]
            else:
                default_val = props

            if default_val != attr_val:
                if is_subelt:
                    subelt = ET.Element(attr)
                    subelt.text = unicode(getattr(self, attr))
                    elt.append(subelt)
                else:
                    elt.set(attr, unicode(attr_val))
        return elt

    @classmethod
    def internal_from_xml(cls, elt, obj=None):
        arg = elt.get("arg", "")
        if obj is None:
            obj = cls(arg)
        else:
            obj.arg = arg

        child_elts = {}
        for child in elt.getchildren():
            # if child.tag not in obj.attrs:
            #     raise RuntimeError('Cannot deal with tag "%s"' % child.tag)
            if child.tag not in child_elts:
                child_elts[child.tag] = []
            child_elts[child.tag].append(child)

        kwargs = {}
        for attr, props in obj.attrs.iteritems():
            is_subelt = False
            run_eval = False
            if isinstance(props, tuple):
                if len(props) > 1:
                    is_subelt = props[1]
                if len(props) > 2:
                    run_eval = props[2]
            attr_vals = []
            if is_subelt:
                if attr in child_elts:
                    attr_vals = [c.text for c in child_elts[attr]
                                 if c.text is not None]
            else:
                attr_val = elt.get(attr)
                if attr_val is not None:
                    attr_vals = [attr_val]
            
            if len(attr_vals) > 1:
                raise ValueError('Should have only one value for '
                                'attribute "%s"' % attr)
            if len(attr_vals) > 0:
                attr_val = attr_vals[0]
                if run_eval:
                    try:
                        kwargs[attr] = ast.literal_eval(attr_val)
                    except (NameError, SyntaxError, ValueError):
                        kwargs[attr] = attr_val                        
                else:
                    kwargs[attr] = attr_val
        obj.set_defaults(**kwargs)
        return obj, child_elts
        
    @classmethod
    def from_xml(cls, elt, obj=None):
        obj, child_elts = cls.internal_from_xml(elt, obj)
        return obj

    @staticmethod
    def create_from_xml(elt):
        if elt.tag == "inputPortSpec":
            return InputPortSpec.from_xml(elt)
        elif elt.tag == "outputPortSpec":
            return OutputPortSpec.from_xml(elt)
        raise TypeError('Cannot create spec from element of type "%s"' %
                        elt.tag)

    def get_port_type(self):
        if self.port_type is None:
            return "basic:Null"
        try:
            port_types = ast.literal_eval(self.port_type)
            def flatten(t):
                if not isinstance(t, list):
                    raise Exception("Expected a list")
                flat = []
                for elt in t:
                    if isinstance(elt, list):
                        flat.extend(flatten(elt))
                    else:
                        flat.append(elt)
                return flat
            return ','.join(flatten(port_types))
        except (SyntaxError, ValueError):
            pass
        return self.port_type
        
    def get_port_shape(self):
        """ TODO: Is this needed for vtk?
        """

        if self.port_type is not None:
            try:
                port_types = ast.literal_eval(self.port_type)
                def build_shape(t):
                    if not isinstance(t, list):
                        raise Exception("Expected a list for " + str(t))
                    shape = []
                    count = 0
                    for elt in t:
                        if isinstance(elt, list):
                            if count > 0:
                                shape.append(count)
                            shape.append(build_shape(elt))
                        else:
                            count += 1
                    if count > 0:
                        shape.append(count)
                    return shape
                return build_shape(port_types)
            except (SyntaxError, ValueError):
                pass
        return None

    def get_other_params(self):
        if self.other_params is None:
            return []
        return self.other_params

class InputPortSpec(PortSpec):
    xml_name = "inputPortSpec"
    attrs = {"entry_types": (None, True, True),# custom entry type (like enum)
             "values": (None, True, True),     # values for enums
             "labels": (None, True, True),   # custom labels on enum values
             "defaults": (None, True, True),   # default value list
             }
    attrs.update(PortSpec.attrs)

    def __init__(self, arg, **kwargs):
        PortSpec.__init__(self, arg, **kwargs)

    def get_port_attrs(self):
        """ Port attribute dict that will be used to create the port

        """
        attrs = {}
        if self.sort_key != -1:
            attrs["sort_key"] = self.sort_key
        if self.shape:
            attrs["shape"] = self.shape
        if self.depth:
            attrs["depth"] = self.depth
        if self.values:
            attrs["values"] = unicode(self.values)
        if self.labels:
            attrs["labels"] = unicode(self.labels)
        if self.entry_types:
            attrs["entry_types"] = unicode(self.entry_types)
        if self.defaults:
            attrs["defaults"] = unicode(self.defaults)
        if self.docstring:
            attrs["docstring"] = self.docstring
        if self.min_conns:
            attrs["min_conns"] = self.min_conns
        if self.max_conns != -1:
            attrs["max_conns"] = self.max_conns
        if not self.show_port:
            attrs["optional"] = True
        return attrs

class OutputPortSpec(PortSpec):
    xml_name = "outputPortSpec"
    attrs = {"compute_name": "",
             "compute_parent": "",
             }
    attrs.update(PortSpec.attrs)
    
    def set_defaults(self, **kwargs):
        PortSpec.set_defaults(self, **kwargs)
        if self.compute_name == "":
            self.compute_name = self.arg

    @classmethod
    def from_xml(cls, elt, obj=None):
        obj, child_elts = cls.internal_from_xml(elt, obj)
        return obj

    def get_port_attrs(self):
        """ Port attribute dict that will be used to create the port

        """
        attrs = {}
        if self.sort_key != -1:
            attrs["sort_key"] = self.sort_key
        if self.shape:
            attrs["shape"] = self.shape
        if self.depth:
            attrs["depth"] = self.depth
        if self.docstring:
            attrs["docstring"] = self.docstring
        if self.min_conns:
            attrs["min_conns"] = self.min_conns
        if self.max_conns != -1:
            attrs["max_conns"] = self.max_conns
        if not self.show_port:
            attrs["optional"] = True
        return attrs

#def run():
#    specs = SpecList.read_from_xml("mpl_plots_raw.xml")
#    specs.write_to_xml("mpl_plots_raw_out.xml")

#if __name__ == '__main__':
#    run()