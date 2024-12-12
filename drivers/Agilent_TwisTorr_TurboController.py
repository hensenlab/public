# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import serial

STATUS = {0 : 'Stop', 1 : 'Waiting intlk', 2 : 'Starting', 3 : 'Auto-tuning', 4 : 'Braking', 5 : 'Normal', 6 : 'Fail'}


class AgilentTwisTorr:
    
    def __init__(self,name,address='COM10', **kwargs):
        
        self.s = serial.Serial('COM10', timeout=1)
        

    def _crc_bytes(self,m):
        crc=0
        for c in m:
            crc = crc ^ c
        return hex(crc).upper()[-2:].encode('ascii')
    
    
    
    def _read_window(self, window : str, write=False, data=None):
        self.s.read_all()
        stx = b'\x02'
        addr = b'\x80'
        w_b = window.encode('ascii')
        rd = b'\x31' if write else b'\x30'
        data = data.encode('ascii') if write else b'' #
        etx = b'\x03'
        m_b = addr + w_b + rd + data + etx
        crc = self._crc_bytes(m_b)
        m_t = stx + m_b + crc
        self.s.write(m_t)
        
        d = self.s.read_until(expected = etx)# %%
        d_crc = self.s.read(size=2)
        
        crc_ret = self._crc_bytes(d[1:])
        if d_crc!= crc_ret:
            raise Exception(f'Message checksum error: message: {d}')

        if write:
            assert d[:2] == m_t[:2] 
            assert d[2:] == b'\x06\x03'
        else:
            assert d[:6] == m_t[:6]
        ret_data = d[6:-1]
        return ret_data
    
    def get_status(self):
        """# 205 R N Pump status """
        d=self._read_window('205')
        status = STATUS[int(d)]
        print(f'Status: {status}')
        return status
    
    def get_driving_frequency(self):
        """# %% 203 R N Driving frequency in Hz"""
        d=self._read_window('203')
        f = int(d)
        print(f'Present frequency: {f:d} Hz')
        return f
    
    def get_pump_temperature(self):
        # %% 204 R N Pump temperature in °C 0 to 70
        d=self._read_window('204')
        T =  int(d)
        print(f'Pump temperature: {T} degC')
        return T
    
    def start_pump(self):
        self._read_window('000',True,'1') #turn on
    
    def stop_pump(self):
        self._read_window('000',True,'0')#turn off
    
        
if __name__ == '__main__':
    turbo = AgilentTwisTorr(name = 'turbo_controller')   
    
    message_sender = False
    
    if message_sender:
    
        from lib.io import slack_message_sender
        import time
        i = 0
        while 1:
            temp = float(turbo.get_pump_temperature())
            if temp > 48 and i < 10:
                slack_message_sender.send_slack_message_to_lab_alerts_channel(f'Warning turbo temp: {temp:.0f}')
                i+=1
                time.sleep(300)
            time.sleep(60)

    
    
    
    
# %% read status
# 205 R N Pump status 

# Stop = 0
# Waiting intlk = 1
# Starting = 2
# Auto-tuning = 3
# Braking = 4
# # Normal = 5
# # Fail = 6

# d=read_window('205')
# print(d)

# # %% 203 R N Driving frequency in Hz
# d=read_window('203')
# print(d)

# # %% 204 R N Pump temperature in °C 0 to 70
# d=read_window('204')
# print(d)

# # %%

# # %% Start pump
# d = read_window('000',True,'1') #turn on

# # %% Stop pump
# d = read_window('000',True,'0') #turn off



# %%





# %%
# 200 R N Pump current in mA dc
# 201 R N Pump voltage in Vdc
# 202 R N Pump power in W (pump current x pump
# voltage duty cycle)

# 204 R N Pump temperature in °C 0 to 70



# # %%
# mr = b'\x02\x80\x30\x30\x30\x31\x31\x03\x42\x33'
# s.write(mr)

# # %%
# s.read()
# # %%
# mr = b'\x80\x32\x30\x35\x30\x03'

# # %%

# mr=bytes.fromhex('803230353003')
# # %%
# crc=0
# for c in mr:
#     crc = crc ^ c
# mrcrc = mr+hex(crc).upper()[-2:].encode('ascii')
# print(mrcrc.hex())


# # %%
# s.write(m)

# # %%
# d=s.read(size=20)
# print(d.hex())
# # %%
# s.close()
