terraform {
  backend "s3" {}
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      TF_Managed = "True"
    }
  }
}

# Any remote state data blocks here
# data "terraform_remote_state" "noc" {
#   backend = "s3"
#
#   config = {
#     bucket         = var.noc_bucket
#     key            = var.noc_key
#     region         = "eu-west-2"
#     dynamodb_table = var.noc_dynamodb_table
#     encrypt        = true
#   }
# }