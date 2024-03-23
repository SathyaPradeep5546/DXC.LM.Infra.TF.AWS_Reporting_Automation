# For complete list of options see https://github.com/terraform-linters/tflint/blob/master/docs/user-guide/config.md

# AWS-specific rules. 
# See https://github.com/terraform-linters/tflint-ruleset-aws
plugin "aws" {
    enabled = true
    version = "0.15.0"
    source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

# Naming conventions

rule "terraform_naming_convention" {
  enabled = true
}

# Version constraints

rule "terraform_required_providers" {
  enabled = true
}

# Unused resources

rule "terraform_unused_declarations" {
  enabled = true
}

rule "terraform_unused_required_providers" {
  enabled = true
}

# Documentation constraints

rule "terraform_documented_outputs" {
  enabled = true
}

rule "terraform_documented_variables" {
  enabled = true
}

# Deprecated syntax checks

rule "terraform_deprecated_index" {
  enabled = true
}