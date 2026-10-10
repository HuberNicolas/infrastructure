#!/usr/bin/env bash
# Prepares a fresh Ubuntu 24.04 server for Coolify: updates, SSH hardening, firewall, swap, automatic security
# updates, Coolify. Safe to run again; every step checks its current state first.
#
#   ssh root@<server-ip> 'bash -s' < bootstrap/setup.sh
#
# Optional: limit SSH to your network
#   ssh root@<server-ip> 'ADMIN_CIDR=203.0.113.10/32 bash -s' < bootstrap/setup.sh

set -euo pipefail

ADMIN_CIDR="${ADMIN_CIDR:-any}"
SWAP_SIZE="${SWAP_SIZE:-4G}"
# Ports Coolify publishes on all interfaces: dashboard, realtime, terminal. They stay reachable over an SSH tunnel
COOLIFY_PORTS=(8000 6001 6002)

log() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

[[ $EUID -eq 0 ]] || { echo "Run as root." >&2; exit 1; }
grep -q 'VERSION_ID="24.04"' /etc/os-release || echo "Warning: tested on Ubuntu 24.04 only." >&2

# Key-only login would lock us out without a key
if [[ ! -s /root/.ssh/authorized_keys ]]; then
  echo "No SSH key in /root/.ssh/authorized_keys. First run on your machine: ssh-copy-id root@<server-ip>" >&2
  exit 1
fi

log "Updating packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get upgrade -yq
apt-get install -yq unattended-upgrades fail2ban ufw curl

log "Hardening SSH (key only; root keeps key login because Coolify manages the server as root)"
cat > /etc/ssh/sshd_config.d/10-hardening.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
sshd -t
systemctl reload ssh

log "Enabling automatic security updates and fail2ban"
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF
systemctl enable --now fail2ban

log "Swap ($SWAP_SIZE)"
if ! swapon --show | grep -q /swapfile; then
  fallocate -l "$SWAP_SIZE" /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
echo 'vm.swappiness = 10' > /etc/sysctl.d/90-swap.conf
sysctl -q --system

log "Firewall: SSH from $ADMIN_CIDR, HTTP and HTTPS from everywhere"
ufw default deny incoming
ufw default allow outgoing
if [[ "$ADMIN_CIDR" == any ]]; then
  ufw allow 22/tcp
else
  ufw allow from "$ADMIN_CIDR" to any port 22 proto tcp
fi
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw --force enable

# Docker publishes container ports through its own iptables chains, past ufw. DOCKER-USER is the hook Docker leaves
# for this: drop new outside connections to the Coolify ports there. A unit reapplies the rules after every start
log "Closing the Coolify ports to the outside (Docker bypasses ufw)"
cat > /usr/local/sbin/coolify-port-guard <<EOF
#!/usr/bin/env bash
set -euo pipefail
iface=\$(ip route show default | awk '{print \$5; exit}')
iptables -N DOCKER-USER 2>/dev/null || true
for port in ${COOLIFY_PORTS[*]}; do
  rule=(DOCKER-USER -i "\$iface" -p tcp -m conntrack --ctstate NEW --ctorigdstport "\$port" -j DROP)
  iptables -C "\${rule[@]}" 2>/dev/null || iptables -I "\${rule[@]}"
done
EOF
chmod 755 /usr/local/sbin/coolify-port-guard
cat > /etc/systemd/system/coolify-port-guard.service <<'EOF'
[Unit]
Description=Drop outside connections to the Coolify ports
After=docker.service
PartOf=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/coolify-port-guard

[Install]
WantedBy=docker.service
EOF
# Containers labelled infrastructure.egress=internet-only (Hermes Agent) may reach the internet, but not this server
# (SSH, the Coolify ports) and no private network (other containers, published ports, which Docker translates to
# container addresses). Their addresses change on every deployment, so a watcher rebuilds the rules whenever such a
# container starts or stops, and a timer repeats it in case a firewall reload removed the jumps
log "Limiting labelled containers to the internet"
cat > /usr/local/sbin/egress-guard <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
private=(10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 100.64.0.0/10 169.254.0.0/16 127.0.0.0/8)
for chain in EGRESS-GUARD-FWD EGRESS-GUARD-IN; do
  iptables -N "$chain" 2>/dev/null || iptables -F "$chain"
done
iptables -N DOCKER-USER 2>/dev/null || true
iptables -C DOCKER-USER -j EGRESS-GUARD-FWD 2>/dev/null || iptables -I DOCKER-USER -j EGRESS-GUARD-FWD
iptables -C INPUT -j EGRESS-GUARD-IN 2>/dev/null || iptables -I INPUT -j EGRESS-GUARD-IN
for id in $(docker ps -q --filter label=infrastructure.egress=internet-only); do
  for ip in $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' "$id"); do
    for net in "${private[@]}"; do
      iptables -A EGRESS-GUARD-FWD -s "$ip" -d "$net" -m conntrack --ctstate NEW -j DROP
    done
    iptables -A EGRESS-GUARD-IN -s "$ip" -m conntrack --ctstate NEW -j DROP
  done
done
EOF
chmod 755 /usr/local/sbin/egress-guard
cat > /etc/systemd/system/egress-guard.service <<'EOF'
[Unit]
Description=Limit labelled containers to the internet (rebuilt on container start and stop)
After=docker.service coolify-port-guard.service
PartOf=docker.service

[Service]
ExecStartPre=/usr/local/sbin/egress-guard
ExecStart=/bin/sh -c 'docker events --filter type=container --filter label=infrastructure.egress=internet-only --filter event=start --filter event=die --format x | while read -r _; do /usr/local/sbin/egress-guard; done'
Restart=always

[Install]
WantedBy=docker.service
EOF
cat > /etc/systemd/system/egress-guard-refresh.service <<'EOF'
[Unit]
Description=Reapply the egress guard rules

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/egress-guard
EOF
cat > /etc/systemd/system/egress-guard-refresh.timer <<'EOF'
[Unit]
Description=Reapply the egress guard rules every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload

log "Installing Coolify"
if [[ -f /data/coolify/source/.env ]]; then
  echo "Coolify is already installed; update it from its dashboard."
else
  # https://coolify.io/docs/get-started/installation
  curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
fi

systemctl enable coolify-port-guard.service
systemctl restart coolify-port-guard.service
systemctl enable egress-guard.service egress-guard-refresh.timer
systemctl restart egress-guard.service egress-guard-refresh.timer

log "Done"
cat <<'EOF'
Open the Coolify dashboard through an SSH tunnel (the port is closed to the outside):

  ssh -N -L 8000:localhost:8000 -L 6001:localhost:6001 -L 6002:localhost:6002 root@<server-ip>

then visit http://localhost:8000 and create the admin account.
EOF
