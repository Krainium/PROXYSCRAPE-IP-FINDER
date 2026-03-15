#!/usr/bin/env python3

import http.client
import os
import sys
import base64
import time
import threading
from datetime import datetime

try:
    import pyfiglet
except ImportError:
    print("Missing required package: pyfiglet")
    print("Install it with: pip install pyfiglet")
    sys.exit(1)

lock = threading.Lock()
found_event = threading.Event()

stats = {
    "attempts": 0,
    "successes": 0,
    "failures": 0,
    "matches": 0,
    "start_time": None,
    "ips_seen": set(),
}

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "env")


def load_env():
    config = {
        "proxy_host": "",
        "proxy_port": 0,
        "base_username": "",
        "password": "",
    }

    if not os.path.isfile(ENV_FILE):
        return None

    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key == "proxy_host":
                config["proxy_host"] = value
            elif key == "proxy_port":
                try:
                    config["proxy_port"] = int(value)
                except ValueError:
                    pass
            elif key == "base_username":
                config["base_username"] = value
            elif key == "password":
                config["password"] = value

    return config


def print_banner():
    banner = pyfiglet.figlet_format("IP Finder", font="slant")
    print("\033[96m" + banner + "\033[0m")
    print("\033[93m  Proxy IP Address Finder (ProxyScrape API)\033[0m")
    print("\033[90m  Rotate through proxy sessions to find\033[0m")
    print("\033[90m  an IP matching your target prefix.\033[0m")
    print()
    print("\033[90m  ─────────────────────────────────────────────\033[0m")
    print()


def print_success(msg):
    print(f"\033[92m  [+] {msg}\033[0m")


def print_info(msg):
    print(f"\033[94m  [*] {msg}\033[0m")


def print_warn(msg):
    print(f"\033[93m  [!] {msg}\033[0m")


def print_error(msg):
    print(f"\033[91m  [-] {msg}\033[0m")


def print_found(msg):
    print(f"\n\033[92;1m  ★ {msg} ★\033[0m")


def print_stats():
    elapsed = time.time() - stats["start_time"]
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    rate = stats["attempts"] / elapsed if elapsed > 0 else 0
    unique = len(stats["ips_seen"])
    print()
    print("\033[90m  ─────────────────────────────────────────────\033[0m")
    print(f"\033[96m  [Stats]\033[0m")
    print_info(f"Total attempts:   {stats['attempts']:,}")
    print_success(f"Successful:       {stats['successes']:,}")
    print_error(f"Failed:           {stats['failures']:,}")
    print_info(f"Unique IPs seen:  {unique:,}")
    print_info(f"Speed:            {rate:.1f} checks/sec")
    print_info(f"Elapsed:          {mins}m {secs}s")
    print("\033[90m  ─────────────────────────────────────────────\033[0m")


def check_ip(target_prefix, proxy_host, proxy_port, username, password, lifetime_suffix):
    if found_event.is_set():
        return

    current_username = f"{username}{lifetime_suffix}"
    auth = base64.b64encode(f"{current_username}:{password}".encode()).decode("ascii")
    headers = {"Proxy-Authorization": f"Basic {auth}"}

    conn = http.client.HTTPConnection(proxy_host, proxy_port, timeout=15)
    try:
        conn.set_tunnel("wtfismyip.com", headers=headers)
        conn.request("GET", "/text")
        response = conn.getresponse()

        if response.status == 200:
            ip_address = response.read().decode().strip()

            with lock:
                stats["attempts"] += 1
                stats["successes"] += 1
                stats["ips_seen"].add(ip_address)

            if ip_address.startswith(target_prefix):
                with lock:
                    stats["matches"] += 1

                print_found(f"MATCH FOUND: {ip_address}")
                print_success(f"Username: {current_username}")
                print_success(f"Lifetime suffix: {lifetime_suffix}")

                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

                if not os.path.exists("results"):
                    os.makedirs("results")

                filepath = os.path.join("results", "found.txt")
                with open(filepath, "a") as f:
                    f.write(f"[{timestamp}] IP: {ip_address} | Username: {current_username} | Suffix: {lifetime_suffix}\n")

                print_success(f"Saved to {filepath}")
                print_stats()
                found_event.set()
            else:
                attempt_num = stats["attempts"]
                if attempt_num % 10 == 0:
                    unique = len(stats["ips_seen"])
                    elapsed = time.time() - stats["start_time"]
                    rate = attempt_num / elapsed if elapsed > 0 else 0
                    print(f"\033[90m  [{attempt_num:>5}] IP: {ip_address:<16} | Unique: {unique} | {rate:.1f}/s\033[0m")
        else:
            with lock:
                stats["attempts"] += 1
                stats["failures"] += 1
            if stats["failures"] % 20 == 0:
                print_warn(f"HTTP {response.status} {response.reason} (suffix: {lifetime_suffix})")
    except (http.client.RemoteDisconnected, http.client.HTTPException, ConnectionError, OSError, TimeoutError) as e:
        with lock:
            stats["attempts"] += 1
            stats["failures"] += 1
        if stats["failures"] % 20 == 0:
            print_error(f"Connection error: {str(e)[:60]}")
    finally:
        conn.close()


def main():
    print_banner()

    config = load_env()

    if config and config["proxy_host"] and config["base_username"] and config["password"] and config["proxy_port"] > 0:
        proxy_host = config["proxy_host"]
        proxy_port = config["proxy_port"]
        username_base = config["base_username"]
        password = config["password"]

        masked_user = username_base[:12] + "..." if len(username_base) > 12 else username_base
        masked_pass = password[:4] + "*" * (len(password) - 4) if len(password) > 4 else "****"

        print_success("Loaded ProxyScrape credentials from env file")
        print_info(f"Host:     {proxy_host}:{proxy_port}")
        print_info(f"Username: {masked_user}")
        print_info(f"Password: {masked_pass}")
        print()
    else:
        if config is None:
            print_warn(f"No env file found at: {ENV_FILE}")
        else:
            print_warn("env file is incomplete — some fields are empty.")
        print_info("Fill in your ProxyScrape details in the env file:")
        print(f"\033[90m    proxy_host = 'rp.proxyscrape.com'\033[0m")
        print(f"\033[90m    proxy_port = 6060\033[0m")
        print(f"\033[90m    base_username = 'your-username-here-lifetime-'\033[0m")
        print(f"\033[90m    password = 'your-password-here'\033[0m")
        print()

        proxy_host = input("\033[97m  Proxy host [rp.proxyscrape.com]: \033[0m").strip() or "rp.proxyscrape.com"
        proxy_port_str = input("\033[97m  Proxy port [6060]: \033[0m").strip() or "6060"
        try:
            proxy_port = int(proxy_port_str)
        except ValueError:
            print_error("Invalid port number.")
            return

        username_base = input("\033[97m  Username base (with -lifetime- suffix): \033[0m").strip()
        if not username_base:
            print_error("Username base is required.")
            return

        password = input("\033[97m  Password: \033[0m").strip()
        if not password:
            print_error("Password is required.")
            return

    if not username_base.endswith("-lifetime-"):
        if not username_base.endswith("-"):
            username_base += "-"
        if "lifetime" not in username_base:
            username_base += "lifetime-"

    print("\033[90m  ─────────────────────────────────────────────\033[0m")
    print()

    target_prefix = input("\033[97m  Enter target IP prefix (e.g. 192.168): \033[0m").strip()
    if not target_prefix:
        print_error("No prefix entered.")
        return

    print()
    print_info(f"Target prefix: {target_prefix}.*")

    threads_str = input("\033[97m  Concurrent threads [30]: \033[0m").strip() or "30"
    try:
        thread_count = int(threads_str)
    except ValueError:
        print_error("Invalid thread count.")
        return

    start_suffix_str = input("\033[97m  Starting lifetime suffix [500]: \033[0m").strip() or "500"
    try:
        start_suffix = int(start_suffix_str)
    except ValueError:
        print_error("Invalid suffix number.")
        return

    print()
    print("\033[90m  ─────────────────────────────────────────────\033[0m")
    print(f"\033[96m  [Configuration]\033[0m")
    print_info(f"Target:     {target_prefix}.*")
    print_info(f"Proxy:      {proxy_host}:{proxy_port}")
    print_info(f"Threads:    {thread_count}")
    print_info(f"Start at:   suffix {start_suffix}")
    print("\033[90m  ─────────────────────────────────────────────\033[0m")
    print()
    print_warn("Press Ctrl+C to stop at any time.")
    print()

    stats["start_time"] = time.time()
    lifetime_suffix = start_suffix

    try:
        while not found_event.is_set():
            threads = []
            for _ in range(thread_count):
                if found_event.is_set():
                    break
                t = threading.Thread(
                    target=check_ip,
                    args=(target_prefix, proxy_host, proxy_port, username_base, password, lifetime_suffix),
                )
                threads.append(t)
                t.start()
                lifetime_suffix += 1

            for t in threads:
                t.join(timeout=20)

    except KeyboardInterrupt:
        print()
        print_warn("Stopped by user.")
        found_event.set()

    if stats["matches"] == 0:
        print()
        print_warn("No matching IP found yet.")

    print_stats()
    print()
    print_info("Done.")
    print()


if __name__ == "__main__":
    main()
