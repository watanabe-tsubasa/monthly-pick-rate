import matplotlib.pyplot as plt
import seaborn as sns; sns.set_theme(style="whitegrid", palette="pastel")
import matplotlib_fontja; matplotlib_fontja.japanize()
import polars as pl
from io import BytesIO

class Plotter:
  def __init__(self):
    self.__df = pl.DataFrame()
    self.__buf = BytesIO()
    self.__figure = None
  
  @property
  def selected_df(self):
    return self.__df
  
  @selected_df.setter
  def selected_df(self, new_dataframe: pl.DataFrame):
    if not new_dataframe.columns:
      raise ValueError('pl.DataFrameを入れてください')
    self.__df = new_dataframe
    
  @property
  def buf(self):
    return self.__buf
  
  @property
  def figure(self):
    return self.__figure
    
  def set_plt_image(self):
    plt.savefig(self.__buf, format="png")
    self.__buf.seek(0)
    
  def debug_image(self, name:str):
    # バッファの内容を画像として一時的に保存
    with open(f"{name}.png", "wb") as f:
        f.write(self.__buf.getvalue())
    
    print("画像が 'debug_output.png' として保存されました。")
    plt.close()
    
  def box_prot(self, y_max: int, colname: str , **kwargs: pl.DataFrame):
    fig, ax = plt.subplots()
    self.__figure = fig
    plot_df = pl.DataFrame()
    for key, df in kwargs.items():
      concat_df = (
        df
        .select(colname)
        .with_columns(
          pl.lit(key).alias('方式')
        )
      )
      if len(plot_df) == 0:
        plot_df = concat_df
      else:
        plot_df = pl.concat([plot_df, concat_df], how='vertical')
    print(plot_df)

    sns.boxplot(
      data=plot_df,
      x='方式',
      y=colname,
      hue='方式',
      palette='pastel',
      linewidth=1.2
    )
    sns.stripplot(
      data=plot_df, 
      x='方式', 
      y=colname, 
      ax=ax, 
      size=6, 
      jitter=True,
      # dodge=True,
      hue='方式',
      alpha=0.9,
      palette='pastel',
    )

    ax.set_ylim(bottom=0, top=y_max)
    self.set_plt_image()
    
  def for_quadrants_plot(self, data: pl.DataFrame):
    fig, ax = plt.subplots()
    self.__figure = fig
    x_axis = '処理点数'
    y_axis = '遅れ率'

    sns.scatterplot(
      data=data,
      x=x_axis,
      y=y_axis,
      hue='カンパニー'
    )
    ax.set_xlim(left=0, right=250)
    x_med = data.select(x_axis).median().item(0,0)
    y_med = data.select(y_axis).median().item(0,0)
    ax.axvline(x=x_med, color='red', linestyle='--', label='XMedian')  # 中央値の線を描画
    ax.axhline(y=y_med, color='red', linestyle='--', label='YMedian')  # 中央値の線を描画
    self.set_plt_image()
