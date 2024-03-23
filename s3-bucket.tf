#S3 Bucket for reporting automation
resource "aws_s3_bucket" "s3-bucket-reporting-automation" {
  count  = var.cdeploycentralonly == true ? 1 : 0
  bucket = "lm-cloudops-aws-reporting-automation-bucket"
  tags = {
    Name         = "lm-cloudops-reporting-automation-bucket"
    Description  = "Bucket to store AWS Rporting Automation Reports"
    map-migrated = "mig37922"
    Environment  = "001"
    OwnedBy      = "CPS"
    IaCTool      = "terraform"
    Region       = var.region
    Owner        = "CPS"
    Project      = "TROK"
    Application  = "LM-AWS-Reporting-Automation"
    Backup       = "False"
  }
}
resource "aws_s3_bucket_versioning" "ec2_checklist_s3_bucket_versioning" {
  count  = var.cdeploycentralonly == true ? 1 : 0
  bucket = aws_s3_bucket.s3-bucket-reporting-automation[0].id
  versioning_configuration {
    status = "Disabled"
  }
}
resource "aws_s3_bucket_public_access_block" "s3-bucket-reporting-automation_bucket_access" {
  count  = var.cdeploycentralonly == true ? 1 : 0
  bucket                  = aws_s3_bucket.s3-bucket-reporting-automation[0].id
  block_public_acls       = true
  block_public_policy     = true
  restrict_public_buckets = true
  ignore_public_acls      = true
}

# S3 Bucket policy for reporting automation
resource "aws_s3_bucket_policy" "s3-bucket-reporting-automation_bucket_policy" {
  count  = var.cdeploycentralonly == true ? 1 : 0
  bucket = aws_s3_bucket.s3-bucket-reporting-automation[0].id
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "Statement",
        "Effect" : "Allow",
        "Principal" : {
          "AWS" : "arn:aws:iam::${var.account_no}:role/IAMR-AUTODEPLOY-LAMBDA-SVC-REPORTING-AUTOMATION-LM"
        },
        "Action" : [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:PutObjectTagging",
          "s3:PutObjectVersionAcl",
          "s3:PutObjectVersionTagging",
          "s3:GetObject",
          "s3:ListBucket"
        ],
        "Resource" : ["arn:aws:s3:::lm-cloudops-aws-reporting-automation-bucket/*", "arn:aws:s3:::lm-cloudops-aws-reporting-automation-bucket"]
      }
    ]
  })

}