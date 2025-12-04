"""
Gestor de PDFs - Aplicación para unir, separar y organizar documentos PDF
Autor: Para uso docente universitario
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListView, QFileDialog,
                             QMessageBox, QInputDialog, QLabel, QSpinBox, QGroupBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap
from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF


class PDFManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pdf_files = []
        self.thumbnail_cache = {}  # Cache para miniaturas
        self.view_mode = 'list'  # 'list' o 'grid'
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Gestor de PDFs')
        self.setGeometry(100, 100, 800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Título
        title = QLabel('Gestor de Documentos PDF')
        title.setStyleSheet('font-size: 18px; font-weight: bold; padding: 10px;')
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Sección de carga de archivos
        load_group = QGroupBox('Cargar Archivos')
        load_layout = QHBoxLayout()
        
        btn_add = QPushButton('Agregar PDF(s)')
        btn_add.clicked.connect(self.add_pdfs)
        load_layout.addWidget(btn_add)
        
        btn_clear = QPushButton('Limpiar Lista')
        btn_clear.clicked.connect(self.clear_list)
        load_layout.addWidget(btn_clear)
        
        load_group.setLayout(load_layout)
        main_layout.addWidget(load_group)
        
        # Lista de archivos con selector de vista
        list_header_layout = QHBoxLayout()
        list_label = QLabel('Archivos cargados:')
        list_header_layout.addWidget(list_label)
        
        # Botones para cambiar vista
        self.btn_list_view = QPushButton('📋 Lista')
        self.btn_list_view.setCheckable(True)
        self.btn_list_view.setChecked(True)
        self.btn_list_view.clicked.connect(lambda: self.change_view_mode('list'))
        list_header_layout.addWidget(self.btn_list_view)
        
        self.btn_grid_view = QPushButton('🔲 Cuadrícula')
        self.btn_grid_view.setCheckable(True)
        self.btn_grid_view.clicked.connect(lambda: self.change_view_mode('grid'))
        list_header_layout.addWidget(self.btn_grid_view)
        
        list_header_layout.addStretch()
        main_layout.addLayout(list_header_layout)
        
        # Lista/Vista de archivos
        self.file_list_view = QListView()
        self.file_list_view.setSelectionMode(QListView.ExtendedSelection)
        self.file_model = QStandardItemModel()
        self.file_list_view.setModel(self.file_model)
        self.file_list_view.setViewMode(QListView.ListMode)
        self.file_list_view.setIconSize(QSize(150, 200))  # Tamaño de miniaturas
        main_layout.addWidget(self.file_list_view)
        
        # Botones de organización
        org_group = QGroupBox('Organizar')
        org_layout = QHBoxLayout()
        
        btn_up = QPushButton('Subir')
        btn_up.clicked.connect(self.move_up)
        org_layout.addWidget(btn_up)
        
        btn_down = QPushButton('Bajar')
        btn_down.clicked.connect(self.move_down)
        org_layout.addWidget(btn_down)
        
        btn_remove = QPushButton('Quitar Seleccionado')
        btn_remove.clicked.connect(self.remove_selected)
        org_layout.addWidget(btn_remove)
        
        org_group.setLayout(org_layout)
        main_layout.addWidget(org_group)
        
        # Operaciones con PDFs
        ops_group = QGroupBox('Operaciones')
        ops_layout = QVBoxLayout()
        
        # Fila 1
        row1 = QHBoxLayout()
        btn_merge = QPushButton('Unir Todos los PDFs')
        btn_merge.clicked.connect(self.merge_pdfs)
        row1.addWidget(btn_merge)
        
        btn_split = QPushButton('Separar PDF por Páginas')
        btn_split.clicked.connect(self.split_pdf)
        row1.addWidget(btn_split)
        ops_layout.addLayout(row1)
        
        # Fila 2
        row2 = QHBoxLayout()
        btn_extract = QPushButton('Extraer Rango de Páginas')
        btn_extract.clicked.connect(self.extract_pages)
        row2.addWidget(btn_extract)
        
        btn_info = QPushButton('Ver Info del PDF')
        btn_info.clicked.connect(self.show_pdf_info)
        row2.addWidget(btn_info)
        ops_layout.addLayout(row2)
        
        ops_group.setLayout(ops_layout)
        main_layout.addWidget(ops_group)
    
    def generate_thumbnail(self, pdf_path):
        """Genera una miniatura de la primera página del PDF"""
        if pdf_path in self.thumbnail_cache:
            return self.thumbnail_cache[pdf_path]
        
        try:
            # Abrir PDF con PyMuPDF
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                return None
            
            # Renderizar primera página
            page = doc[0]
            zoom = 0.5  # Factor de zoom para la miniatura
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convertir a QPixmap
            img_data = pix.tobytes("ppm")
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            
            doc.close()
            
            # Guardar en cache
            self.thumbnail_cache[pdf_path] = pixmap
            return pixmap
        except Exception as e:
            print(f"Error generando miniatura: {e}")
            return None
    
    def change_view_mode(self, mode):
        """Cambia entre vista de lista y cuadrícula"""
        self.view_mode = mode
        
        if mode == 'list':
            self.file_list_view.setViewMode(QListView.ListMode)
            self.file_list_view.setIconSize(QSize(32, 32))
            self.btn_list_view.setChecked(True)
            self.btn_grid_view.setChecked(False)
        else:  # grid
            self.file_list_view.setViewMode(QListView.IconMode)
            self.file_list_view.setIconSize(QSize(150, 200))
            self.file_list_view.setGridSize(QSize(180, 220))
            self.file_list_view.setSpacing(10)
            self.btn_list_view.setChecked(False)
            self.btn_grid_view.setChecked(True)
        
        # Refrescar la vista
        self.refresh_view()
    
    def refresh_view(self):
        """Refresca la vista con los archivos actuales"""
        self.file_model.clear()
        
        for pdf_file in self.pdf_files:
            item = QStandardItem(os.path.basename(pdf_file))
            
            # Generar miniatura si está en modo cuadrícula o si queremos mostrarla siempre
            thumbnail = self.generate_thumbnail(pdf_file)
            if thumbnail:
                # Escalar miniatura según el modo de vista
                if self.view_mode == 'grid':
                    scaled_thumbnail = thumbnail.scaled(150, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                else:
                    scaled_thumbnail = thumbnail.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                item.setIcon(QIcon(scaled_thumbnail))
            
            item.setToolTip(pdf_file)  # Mostrar ruta completa en tooltip
            self.file_model.appendRow(item)
        
    def add_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            'Seleccionar archivos PDF', 
            '', 
            'PDF Files (*.pdf)'
        )
        
        for file in files:
            if file not in self.pdf_files:
                self.pdf_files.append(file)
        
        self.refresh_view()
    
    def clear_list(self):
        self.pdf_files.clear()
        self.thumbnail_cache.clear()
        self.file_model.clear()
    
    def move_up(self):
        current_index = self.file_list_view.currentIndex()
        if not current_index.isValid():
            return
        
        current_row = current_index.row()
        if current_row > 0:
            self.pdf_files[current_row], self.pdf_files[current_row - 1] = \
                self.pdf_files[current_row - 1], self.pdf_files[current_row]
            
            self.refresh_view()
            # Restaurar selección
            new_index = self.file_model.index(current_row - 1, 0)
            self.file_list_view.setCurrentIndex(new_index)
    
    def move_down(self):
        current_index = self.file_list_view.currentIndex()
        if not current_index.isValid():
            return
        
        current_row = current_index.row()
        if current_row < len(self.pdf_files) - 1 and current_row >= 0:
            self.pdf_files[current_row], self.pdf_files[current_row + 1] = \
                self.pdf_files[current_row + 1], self.pdf_files[current_row]
            
            self.refresh_view()
            # Restaurar selección
            new_index = self.file_model.index(current_row + 1, 0)
            self.file_list_view.setCurrentIndex(new_index)
    
    def remove_selected(self):
        selected_indexes = self.file_list_view.selectedIndexes()
        if not selected_indexes:
            return
        
        # Obtener índices ordenados de mayor a menor para evitar problemas al eliminar
        rows_to_remove = sorted([idx.row() for idx in selected_indexes], reverse=True)
        
        for row in rows_to_remove:
            if 0 <= row < len(self.pdf_files):
                pdf_file = self.pdf_files[row]
                # Limpiar cache de miniatura si existe
                if pdf_file in self.thumbnail_cache:
                    del self.thumbnail_cache[pdf_file]
                self.pdf_files.pop(row)
        
        self.refresh_view()
    
    def merge_pdfs(self):
        if len(self.pdf_files) < 2:
            QMessageBox.warning(self, 'Advertencia', 
                              'Debe cargar al menos 2 archivos PDF para unir.')
            return
        
        output_file, _ = QFileDialog.getSaveFileName(
            self, 
            'Guardar PDF unido', 
            'documento_unido.pdf', 
            'PDF Files (*.pdf)'
        )
        
        if not output_file:
            return
        
        try:
            writer = PdfWriter()
            
            for pdf_file in self.pdf_files:
                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    writer.add_page(page)
            
            with open(output_file, 'wb') as output:
                writer.write(output)
            
            QMessageBox.information(self, 'Éxito', 
                                  f'PDFs unidos correctamente.\nArchivo guardado: {output_file}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error al unir PDFs: {str(e)}')
    
    def split_pdf(self):
        if not self.pdf_files:
            QMessageBox.warning(self, 'Advertencia', 
                              'Debe cargar al menos un archivo PDF.')
            return
        
        selected_indexes = self.file_list_view.selectedIndexes()
        if len(selected_indexes) != 1:
            QMessageBox.warning(self, 'Advertencia', 
                              'Seleccione exactamente un PDF para separar.')
            return
        
        selected_row = selected_indexes[0].row()
        pdf_file = self.pdf_files[selected_row]
        
        output_dir = QFileDialog.getExistingDirectory(
            self, 
            'Seleccionar carpeta para guardar páginas'
        )
        
        if not output_dir:
            return
        
        try:
            reader = PdfReader(pdf_file)
            total_pages = len(reader.pages)
            base_name = os.path.splitext(os.path.basename(pdf_file))[0]
            
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                
                output_file = os.path.join(output_dir, f'{base_name}_pagina_{i+1}.pdf')
                with open(output_file, 'wb') as output:
                    writer.write(output)
            
            QMessageBox.information(self, 'Éxito', 
                                  f'PDF separado en {total_pages} páginas.\nGuardado en: {output_dir}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error al separar PDF: {str(e)}')
    
    def extract_pages(self):
        if not self.pdf_files:
            QMessageBox.warning(self, 'Advertencia', 
                              'Debe cargar al menos un archivo PDF.')
            return
        
        selected_indexes = self.file_list_view.selectedIndexes()
        if len(selected_indexes) != 1:
            QMessageBox.warning(self, 'Advertencia', 
                              'Seleccione exactamente un PDF para extraer páginas.')
            return
        
        selected_row = selected_indexes[0].row()
        pdf_file = self.pdf_files[selected_row]
        
        try:
            reader = PdfReader(pdf_file)
            total_pages = len(reader.pages)
            
            start_page, ok1 = QInputDialog.getInt(
                self, 
                'Página inicial', 
                f'Página inicial (1-{total_pages}):', 
                1, 1, total_pages
            )
            
            if not ok1:
                return
            
            end_page, ok2 = QInputDialog.getInt(
                self, 
                'Página final', 
                f'Página final ({start_page}-{total_pages}):', 
                start_page, start_page, total_pages
            )
            
            if not ok2:
                return
            
            output_file, _ = QFileDialog.getSaveFileName(
                self, 
                'Guardar páginas extraídas', 
                f'paginas_{start_page}-{end_page}.pdf', 
                'PDF Files (*.pdf)'
            )
            
            if not output_file:
                return
            
            writer = PdfWriter()
            for i in range(start_page - 1, end_page):
                writer.add_page(reader.pages[i])
            
            with open(output_file, 'wb') as output:
                writer.write(output)
            
            QMessageBox.information(self, 'Éxito', 
                                  f'Páginas {start_page}-{end_page} extraídas.\nGuardado: {output_file}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error al extraer páginas: {str(e)}')
    
    def show_pdf_info(self):
        selected_indexes = self.file_list_view.selectedIndexes()
        if len(selected_indexes) != 1:
            QMessageBox.warning(self, 'Advertencia', 
                              'Seleccione exactamente un PDF para ver información.')
            return
        
        selected_row = selected_indexes[0].row()
        pdf_file = self.pdf_files[selected_row]
        
        try:
            reader = PdfReader(pdf_file)
            total_pages = len(reader.pages)
            
            info = f"Archivo: {os.path.basename(pdf_file)}\n"
            info += f"Número de páginas: {total_pages}\n"
            info += f"Ruta: {pdf_file}\n"
            
            if reader.metadata:
                info += "\nMetadatos:\n"
                if reader.metadata.title:
                    info += f"Título: {reader.metadata.title}\n"
                if reader.metadata.author:
                    info += f"Autor: {reader.metadata.author}\n"
                if reader.metadata.creator:
                    info += f"Creador: {reader.metadata.creator}\n"
            
            QMessageBox.information(self, 'Información del PDF', info)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error al leer información: {str(e)}')


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = PDFManager()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()