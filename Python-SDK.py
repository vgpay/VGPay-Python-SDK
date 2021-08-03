
'''vgpay接口对接程序'''
import time
from hashlib import md5
import requests


class Api_vgpay:

    #默认请求的最长响应时间（秒），超时报异常
    timeout = 10

    #接口名
    payment = '/api/v3/Payment'          #充币申请
    cancel_Payment = '/api/v3/CancelPayment' #撤销充币申请
    query_Recharge_Orders = '/api/v3/QueryRechargeOrder' #充币申请单查询
    withdrawal_apply = '/api/v3/Withdrawal'     #提币申请
    query_Withdrawal_Orders = '/api/v3/QueryWithdrawalOrder' #提币申请单查询

    #初始化参数（域名、秘钥、商户ID）
    def __init__(self,baseUrl='',secret_key='',businessId=''):
        '''
        :param baseUrl:  （必填）域名
        :param secret_key:  （必填）密钥
        :param businessId:  （必填）商户ID
        '''
        self.baseUrl = baseUrl
        self.secret_key = secret_key
        self.businessId = businessId

    #请求web数据
    def __request(self,submitType,url,data:dict):
        '''
        :param submitType: 请求类型post 、 get
        :param url:  接口地址
        :param data: 请求数据
        :return: 接口返回值
        '''
        data['businessId'] = self.businessId
        data['timeStamp'] = str(int(time.time()))
        md5_pwd = self.getMac(data)   #根据请求参数，返回mac值
        data['mac'] = md5_pwd
        temp = ''     #临时变量，存储请求参数拼接后的字符串
        key_list = list(data.keys())
        for i in key_list:
            if data.get(i) != '':
                temp = temp + i + '=' + data.get(i) + '&'
        data_str = temp.strip('&')
        # print(self.baseUrl+url+'?'+data_str)
        try:
            res = requests.request(submitType,self.baseUrl+url+'?'+data_str,timeout=10)  #发送请求并接收响应
        except:
            return {'msg':'请求响应超时，当前设置最长响应时间为：%d秒' %self.timeout}
        res.encoding = res.apparent_encoding
        print('a',res)
        data_res = res.json()     #将返回值转换为JSON格式
        try:
            if bool(data_res.get('data')) != True or data_res.get('code') != '200' or data_res.get('isSuccess') != True:
                return data_res
            bol = self.__verifyMac(data_res, data_res.get('mac'))  #验证接口返回的mac值
            if data_res.get('code') == '200' and bol != True:
                data_res['isSuccess'] = False
                data_res['code'] = 401
            return data_res
        except Exception as e:
            # print('返回结果处理异常：',e)
            pass
        return data_res

    #md5加密 32位 小写
    def md5Hash(self,data:str):
        '''
        :param data: 需要加密的字符串
        :return: md5加密后的数据  32位 小写
        '''
        new_md5 = md5()
        new_md5.update(data.encode(encoding='utf-8'))
        return new_md5.hexdigest()

    #获取mac值
    def getMac(self,data:dict):
        '''
        :param data: 参数
        :return: 加密后的数据
        '''
        temp_str = ''
        key_list = list(data.keys())
        key_list.sort()   #列表排序
        for i in key_list:
            if data.get(i) != '':
                temp_str = temp_str + i + '=' + data.get(i) + '&'
        temp_str = temp_str + 'secretKey=%s' %self.secret_key
        # print(temp_str)
        md5_pwd = self.md5Hash(temp_str.strip('&')) #删除字符串前后的&符号，进行加密
        # print(md5_pwd)
        return md5_pwd

    #mac验证
    def __verifyMac(self,data:dict,mac:str):
        '''
        :param data: 返回字符串
        :param mac: 返回对象
        :return: 签名相同返回True,否则返回False
        '''
        # 可以使用类似参数：{'data': {'address': None, 'orderNo': None, 'outOrderNo': None}, 'mac': None, 'isSuccess': False, 'code': 500, 'msg': 'server error!'}，如果'data'对应的字典中有其他集合，会产生异常
        res_mac = data.get('data')
        temp_str = ''
        key_list = list(res_mac.keys())
        key_list.sort()
        for i in key_list:
            if res_mac.get(i):
                temp_str = temp_str + i + '=' + str(res_mac.get(i)) + '&'
        temp_str = temp_str + 'secretKey=%s' % self.secret_key
        # print(temp_str)
        mac_data = self.md5Hash(temp_str)
        print(mac_data)
        # print(mac)
        return  mac_data == mac

    #充币申请
    def regUserInfo(self,outOrderNo:str='',paymentUserId:str='',coin:str='',amount:float=None,ordertype:str='',productName:str='',exData:str=''):
        '''
        :param outOrderNo: （必填）商户端订单号.由商家自定义，64个字符以内，仅支持字母、数字、下划线且需保证在商户端不重复
        :param paymentUserId: （选填）商户端用户标识,64个字符以内
        :param coin: （必填）币种标识(BTC、ETH、ERC20_USDT、TRC20_USDT)
        :param amount: （必填）支付数量,取值范围：[0.00001, ∞ ]
        :param ordertype: （必填）订单类型(0、消费 1、充值)
        :param productName: （选填）商品名称
        :param exData: （选填）商户扩展数据
        :return: 返回充币申请结果
        '''
        data = {}
        data['outOrderNo'] = outOrderNo
        if bool(paymentUserId):   #判断参数不为空
            data['paymentUserId'] = paymentUserId
        data['coin'] = coin
        data['amount'] = str(amount)
        data['orderType'] = ordertype
        if bool(productName):
            data['productName'] = productName
        if bool(exData):
            data['exData'] = exData
        return self.__request('post',self.payment,data)

    #撤销充币申请
    def cancelPayment(self, outOrderNo:str='',orderNo:str=''):
        '''
        :param outOrderNo: （选填），商户端订单号.由商家自定义，64个字符以内，仅支持字母、数字、下划线且需保证在商户端不重复
        :param orderNo: （选填），商户端用户标识,64个字符以内---(outOrderNo和orderNo不能同时为空)
        :return: 返回撤销充币申请结果，字典类型
        '''
        data = {}
        if bool(outOrderNo):
            data['outOrderNo'] = outOrderNo
        if bool(orderNo):
            data['orderNo'] = orderNo
        return self.__request('post', self.cancel_Payment, data)

    #充币申请单查询
    def queryRechargeOrders(self,outOrderNo:str='',orderNo:str='',paymentUserId:str='',coin:str='',txId:str=''):
        '''
        :param outOrderNo: （选填），商户端订单号.由商家自定义，64个字符以内，仅支持字母、数字、下划线且需保证在商户端不重复
        :param orderNo: （选填），平台订单号,64个字符以内---(outOrderNo和orderNo不能同时为空)
        :param paymentUserId: （选填），商户端用户标识,64个字符以内
        :param coin: （选填），币种标识(BTC、ETH、ERC20_USDT、TRC20_USDT)
        :param txId: （选填），链交易ID
        :return: 返回充币申请单查询结果，字典类型
        '''
        data = {}
        if bool(outOrderNo):
            data['outOrderNo'] = outOrderNo
        if bool(orderNo):
            data['orderNo'] = orderNo
        if bool(paymentUserId):
            data['paymentUserId'] = paymentUserId
        if bool(coin):
            data['coin'] = coin
        if bool(txId):
            data['txId'] = txId
        return self.__request('get',self.query_Recharge_Orders,data)

    #提币申请
    def withdrawal(self,outWithdrawalNo:str='',withdrawalUserId:str='',coin:str='',amount:float=None,address:str=''):
        '''
        :param outWithdrawalNo: （必填）商户端提币单号.由商家自定义，64个字符以内，仅支持字母、数字、下划线且需保证在商户端不重复
        :param withdrawalUserId: （选填）商户端用户标识,64个字符以内
        :param coin: （必填）币种标识(BTC、ETH、ERC20_USDT、TRC20_USDT)
        :param amount: （必填）提币数量
        :param address: （必填）提币地址
        :return: 返回提币申请结果，字典类型
        '''
        data = {}
        data['outWithdrawalNo'] = outWithdrawalNo
        if bool(withdrawalUserId):
            data['withdrawalUserId'] = withdrawalUserId
        data['coin'] = coin
        data['amount'] = str(amount)
        data['address'] = address
        return  self.__request('post', self.withdrawal_apply, data)

    #提币申请单查询
    def queryWithdrawalOrders(self,outWithdrawalNo:str='',withdrawalNo:str='',withdrawalUserId:str='',coin:str='',txId:str=''):
        '''
        :param outWithdrawalNo: （选填）商户端提币单号.由商家自定义，64个字符以内，仅支持字母、数字、下划线且需保证在商户端不重复
        :param withdrawalNo: （选填）平台提币单号,64个字符以内---(outOrderNo和orderNo不能同时为空)
        :param withdrawalUserId: （选填）商户端用户标识,64个字符以内
        :param coin: （选填）币种标识(BTC、ETH、ERC20_USDT、TRC20_USDT)
        :param txId: （选填）链交易ID
        :return: 返回提币申请单查询结果，字典类型
        '''
        data = {}
        if bool(outWithdrawalNo):
            data['outWithdrawalNo'] = outWithdrawalNo
        if bool(withdrawalNo):
            data['withdrawalNo'] = withdrawalNo
        if bool(withdrawalUserId):
            data['withdrawalUserId'] = withdrawalUserId
        if bool(coin):
            data['coin'] = coin
        if bool(txId):
            data['txId'] = txId
        return self.__request('get', self.query_Withdrawal_Orders, data)

if __name__ == '__main__':
    #初始化参数，依次传入（域名、秘钥、商户ID）
    vg = Api_vgpay()
    # data = vg.regUserInfo(outOrderNo='aaaaac',coin='TRC20_USDT',amount=1,ordertype='0')       #充币示例
    # data = vg.cancelPayment(outOrderNo='aaaaac')                                              #撤销充币示例
    # data = vg.queryRechargeOrders(outOrderNo='aaaaaa7')                                       #充币申请单查询示例
    # data = vg.withdrawal(outWithdrawalNo='abcde',coin='BTC',amount=10,address='4564687468')   #提币申请示例
    # data = vg.queryWithdrawalOrders(withdrawalNo='T202107135d0935fd62034acc817a7ba03d3b9489')                                  #提币申请单查询示例
    # print(data)
