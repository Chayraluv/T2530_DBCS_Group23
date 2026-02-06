output "alb_dns_name" {
  value = aws_lb.mmu_alb.dns_name
}

output "web_public_ip" {
  value = aws_instance.web_server.public_ip
}
