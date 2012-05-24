from core import get_vistrails_application
from core.modules.module_registry import get_module_registry

from javax.swing import JScrollPane, JTree, TransferHandler
from javax.swing.tree import DefaultMutableTreeNode
from java.awt.datatransfer import DataFlavor, Transferable
from java.lang import Object as JavaObject


moduleData = DataFlavor(
        JavaObject,
        'X-Vistrails-Module; class=<java.lang.Object>')


class ModuleTransferable(Transferable):
    """The data that is dragged and dropped from the palette to the pipeline.
    """
    def __init__(self, descriptor):
        self.descriptor = descriptor
    
    # @Override
    def getTransferData(self, flavor):
        if flavor == moduleData:
            return self.descriptor
        else:
            return None
    
    # @Override
    def getTransferDataFlavors(self):
        return [moduleData]
    
    # @Override
    def isDataFlavorSupported(self, flavor):
        return flavor == moduleData


class ModuleTreeNode(DefaultMutableTreeNode):
    """A custom tree node that holds the module descriptor.
    """
    def __init__(self, descriptor):
        self.descriptor = descriptor
    
    # @Override
    def getAllowsChildren(self):
        return False
    
    # @Override
    def isLeaf(self):
        return True
    
    # @Override
    def toString(self):
        return self.descriptor.name


class PackageTreeNode(DefaultMutableTreeNode):
    """A custom tree node for packages.
    """
    # @Override
    def getAllowsChildren(self):
        return True
    
    # @Override
    def isLeaf(self):
        return False


class SourceTransferHandler(TransferHandler):
    # @Override
    def getSourceActions(self, c):
        return TransferHandler.COPY
    
    # @Override
    def createTransferable(self, tree):
        node = tree.getSelectionPath().getLastPathComponent()
        if isinstance(node, ModuleTreeNode):
            return ModuleTransferable(node.descriptor)
        else:
            return None


class JModulePalette(JScrollPane):
    """The module palette, that allows the addition of modules to the pipeline.
    """
    def __init__(self):
        self.root = DefaultMutableTreeNode("Available modules")
        self.tree = JTree(self.root)
        
        self.tree.setDragEnabled(True)
        self.tree.setTransferHandler(SourceTransferHandler())
        
        self.setViewportView(self.tree)
        self.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS)
        self.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_NEVER)
        
        self.packages = {}
        
    def connect_registry_signals(self):
        app = get_vistrails_application()
        app.register_notification('reg_new_package', self.newPackage)
        app.register_notification('reg_new_module', self.newModule)
        app.register_notification('reg_deleted_module', self.deletedModule)
        app.register_notification('reg_deleted_package', self.deletedPackage)
        app.register_notification('reg_show_module', self.showModule)
        app.register_notification('reg_hide_module', self.hideModule)
        app.register_notification('reg_module_updated', self.switchDescriptors)

    def newPackage(self, package_identifier, prepend=False):
        registry = get_module_registry()
        package_name = registry.packages[package_identifier].name
        package_item = PackageTreeNode(package_name)
        self.packages[package_identifier] = package_item
        if prepend:
            self.root.insert(package_item, 0)
        else:
            self.root.add(package_item)

    def newModule(self, descriptor, recurse=False):
        registry = get_module_registry()
        if not descriptor.module_abstract():
            package_identifier = (
                    descriptor.ghost_identifier or
                    descriptor.identifier)
            if package_identifier not in self.packages:
                package_item = self.newPackage(package_identifier, True)
            else:
                package_item = self.packages[package_identifier]
                
            if descriptor.ghost_namespace is not None:
                namespace = descriptor.ghost_namespace
            else:
                namespace = descriptor.namespace
            if descriptor.namespace_hidden or not namespace:
                parent_item = package_item
            else:
                parent_item = \
                        package_item.get_namespace(namespace.split('|'))
            
            item = ModuleTreeNode(descriptor)
            parent_item.add(item)
        if recurse:
            for child in descriptor.children:
                self.newModule(child, recurse)

    def deletedModule(self, descriptor):
        pass

    def deletedPackage(self, package):
        pass

    def showModule(self, descriptor):
        pass

    def hideModule(self, descriptor):
        pass

    def switchDescriptors(self, old_descriptor, new_descriptor):
        pass
    
    def link_registry(self):
        self.updateFromModuleRegistry()
        self.connect_registry_signals()

    def updateFromModuleRegistry(self):
        registry = get_module_registry()
        for package in registry.package_list:
            self.newPackage(package.identifier)
        self.newModule(registry.root_descriptor, True)