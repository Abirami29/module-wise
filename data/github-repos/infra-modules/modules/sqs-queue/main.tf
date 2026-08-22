resource "aws_sqs_queue" "this" {
  name                       = var.queue_name
  visibility_timeout_seconds = var.visibility_timeout
  message_retention_seconds  = var.message_retention_seconds
}

resource "aws_sqs_queue" "dlq" {
  count = var.enable_dlq ? 1 : 0
  name  = "${var.queue_name}-dlq"
}
