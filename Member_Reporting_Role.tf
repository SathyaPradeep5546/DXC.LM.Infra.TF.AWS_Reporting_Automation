resource "aws_iam_role" "Member_Reporting_Role" {
  for_each = var.Member_Reporting_Role == true ? toset(["true"]) : toset([])
  name     = "IAMR-AUTODEPLOY-MEMBER-REPORTING-ROLE-LM"
  tags     = var.Member_Reporting_Role_tags
  assume_role_policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Sid" : "Statement1",
          "Effect" : "Allow",
          "Principal" : {
            "AWS" : "arn:aws:iam::${var.account_no}:root"
          },
          "Action" : ["sts:AssumeRole"],
          "Condition" : {}
        }
      ]
  })
}
resource "aws_iam_role_policy_attachment" "Member_Reporting_Role_ReadOnlyAccess" {
  for_each   = aws_iam_role.Member_Reporting_Role
  role       = each.value.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}
