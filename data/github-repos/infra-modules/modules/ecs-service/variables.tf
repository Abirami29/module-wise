variable "service_name" {
  type = string
}
variable "cluster_id" {
  type = string
}
variable "container_image" {
  type = string
}
variable "container_port" {
  type    = number
  default = 8080
}
variable "cpu" {
  type    = number
  default = 256
}
variable "memory" {
  type    = number
  default = 512
}
variable "desired_count" {
  type    = number
  default = 2 # bumped default replica count
}
variable "subnet_ids" {
  type = list(string)
}
variable "security_group_ids" {
  type = list(string)
}
