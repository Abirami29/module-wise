module "vpc" {
  source = "git::https://example.com/infra-modules.git//modules/vpc-base?ref=v2.0.0"

  name                 = "webshop"
  cidr_block           = "10.10.0.0/16"
  public_subnet_cidrs  = ["10.10.1.0/24", "10.10.2.0/24"]
  availability_zones   = ["us-east-1a", "us-east-1b"]
}

module "web_sg" {
  source = "git::https://example.com/infra-modules.git//modules/security-group-web?ref=v1.0.0"

  name   = "webshop"
  vpc_id = module.vpc.vpc_id
}

module "assets_bucket" {
  source = "git::https://example.com/infra-modules.git//modules/s3-bucket-standard?ref=v1.0.0"

  bucket_name = "webshop-assets-prod"
  environment = "prod"
}

module "webshop_service" {
  source = "git::https://example.com/infra-modules.git//modules/ecs-service?ref=v1.2.0"

  service_name    = "webshop"
  cluster_id      = var.ecs_cluster_id
  container_image = var.container_image
  subnet_ids      = module.vpc.public_subnet_ids
  security_group_ids = [module.web_sg.security_group_id]
}
