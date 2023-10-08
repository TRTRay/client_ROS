from paho.mqtt import client as mqtt_client
import multiprocessing
import json
import os
from utils.utils import *


class MqtterProcess(multiprocessing.Process):
    def __init__(self, host, port, _flag, queue):
        super().__init__()
        self.broker = host
        self.port = port
        self._flag = _flag
        self.queue = queue
        self.keepalive = 60  # 与代理通信之间允许的最长时间段（以秒为单位）
        self.client = None
        with open("./static/deviceInform.json", 'r') as f:
            self.deviceInform = json.load(f)
        # self topic: /client/ROS/huanyu
        self.selfTopic = '/client/{0}/{1}'.format(self.deviceInform['devType'], self.deviceInform['deviceId'])

    def run(self):
        self.client = self.connect_mqtt()
        self.client.loop_start()
        while True:
            # 发送数据的部分，可以复用
            if self._flag.value and ~self.queue.empty():
                data = self.queue.get()
                self.client.publish(self.selfTopic + '/showdata/map', data, 2)

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            # 响应状态码为0表示连接成功
            if rc == 0:
                inform = json.dumps({
                    'timestamp': '',
                    'message': 'Device online',
                    'data': self._parse_inform()
                })
                self.publish('/client/online', inform)
                print("Connection returned with result code:" + str(rc))
            else:
                print("连接失败！")
            client.subscribe(
                '/broker/{0}/{1}/#'.format(self.deviceInform['devType'], self.deviceInform['deviceId']))

        def on_message(client, userdata, msg):
            print("Received message, topic:" + msg.topic + ' and payload:' + str(msg.payload))
            msg_topic = msg.topic
            msg_payload = json.loads(msg.payload)
            # 手动初始化
            if msg_topic.endswith('/config'):
                self._res_init(client, userdata, msg)
            # 更新设备参数
            if msg_topic.endswith('/update'):
                # 预留接口
                pass
            # 重启
            if msg_topic.endswith('/reboot'):
                self._res_reboot(client, userdata, msg)
            if msg_topic.endswith('/add'):
                # 预留接口
                pass
            if msg_topic.endswith('/remove'):
                # 预留接口
                pass
            # 开启slam
            if msg_topic.endswith('/start'):
                if self._flag.value:
                    self._stop()
                self._start()
            # 停止slam
            if msg_topic.endswith('/stop'):
                if self._flag.value:
                    self._stop()
            # 上传地图
            if msg_topic.endswith('/showmap'):
                self._res_showmap(client, userdata, msg)
        client = mqtt_client.Client()
        # # 设置账号密码（如果需要的话）
        # client.username_pw_set('username', 'password')
        client.on_connect = on_connect
        client.on_message = on_message
        # 设立遗嘱消息
        msg = json.dumps({
            'timestamp': '',
            'message': 'Device offline',
            'data': self._parse_inform()
        })
        client.will_set('/client/offline', payload=msg)
        client.connect(self.broker, self.port, self.keepalive)
        return client

    def subscribe(self, topic):
        self.client.subscribe(topic)  # 命令的Qos设置为0

    def publish(self, topic, msg):
        self.client.publish(topic, payload=msg)

    def _parse_inform(self):
        inform = {
            'deviceId': self.deviceInform['deviceId'],
            'devType': self.deviceInform['devType'],
            'stat': self.deviceInform['stat'],
            'param': self.deviceInform['param'],
            'position': self.deviceInform['position'],
            'ip': self.deviceInform['ip']
        }
        return inform

    # _res_showdata()
    def _start(self):
        inform = json.dumps({'message': '{0} received the request for start sampling'.format(self.deviceInform['deviceId'])})
        self.client.publish('/client/{0}/{1}/start'.format(self.deviceInform['devType'], self.deviceInform['deviceId']), inform)
        # 打开gmapping
        self.deviceInform['stat'] = 'working'
        self._flag.value = True

    def _stop(self):
        inform = json.dumps({'message': '{0} received the request for stop sampling'.format(self.deviceInform['deviceId'])})
        self.client.publish('/client/{0}/{1}/stop'.format(self.deviceInform['devType'], self.deviceInform['deviceId']), inform)
        # 关闭gmapping
        self.deviceInform['stat'] = 'on'
        self._flag.value = False

    def _res_init(self, client, userdata, msg):
        inform = json.dumps({'message': '{0} reinit successfully.'.format(self.deviceInform['deviceId'])})
        # 重新初始化
        # 依次执行脚本
        # 然后检查状态
        self.client.publish(self.selfTopic + "/update", payload=inform)

    def _res_reboot(self, client, userdata, msg):
        inform = json.dumps({'message': 'Acoustic8 received the request for rebooting'})
        self.client.publish(self.selfTopic + "/update", payload=inform)
        # 端设备回应broker已经收到消息，下面需要执行一个指令来重启设备
        inform = json.dumps({
            'timestamp': '',
            'message': 'Device offline',
            'data': self._parse_inform()
        })
        client.publish('/client/offline', payload=inform)
        os.system("sudo reboot")

    def _res_showmap(self, client, userdate, msg):
        # 本地保存地图，转换成二进制，发送
        pass
