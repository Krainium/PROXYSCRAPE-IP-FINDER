# IP Finder — Proxy IP Address Finder (ProxyScrape API)

A Python CLI tool that rotates through ProxyScrape proxy sessions to find an IP address matching a target prefix. Uses multi-threaded requests to cycle through session lifetimes rapidly, checking each resulting IP until a match is found.

---

## Features

- **ProxyScrape API integration** — built specifically for ProxyScrape's rotating residential proxy service
- **Credential file** — store your ProxyScrape credentials in an `env` file so you don't re-enter them every run
- **Multi-threaded** — 30 concurrent threads by default, configurable per run
- **Auto-rotating sessions** — increments the lifetime suffix on each attempt to get a fresh proxy IP
- **Live progress** — shows IPs as they're checked, unique count, and speed
- **Match detection** — stops immediately when a matching IP is found
- **Result logging** — saves matches to `results/found.txt` with timestamps
- **Stats summary** — total attempts, successes, failures, unique IPs, speed, and elapsed time
- **Styled output** — pyfiglet ASCII banner, color-coded messages
- **Graceful Ctrl+C** — stops cleanly and shows final stats
- **Works on Windows, macOS, and Linux**

---

## Preview

```
    ________     _______           __         
   /  _/ __ \   / ____(_)___  ____/ /__  _____
   / // /_/ /  / /_  / / __ \/ __  / _ \/ ___/
 _/ // ____/  / __/ / / / / / /_/ /  __/ /    
/___/_/      /_/   /_/_/ /_/\__,_/\___/_/     

  Proxy IP Address Finder (ProxyScrape API)
  Rotate through proxy sessions to find
  an IP matching your target prefix.

  ─────────────────────────────────────────────

  [+] Loaded ProxyScrape credentials from env file
  [*] Host:     rp.proxyscrape.com:6060
  [*] Username: kmw06dm2rq7k...
  [*] Password: el3x********

  ─────────────────────────────────────────────

  Enter target IP prefix (e.g. 192.168): 45.33

  [*] Target prefix: 45.33.*
  Concurrent threads [30]: 30
  Starting lifetime suffix [500]: 500

  ─────────────────────────────────────────────
  [Configuration]
  [*] Target:     45.33.*
  [*] Proxy:      rp.proxyscrape.com:6060
  [*] Threads:    30
  [*] Start at:   suffix 500
  ─────────────────────────────────────────────

  [!] Press Ctrl+C to stop at any time.

  [   10] IP: 104.238.51.12    | Unique: 9 | 12.3/s
  [   20] IP: 72.14.201.87     | Unique: 18 | 14.1/s
  [   30] IP: 198.52.100.6     | Unique: 24 | 13.8/s

  ★ MATCH FOUND: 45.33.72.119 ★
  [+] Username: kmw06dm2rq7kzy1-country-us-session-l9mwlagj47-lifetime-537
  [+] Lifetime suffix: 537
  [+] Saved to results/found.txt

  ─────────────────────────────────────────────
  [Stats]
  [*] Total attempts:   37
  [+] Successful:       34
  [-] Failed:           3
  [*] Unique IPs seen:  31
  [*] Speed:            13.5 checks/sec
  [*] Elapsed:          0m 2s
  ─────────────────────────────────────────────
```

---

## Requirements

- **Python 3.7+** — [Download here](https://www.python.org/downloads/)
- **ProxyScrape account** — [proxyscrape.com](https://proxyscrape.com) with a residential proxy plan
- One pip package:

```bash
pip install pyfiglet
```

No other dependencies — the script uses only Python built-in modules (`http.client`, `threading`, `base64`) for all proxy and network operations.

---

## Setup

### 1. Install pyfiglet

```bash
pip install pyfiglet
```

### 2. Configure credentials

Create an `env` file in the same folder as `ip-finder.py`:

```
proxy_host = 'rp.proxyscrape.com'
proxy_port = 6060
base_username = 'your-proxyscrape-username-here-country-us-session-abc123-lifetime-'
password = 'your-proxyscrape-password-here'
```

**Where to find these values:**

1. Log in to [proxyscrape.com](https://proxyscrape.com)
2. Go to your residential proxy dashboard
3. Copy your **username** and **password** from the connection details
4. The username should include your session parameters and end with `-lifetime-` (the script appends a rotating number after this)

### 3. Run

```bash
python ip-finder.py
```

---

## Usage

### With env file (recommended)

If your `env` file is configured, the script loads credentials automatically:

```bash
python ip-finder.py
```

You'll only be prompted for:
- **Target IP prefix** — the first octets to match (e.g. `192.168`, `45.33`, `104.238.51`)
- **Thread count** — how many concurrent connections (default: 30)
- **Starting suffix** — where to start the lifetime counter (default: 500)

### Without env file

If no `env` file exists or it's incomplete, the script falls back to manual input and prompts for all ProxyScrape details interactively.

### Stopping

Press **Ctrl+C** at any time. The script stops gracefully and shows your final stats.

---

## How It Works

1. **Session rotation** — ProxyScrape's residential proxies assign a different IP based on the `lifetime` parameter in the username. The script increments this number on every attempt to get a fresh IP.

2. **IP checking** — each thread connects through the proxy to `wtfismyip.com/text`, which returns the public IP address seen by the outside world.

3. **Prefix matching** — the returned IP is compared against your target prefix. If it starts with your prefix (e.g. `45.33`), it's a match.

4. **Multi-threading** — runs 30 threads simultaneously by default. Each thread gets a unique lifetime suffix, so they all hit different proxy sessions in parallel.

5. **Match found** — when a match is detected, the script saves the full username (with the working lifetime suffix) to `results/found.txt` and stops all threads.

---

## env File Format

The `env` file uses a simple `key = value` format:

```
proxy_host = 'rp.proxyscrape.com'
proxy_port = 6060
base_username = 'your-username-here-lifetime-'
password = 'your-password-here'
```

| Field | Description |
|-------|-------------|
| `proxy_host` | ProxyScrape proxy hostname |
| `proxy_port` | ProxyScrape proxy port |
| `base_username` | Your ProxyScrape username ending with `-lifetime-` |
| `password` | Your ProxyScrape password |

- Values can be wrapped in single quotes, double quotes, or no quotes
- Lines starting with `#` are treated as comments
- Empty lines are ignored
- The file must be in the same directory as `ip-finder.py`

### Username format

A typical ProxyScrape username looks like:

```
kmw06dm2rq7kzy1-country-us-state-newyork-session-l9mwlagj47-lifetime-
```

The script appends a number after `-lifetime-` (e.g. `-lifetime-500`, `-lifetime-501`, etc.) to rotate through different proxy sessions. Make sure your username ends with `-lifetime-`. If you forget the suffix, the script will add it automatically.

---

## Output

### Match file

When a matching IP is found, it's saved to `results/found.txt`:

```
[2026-03-15_16-30-00] IP: 45.33.72.119 | Username: kmw06dm2rq7kzy1-country-us-session-abc-lifetime-537 | Suffix: 537
```

Each match is appended to the file, so previous results are preserved across runs.

### Stats

After every run (match found or Ctrl+C), the script shows:

| Stat | Description |
|------|-------------|
| Total attempts | Number of proxy connections tried |
| Successful | Connections that returned an IP |
| Failed | Connections that timed out or errored |
| Unique IPs seen | How many different IPs were returned |
| Speed | Checks per second |
| Elapsed | Total run time |

---

## Configuration Tips

### Target prefix

The prefix can be any number of octets:

| Prefix | Matches | Specificity |
|--------|---------|-------------|
| `45` | 45.*.*.* | Very broad — fast to find |
| `45.33` | 45.33.*.* | Moderate — typical usage |
| `45.33.72` | 45.33.72.* | Narrow — takes longer |
| `45.33.72.119` | Exact IP | Very specific — may take a long time |

### Thread count

| Threads | Use case |
|---------|----------|
| 10 | Conservative, less likely to trigger rate limits |
| 30 | Default, good balance of speed and reliability |
| 50 | Aggressive, faster but more connection errors |
| 100 | Maximum speed, may overwhelm the proxy |

### Starting suffix

The default is 500. If you've already searched suffixes 500–1000 in a previous run, start at 1000 next time to avoid repeating the same sessions.

---

## Troubleshooting

### "env file is incomplete"

Make sure all four fields in the `env` file have values. The `base_username` and `password` fields cannot be empty.

### Connection errors / timeouts

- Check your internet connection
- Verify your ProxyScrape subscription is active
- Try reducing the thread count to 10
- ProxyScrape may rate-limit aggressive usage — the script only logs every 20th error to keep output clean

### No match found after many attempts

- Try a broader prefix (fewer octets)
- The target IP range may not exist in ProxyScrape's residential pool
- Try different session parameters in your username (different country, state)
- Increase the thread count and let it run longer

### "Missing required package: pyfiglet"

```bash
pip install pyfiglet
```

If you have both Python 2 and 3:
```bash
pip3 install pyfiglet
```

---

## File Structure

```
ip-finder.py    # Main script
env             # ProxyScrape credentials (you fill this in)
results/
  found.txt     # Matching IPs saved here
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| [pyfiglet](https://pypi.org/project/pyfiglet/) | ASCII art banner |

All networking is handled by Python's built-in `http.client` module — no requests library needed.
