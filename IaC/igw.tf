resource "aws_internet_gateway" "mmu_igw" {
  vpc_id = aws_vpc.mmu_vpc.id
  tags = { Name = "MMU-VPC-igw" }
}
