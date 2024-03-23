Member_Reporting_Role = true

#Member_Role_tag
Member_Reporting_Role_tags ={
      Name = "IAMR-AUTODEPLOY-MEMBER-REPORTING-ROLE-LM"
      Description = "IAM-Role-that-is-responsible-for-member-reporting-role"
      OwnedBy = "LM AWS CloudOps Team"
      Backup = "False"
      IaCTool = "Terraform"
      Region = "eu-west-2"
      Environment = "001"
      Owner = "LM AWS CloudOps Team"
      Project = "TROK"
      Application = "LM-AWS-Reporting-Automation"
      TF_Managed = "True"
      TF_Repo = "DXC.LM.Infra.TF.AWS_Reporting_Automation"
  }

#Variable for reporting lambdas deployment in central management account
cdeploycentralonly = true

#Lambda_Role_tag
Reporting_Lambda_Role_tags ={
      Name = "IAMR-AUTODEPLOY-LAMBDA-SVC-REPORTING-AUTOMATION-LM"
      Description = "IAM-Role-that-is-responsible-for-reporting-lambda"
      OwnedBy = "LM AWS CloudOps Team"
      Backup = "False"
      IaCTool = "Terraform"
      Region = "eu-west-2"
      Environment = "001"
      Owner = "LM AWS CloudOps Team"
      Project = "TROK"
      Application = "LM-AWS-Reporting-Automation"
      TF_Managed = "True"
      TF_Repo = "DXC.LM.Infra.TF.AWS_Reporting_Automation"
  }

#LAMBDA_EC2_Inventory_tag
ec2_inventory_lambda_tags = {
      Name = "LF-CENTRAL-REPORTING-EC2-INVENTORY-SVC-LM"
      Description = "ec2_inventory_lambda"
      OwnedBy = "LM AWS CloudOps Team"
      Backup = "False"
      IaCTool = "Terraform"
      Region = "eu-west-2"
      Environment = "001"
      Owner = "LM AWS CloudOps Team"
      Project = "TROK" 
      Application = "LM-AWS-Reporting-Automation"
      map-migrated = "mig37922"
      TF_Managed = "True"
      TF_Repo = "DXC.LM.Infra.TF.AWS_Reporting_Automation"
  }

#LAMBDA_AWS_Services_Inventory_tag
aws_services_inventory_lambda_tags = {
      Name = "LF-CENTRAL-REPORTING-AWS-SERVICES-INVENTORY-SVC-LM"
      Description = "aws_services_inventory_lambda"
      OwnedBy = "LM AWS CloudOps Team"
      Backup = "False"
      IaCTool = "Terraform"
      Region = "eu-west-2"
      Environment = "001"
      Owner = "LM AWS CloudOps Team"
      Project = "TROK" 
      Application = "LM-AWS-Reporting-Automation"
      map-migrated = "mig37922"
      TF_Managed = "True"
      TF_Repo = "DXC.LM.Infra.TF.AWS_Reporting_Automation"
}

#LAMBDA_patch-scan-report_lambda_tags
patch-scan-report_lambda_tags = {
      Name = "LF-CENTRAL-REPORTING-PATCH-SCAN-REPORT-SVC-LM"
      Description = "patch-scan-report_lambda"
      OwnedBy = "LM AWS CloudOps Team"
      Backup = "False"
      IaCTool = "Terraform"
      Region = "eu-west-2"
      Environment = "001"
      Owner = "LM AWS CloudOps Team"
      Project = "TROK" 
      Application = "LM-AWS-Reporting-Automation"
      map-migrated = "mig37922"  
      TF_Managed = "True"
      TF_Repo = "DXC.LM.Infra.TF.AWS_Reporting_Automation"
}

#LAMBDA_aws_health_events_lambda_tags
aws_health_events_lambda_tags = {
      Name = "LF-CENTRAL-REPORTING-AWS-HEALTH-EVENTS-SVC-LM"
      Description = "aws_health_events_lambda"
      OwnedBy = "LM AWS CloudOps Team"
      Backup = "False"
      IaCTool = "Terraform"
      Region = "eu-west-2"
      Environment = "001"
      Owner = "LM AWS CloudOps Team"
      Project = "TROK" 
      Application = "LM-AWS-Reporting-Automation"
      map-migrated = "mig37922" 
      TF_Managed = "True"
      TF_Repo = "DXC.LM.Infra.TF.AWS_Reporting_Automation"
}

#LAMBDA_host_retirement_lambda_tags
host_retirement_lambda_tags = {
      Name = "LF-CENTRAL-REPORTING-EC2-HOST-RETIREMENT-SVC-LM"
      Description = "host_retirement_lambda"
      OwnedBy = "LM AWS CloudOps Team"
      Backup = "False"
      IaCTool = "Terraform"
      Region = "eu-west-2"
      Environment = "001"
      Owner = "LM AWS CloudOps Team"
      Project = "TROK" 
      Application = "LM-AWS-Reporting-Automation"
      map-migrated = "mig37922" 
      TF_Managed = "True"
      TF_Repo = "DXC.LM.Infra.TF.AWS_Reporting_Automation"
}

#LAMBDA_aws_support_cases_lambda_tags
aws_support_cases_lambda_tags = {
      Name = "LF-CENTRAL-REPORTING-AWS-SUPPORT-CASES-SVC-LM"
      Description = "aws_support_cases_lambda"
      OwnedBy = "LM AWS CloudOps Team"
      Backup = "False"
      IaCTool = "Terraform"
      Region = "eu-west-2"
      Environment = "001"
      Owner = "LM AWS CloudOps Team"
      Project = "TROK" 
      Application = "LM-AWS-Reporting-Automation"
      map-migrated = "mig37922"      
      TF_Managed = "True"
      TF_Repo = "DXC.LM.Infra.TF.AWS_Reporting_Automation"
}

#Scheduler Tags
Reporting_Scheduler_tags = {
      Description = "Event_Bridge_Scheduler_used_for_AWS_Reporting_Solution_Lambda_only"
      OwnedBy = "LM AWS CloudOps Team"
      Backup = "False"
      IaCTool = "Terraform"
      Region = "eu-west-2"
      Environment = "001"
      Owner = "LM AWS CloudOps Team"
      Project = "TROK" 
      Application = "LM-AWS-Reporting-Automation"
      map-migrated = "mig37922"      
      TF_Managed = "True"
      TF_Repo = "DXC.LM.Infra.TF.AWS_Reporting_Automation"     
}
