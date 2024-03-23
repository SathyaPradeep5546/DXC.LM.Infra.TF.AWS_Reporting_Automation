# All variables that defined here that are passed in via TF Vars or can be defined here if they apply to all environments

# Example var passed in from TFVARS
# variable "env_id" {}

# Example var that applies to all environments
# variable "aws_ranges" {
#   description = "AWS CIDR Ranges"
#   default = ["13.248.0.0/16", "15.177.0.0/16", "15.193.0.0/16", "150.222.0.0/16", "18.130.0.0/16", "18.132.0.0/14", "18.175.0.0/16", "3.8.0.0/14", "3.8.168.0/23", "35.176.0.0/15", "35.178.0.0/15", "52.144.128.0/17", "52.56.0.0/16", "52.92.0.0/14", "54.239.0.0/16", "64.252.64.0/18", "64.252.128.0/18", "99.77.0.0/16", "99.82.0.0/16", "52.46.128.0/19"]
# }

variable "region" {
  type        = string
  description = "Region for AWS Resources"
  default     = "eu-west-2"
}

variable "account_no" {
  type    = string
  description = "Central Management Account Number"
  default = "756838015244"
  #046855091061 
}

variable "cdeploycentralonly" {
  type    = bool
  default = false
}

variable "Member_Reporting_Role" {
  type    = bool
  default = false
}

variable "Member_Reporting_Role_tags" {
  type        = map(any)
  description = "Tags used in IAMRole for Member_reporting_role"
  default     = {}
}

variable "Reporting_Lambda_Role_tags" {
  type        = map(any)
  description = "Tags used in IAMRole for Reporting_Automation_Lambda_role"
  default     = {}
}

variable "Reporting_Scheduler_tags"{
  type        = map(any)
  description = "Tags used in IAMRole for Reporting_Automation_Scheduler_role"
  default     = {} 
}

variable "ec2_inventory_lambda_tags" {
  type        = map(any)
  description = "Tags used in Lambda for EC2 Inventory"
  default     = {}  
}

variable "aws_services_inventory_lambda_tags" {
  type        = map(any)
  description = "Tags used in Lambda for AWS Services Inventory"
  default     = {}  
}

variable "patch-scan-report_lambda_tags" {
  type        = map(any)
  description = "Tags used in Lambda for patch scan report"
  default     = {}  
}

variable "aws_health_events_lambda_tags" {
  type        = map(any)
  description = "Tags used in Lambda for aws_health_events_lambda_tags"
  default     = {}  
}

variable "host_retirement_lambda_tags" {
  type        = map(any)
  description = "Tags used in Lambda for host_retirement_lambda_tags"
  default     = {}  
}

variable "aws_support_cases_lambda_tags" {
  type        = map(any)
  description = "Tags used in Lambda for aws-support-cases"
  default     = {}    
}

variable "sender_email" {
  type        = string
  description = "The email address that will be shown as the sender of the alerts."
  default     = "csathya.pradeep@dxc.com"
}