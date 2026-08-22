variable "queue_name" {
  type = string
}
variable "visibility_timeout" {
  type    = number
  default = 30
}
variable "message_retention_seconds" {
  type    = number
  default = 345600
}
variable "enable_dlq" {
  type    = bool
  default = true
}
