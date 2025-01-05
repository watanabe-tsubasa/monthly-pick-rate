from modules.data_cleaner import DataCleaner
import glob
import polars as pl

class DataSeparator:
  def __init__(self):
    self.__base_df = pl.DataFrame()
    self.__single_df = pl.DataFrame()
    self.__tsumitori_df = pl.DataFrame()
    self.__tanemaki_df = pl.DataFrame()
    self.__single_df_static = pl.DataFrame()
    self.__tsumitori_df_static = pl.DataFrame()
    self.__tanemaki_df_static = pl.DataFrame()
    self.__info_cols = [
      '事業会社',
      'カンパニー・事業部',
      '店舗コード',
      '店舗',
      'ピッキング方式',
    ]
    self.__category_list = [
      '店舗合計',
      'NS合計',
      '売場のみ_シングル(NS)',
      '売場のみ_総量(MD)',
      '作業場のみ(NS)',
    ]
    self.__kpi_list = [
      '作業点数',
      '作業時間（単位：分）'
    ]
    self.__result_list = [
      '処理点数'
    ]
    self.__sorter_df = pl.DataFrame()
  
  @property
  def all(self):
    return self.__base_df
  
  @property
  def single(self):
    return self.__single_df

  @property
  def tsumitori(self):
    return self.__tsumitori_df

  @property
  def tanemaki(self):
    return self.__tanemaki_df
  
  @property
  def single_static(self):
    return self.__single_df_static

  @property
  def tsumitori_static(self):
    return self.__tsumitori_df_static

  @property
  def tanemaki_static(self):
    return self.__tanemaki_df_static
  
  def __set_sorter_df(self, df: pl.DataFrame):
    self.__sorter_df = (df
      .select('カンパニー・事業部')
      .with_columns(
        pl.int_range(pl.len(), dtype=pl.Int32).alias('index')
      )
      .group_by('カンパニー・事業部')
      .mean()
      .sort('index', descending=False)
      .drop('index')
      .with_columns(
        pl.int_range(pl.len(), dtype=pl.Int32).alias('index')
      )
    )
  
  def __create_monthly_df(self):
    files = glob.iglob('./data/ピッキング管理帳票エクスポート_*.xlsx')
    df_concat = pl.DataFrame()
    for file in files:
      cl = DataCleaner()
      cl.dataframe = pl.read_excel(file, read_options={"header_row": 3})
      cl.fix_colnames()
      cl.cast_to_float_and_drop()
      if len(df_concat) == 0:
        df_concat = cl.dataframe
        self.__set_sorter_df(cl.dataframe)
      else:
        df_concat = pl.concat([df_concat, cl.dataframe], how="vertical")

    df_groupby = (
      df_concat
      .group_by(self.__info_cols)
      .sum()
    )

    df_add_rate = pl.DataFrame()
    for category in self.__category_list:
      if len(df_add_rate) == 0:
        df_add_rate = (
          df_groupby
          .with_columns(
            ((pl.col(f'{category}_{self.__kpi_list[0]}') / pl.col(f'{category}_{self.__kpi_list[1]}')) * 60).alias(f'{category}_{self.__result_list[0]}')
          )
        )
      else:
        df_add_rate = (
          df_add_rate
          .with_columns(
            ((pl.col(f'{category}_{self.__kpi_list[0]}') / pl.col(f'{category}_{self.__kpi_list[1]}')) * 60).alias(f'{category}_{self.__result_list[0]}')
          )
        )
    generated_cols = [
      f'{category}_{kpi}'
      for category in self.__category_list
      for kpi in [*self.__kpi_list, *self.__result_list]
    ]
    result_cols = [
      *self.__info_cols,
      *generated_cols
    ]
    
    return (
      df_add_rate
      .select(result_cols)
      .fill_nan(0)
      .join(self.__sorter_df, on='カンパニー・事業部', how='left')
      .sort(['index', '店舗コード'], descending=False)
      .drop('index')
    )
    
  def __get_static(self, df: pl.DataFrame):
    return(
      df.describe()
      .with_columns(
        pl.col('statistic')
        .str.replace('count', '店舗数')
        .str.replace('mean', '平均')
        .str.replace('std', '標準偏差')
        .str.replace('min', '最小値')
        .str.replace('25%', '25%点')
        .str.replace('50%', '中央値')
        .str.replace('75%', '75%点')
        .str.replace('max', '最大値')
        .alias('統計量')
      )
      .filter(pl.col('統計量') != 'null_店舗数')
      .select(['統計量', *[col for col in df.columns if '処理点数' in col]])
    )
  
  def run(self):
    df_base = self.__create_monthly_df()
    self.__base_df = df_base
    df_base_tanemaki = df_base.filter(pl.col('ピッキング方式') == '寺岡用種まきピッキング')
    df_base_single = df_base.filter(
      (pl.col('ピッキング方式') == '混合シングルピッキング') &
      (pl.col('売場のみ_シングル(NS)_作業点数') > 100)
    )
    df_base_tsumitori = df_base.filter(
      (pl.col('ピッキング方式') == '混合シングルピッキング') &
      (pl.col('売場のみ_シングル(NS)_作業点数') < 100)
    )
    self.__tanemaki_df = df_base_tanemaki
    self.__single_df = df_base_single
    self.__tsumitori_df = df_base_tsumitori
    self.__tanemaki_df_static = self.__get_static(df_base_tanemaki)
    self.__single_df_static = self.__get_static(df_base_single)
    self.__tsumitori_df_static = self.__get_static(df_base_tsumitori)
    