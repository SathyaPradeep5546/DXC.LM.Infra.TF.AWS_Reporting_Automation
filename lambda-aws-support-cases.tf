###Create a ZIP file because  `aws_lambda_function` needs the code to be stored in a ZIP file in order to upload to AWS.

data "archive_file" "zip_the_python_code_aws_support_case" {
type        = "zip"
source_file  = "${path.module}/Python-Scripts/aws-support-cases.py"
output_path = "${path.module}/Python-Scripts/Python-Scripts-Archives/aws-support-cases.zip"
}

###################################################################################
# Creating AWS Lamda Function for Central AWS Support case Reports

resource "aws_lambda_function" "aws-support-cases-lambda" {
  count              = var.cdeploycentralonly == true ? 1 : 0
  source_code_hash = data.archive_file.zip_the_python_code_aws_support_case.output_base64sha256
  description = "Function to create central AWS Support Case Reports"
  filename      = "${path.module}/Python-Scripts/Python-Scripts-Archives/aws-support-cases.zip" 
  function_name = "LF-CENTRAL-AWS-SUPPORT-CASES-SVC-LM"
  role          = aws_iam_role.Reporting_Automation_Lambda_role[count.index].arn
  handler       = "aws-support-cases.lambda_handler"
  memory_size = 300
  timeout = 900
  runtime = "python3.10"
  tags = merge(
    {map-migrated = null},
    var.aws_support_cases_lambda_tags
  )
  
  # ===========NOTE --- NOTE ---- NOTE===================
  # This Layer is compulsory for this lambda to function. And it is from open source. 
  # If there is a need to upgrade the Python runtime, please locate the corresponding ARNs for the "PANDAS" and "NUMPY" layers in the provided link based on the desired runtime upgrade.
  # https://github.com/keithrozario/Klayers?tab=readme-ov-file#list-of-arns
  layers = [
    "arn:aws:lambda:eu-west-2:770693421928:layer:Klayers-p310-pandas:9",
    "arn:aws:lambda:eu-west-2:770693421928:layer:Klayers-p310-numpy:6",
    ]

  environment {
    variables = {
    #   RECIPIENT_LIST = "csathya.pradeep@dxc.com"
    #   SENDER_LIST = "csathya.pradeep@dxc.com"
    #   REPORTING_AUTOMATION_BUCKET = "lm-cloudops-reporting-automation-bucket"
    #   MEMBER_ROLE_TABLE = "dxc_report_readonly_all_roles"
    #   EC2_INVENTORY_DYNAMODB_TABLE = "lm-dxc-ec2-inventory-dynamodb-table"
      RECIPIENT_LIST = "${aws_ses_email_identity.CloudOps_email_identity[0].email}"
      SENDER_LIST = var.sender_email
      REPORTING_AUTOMATION_BUCKET = "${aws_s3_bucket.s3-bucket-reporting-automation[0].id}"
      MEMBER_ROLE_TABLE = "${aws_dynamodb_table.member-role-dynamodb-table[0].name}"
    }
  }
}