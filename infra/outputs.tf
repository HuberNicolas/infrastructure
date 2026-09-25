output "ipv4" {
  description = "Point the DNS records (A) here."
  value       = hcloud_server.apps.ipv4_address
}

output "ipv6" {
  description = "Point the DNS records (AAAA) here."
  value       = hcloud_server.apps.ipv6_address
}

output "ssh" {
  value = "ssh root@${hcloud_server.apps.ipv4_address}"
}

output "coolify_setup_url" {
  description = "First login; create the admin account right away (the first visitor becomes admin)."
  value       = "http://${hcloud_server.apps.ipv4_address}:8000"
}
