module "vpc" {
  source = "git::https://example.com/infra-modules.git//modules/vpc-base?ref=v2.0.0"

  name                = "analytics"
  cidr_block          = "10.30.0.0/16"
  public_subnet_cidrs = ["10.30.1.0/24", "10.30.2.0/24"]
  availability_zones  = ["us-east-1a", "us-east-1b"]
  enable_flow_logs    = true
}

module "logs_bucket" {
  source = "git::https://example.com/infra-modules.git//modules/s3-bucket-logging?ref=v1.0.0"

  bucket_name    = "analytics-event-logs"
  environment    = "prod"
  retention_days = 180
}

module "event_processor" {
  source = "git::https://example.com/infra-modules.git//modules/lambda-function?ref=v1.0.0"

  function_name = "analytics-event-processor"
  package_path  = "./build/event_processor.zip"
  runtime       = "python3.12"
  memory_size   = 256
}
