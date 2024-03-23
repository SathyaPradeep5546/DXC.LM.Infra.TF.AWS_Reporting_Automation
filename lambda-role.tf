resource "aws_iam_role" "Reporting_Automation_Lambda_role" {
  count              = var.cdeploycentralonly == true ? 1 : 0
  name               = "IAMR-AUTODEPLOY-LAMBDA-SVC-REPORTING-AUTOMATION-LM"
  tags               = var.Reporting_Lambda_Role_tags
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LambdaAssume",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_execution_policy" {
  count      = var.cdeploycentralonly == true ? 1 : 0
  role       = aws_iam_role.Reporting_Automation_Lambda_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_read_only_policy" {
  count      = var.cdeploycentralonly == true ? 1 : 0
  role       = aws_iam_role.Reporting_Automation_Lambda_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

resource "aws_iam_policy" "lambda_cloudops_policy" {
  count = var.cdeploycentralonly == true ? 1 : 0
  name  = "lambda_cloudops_policy"
  policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Sid" : "DDActions",
          "Effect" : "Allow",
          "Action" : [
            "dynamodb:ListTables",
            "dynamodb:DescribeContributorInsights",
            "dynamodb:ListTagsOfResource",
            "dynamodb:DescribeReservedCapacityOfferings",
            "dynamodb:PartiQLSelect",
            "dynamodb:DescribeTable",
            "dynamodb:GetItem",
            "dynamodb:DescribeContinuousBackups",
            "dynamodb:DescribeExport",
            "dynamodb:DescribeKinesisStreamingDestination",
            "dynamodb:ListExports",
            "dynamodb:DescribeLimits",
            "dynamodb:BatchGetItem",
            "dynamodb:ConditionCheckItem",
            "dynamodb:PutItem",
            "dynamodb:ListBackups",
            "dynamodb:Scan",
            "dynamodb:Query",
            "dynamodb:DescribeStream",
            "dynamodb:UpdateItem",
            "dynamodb:DescribeTimeToLive",
            "dynamodb:ListStreams",
            "dynamodb:CreateTable",
            "dynamodb:ListContributorInsights",
            "dynamodb:DescribeGlobalTableSettings",
            "dynamodb:ListGlobalTables",
            "dynamodb:GetShardIterator",
            "dynamodb:DescribeGlobalTable",
            "dynamodb:DescribeReservedCapacity",
            "dynamodb:DescribeBackup",
            "dynamodb:UpdateTable",
            "dynamodb:GetRecords",
            "dynamodb:DescribeTableReplicaAutoScaling"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "s3Actions",
          "Effect" : "Allow",
          "Action" : [
            "s3:PutObject",
            "s3:GetObject"
          ],
          "Resource" : [
            "${aws_s3_bucket.s3-bucket-reporting-automation[0].arn}",
            "${aws_s3_bucket.s3-bucket-reporting-automation[0].arn}/*"
          ]
        },
        {
          "Sid" : "SESActions",
          "Effect" : "Allow",
          "Action" : [
            "ses:SendRawEmail",
            "ses:SendEmail",
            "ses:VerifyEmailAddress"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "ReadOnlyAssumeRole",
          "Effect" : "Allow",
          "Action" : "sts:AssumeRole",
          "Resource" : "*"
        }
      ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_cloudops_policy-attachment" {
  count      = var.cdeploycentralonly == true ? 1 : 0
  role       = aws_iam_role.Reporting_Automation_Lambda_role[0].name
  policy_arn = aws_iam_policy.lambda_cloudops_policy[0].arn
}