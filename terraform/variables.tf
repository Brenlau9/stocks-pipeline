variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "table_name" {
  type    = string
  default = "daily-stock-movers"
}

variable "massive_api_key" {
  type      = string
  sensitive = true
}