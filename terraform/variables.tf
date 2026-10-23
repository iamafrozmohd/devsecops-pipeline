variable "project" {
  description = "Short project name used in resource names."
  type        = string
  default     = "hashapi"
}

variable "environment" {
  description = "Deployment environment (dev, test, prod)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test or prod."
  }
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "eastus"
}

variable "storage_account_name" {
  description = "Globally unique storage account name (3-24 lowercase letters and numbers)."
  type        = string
  default     = "sthashapireportsdev01"

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "storage_account_name must be 3-24 lowercase letters and numbers."
  }
}
