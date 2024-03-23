#==================================================================================
#===========CloudOps PDL as SES identity for notification purpose only=============
#==================================================================================

resource "aws_ses_email_identity" "CloudOps_email_identity" {
  count = var.cdeploycentralonly == true ? 1 : 0
  email = "csathya.pradeep@dxc.com"
}