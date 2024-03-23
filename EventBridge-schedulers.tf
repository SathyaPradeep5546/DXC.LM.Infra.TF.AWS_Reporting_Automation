#AWS-Health_Events-Lambda-scheduler
resource "aws_scheduler_schedule" "AWS-Health_Events-Lambda" {
  count  = var.cdeploycentralonly == true ? 1 : 0
  name       = "EB-RULE-AWS-Health_Events-Lambda"
  group_name = "default"
  state = "ENABLED"
  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(00 9 1 * ? *)"

  target {
    arn      = aws_lambda_function.aws-health-events-lambda[0].arn
    role_arn = aws_iam_role.Reporting_Automation_Scheduler_role[0].arn
  }
}

#aws-services_inventory-lambda-scheduler
resource "aws_scheduler_schedule" "aws-services_inventory-lambda" {
  count  = var.cdeploycentralonly == true ? 1 : 0
  name       = "EB-RULE-AWS-services_inventory-lambda"
  group_name = "default"
  state = "ENABLED"
  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(00 9 1 * ? *)"

  target {
    arn      = aws_lambda_function.aws-services-inventory-lambda[0].arn
    role_arn = aws_iam_role.Reporting_Automation_Scheduler_role[0].arn
  }
}

#AWS Support cases lambda scheduler
resource "aws_scheduler_schedule" "aws-support_cases-lambda" {
  count  = var.cdeploycentralonly == true ? 1 : 0
  name       = "EB-RULE-AWS-support-cases-lambda"
  group_name = "default"
  state = "ENABLED"
  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(00 9 1 * ? *)"

  target {
    arn      = aws_lambda_function.aws-support-cases-lambda[0].arn
    role_arn = aws_iam_role.Reporting_Automation_Scheduler_role[0].arn
  }
}

#EC2 Inventory lambda scheduler
resource "aws_scheduler_schedule" "AWS_ec2-inventory-lambda" {
  count  = var.cdeploycentralonly == true ? 1 : 0
  name       = "EB-RULE-AWS-EC2-inventory-lambda"
  group_name = "default"
  state = "ENABLED"
  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(30 6 ? * MON *)"

  target {
    arn      = aws_lambda_function.ec2-inventory-lambda[0].arn
    role_arn = aws_iam_role.Reporting_Automation_Scheduler_role[0].arn
  }
}

#AWS-host-retirement-lambda
resource "aws_scheduler_schedule" "AWS_host-retirement-lambda" {
  count  = var.cdeploycentralonly == true ? 1 : 0
  name       = "EB-RULE-AWS-Host-retirement-lambda"
  group_name = "default"
  state = "ENABLED"
  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(00 9 1 * ? *)"

  target {
    arn      = aws_lambda_function.host-retirement-lambda[0].arn
    role_arn = aws_iam_role.Reporting_Automation_Scheduler_role[0].arn
  }
}

#Patch scan lambda scheduler
resource "aws_scheduler_schedule" "AWS_Patch-scan-report-lambda" {
  count  = var.cdeploycentralonly == true ? 1 : 0
  name       = "EB-RULE-AWS-Patch-scan-report-lambda"
  group_name = "default"
  state = "ENABLED"
  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(30 13 ? * 5,6 *)"

  target {
    arn      = aws_lambda_function.patch-scan-report-lambda[0].arn
    role_arn = aws_iam_role.Reporting_Automation_Scheduler_role[0].arn
  }
}