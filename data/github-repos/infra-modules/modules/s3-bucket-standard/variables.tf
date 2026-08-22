variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "environment" {
  description = "Environment tag (dev/staging/prod)"
  type        = string
}

variable "versioning_enabled" {
  description = "Whether to enable bucket versioning"
  type        = bool
  default     = true
}
