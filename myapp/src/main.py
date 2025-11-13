import fire
import os
import sys
from datetime import datetime

from wtpy import WtBtEngine,EngineType
from wtpy.apps import WtBtAnalyst
from wtpy.apps.datahelper import DHFactory as DHF

CURRENT_DIR= os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CURRENT_DIR, 'strategy'))
from DualThrust import StraDualThrust

COMMON_PATH = os.path.join(CURRENT_DIR, 'common')
STORAGE_PATH = os.path.join(CURRENT_DIR, 'storage')
OUTPUTS_PATH = os.path.join(CURRENT_DIR, 'outputs_bt')
LOGCFG_FILE = os.path.join(CURRENT_DIR, 'logcfgbt.yaml')

def cta_stk_bt(start_time:int=202501010930, end_time:int=202510311500):
    #创建一个运行环境，并加入策略
    engine = WtBtEngine(EngineType.ET_CTA, logCfg=LOGCFG_FILE, outDir=OUTPUTS_PATH)
    engine.init(
        folder=COMMON_PATH, 
        commfile="stk_comms.json", 
        contractfile="stocks.json",
    )
    engine.configBacktest(start_time, end_time)
    engine.configBTStorage(mode="csv", path=STORAGE_PATH)
    engine.commitBTConfig()
    
    name = 'pydt_SH600008'
    straInfo = StraDualThrust(
        name=name, 
        code="SSE.STK.600008", 
        barCnt=50,           # 增加历史数据量
        period="m5",         # 5分钟K线
        days=30,             # 回看20天（稳定股票需要更长周期）
        k1=0.1,             # 上轨系数（适中，不会过于敏感）
        k2=0.1,             # 下轨系数（与k1保持一致）
        isForStk=True
    )
    engine.set_cta_strategy(straInfo)

    engine.run_backtest()

    #绩效分析
    analyst = WtBtAnalyst()
    analyst.add_strategy(name, folder=OUTPUTS_PATH, init_capital=5000, rf=0.0, annual_trading_days=240)
    analyst.run(outFileName=os.path.join(OUTPUTS_PATH, f'analysis-{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'))

    engine.release_backtest()

def download_bars(code:str, folder:str=STORAGE_PATH,  period:str='min5'):
    """下载K线数据
    
    Args:
        code: 合约代码，如 SSE.STK.600008
        folder: 数据保存目录，默认 storage
        period: K线周期，可选 day/min5/min1，默认 min5
    """
    hlper = DHF.createHelper("baostock")
    hlper.auth()
    hlper.dmpBarsToFile(folder=folder, codes=[code], period=period)
    print("K线数据下载完成！")

def main():
    """主入口函数，使用 fire 库自动生成命令行接口"""
    fire.Fire()

if __name__ == "__main__":
    main()