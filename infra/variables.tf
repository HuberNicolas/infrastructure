variable "hcloud_token" {
  description = "Hetzner Cloud API token (read/write) of the project the server lives in."
  type        = string
  sensitive   = true
}

variable "name" {
  description = "Name of the server and prefix of all related resources."
  type        = string
  default     = "apps"
}

variable "server_type" {
  description = "Hetzner server type. cx33 = 4 vCPU, 8 GB RAM, 80 GB disk. Scale up to cx43 (16 GB) if memory gets tight."
  type        = string
  default     = "cx33"
}

variable "location" {
  description = "Hetzner location: nbg1 (Nuremberg), fsn1 (Falkenstein) or hel1 (Helsinki)."
  type        = string
  default     = "nbg1"
}

variable "image" {
  description = "Operating system image."
  type        = string
  default     = "ubuntu-24.04"
}

variable "ssh_public_key_path" {
  description = "Public key that may log in as root. Coolify also manages the server over SSH as root."
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "admin_cidrs" {
  description = "Networks allowed to reach SSH (22) and, during setup, the Coolify dashboard (8000)."
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}

variable "coolify_setup_port_open" {
  description = "Open port 8000 for the first Coolify login. Set to false once the dashboard has its own domain."
  type        = bool
  default     = true
}

variable "backups" {
  description = "Hetzner daily backups (7 kept, +20 % of the server price)."
  type        = bool
  default     = true
}

variable "protected" {
  description = "Protect the server against accidental deletion and rebuild."
  type        = bool
  default     = true
}
