
from numpy import random
from functools import partial

from qtpy import QtCore as QC
from qtpy import QtWidgets as QW
from qtpy import QtGui as QG

from hydrus.client import ClientConstants as CC

class EdgeLightingWidget( QW.QWidget ):
    
    def __init__( self, parent ):
        
        super().__init__( parent )
        
        self.setAttribute( QC.Qt.WidgetAttribute.WA_TransparentForMouseEvents )
        self.setAttribute( QC.Qt.WidgetAttribute.WA_NoSystemBackground )
        self.setAttribute( QC.Qt.WidgetAttribute.WA_TranslucentBackground )
        
        self._color = QG.QColor( 120, 160, 255, 80 )
        self._thickness = 16
        
        self.hide()
        
    
    def SetGeometryFromRect( self, rect: QC.QRect ):
        
        pad = self._thickness
        
        self.setGeometry(
            rect.adjusted( -pad, -pad, pad, pad )
        )
        
        self.show()
        
    
    def paintEvent( self, event ):
        
        painter = QG.QPainter( self )
        painter.setRenderHint( QG.QPainter.RenderHint.Antialiasing )
        
        r = self.rect().adjusted(
            self._thickness // 2,
            self._thickness // 2,
            -self._thickness // 2,
            -self._thickness // 2
        )
        
        pen = QG.QPen( self._color )
        pen.setWidth( self._thickness )
        
        painter.setPen( pen )
        painter.setBrush( QC.Qt.BrushStyle.NoBrush )
        
        painter.drawRoundedRect( r, 12, 12 )
        
    
class _FadeLabel( QW.QLabel ):
    
    def __init__( self, parent = None ):
        
        super().__init__( parent )
        
        self._opacity = 1.0
        
    
    def GetOpacity( self ):
        
        return self._opacity
        
    
    def SetOpacity( self, value ):
        
        self._opacity = value
        self.update()
        
    
    opacity = QC.Property( float, GetOpacity, SetOpacity )
    
    def paintEvent( self, event ):
        
        pixmap = self.pixmap()
        
        if pixmap is None or pixmap.isNull():
            return
            
        painter = QG.QPainter( self )
        painter.setOpacity( self._opacity )
        painter.drawPixmap( self.rect(), pixmap )
        
    
class _ZoomBlurLabel( QW.QLabel ):
    
    def __init__( self, parent = None ):
        
        super().__init__( parent )
        
        self._opacity = 1.0
        self._blur_radius = 0.0
        
    
    def GetOpacity( self ):
        
        return self._opacity
        
    
    def SetOpacity( self, value ):
        
        self._opacity = value
        self.update()
        
    
    def GetBlurRadius( self ):
        
        return self._blur_radius
        
    
    def SetBlurRadius( self, value ):
        
        self._blur_radius = value
        self.update()
        
    
    opacity = QC.Property( float, GetOpacity, SetOpacity )
    blurRadius = QC.Property( float, GetBlurRadius, SetBlurRadius )
    
    def paintEvent( self, event ):
        
        pixmap = self.pixmap()
        
        if pixmap is None or pixmap.isNull():
            
            return
            
        
        painter = QG.QPainter( self )
        painter.setRenderHint( QG.QPainter.RenderHint.SmoothPixmapTransform )
        painter.setOpacity( self._opacity )
        
        if self._blur_radius <= 0.0:
            
            painter.drawPixmap( self.rect(), pixmap )
            
            return
            
        
        temp = QG.QImage( self.size(), QG.QImage.Format.Format_ARGB32_Premultiplied )
        temp.fill( QC.Qt.GlobalColor.transparent )
        
        temp_painter = QG.QPainter( temp )
        temp_painter.setRenderHint( QG.QPainter.RenderHint.SmoothPixmapTransform )
        temp_painter.drawPixmap( self.rect(), pixmap )
        temp_painter.end()
        
        scene = QW.QGraphicsScene()
        item = QW.QGraphicsPixmapItem( QG.QPixmap.fromImage( temp ) )
        
        blur = QW.QGraphicsBlurEffect()
        blur.setBlurRadius( self._blur_radius )
        item.setGraphicsEffect( blur )
        
        scene.addItem( item )
        
        blurred = QG.QImage( self.size(), QG.QImage.Format.Format_ARGB32_Premultiplied )
        blurred.fill( QC.Qt.GlobalColor.transparent )
        
        scene_painter = QG.QPainter( blurred )
        scene.render( scene_painter, QC.QRectF( blurred.rect() ), QC.QRectF( temp.rect() ) )
        scene_painter.end()
        
        painter.drawImage( 0, 0, blurred )
        
    


###################
# media transition effects
# ------------------------
# run on widgets + pass in the old pixels to transition out of + duration ms
#################

def GetEffectFunctions():
    return {
        
        CC.MEDIA_TRANSITION_EFFECT_FADE_IN: _TransitionFadeInFromBackground,
        CC.MEDIA_TRANSITION_EFFECT_FADE_OUT: _TransitionFadeOldOutToBG,
        CC.MEDIA_TRANSITION_EFFECT_CROSSFADE: _TransitionCrossFade,
        
        CC.MEDIA_TRANSITION_EFFECT_SLIDE_LEFT: partial( _TransitionSlideOut, direction = 'left' ),
        CC.MEDIA_TRANSITION_EFFECT_SLIDE_RIGHT: partial( _TransitionSlideOut, direction = 'right' ),
        CC.MEDIA_TRANSITION_EFFECT_SLIDE_UP: partial( _TransitionSlideOut, direction = 'up' ),
        CC.MEDIA_TRANSITION_EFFECT_SLIDE_DOWN: partial( _TransitionSlideOut, direction = 'down' ),
        
        CC.MEDIA_TRANSITION_EFFECT_SLIDE_TL: partial( _TransitionSlideOutDiagonal, corner = 'tl' ),
        CC.MEDIA_TRANSITION_EFFECT_SLIDE_TR: partial( _TransitionSlideOutDiagonal, corner = 'tr' ),
        CC.MEDIA_TRANSITION_EFFECT_SLIDE_BL: partial( _TransitionSlideOutDiagonal, corner = 'bl' ),
        CC.MEDIA_TRANSITION_EFFECT_SLIDE_BR: partial( _TransitionSlideOutDiagonal, corner = 'br' ),
        
        CC.MEDIA_TRANSITION_EFFECT_ZOOM_IN: _TransitionZoomInFromOld,
        CC.MEDIA_TRANSITION_EFFECT_ZOOM_OUT: _TransitionZoomOutFromOld,
        
        CC.MEDIA_TRANSITION_EFFECT_RANDOM_SLIDE: _RandomSlide,
        CC.MEDIA_TRANSITION_EFFECT_RAND_DIAG_SLIDE: _RandomDiagSlide,
        CC.MEDIA_TRANSITION_EFFECT_RAND_ANY_SLIDE: _RandomSlide8Way,
        CC.MEDIA_TRANSITION_EFFECT_RANDOM_ZOOM: _RandomZoom
        
    }

SLIDE_DIRS = ( 'left', 'right', 'up', 'down' )
DIAG_DIRS  = ( 'tl', 'tr', 'bl', 'br' )

def _RandomSlide( self, old_pixmap, duration = None ):
    
    direction = random.choice( SLIDE_DIRS )
    
    _TransitionSlideOut( self, old_pixmap, duration, direction )


def _RandomDiagSlide( self, old_pixmap, duration = None ):
    
    corner = random.choice( DIAG_DIRS )
    
    _TransitionSlideOutDiagonal( self, old_pixmap, duration, corner )


def _RandomSlide8Way( self, old_pixmap, duration = None ):
    
    way = random.choice( SLIDE_DIRS + DIAG_DIRS )
    
    if way in SLIDE_DIRS:
        
        _TransitionSlideOut( self, old_pixmap, duration, way )
        
    else:
        
        _TransitionSlideOutDiagonal( self, old_pixmap, duration, way )


def _RandomZoom( self, old_pixmap, duration = None ):
    
    zoom_in = random.choice( ( True, False ) )
    
    if zoom_in:
        
        _TransitionZoomOutFromOld( self, old_pixmap, duration )
        
    else:
        
        _TransitionZoomInFromOld( self, old_pixmap, duration )
        
    

def _TransitionFadeInFromBackground( self, old_pixmap, duration = None ):
    
    if duration is None:
        duration = 300
        
    
    effect = QW.QGraphicsOpacityEffect( self )
    
    self.setGraphicsEffect( effect )
    overlay = QW.QLabel( self )
    overlay.setGeometry( self.rect() )
    anim = QC.QPropertyAnimation( effect, b'opacity', self )
    
    anim.setDuration( duration )
    anim.setStartValue( 0.0 )
    anim.setEndValue( 1.0 )
    anim.start( QC.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped )
    
    overlay._fade_anchor = anim
    

def _TransitionFadeOldOutToBG( self, old_pixmap, duration = None ):
    
    if old_pixmap is None or old_pixmap.isNull():
        return
    
    if duration is None:
        duration = 300
        
    
    canvas_size = self.rect().size()
    
    composed = QG.QPixmap( canvas_size )
    composed.fill( self.palette().color( QG.QPalette.ColorRole.Window ) )
    
    painter = QG.QPainter( composed )
    painter.setRenderHint( QG.QPainter.RenderHint.SmoothPixmapTransform )
    
    x = ( canvas_size.width() - old_pixmap.width() ) // 2
    y = ( canvas_size.height() - old_pixmap.height() ) // 2
    
    painter.drawPixmap( x, y, old_pixmap )
    painter.end()
    
    overlay = _FadeLabel( self )
    
    overlay.setPixmap( composed )
    overlay.setGeometry( self.rect() )
    overlay.raise_()
    overlay.show()
    
    anim = QC.QPropertyAnimation( overlay, b'opacity', overlay )
    
    anim.setDuration( duration )
    anim.setStartValue( 1.0 )
    anim.setEndValue( 0.0 )
    anim.setEasingCurve( QC.QEasingCurve.Type.OutCubic )
    
    anim.finished.connect( overlay.deleteLater )
    
    overlay._anim_anchor = anim
    
    anim.start()
    

def _TransitionCrossFade( self, old_pixmap, duration = None ):
    
    if old_pixmap is None or old_pixmap.isNull():
        return
    
    if duration is None:
        duration = 300
        
    overlay = QW.QLabel( self )
    overlay.setPixmap( old_pixmap )
    overlay.setGeometry( old_pixmap.rect() )
    overlay.show()
    
    effect = QW.QGraphicsOpacityEffect( overlay )
    overlay.setGraphicsEffect( effect )
    
    anim = QC.QPropertyAnimation( effect, b'opacity', overlay )
    
    anim.setDuration( duration )
    anim.setStartValue( 1.0 )
    anim.setEndValue( 0.0 )
    
    anim.finished.connect( overlay.deleteLater )
    
    anim.start( QC.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped )
    

def _TransitionSlideOut( self, old_pixmap, duration = None, direction = None ):
    
    if old_pixmap is None or old_pixmap.isNull():
        return
        
    if direction is None:
        direction = random.choice( SLIDE_DIRS )
        
    if duration is None:
        duration = 300
        
    
    overlay = QW.QLabel( self )
    
    overlay.setPixmap( old_pixmap )
    overlay.raise_()
    overlay.show()
    
    start_pos = overlay.pos()
    
    if direction == 'left':
        
        end_pos = start_pos - QC.QPoint( overlay.width(), 0 )
        
    elif direction == 'right':
        
        end_pos = start_pos + QC.QPoint( overlay.width(), 0 )
        
    elif direction == 'up':
        
        end_pos = start_pos - QC.QPoint( 0, overlay.height() )
        
    elif direction == 'down':
        
        end_pos = start_pos + QC.QPoint( 0, overlay.height() )
        
    else:
        
        return
        
    anim = QC.QPropertyAnimation( overlay, b'pos', overlay )
    
    anim.setDuration( duration )
    anim.setStartValue( start_pos )
    anim.setEndValue( end_pos )
    anim.setEasingCurve( QC.QEasingCurve.Type.OutCubic )
    
    anim.finished.connect( overlay.deleteLater )
    
    overlay._slide_anim = anim
    
    anim.start()
    

def _TransitionSlideOutDiagonal( self, old_pixmap, duration = None, corner = None ):
    
    if old_pixmap is None or old_pixmap.isNull():
        return
        
    if corner is None:
        corner = random.choice( DIAG_DIRS )
        
    if duration is None:
        duration = 300
        
    
    overlay = QW.QLabel( self )
    overlay.setPixmap( old_pixmap )
    overlay.raise_()
    overlay.show()
    
    start_pos = overlay.pos()
    
    dx = overlay.width()
    dy = overlay.height()
    
    offsets = {
        'tl' : QC.QPoint( -dx, -dy ),
        'tr' : QC.QPoint(  dx, -dy ),
        'bl' : QC.QPoint( -dx,  dy ),
        'br' : QC.QPoint(  dx,  dy ),
    }
    
    offset = offsets.get( corner )
    if offset is None:
        return
        
    anim = QC.QPropertyAnimation( overlay, b'pos', overlay )
    anim.setDuration( duration )
    anim.setStartValue( start_pos )
    anim.setEndValue( start_pos + offset )
    anim.setEasingCurve( QC.QEasingCurve.Type.OutCubic )
    
    anim.finished.connect( overlay.deleteLater )
    overlay._diag_anim = anim
    anim.start()
    

def _TransitionSlide( self, old_pixmap, duration = None, direction = None ):
    
    if direction is None:
        direction = random.choice( SLIDE_DIRS )
    
    if duration is None:
        duration = 300
        
    start_pos = self.pos()
    
    offset = QC.QPoint( self.width(), 0 )
    
    if direction == 'left':

        offset = -offset
        
    self.move( start_pos + offset )
    
    anim = QC.QPropertyAnimation( self, b'pos', self )
    
    anim.setDuration( duration )
    anim.setStartValue( self.pos() )
    anim.setEndValue( start_pos )
    anim.setEasingCurve( QC.QEasingCurve.Type.OutCubic )
    
    anim.start( QC.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped )
    

def _TransitionZoomOutFromOld( self, old_pixmap, duration = None ):
    
    if old_pixmap is None or old_pixmap.isNull():
        return
        
    if duration is None:
        duration = 300
        
    
    overlay = QW.QLabel( self )
    
    overlay.setPixmap( old_pixmap )
    overlay.setGeometry( self.rect() )
    overlay.setScaledContents( True )
    overlay.raise_()
    overlay.show()
    
    start_rect = overlay.geometry()
    center = start_rect.center()
    
    end_rect = QC.QRect( center.x(), center.y(), 1, 1 )
    
    anim = QC.QPropertyAnimation( overlay, b'geometry', overlay )
    
    anim.setDuration( duration )
    anim.setStartValue( start_rect )
    anim.setEndValue( end_rect )
    anim.setEasingCurve( QC.QEasingCurve.Type.InCubic )
    
    anim.finished.connect( overlay.deleteLater )
    
    overlay._zoom_anim = anim
    
    anim.start()
    

def _TransitionZoomInFromOld( self, old_pixmap, duration = None ):
    
    if old_pixmap is None or old_pixmap.isNull():
        return
        
    if duration is None:
        duration = 300
        
    
    overlay = _ZoomBlurLabel( self )
    
    overlay.setPixmap( old_pixmap )
    #overlay.setGeometry( self.rect() )
    overlay.setScaledContents( True )
    overlay.raise_()
    overlay.show()
    
    start_rect = overlay.geometry()
    
    grow_w = int( start_rect.width() * 1.5 )
    grow_h = int( start_rect.height() * 1.5 )
    
    end_rect = start_rect.adjusted( -grow_w, -grow_h, grow_w, grow_h )
    
    geom_anim = QC.QPropertyAnimation( overlay, b'geometry', overlay )
    geom_anim.setDuration( duration )
    geom_anim.setStartValue( start_rect )
    geom_anim.setEndValue( end_rect )
    geom_anim.setEasingCurve( QC.QEasingCurve.Type.OutCubic )
    
    blur_anim = QC.QPropertyAnimation( overlay, b'blurRadius', overlay )
    blur_anim.setDuration( duration )
    blur_anim.setStartValue( 0.0 )
    blur_anim.setEndValue( 24.0 )
    blur_anim.setEasingCurve( QC.QEasingCurve.Type.OutCubic )
    
    opacity_anim = QC.QPropertyAnimation( overlay, b'opacity', overlay )
    opacity_anim.setDuration( duration )
    opacity_anim.setStartValue( 1.0 )
    opacity_anim.setEndValue( 0.0 )
    opacity_anim.setEasingCurve( QC.QEasingCurve.Type.OutCubic )
    
    group = QC.QParallelAnimationGroup( overlay )
    group.addAnimation( geom_anim )
    group.addAnimation( blur_anim )
    group.addAnimation( opacity_anim )
    
    group.finished.connect( overlay.deleteLater )
    
    overlay._zoom_anim = group
    
    group.start()