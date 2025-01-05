import polars as pl

class DataCleaner:
  def __init__(self):
    self.__df = pl.DataFrame()
    self.__colname_dict = {
      '__UNNAMED__6': '店舗合計',
      '__UNNAMED__7': '店舗合計',
      '__UNNAMED__9': 'NS合計',
      '__UNNAMED__10': 'NS合計',
      '__UNNAMED__12': '売場のみ',
      '__UNNAMED__13': '売場のみ',
      '__UNNAMED__14': '売場のみ',
      '__UNNAMED__15': '売場のみ',
      '__UNNAMED__16': '売場のみ',
      '__UNNAMED__18': '作業場のみ(NS)',
      '__UNNAMED__19': '作業場のみ(NS)',
    }
    self.__info_cols = [
      '事業会社',
      'カンパニー・事業部',
      '店舗コード',
      '店舗',
      'ピッキング方式',
    ]

  @property
  def dataframe(self):
    return self.__df
  
  @dataframe.setter
  def dataframe(self, new_dataframe: pl.DataFrame):
    if not new_dataframe.columns:
      raise ValueError('pl.DataFrameを入れてください')
    self.__df = new_dataframe
    self.__cols = new_dataframe.columns
  
  def __concat_col_name(self, col: str):
    def get_val_from_colnumber(col: str, colnumber: int) -> str | None:
      return (
        self.__df
        .select(col)[colnumber]
        .to_series()
        .to_list()[0]
      )
        
    def get_sub_category(col: str):
      index = self.__cols.index(col)
      if index < 5:
        return None
      
      val_from_col = get_val_from_colnumber(col, 0)
      colval_minus_one = get_val_from_colnumber(self.__cols[index - 1], 0)
      colval_minus_two = get_val_from_colnumber(self.__cols[index - 2], 0)
      if val_from_col is not None:
        return val_from_col
      elif colval_minus_one is not None:
        return colval_minus_one
      elif colval_minus_two is not None:
        return colval_minus_two
      else:
        return None
      
    col_first_val = get_sub_category(col)
    col_second_val = get_val_from_colnumber(col, 1)
    colname_keys = self.__colname_dict.keys()
    updated_col_name = self.__colname_dict[col] if col in colname_keys else col
    updated_col_name = updated_col_name + '_' + col_first_val if col_first_val is not None else updated_col_name
    updated_col_name = updated_col_name + '_' + col_second_val if col_second_val is not None else updated_col_name
    
    return updated_col_name
  
  def fix_colnames(self):
    new_col_dict = {}
    for col in self.__cols:
      new_col_dict[col] = self.__concat_col_name(col)
    self.__df = self.__df.rename(new_col_dict)[2:]
    
  def cast_to_float_and_drop(self):
    new_cols = self.__df.columns
    info_df = self.__df.select(self.__info_cols)
    val_df = self.__df.drop(self.__info_cols)
    for col in val_df.columns:
      val_df = (
        val_df
        .with_columns(
          pl.col(col).cast(pl.Float64)
        )
      )
    self.__df = (
      pl.concat([info_df, val_df], how='horizontal')
        .drop([x for x in new_cols if '処理点数' in x])
    )