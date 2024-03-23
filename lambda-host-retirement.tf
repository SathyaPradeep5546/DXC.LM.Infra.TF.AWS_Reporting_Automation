###Create a ZIP file because  `aws_lambda_function` needs the code to be stored in a ZIP file in order to upload to AWS.

data "archive_file" "zip_the_python_code_host_retirement" {
type        = "zip"
source_file  = "${path.module}/Python-Scripts/host-retirement.py"
output_path = "${path.module}/Python-Scripts/Python-Scripts-Archives/host-retirement.zip"
}

###################################################################################
# Creating AWS Lamda Function for EC2 Health Events (HOST RETIREMENTS) Reports

resource "aws_lambda_function" "host-retirement-lambda" {
  count              = var.cdeploycentralonly == true ? 1 : 0
  source_code_hash = data.archive_file.zip_the_python_code_host_retirement.output_base64sha256
  description = "Function to create central EC2 Health Events (HOST RETIREMENTS) Reports"
  filename      = "${path.module}/Python-Scripts/Python-Scripts-Archives/host-retirement.zip" 
  function_name = "LF-CENTRAL-EC2-HOST-RETIREMENT-SVC-LM"
  role          = aws_iam_role.Reporting_Automation_Lambda_role[count.index].arn
  handler       = "host-retirement.lambda_handler"
  memory_size = 300
  timeout = 900
  runtime = "python3.10"
  tags = merge(
    {map-migrated = null},
    var.host_retirement_lambda_tags
  )

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