from flask import Flask, request, jsonify, render_template_string
import json
import os
import subprocess
import threading
import time
import sys

sys.path.insert(0, "/opt/sarayu-gateway")

import network_manager


app = Flask(__name__)

CONFIG_FILE = "/etc/sarayu-gateway/network.json"
BACKUP_FILE = "/etc/sarayu-gateway/network_backup.json"
PENDING_FILE = "/etc/sarayu-gateway/network_pending.json"


HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sarayu Gateway — Network Setup</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0f172a;
  --surface:#1e293b;
  --surface2:#273449;
  --border:#334155;
  --accent:#3b82f6;
  --accent-h:#2563eb;
  --danger:#ef4444;
  --success:#22c55e;
  --text:#f1f5f9;
  --sub:#94a3b8;
  --radius:14px;
  --shadow:0 24px 60px rgba(0,0,0,.55);
}
body{
  font-family:'Segoe UI',system-ui,sans-serif;
  background:var(--bg);
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:1rem;
  color:var(--text);
}

.orb{position:fixed;border-radius:50%;filter:blur(80px);opacity:.18;pointer-events:none;z-index:0}
.orb1{width:520px;height:520px;background:#3b82f6;top:-120px;left:-120px;animation:drift1 12s ease-in-out infinite alternate}
.orb2{width:400px;height:400px;background:#8b5cf6;bottom:-100px;right:-100px;animation:drift2 15s ease-in-out infinite alternate}
.orb3{width:300px;height:300px;background:#06b6d4;bottom:30%;left:50%;animation:drift3 10s ease-in-out infinite alternate}
@keyframes drift1{to{transform:translate(60px,80px)}}
@keyframes drift2{to{transform:translate(-40px,-60px)}}
@keyframes drift3{to{transform:translate(-80px,40px)}}

/* Three-column layout: Current | Main | Previous */
.layout{
  position:relative;z-index:1;
  display:flex;
  align-items:center;
  justify-content:center;
  gap:1.5rem;
  width:100%;
  max-width:1100px;
}
.layout > .card{flex:1 1 420px;max-width:420px}
.layout > .side{flex:1 1 300px;max-width:300px;padding:1.6rem 1.4rem}
.layout > .side-left{order:1}
.layout > .main{order:2}
.layout > .side-right{order:3}

@media (max-width:1000px){
  .layout{flex-direction:column;align-items:center}
  .layout > .main{order:1}
  .layout > .side-left{order:2}
  .layout > .side-right{order:3}
  .layout > .card,.layout > .side{width:100%;max-width:420px;flex:none}
}

.card{
  position:relative;z-index:1;
  background:rgba(30,41,59,.85);
  backdrop-filter:blur(18px);
  -webkit-backdrop-filter:blur(18px);
  border:1px solid var(--border);
  border-radius:var(--radius);
  padding:2.2rem 2rem;
  width:100%;max-width:420px;
  box-shadow:var(--shadow);
}

.logo{display:flex;align-items:center;gap:.7rem;margin-bottom:1.6rem}
.logo-icon{
  width:44px;height:44px;border-radius:10px;
  background:linear-gradient(135deg,#3b82f6,#8b5cf6);
  display:flex;align-items:center;justify-content:center;font-size:1.3rem;
  box-shadow:0 4px 16px rgba(59,130,246,.4);
}
.logo-text h1{font-size:1.1rem;font-weight:700;line-height:1.1}
.logo-text span{font-size:.75rem;color:var(--sub)}

.badge{
  display:inline-flex;align-items:center;gap:.4rem;
  font-size:.72rem;font-weight:600;letter-spacing:.04em;text-transform:uppercase;
  padding:.25rem .7rem;border-radius:999px;margin-bottom:1.4rem;
  background:rgba(59,130,246,.15);color:var(--accent);border:1px solid rgba(59,130,246,.3);
}
.badge-dot{width:6px;height:6px;border-radius:50%;background:currentColor;animation:pulse 1.4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}

.section-label{
  font-size:.7rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--sub);margin-bottom:1rem;
}

.field{margin-bottom:1rem}
.field label{display:block;font-size:.8rem;font-weight:600;color:var(--sub);margin-bottom:.4rem}
.input-wrap{position:relative}
.input-wrap input,.input-wrap select{
  width:100%;padding:.7rem .9rem;
  background:var(--surface2);border:1.5px solid var(--border);
  border-radius:8px;color:var(--text);font-size:.95rem;
  outline:none;transition:border-color .2s,box-shadow .2s;
  font-family:inherit;
}
.input-wrap input[type=password]{padding-right:2.6rem}
.input-wrap input:focus,.input-wrap select:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(59,130,246,.18)}
.input-wrap select{
  appearance:none;-webkit-appearance:none;cursor:pointer;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6'><path d='M0 0l5 6 5-6z' fill='%2394a3b8'/></svg>");
  background-repeat:no-repeat;background-position:right 12px center;padding-right:30px;
}
.eye-btn{
  position:absolute;right:.7rem;top:50%;transform:translateY(-50%);
  background:none;border:none;cursor:pointer;color:var(--sub);
  display:flex;align-items:center;padding:0;
  transition:color .2s;
}
.eye-btn:hover{color:var(--text)}

.radio-group{display:flex;gap:.6rem;margin-bottom:1rem}
.radio-group label{
  flex:1;display:flex;align-items:center;justify-content:center;gap:.4rem;
  padding:.6rem .5rem;border:1.5px solid var(--border);border-radius:8px;
  background:var(--surface2);color:var(--sub);font-size:.82rem;font-weight:600;
  cursor:pointer;transition:border-color .2s,color .2s;margin:0;
}
.radio-group input{width:auto;margin:0;accent-color:var(--accent)}
.radio-group label:has(input:checked){border-color:var(--accent);color:var(--text)}

.section{display:none}

.divider{display:flex;align-items:center;gap:.8rem;margin:1.4rem 0}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:var(--border)}
.divider span{font-size:.72rem;color:var(--sub);white-space:nowrap;letter-spacing:.06em;text-transform:uppercase}

.buttons{display:flex;flex-direction:column;gap:.6rem;margin-top:.4rem}
.btn{
  width:100%;padding:.75rem;border:none;border-radius:8px;
  font-size:.95rem;font-weight:600;cursor:pointer;
  display:flex;align-items:center;justify-content:center;gap:.5rem;
  transition:background .2s,transform .1s,box-shadow .2s;
  letter-spacing:.01em;font-family:inherit;
}
.btn:active{transform:scale(.98)}
.btn:disabled{opacity:.7;cursor:default}
.btn-primary{background:linear-gradient(135deg,#3b82f6,#2563eb);color:#fff;box-shadow:0 4px 18px rgba(59,130,246,.35)}
.btn-primary:hover{background:linear-gradient(135deg,#2563eb,#1d4ed8);box-shadow:0 6px 22px rgba(59,130,246,.45)}
.btn-ghost{background:transparent;border:1.5px solid var(--border);color:var(--sub)}
.btn-ghost:hover{border-color:var(--accent);color:var(--accent)}

.spin{
  width:18px;height:18px;border:2.5px solid rgba(255,255,255,.3);
  border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite;display:none;
}
@keyframes spin{to{transform:rotate(360deg)}}

#toast{
  position:fixed;top:1.2rem;left:50%;transform:translateX(-50%) translateY(-80px);
  z-index:999;background:var(--surface);border:1px solid var(--border);
  border-radius:10px;padding:.65rem 1.2rem;font-size:.85rem;font-weight:600;
  display:flex;align-items:center;gap:.5rem;box-shadow:var(--shadow);
  transition:transform .35s cubic-bezier(.34,1.56,.64,1);pointer-events:none;
  white-space:nowrap;max-width:90vw;
}
#toast.show{transform:translateX(-50%) translateY(0)}
#toast.success{color:var(--success);border-color:rgba(34,197,94,.3)}
#toast.error{color:var(--danger);border-color:rgba(239,68,68,.3)}
#toast.info{color:var(--accent);border-color:rgba(59,130,246,.3)}

/* Status side panels */
.status-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem}
.status-head .section-label{margin:0}
.side-title{
  font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  color:var(--accent);
}
.side-right .side-title{color:var(--sub)}
.refresh-btn{background:none;border:1px solid var(--border);color:var(--sub);
  border-radius:6px;font-size:.72rem;padding:.25rem .6rem;cursor:pointer;font-family:inherit}
.refresh-btn:hover{border-color:var(--accent);color:var(--accent)}
.status-card{background:var(--surface2);border:1px solid var(--border);
  border-radius:8px;padding:.7rem .9rem}
.srow{display:flex;justify-content:space-between;gap:1rem;font-size:.82rem;padding:.25rem 0}
.srow span:first-child{color:var(--sub)}
.srow span:last-child{font-weight:600;word-break:break-all;text-align:right}
.status-empty{font-size:.82rem;color:var(--sub)}
</style>
</head>
<body>

<div class="orb orb1"></div>
<div class="orb orb2"></div>
<div class="orb orb3"></div>

<div id="toast"></div>

<div class="layout">

  <!-- LEFT: Current configuration -->
  <div class="card side side-left">
    <div class="status-head">
      <div class="side-title">Current</div>
      <button type="button" class="refresh-btn" onclick="loadStatus()">Refresh</button>
    </div>
    <div class="status-card">
      <div id="statusCurrent" class="status-empty">Loading&#8230;</div>
    </div>
  </div>

  <!-- CENTER: Main form -->
  <div class="card main">

    <div class="logo">
      <div class="logo-icon">&#x1F4E1;</div>
      <div class="logo-text">
        <h1>Sarayu Gateway</h1>
        <span>Network configuration portal</span>
      </div>
    </div>

    <div class="badge">
      <span class="badge-dot"></span>
      Setup mode active
    </div>

    <form id="networkForm">

      <div class="section-label">Network mode</div>
      <div class="field">
        <label>How should this gateway connect?</label>
        <div class="input-wrap">
          <select id="mode" onchange="updateMode()">
            <option value="wifi">Wi-Fi</option>
            <option value="ethernet">Ethernet</option>
            <option value="both">Wi-Fi + Ethernet</option>
          </select>
        </div>
      </div>

      <div id="wifiSection" class="section">
        <div class="divider"><span>Wi-Fi network</span></div>

        <div class="field">
          <label>Network SSID</label>
          <div class="input-wrap">
            <input type="text" id="ssid" placeholder="Enter Wi-Fi SSID" autocomplete="off">
          </div>
        </div>

        <div class="radio-group">
          <label>
            <input type="radio" name="security" value="closed" checked onchange="updateSecurity()">
            Password protected
          </label>
          <label>
            <input type="radio" name="security" value="open" onchange="updateSecurity()">
            Open network
          </label>
        </div>

        <div id="passwordSection" class="field">
          <label>Password</label>
          <div class="input-wrap">
            <input type="password" id="password" placeholder="Enter password" autocomplete="off">
            <button type="button" class="eye-btn" onclick="toggleEye('password','pwEye')" title="Show/hide">
              <svg id="pwEye" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
          </div>
        </div>
      </div>

      <div id="ethernetSection" class="section">
        <div class="divider"><span>Ethernet</span></div>

        <div class="radio-group">
          <label>
            <input type="radio" name="ipmode" value="dhcp" checked onchange="updateIPMode()">
            Dynamic IP (DHCP)
          </label>
          <label>
            <input type="radio" name="ipmode" value="static" onchange="updateIPMode()">
            Static IP
          </label>
        </div>

        <div id="staticSection">
          <div class="field">
            <label>IP address</label>
            <div class="input-wrap"><input type="text" id="ip" placeholder="192.168.1.100"></div>
          </div>
          <div class="field">
            <label>Subnet mask</label>
            <div class="input-wrap"><input type="text" id="netmask" placeholder="255.255.255.0"></div>
          </div>
          <div class="field">
            <label>Gateway</label>
            <div class="input-wrap"><input type="text" id="gateway" placeholder="192.168.1.1"></div>
          </div>
          <div class="field">
            <label>DNS</label>
            <div class="input-wrap"><input type="text" id="dns" placeholder="8.8.8.8"></div>
          </div>
        </div>
      </div>

      <div id="prioritySection" class="section">
        <div class="divider"><span>Network priority</span></div>
        <div class="field">
          <label>Which connection should this gateway prefer?</label>
          <div class="input-wrap">
            <select id="priority">
              <option value="wifi_first">Wi-Fi &#8594; Ethernet</option>
              <option value="ethernet_first">Ethernet &#8594; Wi-Fi</option>
            </select>
          </div>
        </div>
      </div>

      <div class="buttons">
        <button type="button" class="btn btn-primary" id="saveBtn" onclick="saveConfiguration()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>
          <span id="saveBtnText">Save &amp; Connect</span>
          <div class="spin" id="saveSpin"></div>
        </button>
        <button type="button" class="btn btn-ghost" id="cancelBtn" onclick="cancelConfiguration()">
          <span id="cancelBtnText">Cancel</span>
          <div class="spin" id="cancelSpin"></div>
        </button>
      </div>

    </form>

  </div>

  <!-- RIGHT: Previous configuration -->
  <div class="card side side-right">
    <div class="status-head">
      <div class="side-title">Previous</div>
    </div>
    <div class="status-card">
      <div id="statusPrevious" class="status-empty">Loading&#8230;</div>
    </div>
  </div>

</div>

<script>
function $(id){return document.getElementById(id)}

function toast(msg,type,dur){
  var t=$('toast');
  t.className='';t.innerHTML=msg;
  void t.offsetWidth;
  t.className=type+' show';
  clearTimeout(t._t);
  t._t=setTimeout(function(){t.className=type},dur||3000);
}

function toggleEye(inputId,svgId){
  var inp=$(inputId),svg=$(svgId);
  if(inp.type==='password'){
    inp.type='text';
    svg.innerHTML='<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>';
  }else{
    inp.type='password';
    svg.innerHTML='<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
  }
}

function setLoading(btn,spin,text,label,state){
  $(btn).disabled=state;
  $(spin).style.display=state?'block':'none';
  $(text).style.display=state?'none':'inline';
  if(!state&&label)$(text).innerHTML=label;
}

function updateMode() {
    const mode = $("mode").value;
    $("wifiSection").style.display = (mode === "wifi" || mode === "both") ? "block" : "none";
    $("ethernetSection").style.display = (mode === "ethernet" || mode === "both") ? "block" : "none";
    $("prioritySection").style.display = mode === "both" ? "block" : "none";
}

function updateSecurity() {
    const security = document.querySelector('input[name="security"]:checked').value;
    $("passwordSection").style.display = security === "closed" ? "block" : "none";
}

function updateIPMode() {
    const ipmode = document.querySelector('input[name="ipmode"]:checked').value;
    $("staticSection").style.display = ipmode === "static" ? "block" : "none";
}

function saveConfiguration() {
    const mode = $("mode").value;
    const ssid = $("ssid").value.trim();
    const security = document.querySelector('input[name="security"]:checked').value;
    const password = $("password").value;
    const ipmode = document.querySelector('input[name="ipmode"]:checked').value;
    const ip = $("ip").value.trim();
    const netmask = $("netmask").value.trim();
    const gateway = $("gateway").value.trim();
    const dns = $("dns").value.trim();
    const priority = $("priority").value;

    if (mode === "wifi" || mode === "both") {
        if (!ssid) { toast("&#x26A0; Please enter Wi-Fi SSID","error"); return; }
        if (security === "closed" && password.length < 8) {
            toast("&#x26A0; Wi-Fi password must contain at least 8 characters","error");
            return;
        }
    }

    if ((mode === "ethernet" || mode === "both") && ipmode === "static") {
        if (!ip || !netmask || !gateway || !dns) {
            toast("&#x26A0; Please fill all static Ethernet fields","error");
            return;
        }
    }

    const config = {
        mode: mode,
        priority: priority,
        timeout: 20,
        wifi: { ssid: ssid, security: security, password: password },
        ethernet: { ip_mode: ipmode, ip: ip, netmask: netmask, gateway: gateway, dns: dns }
    };

    setLoading('saveBtn','saveSpin','saveBtnText',null,true);
    toast("Applying network configuration&#8230;","info",4000);

    fetch("/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        setLoading('saveBtn','saveSpin','saveBtnText','Save & Connect',false);
        if (data.success) {
            toast("&#x2705; Configuration saved &#8212; applying network settings&#8230;","success",5000);
            setTimeout(loadStatus, 8000);
        } else {
            toast("&#x274C; " + data.message,"error",5000);
        }
    })
    .catch(error => {
        console.error(error);
        setLoading('saveBtn','saveSpin','saveBtnText','Save & Connect',false);
        toast("Network change started &#8212; connection may temporarily disconnect.","info",5000);
    });
}

function cancelConfiguration() {
    const confirmCancel = confirm("Cancel configuration and return to the current network settings?");
    if (!confirmCancel) return;

    setLoading('cancelBtn','cancelSpin','cancelBtnText',null,true);
    toast("Restoring current network configuration&#8230;","info",4000);

    fetch("/cancel", { method: "POST" })
    .then(response => response.json())
    .then(data => {
        setLoading('cancelBtn','cancelSpin','cancelBtnText','Cancel',false);
        if (data.success) {
            toast("&#x2705; Current configuration restored.","success",4000);
            setTimeout(loadStatus, 8000);
        } else {
            toast("&#x274C; " + data.message,"error",4000);
        }
    })
    .catch(error => {
        console.error(error);
        setLoading('cancelBtn','cancelSpin','cancelBtnText','Cancel',false);
        toast("Restoring current network &#8212; connection may disconnect.","info",4000);
    });
}

function renderStatus(id, cfg) {
    const box = $(id);
    box.innerHTML = '';
    if (!cfg) { box.className = 'status-empty'; box.textContent = 'Not available'; return; }
    if (cfg.error) { box.className = 'status-empty'; box.textContent = 'Error: ' + cfg.error; return; }
    box.className = '';

    const rows = [['Mode', cfg.mode]];
    const wifi = cfg.wifi || {}, eth = cfg.ethernet || {};

    if (cfg.mode === 'both') rows.push(['Priority', cfg.priority]);
    if (cfg.mode === 'wifi' || cfg.mode === 'both') {
        rows.push(['Wi-Fi SSID', wifi.ssid || '-']);
        rows.push(['Security', wifi.security]);
        if (wifi.security === 'closed') rows.push(['Password', wifi.password || '-']);
    }
    if (cfg.mode === 'ethernet' || cfg.mode === 'both') {
        rows.push(['IP mode', eth.ip_mode]);
        if (eth.ip_mode === 'static') {
            rows.push(['IP', eth.ip], ['Netmask', eth.netmask],
                      ['Gateway', eth.gateway], ['DNS', eth.dns]);
        }
    }

    rows.forEach(function (r) {
        const d = document.createElement('div');
        d.className = 'srow';
        const a = document.createElement('span'); a.textContent = r[0];
        const b = document.createElement('span');
        b.textContent = (r[1] === undefined || r[1] === '') ? '-' : r[1];
        d.appendChild(a); d.appendChild(b);
        box.appendChild(d);
    });
}

function loadStatus() {
    fetch('/status')
    .then(r => r.json())
    .then(d => {
        renderStatus('statusCurrent', d.current);
        renderStatus('statusPrevious', d.previous);
    })
    .catch(() => {
        $('statusCurrent').textContent = 'Could not load status';
        $('statusPrevious').textContent = 'Could not load status';
    });
}

updateMode();
updateSecurity();
updateIPMode();
loadStatus();
</script>
</body>
</html>
"""


def load_current_config():

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def read_json_safe(path):

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        return {"error": str(e)}

    # Never send the Wi-Fi password to the browser
    wifi = data.get("wifi")
    if isinstance(wifi, dict) and wifi.get("password"):
        wifi["password"] = "********"

    return data


@app.route("/")
def index():

    return render_template_string(HTML)


@app.route("/status")
def status():

    return jsonify({
        "current": read_json_safe(CONFIG_FILE),
        "previous": read_json_safe(BACKUP_FILE)
    })


@app.route("/save", methods=["POST"])
def save():

    config = request.get_json()

    if not config:
        return jsonify({
            "success": False,
            "message": "No configuration received"
        })

    try:

        # Backup currently working configuration.
        # This backup is ONLY for restore after a failed Save.
        network_manager.backup_current_config()

        # Save new configuration temporarily.
        network_manager.save_config(
            config,
            PENDING_FILE
        )

        def apply():

            try:

                pending = network_manager.load_config(
                    PENDING_FILE
                )

                print("======================================")
                print("APPLYING NEW NETWORK CONFIGURATION")
                print("======================================")

                # Apply pending configuration.
                network_manager.apply_config(pending)

                # Only after successful connection,
                # make it the active boot configuration.
                network_manager.save_config(
                    pending,
                    CONFIG_FILE
                )

                if os.path.exists(PENDING_FILE):
                    os.remove(PENDING_FILE)

                print("======================================")
                print("NEW NETWORK CONFIGURATION ACTIVE")
                print("======================================")

                # Start boot network service again.
                # It will read ONLY network.json.
                result = subprocess.run(
                    [
                        "systemctl",
                        "start",
                        "sarayu-network.service"
                    ],
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    print(
                        "WARNING: Failed to start "
                        "sarayu-network.service"
                    )

                    if result.stderr:
                        print(result.stderr.strip())

                else:
                    print(
                        "Sarayu network service started"
                    )

            except Exception as e:

                print("======================================")
                print("NEW CONFIGURATION FAILED")
                print("ERROR:", e)
                print("======================================")

                # IMPORTANT:
                # Do NOT start sarayu-network.service here.
                # We want to remain in AP setup mode.

                try:

                    network_manager.restore_backup()

                    print(
                        "Previous configuration restored"
                    )

                    # Keep AP alive.
                    network_manager.start_ap()

                    print(
                        "AP remains active because "
                        "new configuration failed"
                    )

                except Exception as restore_error:

                    print(
                        "RESTORE ERROR:",
                        restore_error
                    )

                    network_manager.start_ap()

        threading.Thread(
            target=apply,
            daemon=True
        ).start()

        return jsonify({
            "success": True,
            "message": "Configuration is being applied"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        })


@app.route("/cancel", methods=["POST"])
def cancel():

    def restore():

        try:

            print("======================================")
            print("CANCEL: RE-APPLYING CURRENT NETWORK.JSON")
            print("======================================")

            # Discard any half-finished pending configuration
            if os.path.exists(PENDING_FILE):
                os.remove(PENDING_FILE)

            # Load the CURRENT configuration (not the backup)
            current = network_manager.load_config(CONFIG_FILE)

            # Apply it
            network_manager.apply_config(current)

            print("Current configuration applied successfully")

            # Start boot network service (reads ONLY network.json)
            result = subprocess.run(
                [
                    "systemctl",
                    "start",
                    "sarayu-network.service"
                ],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:

                print("Failed to start Sarayu network service")

                if result.stderr:
                    print(result.stderr.strip())

        except Exception as e:

            print("Cancel error:", e)
            print("Cancel failed - keeping AP active")

            network_manager.start_ap()

    threading.Thread(
        target=restore,
        daemon=True
    ).start()

    return jsonify({
        "success": True,
        "message": "Restoring current configuration"
    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=80,
        debug=False
    )
