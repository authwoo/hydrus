from __future__ import annotations

from typing import Optional, List

from hydrus.client.gui.pages import ClientGUIPages

from qtpy import QtCore as QC
from qtpy import QtWidgets as QW

###
# Model of a TabBar to apply to TreeViewWithDnD
# top_level_PagesNotebook -> any amount of Page or PagesNotebook -> etc
###

class _PagesTreeIndexData:
    
    def __init__( self, kind: str, obj: object, parent: Optional[ '_PagesTreeIndexData' ] ):
        
        self.kind = kind
        self.obj = obj
        self.parent = parent
        
    

class PagesNotebookTreeModel( QC.QAbstractItemModel ):
    
    def __init__( self, top_level_notebook: ClientGUIPages.PagesNotebook, parent = None ):
        
        super().__init__( parent )
        
        self._root_notebook = top_level_notebook
        
        self._root_notebook.freshSessionLoaded.connect( self.Reset )
        self._root_notebook.layoutChanged.connect( self.Reset )
        
        self._tree_view = parent
        
        self._root = _PagesTreeIndexData( 'root', top_level_notebook, None )
        
        self._index_data_store = []
        
    
    def _GetChildKind( self, w: QW.QWidget ) -> str:
        
        if isinstance( w, ClientGUIPages.PagesNotebook ):
            
            return 'notebook'
            
        
        return 'page'
        
    
    def _GetPageKey( self, page: QW.QWidget ):
        
        if hasattr( page, 'GetPageKey' ):
            
            try:
                
                return page.GetPageKey()
                
            except:
                
                return None
                
            
        
        if hasattr( page, '_page_key' ):
            
            return page._page_key
            
        
        return None
        
    def GetViewDepth( self, parent: QC.QModelIndex = QC.QModelIndex() ) -> int:
        
        max_depth = -1
        
        for row in range( self.rowCount( parent ) ):
            
            index = self.index( row, 0, parent )
            
            max_depth = max( max_depth, 1 + self.GetViewDepth( index ) )
            
        return max_depth
        
    
    def GetKindFromIndex( self, index: QC.QModelIndex ) -> Optional[ str ]:
        
        data = self._IndexData( index )
        
        if data is None:
            return None
            
        
        return data.kind
        
    
    def GetParentNotebookFromIndex( self, index: QC.QModelIndex ) -> Optional[ ClientGUIPages.PagesNotebook ]:
        
        data = self._IndexData( index )
        
        if data is None:
            
            return None
            
        
        parent_data = data.parent
        
        if parent_data is None:
            
            return None
            
        
        if parent_data.kind == 'root':
            
            return self._root_notebook
            
        
        if parent_data.kind == 'notebook':
            
            return parent_data.obj
            
        
        return None
        
    
    def GetPageKeyFromIndex( self, index: QC.QModelIndex ):
        
        data = self._IndexData( index )
        
        if data is None or data.kind not in ( 'page', 'notebook' ):
            return None
        
        return self._GetPageKey( data.obj )
        
    
    def Reset( self ):
        
        self.beginResetModel()
        
        self._index_data_store = []
        
        self.endResetModel()
        
    
    def index( self, row: int, column: int, parent: QC.QModelIndex = QC.QModelIndex() ) -> QC.QModelIndex:
        
        if column != 0 or row < 0:
            return QC.QModelIndex()
            
        
        parent_data = self._IndexDataOrRoot( parent )
        
        if parent_data.kind == 'root':
            
            notebook = parent_data.obj
            
            if row >= notebook.count():
                return QC.QModelIndex()
                
            
            child = notebook.widget( row )
            
            if child is None:
                return QC.QModelIndex()
                
            
            kind = self._GetChildKind( child )
            
            data = self._NewIndexData( kind, child, parent_data )
            
            return self.createIndex( row, 0, data )
            
        
        if parent_data.kind == 'notebook':
            
            notebook = parent_data.obj
            
            if row >= notebook.count():
                return QC.QModelIndex()
                
            
            child = notebook.widget( row )
            
            if child is None:
                return QC.QModelIndex()
                
            
            kind = self._GetChildKind( child )
            
            data = self._NewIndexData( kind, child, parent_data )
            
            return self.createIndex( row, 0, data )
            
        
        return QC.QModelIndex()
        
    
    def parent( self, child: QC.QModelIndex ) -> QC.QModelIndex:
        
        data = self._IndexData( child )
        
        if data is None:
            return QC.QModelIndex()
            
        
        parent_data = data.parent
        
        if parent_data is None or parent_data.kind == 'root':
            return QC.QModelIndex()
            
        
        parent_row = self._GetRowForData( parent_data )
        
        if parent_row is None:
            return QC.QModelIndex()
            
        
        return self.createIndex( parent_row, 0, parent_data )
        
    
    def rowCount( self, parent: QC.QModelIndex = QC.QModelIndex() ) -> int:
        
        parent_data = self._IndexDataOrRoot( parent )
        
        if parent_data.kind == 'root':
            
            return parent_data.obj.count()
            
        
        if parent_data.kind == 'notebook':
            
            return parent_data.obj.count()
            
        
        return 0
        
    
    def columnCount( self, parent: QC.QModelIndex = QC.QModelIndex() ) -> int:
        
        return 1
        
    
    def data( self, index: QC.QModelIndex, role: int = QC.Qt.ItemDataRole.DisplayRole ):
        
        data = self._IndexData( index )
        
        if data is None:
            return None
            
        
        if role == QC.Qt.ItemDataRole.DisplayRole:
            
            if data.kind == 'notebook':
                
                notebook = data.obj
                
                name = getattr( notebook, '_name', '' )
                
                if name:
                    return name
                
                obj_name = notebook.objectName()
                
                if obj_name:
                    return obj_name
                    
                
                page_key = self._GetPageKey( notebook )
                
                if page_key is not None:
                    
                    return str( page_key )
                    
                
                return 'pages'
                
            
            elif data.kind == 'page':
                
                parent_data = data.parent
                
                if parent_data is not None:
                    
                    notebook = parent_data.obj
                    
                    row = notebook.indexOf( data.obj )
                    
                    if row != -1 and row < notebook.count():
                        
                        text = notebook.tabText( row )
                        
                        if text:
                            return text
                            
                        
                    
                
                page_key = self._GetPageKey( data.obj )
                
                if page_key is not None:
                    
                    return str( page_key )
                    
                
                return 'page'
                
            
        
        if role == QC.Qt.ItemDataRole.DecorationRole:
            
            parent_data = data.parent
            
            if parent_data is not None:
                
                notebook = parent_data.obj
                
                row = notebook.indexOf( data.obj )
                
                if row != -1 and row < notebook.count():
                    
                    icon = notebook.tabIcon( row )
                    
                    if not icon.isNull():
                        
                        return icon
                        
                    
                
            
        return None
        
    
    def headerData( self, section: int, orientation: QC.Qt.Orientation, role: int = QC.Qt.ItemDataRole.DisplayRole ):
        
        if orientation == QC.Qt.Orientation.Horizontal and role == QC.Qt.ItemDataRole.DisplayRole:
            
            if section == 0:
                
                return 'Pages'
                
        return None
        
    
    def flags( self, index: QC.QModelIndex ) -> QC.Qt.ItemFlag:
        
        data = self._IndexData( index )
        
        if data is None:
            return QC.Qt.ItemFlag.NoItemFlags
        
        return (
            QC.Qt.ItemFlag.ItemIsEnabled |
            QC.Qt.ItemFlag.ItemIsSelectable |
            QC.Qt.ItemFlag.ItemIsDragEnabled
        )
        
    
    def _FindNotebookIndex( self, target_notebook: ClientGUIPages.PagesNotebook, parent: QC.QModelIndex = QC.QModelIndex() ) -> QC.QModelIndex:
        
        for row in range( self.rowCount( parent ) ):
            
            index = self.index( row, 0, parent )
            
            data = self._IndexData( index )
            
            if data is None:
                
                continue
                
            
            if data.kind == 'notebook' and data.obj == target_notebook:
                
                return index
                
            
            result = self._FindNotebookIndex( target_notebook, index )
            
            if result.isValid():
                
                return result
                
            
        
        return QC.QModelIndex()
        
    
    
    def _GetRowForData( self, data: _PagesTreeIndexData ) -> Optional[ int ]:
        
        parent_data = data.parent
        
        if parent_data is None:
            return None
        
        notebook = parent_data.obj
        
        if data.kind == 'page':
            
            row = notebook.indexOf( data.obj )
            
            if row == -1:
                return None
            
            return row
            
        
        if data.kind == 'notebook':
            
            row = notebook.indexOf( data.obj )
            
            if row == -1:
                return None
            
            return row
            
        
        return None
        
    
    def _IndexData( self, index: QC.QModelIndex ) -> Optional[ _PagesTreeIndexData ]:
        
        if not index.isValid():
            return None
            
        
        data = index.internalPointer()
        
        if isinstance( data, _PagesTreeIndexData ):
            
            return data
            
        
        return None
        
    
    def _IndexDataOrRoot( self, index: QC.QModelIndex ) -> _PagesTreeIndexData:
        
        data = self._IndexData( index )
        
        if data is None:
            
            return self._root
            
        
        return data
        
    
    def _NewIndexData( self, kind: str, obj: object, parent: Optional[ _PagesTreeIndexData ] ) -> _PagesTreeIndexData:
        
        for data in self._index_data_store:
            
            if data.kind == kind and data.obj == obj and data.parent is parent:
                
                return data
                
            
        data = _PagesTreeIndexData( kind, obj, parent )
        
        self._index_data_store.append( data )
        
        return data
    