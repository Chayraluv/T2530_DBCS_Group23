# Public
resource "aws_subnet" "public_1a" {
  vpc_id            = aws_vpc.mmu_vpc.id
  cidr_block        = "10.0.0.0/24"
  availability_zone = "us-east-1a"
  tags = { Name = "MMU-VPC-subnet-public1-us-east-1a" }
}

resource "aws_subnet" "public_1b" {
  vpc_id            = aws_vpc.mmu_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1b"
  tags = { Name = "MMU-VPC-subnet-public2-us-east-1b" }
}

# Private App
resource "aws_subnet" "private_1a" {
  vpc_id            = aws_vpc.mmu_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "private_1b" {
  vpc_id            = aws_vpc.mmu_vpc.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "us-east-1b"
}

# Private DB
resource "aws_subnet" "db_a" {
  vpc_id            = aws_vpc.mmu_vpc.id
  cidr_block        = "10.0.4.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "db_b" {
  vpc_id            = aws_vpc.mmu_vpc.id
  cidr_block        = "10.0.5.0/24"
  availability_zone = "us-east-1b"
}
