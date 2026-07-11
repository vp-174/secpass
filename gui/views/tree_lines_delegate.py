from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui import QColor, QPen, QPainter


class TreeLinesDelegate(QStyledItemDelegate):
    """Делегат для отрисовки соединительных линий в дереве групп."""
    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        widget = option.widget
        if not widget:
            return

        model = widget.model()
        if not model:
            return

        item = model.itemFromIndex(index)
        if not item:
            return
        
        rect = option.rect
        indent = widget.indentation()
        row_height = rect.height()
        
        painter.save()
        painter.setPen(QPen(QColor("#999"), 2))
        
        parent = item.parent()
        if parent:
            parent_rect = widget.visualRect(parent.index())
            x = rect.left() - indent // 2
            y_mid = rect.top() + row_height // 2
            y_top = parent_rect.bottom()
            painter.drawLine(x, y_top, x, y_mid)
            painter.drawLine(x, y_mid, rect.left(), y_mid)
        elif item.row() > 0:
            prev_item = model.item(item.row() - 1)
            if prev_item:
                prev_rect = widget.visualRect(prev_item.index())
                x = rect.left() - indent // 2
                y_top = prev_rect.bottom()
                y_mid = rect.top() + row_height // 2
                painter.drawLine(x, y_top, x, y_mid)
        
        painter.restore()
