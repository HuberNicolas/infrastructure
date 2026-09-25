terraform {
  required_version = ">= 1.8"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.60"
    }
  }

  # State stays local (gitignored) for a single server. To share it or run it from CI, switch to an S3 backend on
  # Hetzner Object Storage: https://opentofu.org/docs/language/settings/backends/s3/
}

provider "hcloud" {
  token = var.hcloud_token
}
