locals {
  labels = {
    managed-by = "opentofu"
    stack      = var.name
  }
}

resource "hcloud_ssh_key" "admin" {
  name       = "${var.name}-admin"
  public_key = file(pathexpand(var.ssh_public_key_path))
  labels     = local.labels
}

resource "hcloud_firewall" "apps" {
  name   = var.name
  labels = local.labels

  rule {
    description = "SSH"
    direction   = "in"
    protocol    = "tcp"
    port        = "22"
    source_ips  = var.admin_cidrs
  }

  rule {
    description = "HTTP (Traefik, redirects to HTTPS and serves ACME challenges)"
    direction   = "in"
    protocol    = "tcp"
    port        = "80"
    source_ips  = ["0.0.0.0/0", "::/0"]
  }

  rule {
    description = "HTTPS (Traefik)"
    direction   = "in"
    protocol    = "tcp"
    port        = "443"
    source_ips  = ["0.0.0.0/0", "::/0"]
  }

  rule {
    description = "HTTP/3 (Traefik)"
    direction   = "in"
    protocol    = "udp"
    port        = "443"
    source_ips  = ["0.0.0.0/0", "::/0"]
  }

  dynamic "rule" {
    for_each = var.coolify_setup_port_open ? [1] : []
    content {
      description = "Coolify dashboard before it has a domain"
      direction   = "in"
      protocol    = "tcp"
      port        = "8000"
      source_ips  = var.admin_cidrs
    }
  }
}

resource "hcloud_server" "apps" {
  name         = var.name
  server_type  = var.server_type
  location     = var.location
  image        = var.image
  ssh_keys     = [hcloud_ssh_key.admin.id]
  firewall_ids = [hcloud_firewall.apps.id]
  backups      = var.backups
  labels       = local.labels

  delete_protection  = var.protected
  rebuild_protection = var.protected

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  user_data = file("${path.module}/cloud-init.yaml")

  lifecycle {
    # cloud-init only runs on the first boot; changing it (or a newer image) must not replace the server
    ignore_changes = [user_data, image]
  }
}
