module "vpc" {
  source = "git::https://example.com/infra-modules.git//modules/vpc-base?ref=v1.0.0"

  name                = "billing"
  cidr_block          = "10.20.0.0/16"
  public_subnet_cidrs = ["10.20.1.0/24", "10.20.2.0/24"]
  availability_zones  = ["us-east-1a", "us-east-1b"]
}

module "web_sg" {
  source = "git::https://example.com/infra-modules.git//modules/security-group-web?ref=v1.0.0"

  name   = "billing"
  vpc_id = module.vpc.vpc_id
}

module "billing_db" {
  source = "git::https://example.com/infra-modules.git//modules/rds-postgres?ref=v1.0.0"

  name                = "billing-db"
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.public_subnet_ids
  allowed_cidr_blocks = ["10.20.0.0/16"]
  username            = var.db_username
  password            = var.db_password
}
