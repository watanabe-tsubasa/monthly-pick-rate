from io import BytesIO
import xlwings as xw
from xlwings import Range
import polars as pl
from typing import Literal, List, Tuple, TypedDict

class ExcelHandler:
  def __init__(self):
    self.wb = xw.Book()
    
  @property
  def sheets(self):
    return self.wb.sheet_names
  
  def add_sheet(self, sheet_name: str):
    self.wb.sheets.add(sheet_name)
    
  def add_sheet_and_df(self, df: pl.DataFrame, sheet_name: str):
    ws = self.wb.sheets.add(sheet_name)
    ws.range('A1').value = df.to_pandas().set_index(df.columns[0], drop=True)
    
  def set_data_sheet_props(self, sheet_name: Literal['シングル', '摘み取り', '種まき']):
    sheet = self.wb.sheets(sheet_name)
    sheet_cols: List[str] = [col for col in sheet.range('1:1').value if col is not None]
    
    class NameAndColor(TypedDict):
      name: str
      color: Tuple[int, int, int]
      
    name_and_colors: List[NameAndColor] = [
      {'name': '店舗合計', 'color': (255, 242, 204)},
      {'name': 'NS合計', 'color': (221, 235, 247)},
      {'name': '売場のみ_シングル(NS)', 'color': (226, 239, 218)},
      {'name': '売場のみ_総量(MD)', 'color': (252, 228, 214)},
      {'name': '作業場のみ(NS)', 'color': (231, 230, 230)},
    ]
    for i, col in enumerate(sheet_cols):
      header_cell = sheet.range(1, i + 1)
      val_cells: Range = sheet.range(2, i + 1).expand('down')
      ## ヘッダーの色変更
      for name_and_color in name_and_colors:
        if name_and_color['name'] in col:
          header_cell.color = name_and_color['color']
          break
      ## ヘッダーを折り返しに設定
      header_cell.wrap_text = True
      
      if ('作業点数' in col) | ('作業時間' in col):
        val_cells.number_format = '#,##0'
      elif '処理点数' in col:
        val_cells.number_format = '0.0'
        
  def set_quadrants_sheet_props(self, sheet_name: str):
    sheet = self.wb.sheets(sheet_name)
    sheet_cols: List[str] = [col for col in sheet.range('1:1').value if col is not None]
    for i, col in enumerate(sheet_cols):
      header_cell = sheet.range(1, i + 1)
      header_cell.wrap_text = False
      val_cells: Range = sheet.range(2, i + 1).expand('down')
      if col == '処理点数':
        val_cells.number_format = '0.0'
      elif col == '遅れ率':
        val_cells.number_format = '0.0%'
    sheet.autofit('r')
    sheet.autofit('c')
    
  def insert_image(self, sheet_name: str, cell_address: str, image_buffer: BytesIO):
    """
    指定したシートとセルに画像を挿入
    :param sheet_name: 挿入対象のシート名
    :param cell_address: 挿入対象のセルアドレス（例: 'B2'）
    :param image_buffer: Plotterクラスなどで生成した画像バッファー(BytesIO)
    """
    sheet = self.wb.sheets(sheet_name)
    cell = sheet.range(cell_address)

    # バッファーを画像として挿入
    sheet.pictures.add(
      image_buffer,
      name="InsertedImage",
      left=cell.left,
      top=cell.top,
      update=True
    )
    
  def save(self, file_path: str):
    self.wb.sheets('Sheet1').delete()
    self.wb.save(file_path)
    self.wb.close()