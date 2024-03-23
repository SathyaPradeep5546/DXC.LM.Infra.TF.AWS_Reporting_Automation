resource "aws_iam_role" "Reporting_Automation_Scheduler_role" {
  count              = var.cdeploycentralonly == true ? 1 : 0
  name               = "IAMR-AUTODEPLOY-SCHEDULER-SVC-REPORTING-AUTOMATION-LM"
  tags               = var.Reporting_Scheduler_tags
  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "scheduler.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_scheduler_execution_policy" {
  count      = var.cdeploycentralonly == true ? 1 : 0
  role       = aws_iam_role.Reporting_Automation_Scheduler_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
}

