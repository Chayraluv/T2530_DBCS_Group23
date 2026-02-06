resource "aws_instance" "web_server" {
  ami           = "ami-0532be0f126a3de55"
  instance_type = "t2.medium"
  key_name      = "library_key"

  subnet_id = aws_subnet.public_1a.id
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]

  tags = {
    Name = "Library Web Server"
  }
}
