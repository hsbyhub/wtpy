"""
参数探索模块 - 用于测试不同策略参数组合的收益表现
"""
import pandas as pd
from datetime import datetime
from itertools import product
from typing import List, Dict, Any, Optional
import multiprocessing
from queue import Empty
from tqdm import tqdm

from utils.process import silence_output

import sys
import os
import shutil
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CURRENT_DIR, '../strategy'))
from DualThrust import StraDualThrust
from wtpy import WtBtEngine, EngineType

class StraDualThrustBtParam:
    """回测参数封装类"""
    def __init__(self,
                 common_path: str,
                 storage_path: str,
                 outputs_path: str,
                 logcfg_file: str,
                 configbt_file: str,
                 code: str,
                 start_time: int,
                 end_time: int,
                 init_capital: float,
                 annual_trading_days: int,
                 barCnt: int,
                 period: str,
                 days: int,
                 k1: float,
                 k2: float,
                 isForStk: bool = True,
                 comm_file: str = None,
                 contract_file: str = None,
                 holiday_file: str = None,
                 session_file: str = None,
    ):
        self.common_path = common_path
        self.storage_path = storage_path
        self.outputs_path = outputs_path
        self.logcfg_file = logcfg_file
        self.configbt_file = configbt_file
        self.code = code
        self.start_time = start_time
        self.end_time = end_time
        self.init_capital = init_capital
        self.annual_trading_days = annual_trading_days
        self.barCnt = barCnt
        self.period = period
        self.days = days
        self.k1 = k1
        self.k2 = k2
        self.isForStk = isForStk
        self.comm_file = comm_file
        self.contract_file = contract_file
        self.holiday_file = holiday_file
        self.session_file = session_file
        self.name = self._generate_name()
    
    def _generate_name(self) -> str:
        """生成策略名称"""
        k1_str = str(self.k1).replace('.', '_')
        k2_str = str(self.k2).replace('.', '_')
        name = f"pydt_{self.code.split('.')[-1]}_b{self.barCnt}_p{self.period}_d{self.days}_k1{k1_str}_k2{k2_str}"
        return name.replace('.', '_').replace('-', '_')
    

class StraDualThrustExplorerConfig:
    """参数探索配置类"""
    def __init__(self,
                 common_path: str,
                 storage_path: str,
                 outputs_path: str,
                 logcfg_file: str,
                 configbt_file: str,
                 code: str,
                 start_time: int,
                 end_time: int,
                 init_capital: float,
                 annual_trading_days: int,
                 barCnt_list: List[int],
                 period_list: List[str],
                 days_list: List[int],
                 k1_list: List[float],
                 k2_list: Optional[List[float]],
                 isForStk: bool,
                 comm_file: Optional[str] = None,
                 contract_file: Optional[str] = None,
                 holiday_file: Optional[str] = None,
                 session_file: Optional[str] = None,
                 output_file: Optional[str] = None,
                 num_workers: Optional[int] = None):
        """
        初始化参数探索配置
        
        Args:
            common_path: 配置文件目录
            storage_path: 数据存储目录
            outputs_path: 回测输出目录
            logcfg_file: 日志配置文件
            configbt_file: 回测配置文件路径
            code: 合约代码
            start_time: 回测开始时间
            end_time: 回测结束时间
            init_capital: 初始资金
            annual_trading_days: 年交易天数
            barCnt_list: barCnt参数列表，默认 [50]
            period_list: period参数列表，默认 ["m5"]
            days_list: days参数列表，默认 [20, 25, 30]
            k1_list: k1参数列表，默认 [0.1, 0.15, 0.2, 0.25, 0.3]
            k2_list: k2参数列表，如果为None则使用k1_list
            isForStk: 是否为股票
            output_file: 输出CSV文件路径，如果为None则自动生成
            num_workers: 并行进程数，如果为None则使用CPU核心数
        """
        self.common_path = common_path
        self.storage_path = storage_path
        self.outputs_path = outputs_path
        self.logcfg_file = logcfg_file
        self.configbt_file = configbt_file
        self.code = code
        self.start_time = start_time
        self.end_time = end_time
        self.init_capital = init_capital
        self.annual_trading_days = annual_trading_days
        self.barCnt_list = barCnt_list
        self.period_list = period_list
        self.days_list = days_list
        self.k1_list = k1_list
        self.k2_list = k2_list if k2_list is not None else self.k1_list
        self.isForStk = isForStk
        self.comm_file = comm_file
        self.contract_file = contract_file
        self.holiday_file = holiday_file
        self.session_file = session_file
        self.output_file = output_file
        self.num_workers = num_workers

def explore_stra_dual_thrust_params(config: StraDualThrustExplorerConfig) -> pd.DataFrame:
    """
    探索不同参数组合
    
    Args:
        config: StraDualThrustExplorerConfig 对象
        
    Returns:
        包含所有参数组合结果的DataFrame
    """
    # 生成所有参数组合
    param_combinations = list(product(
        config.barCnt_list, 
        config.period_list, 
        config.days_list, 
        config.k1_list, 
        config.k2_list
    ))
    total_combinations = len(param_combinations)
    
    # 确定并行进程数
    workers = config.num_workers or multiprocessing.cpu_count()
    workers = min(workers, total_combinations)  # 不超过任务数
    
    print(f"🚀 开始参数探索，共 {total_combinations} 个参数组合...")
    print(f"📊 使用 {workers} 个并发进程，每个回测任务都在独立进程中执行（执行完后立即退出）")
    
    # 确定输出文件路径
    output_file = config.output_file
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(config.outputs_path, f'param_exploration_{timestamp}.csv')
    
    # 创建参数对象列表
    param_objects = []
    for barCnt, period, days, k1, k2 in param_combinations:
        param = StraDualThrustBtParam(
            common_path=config.common_path,
            storage_path=config.storage_path,
            outputs_path=config.outputs_path,
            logcfg_file=config.logcfg_file,
            configbt_file=config.configbt_file,
            code=config.code,
            start_time=config.start_time,
            end_time=config.end_time,
            init_capital=config.init_capital,
            annual_trading_days=config.annual_trading_days,
            barCnt=barCnt,
            period=period,
            days=days,
            k1=k1,
            k2=k2,
            isForStk=config.isForStk,
            comm_file=config.comm_file,
            contract_file=config.contract_file,
            holiday_file=config.holiday_file,
            session_file=config.session_file
        )
        param_objects.append(param)
    
    # 并发执行：每个回测任务都在独立进程中执行，执行完后立即退出
    results = []
    
    # 创建结果队列
    result_queue = multiprocessing.Queue()
    
    # 使用tqdm显示进度条
    pbar = tqdm(total=total_combinations, desc="参数探索", unit="个")
    
    # 并发执行：同时启动多个进程，但每个进程执行完后立即退出
    active_processes = {}  # {idx: (param, process)}
    next_idx = 0
    completed = 0
    
    try:
        while next_idx < total_combinations or len(active_processes) > 0:
            # 启动新进程（直到达到并发数限制）
            while len(active_processes) < workers and next_idx < total_combinations:
                idx = next_idx + 1
                param = param_objects[next_idx]
                next_idx += 1
                
                # 创建新进程，每个进程执行完后立即退出
                p = multiprocessing.Process(
                    target=on_stra_dual_thrust_backtest,
                    args=(param, result_queue, idx),
                )
                p.start()
                active_processes[idx] = (param, p)
            
            # 检查是否有进程完成
            finished_indices = []
            for idx, (param, p) in active_processes.items():
                if not p.is_alive():
                    finished_indices.append(idx)
            
            # 处理完成的进程
            for idx in finished_indices:
                param, p = active_processes.pop(idx)
                p.join()  # 确保进程完全退出
                
                # 从队列获取结果
                try:
                    result = result_queue.get(timeout=2)
                    completed += 1
                    
                    # 更新进度条描述（显示当前参数和结果）
                    if 'error' not in result:
                        net_profit = result.get('net_profit', 0)
                        win_rate = result.get('win_rate', 0)
                        pbar.set_postfix({
                            '当前': f"b{param.barCnt}_d{param.days}_k1{param.k1}_k2{param.k2}",
                            '净收益': f"{net_profit:.2f}%",
                            '胜率': f"{win_rate:.1f}%"
                        })
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        # 截断过长的错误信息
                        if len(error_msg) > 50:
                            error_msg = error_msg[:47] + '...'
                        pbar.set_postfix({
                            '当前': f"b{param.barCnt}_d{param.days}_k1{param.k1}_k2{param.k2}",
                            '状态': f'失败: {error_msg}'
                        })
                        # 打印详细错误信息（前几个失败的任务）
                        if completed <= 5:  # 只打印前5个失败的错误，避免输出过多
                            print(f"\n❌ 回测失败 [{param.name}]: {result.get('error', 'Unknown error')}")
                    
                    results.append(result)
                except Empty:
                    pbar.set_postfix({'当前': f"b{param.barCnt}_d{param.days}_k1{param.k1}_k2{param.k2}", '状态': '无结果'})
                    results.append({
                        'name': param.name,
                        'barCnt': param.barCnt,
                        'period': param.period,
                        'days': param.days,
                        'k1': param.k1,
                        'k2': param.k2,
                        'error': 'Process did not return result',
                        'net_profit': 0,
                        'win_rate': 0,
                        'max_drawdown': 0,
                        'total_trades': 0,
                        'win_trades': 0,
                        'loss_trades': 0,
                        'total_profit': 0,
                        'total_fees': 0,
                        'total_profit_from_trades': 0,
                        'avg_profit': 0,
                        'max_profit': 0,
                        'max_loss': 0,
                        'final_balance': param.init_capital,
                        'total_return_pct': 0,
                        '_idx': idx
                    })
                
                # 更新进度条
                pbar.update(1)
            
            # 如果没有进程完成，短暂等待
            if len(finished_indices) == 0:
                import time
                time.sleep(0.1)
    finally:
        pbar.close()
    
    # 按索引排序结果（确保顺序正确）
    results.sort(key=lambda x: x.get('_idx', 999999))
    
    # 移除临时索引字段
    for result in results:
        result.pop('_idx', None)
    
    # 保存最终结果
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values(by='net_profit', ascending=False)
    df_results.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✨ 参数探索完成！结果已保存到: {output_file}")
    
    # 显示Top 10结果
    if 'net_profit' in df_results.columns and len(df_results) > 0:
        print("\n📊 Top 10 净收益最高的参数组合:")
        top10 = df_results.nlargest(10, 'net_profit')[['name', 'days', 'k1', 'k2', 'net_profit', 'win_rate', 'max_drawdown']]
        print(top10.to_string(index=False))
    
    return df_results

def on_stra_dual_thrust_backtest(param: StraDualThrustBtParam, result_queue: multiprocessing.Queue, idx: int, silence: bool = True):
    """
    在独立进程中运行单次回测的工作函数
    
    这个函数会在子进程中执行，每次都会创建新的引擎实例，
    避免单例模式导致的状态污染问题。
    
    Args:
        param: StraDualThrustBtParam 对象
        result_queue: 结果队列
        idx: 任务索引（用于排序）
        silence: 是否静默输出
    """

    # 重定向stdout和stderr到devnull，禁止子进程输出
    if silence:
        silence_output()

    engine = None
    try:
        
        # 创建回测引擎（每个进程都是全新的实例）
        engine = WtBtEngine(EngineType.ET_CTA, logCfg=param.logcfg_file, outDir=param.outputs_path)
        
        # 初始化引擎
        # 处理文件路径：如果提供了完整路径，提取相对于 common_path 的相对路径或文件名
        def get_relative_path(full_path, base_path, default_name):
            if not full_path:
                return default_name
            if os.path.isabs(full_path):
                # 如果是绝对路径，尝试计算相对于 base_path 的相对路径
                try:
                    rel_path = os.path.relpath(full_path, base_path)
                    return rel_path if not rel_path.startswith('..') else os.path.basename(full_path)
                except:
                    return os.path.basename(full_path)
            return full_path
        
        engine.init(
            folder=param.common_path,
            cfgfile=param.configbt_file,
            commfile=get_relative_path(param.comm_file, param.common_path, "stk_comms.json"),
            contractfile=get_relative_path(param.contract_file, param.common_path, "stocks.json"),
            holidayfile=get_relative_path(param.holiday_file, param.common_path, None),
            sessionfile=get_relative_path(param.session_file, param.common_path, None),
        )
        engine.configBacktest(param.start_time, param.end_time)
        engine.configBTStorage(mode="csv", path=param.storage_path)
        engine.commitBTConfig()
        
        # 创建策略
        straInfo = StraDualThrust(
            name=param.name,
            code=param.code,
            barCnt=param.barCnt,
            period=param.period,
            days=param.days,
            k1=param.k1,
            k2=param.k2,
            isForStk=param.isForStk
        )
        engine.set_cta_strategy(straInfo)
        
        # 运行回测
        engine.run_backtest()
        
        # 提取指标
        result = extract_metrics_from_stra_dual_thrust_backtest(param, param.outputs_path, param.init_capital)

        # 释放回测引擎
        engine.release_backtest()
        
        # 删除策略输出目录和日志文件以节省磁盘空间
        strategy_dir = os.path.join(param.outputs_path, param.name)
        try:
            if os.path.exists(strategy_dir):
                shutil.rmtree(strategy_dir)
        except Exception as e:
            # 删除失败不影响结果，只记录警告
            pass
        
        # 删除策略对应的日志文件
        logs_dir = os.path.join(param.outputs_path, 'logs')
        strategy_log_file = os.path.join(logs_dir, f'Strategy_{param.name}.log')
        try:
            if os.path.exists(strategy_log_file):
                os.remove(strategy_log_file)
        except Exception as e:
            # 删除失败不影响结果
            pass

        # 添加索引用于排序
        result['_idx'] = idx
        result_queue.put(result)
    except Exception as e:
        # 确保资源清理
        if engine is not None:
            try:
                engine.release_backtest()
            except:
                pass
        
        # 返回错误结果（确保包含所有必需字段）
        result_queue.put({
            'name': param.name,
            'barCnt': param.barCnt,
            'period': param.period,
            'days': param.days,
            'k1': param.k1,
            'k2': param.k2,
            'error': str(e),
            'net_profit': 0,
            'win_rate': 0,
            'max_drawdown': 0,
            'total_trades': 0,
            'win_trades': 0,
            'loss_trades': 0,
            'total_profit': 0,
            'total_fees': 0,
            'total_profit_from_trades': 0,
            'avg_profit': 0,
            'max_profit': 0,
            'max_loss': 0,
            'final_balance': param.init_capital,
            'total_return_pct': 0,
            '_idx': idx
        })


def extract_metrics_from_stra_dual_thrust_backtest(param: StraDualThrustBtParam, outputs_path: str, init_capital: float) -> Dict[str, Any]:
    """
    从回测结果中提取关键指标（工作函数版本）
    使用 WtBtAnalyst 提供的专业计算方法
    
    Args:
        param: StraDualThrustBtParam 对象
        outputs_path: 输出目录
        init_capital: 初始资金
        
    Returns:
        包含关键指标的字典
    """
    import os
    import json
    import pandas as pd
    from wtpy.apps.WtBtAnalyst import summary_analyze, do_trading_analyze
    
    strategy_name = param.name
    strategy_dir = os.path.join(outputs_path, strategy_name)
    json_file = os.path.join(strategy_dir, f"{strategy_name}.json")
    closes_file = os.path.join(strategy_dir, "closes.csv")
    funds_file = os.path.join(strategy_dir, "funds.csv")
    
    # 基础参数信息
    result = {
        'name': strategy_name,
        'barCnt': param.barCnt,
        'period': param.period,
        'days': param.days,
        'k1': param.k1,
        'k2': param.k2,
    }
    
    # 初始化默认值
    result['total_profit'] = 0
    result['total_fees'] = 0
    result['net_profit'] = 0
    result['total_trades'] = 0
    result['win_trades'] = 0
    result['loss_trades'] = 0
    result['win_rate'] = 0
    result['total_profit_from_trades'] = 0
    result['avg_profit'] = 0
    result['max_profit'] = 0
    result['max_loss'] = 0
    result['max_drawdown'] = 0
    result['final_balance'] = init_capital
    result['total_return_pct'] = 0
    
    try:
        # 读取数据文件
        if not os.path.exists(funds_file) or not os.path.exists(closes_file):
            return result
        
        df_funds = pd.read_csv(funds_file)
        df_closes = pd.read_csv(closes_file)
        
        if len(df_funds) == 0 or len(df_closes) == 0:
            return result
        
        # 确保 df_closes 有 fee 列（do_trading_analyze 需要）
        if 'fee' not in df_closes.columns:
            # 从 totalprofit 计算 fee：fee = profit - (totalprofit - totalprofit.shift(1))
            df_closes = df_closes.copy()
            df_closes['fee'] = df_closes['profit'] - df_closes['totalprofit'] + df_closes['totalprofit'].shift(1).fillna(value=0)
        
        # 使用 WtBtAnalyst 的 summary_analyze 获取资金曲线指标
        summary = summary_analyze(df_funds.copy(), capital=init_capital, rf=0.0, period=param.annual_trading_days)
        
        # 使用 WtBtAnalyst 的 do_trading_analyze 获取交易统计
        trading_stats_df = do_trading_analyze(df_closes.copy(), df_funds.copy())
        # do_trading_analyze 返回的 DataFrame 格式：
        # reset_index() 后，第一列是 'index'（指标名称），第二列是 0（值）
        trading_stats = {}
        if len(trading_stats_df) > 0:
            # 检查列名
            if 'index' in trading_stats_df.columns:
                # 使用列名访问
                trading_stats = dict(zip(trading_stats_df['index'], trading_stats_df[0]))
            else:
                # 如果没有列名，使用位置访问
                trading_stats = dict(zip(trading_stats_df.iloc[:, 0], trading_stats_df.iloc[:, 1]))
        
        # 从JSON文件读取总盈亏和手续费（用于兼容性）
        try:
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'fund' in data:
                        result['total_profit'] = data['fund'].get('total_profit', 0)
                        result['total_fees'] = data['fund'].get('total_fees', 0)
        except Exception as e:
            # 如果JSON读取失败，从交易统计中计算（在 safe_get 定义之后）
            pass
        
        # 定义 safe_get 函数，处理可能为 "N/A" 的值
        def safe_get(key, default=0):
            value = trading_stats.get(key, default)
            if value == "N/A" or value is None:
                return default
            try:
                return float(value) if isinstance(value, (int, float, str)) else default
            except (ValueError, TypeError):
                return default
        
        # 如果JSON中没有手续费信息，从交易统计中计算
        if result['total_fees'] == 0 and len(trading_stats) > 0:
            accnetprofit = safe_get('账户净盈亏', 0)
            trdnetprofit = safe_get('交易净盈亏', 0)
            if trdnetprofit != 0:
                result['total_fees'] = trdnetprofit - accnetprofit
        
        # 从 summary_analyze 获取资金曲线指标
        result['max_drawdown'] = summary.get('max_falldown', 0)
        result['total_return_pct'] = summary.get('total_return', 0)
        
        # 计算最终余额
        if len(df_funds) > 0:
            result['final_balance'] = df_funds['dynbalance'].iloc[-1] + init_capital
        
        # 从 do_trading_analyze 获取交易统计
        
        result['total_trades'] = int(safe_get('交易总数量', 0))
        result['win_trades'] = int(safe_get('盈利交易次数', 0))
        result['loss_trades'] = int(safe_get('亏损交易次数', 0))
        result['win_rate'] = safe_get('% 胜率', 0)
        result['total_profit_from_trades'] = safe_get('交易净盈亏', 0)
        result['avg_profit'] = safe_get('单次平均盈亏', 0)
        result['max_profit'] = safe_get('单笔最大盈利交易', 0)
        result['max_loss'] = safe_get('单笔最大亏损交易', 0)
        
        # 计算净收益率（百分比）
        if result['total_profit'] > 0 or result['total_fees'] > 0:
            result['net_profit'] = (result['total_profit'] - result['total_fees']) / init_capital * 100
        else:
            # 如果没有JSON数据，使用账户净盈亏计算
            accnetprofit = safe_get('账户净盈亏', 0)
            result['net_profit'] = (accnetprofit / init_capital * 100) if init_capital > 0 else 0
        
    except Exception as e:
        print(f"⚠️  提取指标失败 [{strategy_name}]: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return result
