import json
import math
import time
import matplotlib.pyplot as plt

# Генератор случайных чисел
class LCG:
    def __init__(self, seed=12345):
        self.a = 1103515245
        self.c = 12345
        self.m = 2**31
        self.state = seed

    def next(self):
        self.state = (self.a * self.state + self.c) % self.m
        return self.state / self.m

class Attack:
    def __init__(self, type, complexity):
        self.type = type
        self.complexity = complexity

# Генератор атак
class AttackGenerator:
    @staticmethod
    def generate(lcg, lambda_attacks):
        u = lcg.next()

        # Равномерное распределение
        attack_type = "DDoS" if lcg.next() < 0.5 else "Phishing"
        return Attack(attack_type, lcg.next())

# Функциональный блок: Firewall
class Firewall:
    def __init__(self, lcg):
        self.lcg = lcg

    def process(self, attack):
        if attack.type == "DDoS" and self.lcg.next() < 0.8:
            return True
        return False

# Функциональный блок: IDS
class IDS:
    def __init__(self, mu, sigma):
        self.mu = mu
        self.sigma = sigma

    def process(self, lcg):
        u1 = lcg.next()
        u2 = lcg.next()

        # Нормальное распределение (с использованием метода Бокса-Мюллера)
        z0 = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        return self.mu + z0 * self.sigma

# Функциональный блок: IPS
class IPS:
    def __init__(self, mu, sigma, block_rate):
        self.mu = mu
        self.sigma = sigma
        self.block_rate = block_rate

    def process(self, lcg):
        u1 = lcg.next()
        u2 = lcg.next()

        # Нормальное распределение (с использованием метода Бокса-Мюллера)
        z0 = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        processing_time = self.mu + z0 * self.sigma
        
        processing_time = max(processing_time, 0)

        if lcg.next() < self.block_rate:
            return processing_time, True
        return processing_time, False

# Основная функция моделирования
def simulate(config):
    lcg = LCG()
    firewall = Firewall(lcg)
    ids = IDS(config["ids_mu"], config["ids_sigma"])
    ips = IPS(config["ips_mu"], config["ips_sigma"], config["ips_block_rate"])

    total_blocked = 0
    total_detected = 0
    total_ips_blocked = 0
    total_successful = 0
    processing_times = []

    for _ in range(1_000_000):
        attack = AttackGenerator.generate(lcg, config["lambda_attacks"])
        
        # Firewall
        if firewall.process(attack):
            total_blocked += 1
            continue
            
        # IDS
        time_ids = ids.process(lcg)
        if lcg.next() < config["correct_detection"]:
            total_detected += 1
            continue
            
        # IPS
        time_ips, is_blocked = ips.process(lcg)
        if is_blocked:
            total_ips_blocked += 1
            continue
            
        processing_times.append(time_ids + time_ips)
        total_successful += 1

    return (total_blocked, total_detected, total_ips_blocked, 
            total_successful, sum(processing_times), processing_times)