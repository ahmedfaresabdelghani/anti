#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import re
import pandas as pd
from netmiko import ConnectHandler
import os
import getpass

# ============================================
# Nodes Information
# ============================================
nodes = [
    {"name": "CA4-01", "ip": "10.18.4.27"},
    {"name": "CA4-02", "ip": "10.18.4.30"},
    {"name": "CA5-01", "ip": "10.21.2.9"},
    {"name": "CA5-02", "ip": "10.21.2.12"},
    {"name": "HQ-01", "ip": "10.30.2.26"},
    {"name": "HQ-02", "ip": "10.30.2.29"},
    {"name": "RMD-02", "ip": "10.28.3.32"},
    {"name": "RMD-01", "ip": "10.28.3.35"},
]

# ============================================
# SSH Credentials
# ============================================
username = input("Enter your username: ")
password = getpass.getpass("Enter your password: ")

# ============================================
# Regex pattern
# ============================================
pattern = re.compile(
    r"^(?P<interface>\S+)\s+(?P<state1>\S+)\s+(?P<state2>\S+)\s+(?P<desc>.+LR-(?P<lrnum>\d+))",
    re.MULTILINE
)

# ============================================
# Helper Functions
# ============================================
def extract_mtx_b(description):
    first_part = description.split("\\")[0]
    for prefix in ["HQ", "CA4", "CA5", "RMD", "BNS", "MNS", "ALX", "MKT", "TNT"]:
        if prefix in first_part:
            return prefix
    return first_part

def get_rate(interface):
    if interface.startswith("Hu"):
        return "100G"
    elif interface.startswith("Te"):
        return "10G"
    else:
        return "Unknown"

def get_status(state1, state2):
    return "Up" if state1 == "up" and state2 == "up" else "Down"

# ============================================
# Collect Data
# ============================================
results = []

for node in nodes:
    print(f"Connecting to {node['name']} ({node['ip']}) ...")

    device = {
        "device_type": "cisco_xr",
        "ip": node["ip"],
        "username": username,
        "password": password,
    }

    try:
        net_connect = ConnectHandler(**device)
        output = net_connect.send_command("show int des | i LR")
        net_connect.disconnect()

        for match in pattern.finditer(output):
            results.append({
                "MTX-A": node["name"],
                "MTX-B": extract_mtx_b(match.group("desc")),
                "interface": match.group("interface"),
                "rate": get_rate(match.group("interface")),
                "LR Number": int(match.group("lrnum")),
                "status": get_status(match.group("state1"), match.group("state2")),
            })

        print(f"Data collected from {node['name']} ✔\n")

    except Exception as e:
        print(f"Failed on {node['name']}: {e}\n")

    time.sleep(3)

# ============================================
# Export to LR_Database.xlsx
# ============================================
df = pd.DataFrame(
    results,
    columns=["MTX-A", "MTX-B", "interface", "rate", "LR Number", "status"]
)

output_file = "LR_Database.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl", mode="w") as writer:
    df.to_excel(writer, sheet_name="LR_Database", index=False)

print(f"\nDONE ✅ File '{output_file}' created successfully.\n")
