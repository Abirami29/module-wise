variable "bucket_name" {
  description = "Name of the logging S3 bucket"
  type        = string
}

variable "environment" {
  description = "Environment tag (dev/staging/prod)"
  type        = string
}

variable "retention_days" {
  description = "Number of days to retain logs before expiry"
  type        = number
  default     = 90
}
