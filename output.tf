output "member-reporting-role-arn" {
  value = [for role_key, role in aws_iam_role.Member_Reporting_Role : role.arn]
}
