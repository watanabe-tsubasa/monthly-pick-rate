import polars as pl
import glob

class TreatLateData():
  def __init__(self):
    self.__company_list = [
      '北関東',
      '南関東',
      '北陸信越',
      '東海',
      '近畿',
      '中四国',
    ]
    self.__key_df = pl.DataFrame()
  
  def __create_key_row(self, df: pl.DataFrame):
    return (
      df
      .with_columns((
        pl.col('店舗')
        .str.replace('イオン', '')
        .str.replace('スタイル', '')
        .str.replace('店', '')
      ).alias('key'))
    )
    
  def __fix_keys(self):
    if len(self.__key_df) == 0:
      raise ValueError('引き渡し遅れデータを登録してください')
    else:
      self.__key_df = (
        self.__key_df
        .with_columns((
          pl.col('key')
          .str.replace('鎌ケ谷', '鎌ヶ谷')
          .str.replace('今治', '今治馬越')
        ))
        .with_columns((
          pl.col('key')
          .str.replace('今治馬越新都市', '今治新都市')
        ))
      )
    
  def read_data(self):
    files = glob.iglob('./data/商品引渡し状況*.xlsx')
    for file in files:
      path = file
    
    all_company_df = pl.DataFrame()
    for company in self.__company_list:
      sheet_name = f'{company}30分前'
      company_df = pl.read_excel(path, sheet_name=sheet_name)
      if len(all_company_df) == 0:
        all_company_df = company_df
      else:
        all_company_df = pl.concat([all_company_df, company_df], how='vertical')
        
    self.__key_df = self.__create_key_row(all_company_df).select(['key', '遅れ率'])
    self.__fix_keys()
    
  def add_late_data(self, df: pl.DataFrame):
    if len(self.__key_df) == 0:
      raise ValueError('引き渡し遅れデータを登録してください')
    else:
      return(
        self.__create_key_row(df)
        .join(
          self.__key_df,
          on='key',
          how='left'
        )
        .drop('key')
      )
      
  def create_quadrants_df(self, df: pl.DataFrame, colname: str):
    x_med = df.select(colname).median().item(0,0)
    y_med = df.select('遅れ率').median().item(0,0)
    
    quadrants_df = (
      df
      .with_columns(
        pl.col('カンパニー・事業部')
          .str.split("カンパニー")
          .map_elements(lambda x: x[0] if len(x) > 0 else None, return_dtype=pl.Utf8)
          .alias('カンパニー'),
        pl.col('店舗')
          .str.replace('イオン', '')
          .str.replace('スタイル', '')
          .str.replace('店', '')
          .alias('店舗'),
        pl.col(colname)
          .alias('処理点数'),
        pl.when((pl.col(colname) < x_med) & (pl.col('遅れ率') >= y_med))
          .then(pl.lit(1))
          .when((pl.col(colname) >= x_med) & (pl.col('遅れ率') >= y_med))
          .then(pl.lit(2))
          .when((pl.col(colname) < x_med) & (pl.col('遅れ率') < y_med))
          .then(pl.lit(3))
          .when((pl.col(colname) >= x_med) & (pl.col('遅れ率') < y_med))
          .then(pl.lit(4))
          .otherwise(pl.lit('error'))
          .alias('象限')
      )
      .select(['カンパニー', '店舗', '処理点数', '遅れ率', '象限'])
    )
    
    return quadrants_df

      
  def checker(self, df: pl.DataFrame):
    if len(self.__key_df) == 0:
      raise ValueError('引き渡し遅れデータを登録してください')
    else:
      with pl.Config() as cfg:
        cfg.set_tbl_rows(100)
        print(
          self.__create_key_row(df)
          .join(
            self.__key_df,
            on='key',
            how='full'
          )
          .filter(
            pl.col('key').is_null() |
            pl.col('key_right').is_null()
          )
        )