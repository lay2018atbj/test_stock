from datetime import date, timedelta
import time
import re
import pandas as pd
import datetime
from tick_trade_api import DatafeedHqGenerator
from tick_trade_api.api import TradeAPI
import math

def symbol_convert(x):
    if x >= '600000':
        return x + '.SH'
    else:
        return x + '.SZ'


def up_limit(stock_price_list,time_delta,up_limit,pre):
    if len(stock_price_list) < 2:
        return False
    if len(stock_price_list) >= time_delta:
        last_price_list = stock_price_list[-time_delta:]
    else:
        last_price_list = stock_price_list[:]
    min_v = min(last_price_list)
    p = stock_price_list[-1]
    if (p-min_v) / pre >= up_limit:
        return True
    return False

    

def decsion_signal(stock_price_list,stock_volume_list,min_stock_volume,ret,new_price,pre_price,high_price,low_price,vol,high_vol_list,yestoday_agv_stock_volume,time_idx,start_max_10_list,signals_set,result):
    
    # 信号1: 15分钟涨幅超过1%，破前高
    if 'signal_1' in signals_set and up_limit(stock_price_list,15,0.01,pre_price) and new_price >= high_price:
        result['signal_1'] = 1
    
#     信号2: 连续10分钟，10分钟股价分钟级移动平均线保持0度以上，成交量缩量至昨日分时成交量一半以下
    if 'signal_2' in signals_set and len(stock_price_list) >= 20:
        tmp = 0
        for i in range(10):
            if stock_price_list[i+10] >= stock_price_list[i]:
                tmp += 1
        if tmp == 10 and vol <= 0.5 * yestoday_agv_stock_volume:  # stock_volume  yestoday_agv_stock_volume
            result['signal_2'] = 1
    
    
    # 信号3：5分钟涨幅2%
    if 'signal_3' in signals_set and up_limit(stock_price_list,5,0.02,pre_price):
        result['signal_3'] = 1
    
    
    # 信号4: 涨幅3.5% 破前高  #出现后是否重置
    if 'signal_4' in signals_set and ret > 0.035 and new_price >= high_price:
        result['signal_4'] = 1
    else:
        result['signal_4'] = 0
    
    
    # 信号5: 15分钟涨幅2%
    if 'signal_5' in signals_set and up_limit(stock_price_list,15,0.02,pre_price):
        result['signal_5'] = 1  
    
    
    # 信号6：跌破分时最低
    if 'signal_6' in signals_set and new_price <= low_price:
        result['signal_6'] = 1
    else:
        result['signal_6'] = 0
    
    
    # 信号7：10分钟涨1.5, 记一次 start_max_10
    start_max_10 = start_max_10_list[-1]
    if 'signal_7' in signals_set and up_limit(stock_price_list[start_max_10:],10,0.015,pre_price):
        start_max_10_list.append(time_idx)
        if 'signal_7' in result:
            # print('start_max_10',start_max_10)
            result['signal_7'] += 1
        else:
            result['signal_7'] = 1
            
    
    # 信号8：分时新高，成交量微微放大
    # 这个必须
    if new_price >= high_price:
        high_vol_list.append(vol) # stock_volume high_stock_volume_list TODO
 
    if 'signal_8' in signals_set and new_price >= high_price:
        if vol >= max(high_vol_list) and vol <= 2 * min(high_vol_list):
            result['signal_8'] = 1
    
        
    # 信号9，1小时涨2.5, 破前高 ,需要半小时开始
    if 'signal_9' in signals_set and len(stock_price_list) > 30 and up_limit(stock_price_list,60,0.025,pre_price) and new_price >= high_price:
        result['signal_9'] = 1
    
    
    # 信号10： 18分钟有一次缩量至昨日分时均量一半
    t_len = min(18,len(stock_volume_list))
    if 'signal_10' in signals_set and min(stock_volume_list[-t_len:]) <= 0.5 * yestoday_agv_stock_volume:
        result['signal_10'] = 1
    
    
    
    # 信号11   :18分钟移动平均线0度以上
    if 'signal_11' in signals_set and len(stock_price_list) >= 28:
        tmp = 0
        for i in range(18):
            if stock_price_list[i+10] >= stock_price_list[i]:
                tmp += 1
        if tmp == 18:
            result['signal_11'] = 1
    
    
    
    #信号12： 5分钟涨幅超过2%
    t_len = min(5,len(stock_price_list))
    if 'signal_12' in signals_set and t_len >= 2:
        last_5 =  stock_price_list[-t_len:]
        max_v = max(last_5)
        min_v = min(last_5)
        if  (last_5[-1]-min_v)/pre_price > 0.02:
            result['signal_12'] = 1     
    
    
    #信号13：分时成交量日内新低
    if 'signal_13' in signals_set and len(stock_volume_list) >= 2:
        if stock_volume_list[-1] <= min_stock_volume:
            min_stock_volume = stock_volume_list[-1]
            result['signal_13']  = 1 
        else:
            result['signal_13'] = 0
            
    #信号14：分时成交量缩量至昨日分时平均成交量以下
    if 'signal_14' in signals_set and stock_volume_list[-1] <= yestoday_agv_stock_volume:  # stock_volume  yestoday_agv_stock_volume
        result['signal_14'] = 1
    else:
        result['signal_14'] = 0
        
        
    #信号15：10分钟内最低点不跌破开盘5分钟最高价
    if 'signal_15' in signals_set and len(stock_price_list) > 10:
        last_10 =  stock_price_list[-10:]
        max_v = max(stock_price_list[:5])
        min_v = min(last_10)
        if  min_v >= max_v:
            result['signal_15'] = 1
        else:
            result['signal_15'] = 0
            
            
    #信号16：10分钟内涨2%
    if 'signal_16' in signals_set and up_limit(stock_price_list,10,0.02,pre_price):
        result['signal_16'] = 1


    #信号17：分钟成交量未放大至两倍
    
    if (len(stock_volume_list) > 0 and stock_volume_list[-1] <= 2 * min(stock_volume_list)) or ( len(high_vol_list) > 0 and stock_volume_list[-1] <= 2 * min(high_vol_list) ):
        result['signal_17'] = 1
    else:
        result['signal_17'] = 0
            
     
    #信号18：回踩50%
    if 'signal_18' in signals_set and new_price != low_price:
        if (high_price/low_price - 1) / (new_price/ low_price - 1) >= 2:
            result['signal_18'] = 1
        else:
            result['signal_18'] = 0

    return result


# 买入规则
    # TODO   buy_type
    #-------------------
    #----14日线上方 
    #--------100日均量线上方
    #------------高开1%以上
    #----------------开盘先跌         buy_type == 1
    #----------------开盘先涨         buy_type == 2
    #------------正常开
    #----------------开盘先跌         buy_type == 3
    #----------------开盘先涨         buy_type == 4
    #--------100日均量线下方          buy_type == 5
    #----14日线下方
    #--------100日均量线上方
    #------------高开1%以上
    #------------正常开
    #----------------开盘先跌         buy_type == 6
    #----------------开盘先涨         buy_type == 7
    #--------100日均量线下方          buy_type == 8
    # 开盘第一分钟对上面条件进行判断
# 14日均线价,100日量均线,今日股价列表,开盘价，1分钟价,最大价，最小价，昨日价，返回值int type
def buy_type_decision(avg_14_price,avg_100_vol,op,op1,max_op,min_op,pre):
    if avg_14_price > 0:
        # 100日均量线上方
        if avg_100_vol  > 0:
            # 高开
            if op / pre - 1 > 0.01:
                # 开盘先跌
                if op1 - op < 0 and (min_op - op) / pre < -0.01:
                    return 1
                elif op1 - op > 0 and (max_op - op) / pre > 0.01:
                    return 2
                else:
                    return -100
            # 正常开
            else:
                # 开盘先跌
                if op1 - op < 0 and (min_op - op) / pre < -0.01:
                    return 3
                elif op1 - op > 0 and (max_op - op) / pre > 0.01:
                    return 4
                else:
                    return -100
        else:
            return 5
    #14日均线下方
    else:
        # 100日均量线上方
        if avg_100_vol  > 0:
            if op / pre - 1 > 0.01:
                return -1
            else:
                # 开盘先跌
                if op1 - op < 0 and (min_op - op) / pre < -0.01:
                    return 6
                elif op1 - op > 0 and (max_op - op) / pre > 0.01:
                    return 7
                else:
                    return -100
        else:
            return 8
        
        
def stragegy_decision(buy_type,signals,today_strategy_list,p,high,low,ret,yestoday_ret):
    
    buy_signal = 0 
    buy_reason = ""
    buy_stragegy = ""
    
    if buy_type == 1:
        if 's9' in today_strategy_list and signals['signal_1'] >= 1 and p >= high:
            buy_signal = 1
            buy_reason = "[14日线上方,100日均量线上方,高开1%以上,开盘先跌] [15分钟涨幅超过1%，破前高]"
            buy_stragegy = 's9'
                
    elif buy_type == 2:
        if 's8' in today_strategy_list and  signals['signal_2'] >= 1:
            buy_signal = 1
            buy_reason = "[14日线上方,100日均量线上方,高开1%以上,开盘先涨] [连续10分钟，10分钟股价分钟级移动平均线保持0度以上，成交量缩量至昨日分时成交量一半以下]"
            buy_stragegy = 's8'
    
    elif buy_type == 3:
        if 's7' in today_strategy_list and signals['signal_5']  >= 1 and p >= high:
            buy_signal = 1
            buy_reason = "[14日线上方,100日均量线上方,正常开,开盘先跌] [15分钟涨幅超过2%，破前高]"
            buy_stragegy = 's7'
    
    elif buy_type == 4:
        if 's5' in today_strategy_list and  signals['signal_3']  >= 1 and yestoday_ret > 0.05 and signals['signal_2'] >= 1 :
            buy_signal = 1
            buy_reason = "[14日线上方,100日均量线上方,正常开,开盘先涨] [昨日大涨] [5分钟涨2%，10分钟股价移动平均0度以上，缩量至昨日平均成交量下]"
            buy_stragegy = 's5'

        elif 's6' in today_strategy_list and  signals['signal_3'] >= 1 and yestoday_ret < 0.05 and signals['signal_4'] >= 1  :
            buy_signal = 1
            buy_reason = "[14日线上方,100日均量线上方,正常开,开盘先涨] [昨日未大涨] [5分钟涨2%，3.5%突破买入]"
            buy_stragegy = 's6'

        elif 's4' in today_strategy_list and  signals['signal_5']  >= 1 and signals['signal_6'] >=1:
            buy_signal = 1
            buy_reason = "[14日线上方,100日均量线上方,正常开,开盘先涨]  [15分钟涨幅超过2%，跌破分时最低]"
            buy_stragegy = 's4'
    
        if  's3' in today_strategy_list and  signals['signal_5'] >= 1 and signals['signal_13'] >=1:
            buy_signal = 1
            buy_reason = "[14日线上方,100日均量线上方,正常开,开盘先涨]  [15分钟涨幅超过2%，分时成交量日内新低]"    
            buy_stragegy = 's3'


        if  's2' in today_strategy_list and  signals['signal_7'] >= 2 and signals['signal_4']  >=1:
            buy_signal = 1
            buy_reason = "[14日线上方,100日均量线上方,正常开,开盘先涨]  [10分钟涨幅超过1.5%两次，突破3.5%买入]"
            buy_stragegy = 's2'
    
        elif  's1' in today_strategy_list and  signals['signal_7']  >= 2 and signals['signal_14'] >=1:
            buy_signal = 1
            buy_reason = "[14日线上方,100日均量线上方,正常开,开盘先涨]  [10分钟涨幅超过1.5%两次，10分钟成交量缩量至昨日分钟量]"
            buy_stragegy = 's1'


    elif  buy_type == 5:
        if  's10' in today_strategy_list and  signals['signal_4']  >= 1 and signals['signal_12']  >=1:
            buy_signal = 1
            buy_reason = "[14日线上方,100日均量线下方]  [5分钟涨幅超过2%，超过3.5%, 破前高]"  # 需要改，有出入
            buy_stragegy = 's10'
    

    elif buy_type == 6:
        if  's14' in today_strategy_list and signals['signal_3']   >= 1 and yestoday_ret > 0.05 and signals['signal_15'] >= 1 :
            buy_signal = 1
            buy_reason = "[14日线下方,100日均量线上方,正常开,开盘先跌]  [5分钟涨2% ，10分钟内最低点不跌破开盘5分钟最高价]"
            buy_stragegy = 's14'

        if  's15' in today_strategy_list and signals['signal_3']  >= 1 and yestoday_ret < 0.05 and ret >= 0.025 and p >= high :
            buy_signal = 1
            buy_reason = "[14日线下方,100日均量线上方,正常开,开盘先跌] [15分钟涨2% 突破2.5%]"
            buy_stragegy = 's15'

    elif buy_type == 7:
        if  's13' in today_strategy_list and signals['signal_3']  >= 1 and yestoday_ret < 0.05 and signals['signal_4']  >= 1:
            buy_signal = 1
            buy_reason = "[14日线下方,100日均量线上方,正常开,开盘先涨] [昨日未大涨] [5分钟涨2%  3.5%突破买入]"
            buy_stragegy = 's13'

        elif  's12' in today_strategy_list and signals['signal_3']  >= 1 and yestoday_ret < 0.05  and p <= low:
            buy_signal = 1
            buy_reason = "[14日线下方,100日均量线上方,正常开,开盘先涨] [5分钟涨1.5% 跌破分时最低点]"
            buy_stragegy = 's12'

        if  's11' in today_strategy_list and  signals['signal_5']  >= 1 and signals['signal_6'] >=1 and signals['signal_17'] >= 1:
            buy_signal = 1
            buy_reason = "[14日线下方,100日均量线上方,正常开,开盘先涨] [10分钟涨幅超过2%，分钟成交量未放大至2倍，3.5%突破买入]" 
            buy_stragegy = 's11'
    
    elif buy_type == 8 :
        if  's16' in today_strategy_list and  signals['signal_5']  >= 1 and signals['signal_4'] >=1 and signals['signal_17']  >= 1:
            buy_signal = 1
            buy_reason = "[14日线下方,100日均量线下方] [15分钟涨2%  3.5%突破，成交量小于历史成交量2倍]"
            buy_stragegy = 's16'
        
        elif  's17' in today_strategy_list and  signals['signal_3']  >= 1 and  signals['signal_18']>= 1 : 
            buy_signal = 1
            buy_reason = "[14日线下方,100日均量线下方] [15分钟涨2% ，回踩50%]"
            buy_stragegy = 's17'
        
        elif  's18' in today_strategy_list and  signals['signal_8']  >= 1 and  signals['signal_9'] >= 1:
            buy_signal = 1
            buy_reason = "[14日线下方,100日均量线下方] [分时新高，成交量微微放大，1小时涨2.5%]"
            buy_stragegy = 's18'
            
    return buy_signal,buy_reason,buy_stragegy