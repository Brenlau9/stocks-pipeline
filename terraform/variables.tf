variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "table_name" {
  type    = string
  default = "daily-stock-movers"
}

variable "massive_api_key_parameter_name" {
  type    = string
  default = "/stocks-pipeline/massive-api-key"
}

variable "frontend_bucket_name_prefix" {
  type    = string
  default = "stocks-pipeline-frontend"
}
