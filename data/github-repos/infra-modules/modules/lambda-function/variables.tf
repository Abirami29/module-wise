variable "function_name" {
  type = string
}
variable "handler" {
  type    = string
  default = "index.handler"
}
variable "runtime" {
  type    = string
  default = "python3.12"
}
variable "package_path" {
  type = string
}
variable "memory_size" {
  type    = number
  default = 128
}
variable "timeout" {
  type    = number
  default = 30
}
