resource "aws_lb_target_group" "mmu_library_tg" {
  name     = "MMU-Library"
  port     = 5000
  protocol = "HTTP"
  vpc_id  = aws_vpc.mmu_vpc.id
  target_type = "instance"

  health_check {
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 5
    unhealthy_threshold = 2
    matcher             = "200"
  }

  tags = {
    Name = "MMU-Library"
  }
}

resource "aws_lb_target_group_attachment" "ec2_attach" {
  target_group_arn = aws_lb_target_group.mmu_library_tg.arn
  target_id        = aws_instance.web_server.id
  port             = 5000
}
