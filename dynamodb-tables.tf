#==================================================
#===========Reporting-role-dynamodb-table==========
#==================================================

resource "aws_dynamodb_table" "member-role-dynamodb-table" {
  count          = var.cdeploycentralonly == true ? 1 : 0
  name           = "lm-dxc-reporting-role-dynamodb-table"
  billing_mode   = "PROVISIONED"
  hash_key       = "S No."
  read_capacity  = 1
  write_capacity = 1

  attribute {
    name = "S No."
    type = "N"
  }

  tags = {
    Name        = "lm-dxc-reporting-role-dynamodb-table"
    Description = "Used to store member accounts reporting read only role ARNs"
    Backup      = "True"
  }
}

#==================================================
#===========EC2-inventory-dynamodb-table===========
#==================================================

resource "aws_dynamodb_table" "ec2-inventory-dynamodb-table" {
  count          = var.cdeploycentralonly == true ? 1 : 0
  name           = "lm-dxc-ec2-inventory-dynamodb-table"
  billing_mode   = "PROVISIONED"
  hash_key       = "InstanceID"
  read_capacity  = 1
  write_capacity = 1

  attribute {
    name = "InstanceID"
    type = "S"
  }

  tags = {
    Name        = "lm-dxc-reporting-role-dynamodb-table"
    Description = "Used to store EC2 inventory information"
    Backup      = "True"
  }
}

#==========================================================
#===========AWS-Services-inventory-dynamodb-table==========
#==========================================================

resource "aws_dynamodb_table" "aws-services-inventory-dynamodb-table" {
  count          = var.cdeploycentralonly == true ? 1 : 0
  name           = "lm-dxc-aws-services-inventory-dynamodb-table"
  billing_mode   = "PROVISIONED"
  hash_key       = "S No."
  read_capacity  = 1
  write_capacity = 1

  attribute {
    name = "S No."
    type = "S"
  }

  tags = {
    Name        = "lm-dxc-reporting-role-dynamodb-table"
    Description = "Used to store count of aws services inventory"
    Backup      = "True"
  }
}