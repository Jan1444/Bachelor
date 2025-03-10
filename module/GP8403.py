# -*- coding: utf-8 -*
"""
  @file DFRobot_GP8403.py
  @brief This is a function library of the DAC module.
  @copyright  Copyright (c) 2010 DFRobot Co.Ltd (https://www.dfrobot.com)
  @license The MIT License (MIT)
  @author (jie.tang@dfrobot.com)
  @version V1.0
  @date 2022-03-03
  @URL https://github.com/DFRobot/DFRobot_GP8403.
"""
from __future__ import print_function

import datetime
import time

import RPi.GPIO as GPIO
import smbus

# Select DAC output voltage of 0-5V
OUTPUT_RANGE_5V = 0
# Select DAC output voltage of 0-10V
OUTPUT_RANGE_10V = 17
# Select to output from channel 0
CHANNEL0 = 1
# Select to output from channel 1
CHANNEL1 = 2
# Select to output from all the channels
CHANNELALL = 3


class DFRobot_GP8403:
    # Configure current sensor register
    GP8403_CONFIG_CURRENT_REG = 0x02
    # Store function timing start head
    GP8302_STORE_TIMING_HEAD = 0x02
    # The first address for entering store timing
    GP8302_STORE_TIMING_ADDR = 0x10
    # command 1 to enter store timing
    GP8302_STORE_TIMING_CMD1 = 0x03
    # command 2 to enter store timing
    GP8302_STORE_TIMING_CMD2 = 0x00
    # Total I2C communication cycle 5us
    I2C_CYCLE_TOTAL = 0.000005
    # The first half-cycle of the total I2C communication cycle 2us
    I2C_CYCLE_BEFORE = 0.000002
    # The second half cycle of the total I2C communication cycle 3us
    I2C_CYCLE_AFTER = 0.000003

    # Store procedure interval delay time: 10ms (1000us)
    # (should be more than 7ms, according to spec)
    GP8302_STORE_TIMING_DELAY = 0.0000010

    def __init__(self, addr):
        self._addr = addr
        self.outPutSetRange = 0x01
        self.voltage = 5000
        self._scl = 3
        self._sda = 2
        self.dataTransmission = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.i2c = smbus.SMBus(1)

    def begin(self):
        if self.i2c.read_byte(self._addr) != 0:
            return 0
        return 1

    def set_dac_out_range(self, mode):
        if mode == OUTPUT_RANGE_5V:
            self.voltage = 5000
        elif mode == OUTPUT_RANGE_10V:
            self.voltage = 10000
        self.i2c.write_word_data(self._addr, self.outPutSetRange, mode)

    def set_dac_out_voltage(self, data, channel):
        self.dataTransmission = ((float(data) / self.voltage) * 4095)
        self.dataTransmission = int(self.dataTransmission) << 4
        self._send_data(self.dataTransmission, channel)

    def store(self):
        self._start_signal()
        self._send_byte(self.GP8302_STORE_TIMING_HEAD, 0, 3, False)
        self._stop_signal()
        self._start_signal()
        self._send_byte(self.GP8302_STORE_TIMING_ADDR)
        self._send_byte(self.GP8302_STORE_TIMING_CMD1)
        self._stop_signal()

        self._start_signal()
        self._send_byte(self._addr << 1, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._stop_signal()

        time.sleep(self.GP8302_STORE_TIMING_DELAY)

        self._start_signal()
        self._send_byte(self.GP8302_STORE_TIMING_HEAD, 0, 3, False)
        self._stop_signal()
        self._start_signal()
        self._send_byte(self.GP8302_STORE_TIMING_ADDR)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2)
        self._stop_signal()

    def _start_signal(self):
        GPIO.output(self._scl, GPIO.HIGH)
        GPIO.output(self._sda, GPIO.HIGH)
        time.sleep(self.I2C_CYCLE_BEFORE)
        GPIO.output(self._sda, GPIO.LOW)
        time.sleep(self.I2C_CYCLE_AFTER)
        GPIO.output(self._scl, GPIO.LOW)
        time.sleep(self.I2C_CYCLE_TOTAL)

    def _stop_signal(self):
        GPIO.output(self._sda, GPIO.LOW)
        time.sleep(self.I2C_CYCLE_BEFORE)
        GPIO.output(self._scl, GPIO.HIGH)
        time.sleep(self.I2C_CYCLE_TOTAL)
        GPIO.output(self._sda, GPIO.HIGH)
        time.sleep(self.I2C_CYCLE_TOTAL)

    def _recv_ack(self, ack=0):
        error_time = 0
        GPIO.setup(self._sda, GPIO.IN)
        time.sleep(self.I2C_CYCLE_BEFORE)
        GPIO.output(self._scl, GPIO.HIGH)
        time.sleep(self.I2C_CYCLE_AFTER)
        while GPIO.input(self._sda) != ack:
            time.sleep(0.000001)
            error_time += 1
            if error_time > 250:
                break
        ack_ = GPIO.input(self._sda)
        time.sleep(self.I2C_CYCLE_BEFORE)
        GPIO.output(self._scl, GPIO.LOW)
        time.sleep(self.I2C_CYCLE_AFTER)
        GPIO.setup(self._sda, GPIO.OUT)
        return ack_

    def _send_byte(self, data, ack=0, bits=8, flag=True):
        i = bits
        data = data & 0xFF
        while i > 0:
            i -= 1
            if data & (1 << i):
                GPIO.output(self._sda, GPIO.HIGH)
            else:
                GPIO.output(self._sda, GPIO.LOW)
            time.sleep(self.I2C_CYCLE_BEFORE)
            GPIO.output(self._scl, GPIO.HIGH)
            time.sleep(self.I2C_CYCLE_TOTAL)
            GPIO.output(self._scl, GPIO.LOW)
            time.sleep(self.I2C_CYCLE_AFTER)
        if flag:
            return self._recv_ack(ack)
        else:
            GPIO.output(self._sda, GPIO.LOW)
            GPIO.output(self._scl, GPIO.HIGH)
        return ack
