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

sys.path.append(CURRENT_DIR)
from StraDualThrustExplorer import explore_stra_dual_thrust_params, StraDualThrustExplorerConfig

COMMON_PATH = os.path.join(CURRENT_DIR, 'common')
STORAGE_PATH = os.path.join(CURRENT_DIR, 'storage')
OUTPUTS_PATH = os.path.join(CURRENT_DIR, 'outputs')
LOGCFG_FILE = os.path.join(CURRENT_DIR, 'logcfgbt.yaml')
CONFIGBT_FILE = os.path.join(CURRENT_DIR, 'configbt.yaml')

CODES = [
    "SSE.STK.600008",
    "SSE.STK.601179",
    "SSE.ETF.510300",
]

def cta_stk_bt(
    code:str='SSE.STK.600008', 
    start_time:int=202501010930, 
    end_time:int=202510311500, 
    anaylze:bool=True, 
    barCnt:int=50,
    period:str='m5',
    days:int=40,
    k1:float=0.1, 
    k2:float=0.1,
):
    """
    Args:
        start_time: 开始时间
        end_time: 结束时间
        anaylze: 是否进行绩效分析
    """
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
    
    name = f"cta_stk_bt_{code.split('.')[-1]}_b{barCnt}_p{period}_d{days}_k1{k1}_k2{k2}"
    straInfo = StraDualThrust(
        code=code,
        name=name, 
        barCnt=barCnt,
        period=period,
        days=days,
        k1=k1,
        k2=k2,
        isForStk=True
    )
    engine.set_cta_strategy(straInfo)

    engine.run_backtest()

    if anaylze:
        #绩效分析
        analyst = WtBtAnalyst()
        analyst.add_strategy(name, folder=OUTPUTS_PATH, init_capital=5000, rf=0.0, annual_trading_days=240)
        analyst.run(outFileName=os.path.join(OUTPUTS_PATH, f'analysis-{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'))

    engine.release_backtest()

def run_explore_stra_dual_thrust_params(code:str="SSE.ETF.510300", stk:str="false", start_time:int=201901010930, end_time:int=201912311500):
    # 创建配置对象
    config = StraDualThrustExplorerConfig(
        common_path=COMMON_PATH,
        storage_path=STORAGE_PATH,
        outputs_path=OUTPUTS_PATH,
        logcfg_file=LOGCFG_FILE,
        configbt_file=CONFIGBT_FILE,

        code=code,
        isForStk= stk == "true",
        start_time=start_time,
        end_time=end_time,
        init_capital=5000,
        annual_trading_days=240,

        barCnt_list=list(range(30, 80, 10)),
        period_list=["m5"],
        days_list=list(range(10, 60, 10)),
        k1_list=[round(x * 0.1, 1) for x in range(1, 5)], 
        k2_list=None,
    )
    
    # 运行参数探索
    df_results = explore_stra_dual_thrust_params(config)
    
    print(f"\n✅ 参数探索完成！共测试 {len(df_results)} 个参数组合")

def download_bars(code:str, folder:str=STORAGE_PATH+"/csv",  period:str='min5'):
    """下载K线数据
    
    Args:
        code: 合约代码，如 SSE.510300 或 SSE.ETF.510300 或 SSE.STK.600008
        folder: 数据保存目录，默认 storage/csv
        period: K线周期，可选 day/min5/min1，默认 min5
    """
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # 确保目录存在
    import os
    os.makedirs(folder, exist_ok=True)
    
    # 处理代码格式：支持 SSE.510300 和 SSE.ETF.510300 两种格式
    code_parts = code.split(".")
    if len(code_parts) == 3:
        # SSE.ETF.510300 -> SSE.510300
        normalized_code = f"{code_parts[0]}.{code_parts[2]}"
    elif len(code_parts) == 2:
        # SSE.510300 -> SSE.510300
        normalized_code = code
    else:
        print(f"❌ 代码格式错误: {code}，应为 SSE.510300 或 SSE.ETF.510300 格式")
        return
    
    hlper = DHF.createHelper("baostock")
    hlper.auth()
    
    print(f"开始下载 {code} 的K线数据...")
    print(f"标准化代码: {normalized_code}")
    print(f"保存目录: {folder}")
    print(f"周期: {period}")
    
    try:
        hlper.dmpBarsToFile(folder=folder, codes=[normalized_code], period=period)
        
        # 检查文件是否生成
        from wtpy.apps.datahelper.DHBaostock import transCodes
        converted_codes = transCodes([normalized_code])
        if converted_codes:
            converted_code = converted_codes[0]
            exchg = "SSE" if converted_code.startswith("sh") else "SZSE"
            filetag = "m5" if period == "min5" else "d"
            filename = f"{exchg}.{converted_code[3:]}_{filetag}.csv"
            filepath = os.path.join(folder, filename)
            
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        print(f"✅ K线数据下载完成！文件: {filepath}")
                        print(f"   共 {len(lines)-1} 条数据记录")
                    else:
                        print(f"⚠️  文件已生成但数据为空: {filepath}")
                        print(f"   可能原因：1) 代码格式不正确 2) 该代码在baostock中无数据 3) 数据时间范围问题")
                        print(f"   请检查baostock日志中的错误信息")
            else:
                print(f"⚠️  文件未生成: {filepath}")
                print(f"   可能原因：1) baostock API返回错误 2) 代码格式不正确")
                print(f"   请检查baostock日志中的错误信息")
        else:
            print("⚠️  代码转换失败")
    except Exception as e:
        print(f"❌ 下载过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主入口函数，使用 fire 库自动生成命令行接口"""
    fire.Fire()

if __name__ == "__main__":
    main()