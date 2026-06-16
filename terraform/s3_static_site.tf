data "aws_caller_identity" "current" {}

locals {
  frontend_bucket_name = "${var.frontend_bucket_name_prefix}-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
}

resource "aws_s3_bucket" "frontend_site" {
  bucket = local.frontend_bucket_name

  tags = {
    Project = "stocks-pipeline"
  }
}

resource "aws_s3_bucket_ownership_controls" "frontend_site" {
  bucket = aws_s3_bucket.frontend_site.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend_site" {
  bucket = aws_s3_bucket.frontend_site.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "frontend_site" {
  bucket = aws_s3_bucket.frontend_site.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_policy" "frontend_site_public_read" {
  bucket = aws_s3_bucket.frontend_site.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadStaticWebsiteObjects"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend_site.arn}/*"
      }
    ]
  })

  depends_on = [
    aws_s3_bucket_public_access_block.frontend_site
  ]
}
