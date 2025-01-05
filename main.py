from modules.data_separator import DataSeparator
from modules.treat_late_data import TreatLateData
from modules.excel_handler import ExcelHandler
from modules.plotter import Plotter

from datetime import datetime

def main():
  today = datetime.now()
  this_month = today.month
  last_month = this_month - 1 if this_month != 1 else 12
  
  ds = DataSeparator()
  ds.run() ## シングル、摘み取り、種まきの集計と統計データを作成
  
  tld = TreatLateData()
  tld.read_data() ## 種まき4象限作成用に引き渡し遅れデータを読み込み
  df_tanemaki_forquadrants = tld.create_quadrants_df(
    tld.add_late_data(ds.tanemaki),
    '売場のみ_総量(MD)_処理点数'
  )
  
  el = ExcelHandler()
  el.add_sheet_and_df(ds.tanemaki_static, '種まき統計データ')
  el.add_sheet_and_df(ds.tanemaki, '種まき')
  el.add_sheet_and_df(ds.tsumitori_static, '摘み取り統計データ')
  el.add_sheet_and_df(ds.tsumitori, '摘み取り')
  el.add_sheet_and_df(ds.single_static, 'シングル統計データ')
  el.add_sheet_and_df(ds.single, 'シングル')
  el.add_sheet('店舗全体分布')
  el.add_sheet('売場総量分布')
  el.add_sheet_and_df(df_tanemaki_forquadrants, '種まき4象限')
  
  data_sheets = [
    sheet for sheet in el.sheets
    if ('シングル' in sheet) or ('摘み取り' in sheet) or ('種まき' in sheet)  
  ]
  for sheet in data_sheets:
    el.set_data_sheet_props(sheet)
  el.set_quadrants_sheet_props('種まき4象限')
  
  plo = Plotter()
  all_store = {
    'シングル': ds.single,
    '摘み取り': ds.tsumitori,
  }
  store_pick = {
    'シングル': ds.single,
    '摘み取り': ds.tsumitori,
    '種まき': ds.tanemaki,
  }
  plo.box_prot(200, '店舗合計_処理点数', **all_store)
  # plo.debug_image('店舗合計')
  el.insert_image('店舗全体分布', 'B2', plo.figure)
  
  plo.box_prot(400, '売場のみ_総量(MD)_処理点数', **store_pick)
  # plo.debug_image('売場総量')
  el.insert_image('売場総量分布', 'B2', plo.figure)

  plo.for_quadrants_plot(df_tanemaki_forquadrants)
  # plo.debug_image('総量4象限')
  el.insert_image('種まき4象限', 'G2', plo.figure)

  el.save(f'./dist/{last_month}月度管理帳票まとめ.xlsx')

if __name__ == "__main__":
    main()
    