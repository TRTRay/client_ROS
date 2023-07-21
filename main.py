import multiprocessing
import ctypes
from mqtter import MqtterProcess

# cloud server
# MQTT_HOST = '182.92.152.209'
# localhost
MQTT_HOST = '192.168.137.1'
# localhost with hardware link
# MQTT_HOST = '192.168.0.190'
MQTT_PORT = 1883

# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    '''运行标志'''
    _FLAG = multiprocessing.Value(ctypes.c_bool, False)
    '''数据队列'''
    DATA_QUEUE = multiprocessing.Queue()

    # 开启mqtt线程
    mqtter_process = MqtterProcess(MQTT_HOST, MQTT_PORT, _FLAG, DATA_QUEUE)
    mqtter_process.start()
