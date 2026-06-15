resource "aws_dynamodb_table" "daily_stock_movers" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "date"

  attribute {
    name = "date"
    type = "S"
  }

  tags = {
    Project = "stocks-pipeline"
  }
}