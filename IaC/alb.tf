resource "aws_lb" "mmu_alb" {
  name               = "MMU-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.elb_sg.id]

  subnets = [
    aws_subnet.public_1a.id,
    aws_subnet.public_1b.id
  ]

  tags = {
    Name = "MMU-alb"
  }
}
